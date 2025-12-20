"""
Utilities - Helper functions for the textbook processing pipeline
"""

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_structure(structure: Dict) -> Dict:
    """
    Validate and clean up extracted structure
    
    Args:
        structure: Raw structure from AI Studio
    
    Returns:
        Validated and cleaned structure with validation report
    """
    report = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "fixes_applied": []
    }
    
    # Check required fields
    if "book_info" not in structure:
        structure["book_info"] = {"title": "Unknown"}
        report["fixes_applied"].append("Added missing book_info")
    
    if "structure" not in structure:
        structure["structure"] = []
        report["errors"].append("No structure found")
        report["valid"] = False
        return {"structure": structure, "report": report}
    
    # Validate chapters
    chapters = structure.get("structure", [])
    validated_chapters = []
    
    for i, chapter in enumerate(chapters):
        validated_chapter = _validate_chapter(chapter, i + 1, report)
        if validated_chapter:
            validated_chapters.append(validated_chapter)
    
    structure["structure"] = validated_chapters
    
    # Validate page offset
    if "page_offset" in structure:
        offset_info = structure["page_offset"]
        if "detected_offset" not in offset_info:
            offset_info["detected_offset"] = 0
            report["fixes_applied"].append("Set default page offset to 0")
    
    return {"structure": structure, "report": report}


def _validate_chapter(chapter: Dict, index: int, report: Dict) -> Optional[Dict]:
    """Validate a single chapter entry"""
    if not isinstance(chapter, dict):
        report["errors"].append(f"Chapter {index}: Invalid format")
        return None
    
    # Ensure required fields
    if "title" not in chapter:
        chapter["title"] = f"Chapter {index}"
        report["fixes_applied"].append(f"Chapter {index}: Added default title")
    
    if "type" not in chapter:
        chapter["type"] = "chapter"
    
    # Validate page numbers
    if "book_page_start" in chapter:
        page_start = chapter["book_page_start"]
        if not isinstance(page_start, (int, float)):
            try:
                chapter["book_page_start"] = int(re.search(r'\d+', str(page_start)).group())
            except:
                chapter["book_page_start"] = None
                report["warnings"].append(f"Chapter '{chapter['title']}': Invalid page_start")
    
    if "book_page_end" in chapter:
        page_end = chapter["book_page_end"]
        if not isinstance(page_end, (int, float)):
            try:
                chapter["book_page_end"] = int(re.search(r'\d+', str(page_end)).group())
            except:
                chapter["book_page_end"] = None
    
    # Validate topics recursively
    if "topics" in chapter:
        validated_topics = []
        for j, topic in enumerate(chapter.get("topics", [])):
            validated_topic = _validate_topic(topic, f"{index}.{j+1}", report)
            if validated_topic:
                validated_topics.append(validated_topic)
        chapter["topics"] = validated_topics
    
    return chapter


def _validate_topic(topic: Dict, index: str, report: Dict) -> Optional[Dict]:
    """Validate a single topic entry"""
    if not isinstance(topic, dict):
        report["errors"].append(f"Topic {index}: Invalid format")
        return None
    
    # Ensure required fields
    if "title" not in topic:
        topic["title"] = f"Section {index}"
        report["fixes_applied"].append(f"Topic {index}: Added default title")
    
    if "type" not in topic:
        topic["type"] = "section"
    
    # Validate page numbers
    for field in ["book_page_start", "book_page_end"]:
        if field in topic:
            value = topic[field]
            if not isinstance(value, (int, float)):
                try:
                    topic[field] = int(re.search(r'\d+', str(value)).group())
                except:
                    topic[field] = None
    
    # Validate subtopics recursively
    if "subtopics" in topic:
        validated_subtopics = []
        for j, subtopic in enumerate(topic.get("subtopics", [])):
            validated_subtopic = _validate_topic(subtopic, f"{index}.{j+1}", report)
            if validated_subtopic:
                validated_subtopics.append(validated_subtopic)
        topic["subtopics"] = validated_subtopics
    
    return topic


def merge_structures(ai_structure: Dict, pdf_toc: List[Dict], page_offset: int) -> Dict:
    """
    Merge AI-extracted structure with PDF's embedded TOC
    
    Args:
        ai_structure: Structure from AI Studio
        pdf_toc: TOC from PyMuPDF
        page_offset: Detected page offset
    
    Returns:
        Merged and validated structure
    """
    if not pdf_toc:
        return ai_structure
    
    # Build lookup from PDF TOC
    toc_lookup = {}
    for entry in pdf_toc:
        title_clean = entry["title"].lower().strip()
        toc_lookup[title_clean] = entry["pdf_page"]
    
    # Cross-reference AI structure with PDF TOC
    def update_pages(item: Dict) -> Dict:
        title = item.get("title", "").lower().strip()
        
        if title in toc_lookup:
            pdf_page = toc_lookup[title]
            # Calculate book page from PDF page
            book_page = pdf_page - page_offset
            
            if "book_page_start" not in item or item["book_page_start"] is None:
                item["book_page_start"] = book_page
            
            item["_pdf_toc_page"] = pdf_page  # For reference
        
        # Process nested items
        for key in ["topics", "subtopics"]:
            if key in item:
                item[key] = [update_pages(sub) for sub in item[key]]
        
        return item
    
    # Update structure
    for chapter in ai_structure.get("structure", []):
        update_pages(chapter)
    
    return ai_structure


def estimate_page_offset_from_toc(pdf_toc: List[Dict], sample_pages: Dict[int, str]) -> int:
    """
    Estimate page offset by comparing TOC entries with page content
    
    Args:
        pdf_toc: Embedded TOC from PDF
        sample_pages: Dict mapping PDF page numbers to text content
    
    Returns:
        Estimated page offset
    """
    offsets = []
    
    for entry in pdf_toc[:10]:  # Check first 10 TOC entries
        title = entry["title"]
        pdf_page = entry["pdf_page"]
        
        # Look for title in sample pages
        for page_num, text in sample_pages.items():
            if title.lower() in text.lower():
                # Found a match, calculate offset
                offset = pdf_page - page_num
                offsets.append(offset)
                break
    
    if offsets:
        # Return most common offset
        from collections import Counter
        return Counter(offsets).most_common(1)[0][0]
    
    return 0


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a string"""
    # Remove invalid characters
    safe = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    safe = safe.replace(' ', '_')
    # Limit length
    return safe[:100]


def format_json_for_display(data: Dict, max_depth: int = 3) -> str:
    """Format JSON data for display with truncation"""
    def truncate(obj, depth=0):
        if depth >= max_depth:
            if isinstance(obj, dict):
                return "{...}"
            elif isinstance(obj, list):
                return f"[... {len(obj)} items]"
            return obj
        
        if isinstance(obj, dict):
            return {k: truncate(v, depth + 1) for k, v in list(obj.items())[:5]}
        elif isinstance(obj, list):
            return [truncate(item, depth + 1) for item in obj[:3]]
        elif isinstance(obj, str) and len(obj) > 100:
            return obj[:100] + "..."
        return obj
    
    truncated = truncate(data)
    return json.dumps(truncated, indent=2, ensure_ascii=False)


def create_summary_report(content: Dict) -> Dict:
    """Create a summary report from extracted content"""
    report = {
        "book_info": content.get("book_info", {}),
        "statistics": {
            "total_chapters": 0,
            "total_sections": 0,
            "total_subsections": 0,
            "total_content_length": 0,
            "avg_section_length": 0
        },
        "table_of_contents": []
    }
    
    section_lengths = []
    
    def process_chapter(chapter, level=0):
        report["statistics"]["total_chapters"] += 1
        
        toc_entry = {
            "level": level,
            "number": chapter.get("number", ""),
            "title": chapter.get("title", ""),
            "pages": f"{chapter.get('book_page_start', '?')}-{chapter.get('book_page_end', '?')}"
        }
        report["table_of_contents"].append(toc_entry)
        
        for topic in chapter.get("topics", []):
            process_topic(topic, level + 1)
    
    def process_topic(topic, level):
        report["statistics"]["total_sections"] += 1
        
        content_len = len(topic.get("content", ""))
        section_lengths.append(content_len)
        report["statistics"]["total_content_length"] += content_len
        
        toc_entry = {
            "level": level,
            "number": topic.get("number", ""),
            "title": topic.get("title", ""),
            "pages": f"{topic.get('book_page_start', '?')}-{topic.get('book_page_end', '?')}",
            "content_length": content_len
        }
        report["table_of_contents"].append(toc_entry)
        
        for subtopic in topic.get("subtopics", []):
            report["statistics"]["total_subsections"] += 1
            process_topic(subtopic, level + 1)
    
    for chapter in content.get("chapters", []):
        process_chapter(chapter)
    
    if section_lengths:
        report["statistics"]["avg_section_length"] = sum(section_lengths) // len(section_lengths)
    
    return report
