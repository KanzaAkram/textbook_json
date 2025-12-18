"""
Content Extractor - Extracts content from PDF based on structure metadata
Handles multi-column layouts, page offsets, and complex structures
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import re

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts content from PDF based on AI-generated structure metadata"""
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(pdf_path)
        self.total_pages = len(self.doc)
        logger.info(f"ContentExtractor initialized: {self.pdf_path.name} ({self.total_pages} pages)")
    
    def extract_from_structure(self, structure: Dict, page_offset: int = 0) -> Dict:
        """
        Extract content based on AI-generated structure
        
        Args:
            structure: Structure metadata from AI Studio (with book page numbers)
            page_offset: Offset to convert book page -> PDF page
                        (PDF page = book_page + offset)
        
        Returns:
            Dictionary with extracted content
        """
        logger.info(f"Extracting content with page offset: {page_offset}")
        
        # Get layout info
        layout = structure.get("layout", {})
        num_columns = layout.get("columns", 1)
        
        logger.info(f"Layout: {num_columns} column(s)")
        
        # Build result structure
        result = {
            "book_info": structure.get("book_info", {}),
            "page_offset": page_offset,
            "layout": layout,
            "chapters": [],
            "special_sections": {},
            "extraction_stats": {
                "total_chapters": 0,
                "total_topics": 0,
                "total_subtopics": 0,
                "extraction_errors": []
            }
        }
        
        # Process each chapter
        for chapter in structure.get("structure", []):
            try:
                extracted_chapter = self._extract_chapter(chapter, page_offset, num_columns)
                result["chapters"].append(extracted_chapter)
                result["extraction_stats"]["total_chapters"] += 1
                
                # Count topics
                for topic in extracted_chapter.get("topics", []):
                    result["extraction_stats"]["total_topics"] += 1
                    result["extraction_stats"]["total_subtopics"] += len(topic.get("subtopics", []))
                    
            except Exception as e:
                logger.error(f"Error extracting chapter: {e}")
                result["extraction_stats"]["extraction_errors"].append({
                    "chapter": chapter.get("title", "Unknown"),
                    "error": str(e)
                })
        
        # Extract special sections
        special = structure.get("special_sections", {})
        if special:
            result["special_sections"] = self._extract_special_sections(special, page_offset)
        
        logger.info(f"Extraction complete: {result['extraction_stats']['total_chapters']} chapters, "
                   f"{result['extraction_stats']['total_topics']} topics")
        
        return result
    
    def _extract_chapter(self, chapter: Dict, page_offset: int, num_columns: int) -> Dict:
        """Extract content for a single chapter"""
        chapter_data = {
            "type": chapter.get("type", "chapter"),
            "number": chapter.get("number", ""),
            "title": chapter.get("title", ""),
            "book_page_start": chapter.get("book_page_start"),
            "book_page_end": chapter.get("book_page_end"),
            "pdf_page_start": None,
            "pdf_page_end": None,
            "content_preview": "",  # First 500 chars of chapter
            "topics": []
        }
        
        # Convert book pages to PDF pages
        if chapter_data["book_page_start"]:
            chapter_data["pdf_page_start"] = self._book_to_pdf_page(
                chapter_data["book_page_start"], page_offset
            )
        if chapter_data["book_page_end"]:
            chapter_data["pdf_page_end"] = self._book_to_pdf_page(
                chapter_data["book_page_end"], page_offset
            )
        
        logger.info(f"Extracting Chapter {chapter_data['number']}: {chapter_data['title']} "
                   f"(PDF pages {chapter_data['pdf_page_start']}-{chapter_data['pdf_page_end']})")
        
        # Get chapter preview
        if chapter_data["pdf_page_start"]:
            preview_text = self._extract_page_text(
                chapter_data["pdf_page_start"], 
                num_columns
            )
            chapter_data["content_preview"] = preview_text[:500] if preview_text else ""
        
        # Extract each topic
        for topic in chapter.get("topics", []):
            try:
                topic_data = self._extract_topic(topic, page_offset, num_columns)
                chapter_data["topics"].append(topic_data)
            except Exception as e:
                logger.error(f"Error extracting topic '{topic.get('title', 'Unknown')}': {e}")
                chapter_data["topics"].append({
                    "title": topic.get("title", "Unknown"),
                    "error": str(e)
                })
        
        return chapter_data
    
    def _extract_topic(self, topic: Dict, page_offset: int, num_columns: int) -> Dict:
        """Extract content for a single topic/section"""
        topic_data = {
            "type": topic.get("type", "section"),
            "number": topic.get("number", ""),
            "title": topic.get("title", ""),
            "book_page_start": topic.get("book_page_start"),
            "book_page_end": topic.get("book_page_end"),
            "pdf_page_start": None,
            "pdf_page_end": None,
            "content": "",
            "subtopics": []
        }
        
        # Convert book pages to PDF pages
        book_start = self._parse_page_number(topic_data["book_page_start"])
        book_end = self._parse_page_number(topic_data["book_page_end"])
        
        if book_start:
            topic_data["pdf_page_start"] = self._book_to_pdf_page(book_start, page_offset)
        if book_end:
            topic_data["pdf_page_end"] = self._book_to_pdf_page(book_end, page_offset)
        
        # Extract content for this topic
        if topic_data["pdf_page_start"] is not None:
            pdf_start = topic_data["pdf_page_start"]
            pdf_end = topic_data["pdf_page_end"] or pdf_start
            
            # Extract text from page range
            content = self._extract_page_range(
                pdf_start, 
                pdf_end, 
                num_columns,
                topic_data["title"]
            )
            topic_data["content"] = content
        
        # Extract subtopics recursively
        for subtopic in topic.get("subtopics", []):
            try:
                subtopic_data = self._extract_topic(subtopic, page_offset, num_columns)
                topic_data["subtopics"].append(subtopic_data)
            except Exception as e:
                logger.error(f"Error extracting subtopic: {e}")
        
        return topic_data
    
    def _book_to_pdf_page(self, book_page: int, offset: int) -> int:
        """
        Convert book page number to PDF page index (0-indexed)
        
        Args:
            book_page: Page number as printed in the book
            offset: Page offset (PDF page = book_page + offset - 1)
        
        Returns:
            PDF page index (0-indexed)
        """
        if book_page is None:
            return None
            
        pdf_page = book_page + offset - 1  # -1 for 0-indexing
        
        # Clamp to valid range
        return max(0, min(pdf_page, self.total_pages - 1))
    
    def _parse_page_number(self, page_value) -> Optional[int]:
        """Parse page number from various formats"""
        if page_value is None:
            return None
        
        if isinstance(page_value, int):
            return page_value
        
        if isinstance(page_value, str):
            # Try to extract number
            match = re.search(r'\d+', page_value)
            if match:
                return int(match.group())
        
        return None
    
    def _extract_page_text(self, pdf_page: int, num_columns: int) -> str:
        """Extract text from a single PDF page"""
        if pdf_page < 0 or pdf_page >= self.total_pages:
            return ""
        
        page = self.doc[pdf_page]
        
        if num_columns > 1:
            return self._extract_multicolumn_page(page, num_columns)
        else:
            return self._extract_single_column_page(page)
    
    def _extract_page_range(self, pdf_start: int, pdf_end: int, 
                           num_columns: int, topic_title: str = None) -> str:
        """
        Extract text from a range of PDF pages
        
        Args:
            pdf_start: Starting PDF page (0-indexed)
            pdf_end: Ending PDF page (0-indexed)
            num_columns: Number of columns in layout
            topic_title: Title to search for (to start extraction from)
        
        Returns:
            Extracted text content
        """
        content_parts = []
        found_start = topic_title is None  # If no title, start immediately
        
        for page_num in range(pdf_start, pdf_end + 1):
            if page_num >= self.total_pages:
                break
            
            page_text = self._extract_page_text(page_num, num_columns)
            
            # On first page, try to find the topic title
            if page_num == pdf_start and topic_title and not found_start:
                start_pos = self._find_heading_position(page_text, topic_title)
                if start_pos >= 0:
                    page_text = page_text[start_pos:]
                    found_start = True
                elif not found_start:
                    # Title not found on expected page, include full content
                    found_start = True
            
            if page_text.strip():
                content_parts.append(page_text)
        
        return "\n\n".join(content_parts)
    
    def _extract_single_column_page(self, page) -> str:
        """Extract text from single-column page"""
        # Get text with layout preserved
        text = page.get_text("text")
        
        # Clean up the text
        text = self._clean_text(text)
        
        return text
    
    def _extract_multicolumn_page(self, page, num_columns: int) -> str:
        """
        Extract text from multi-column page in correct reading order
        
        Strategy:
        1. Get all text blocks with positions
        2. Determine column boundaries
        3. Sort blocks by column first, then by vertical position
        4. Combine text in reading order
        """
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Get text blocks with positions
        blocks = page.get_text("dict")["blocks"]
        
        # Filter and categorize text blocks
        text_blocks = []
        
        for block in blocks:
            if block.get("type") != 0:  # Not a text block
                continue
            
            bbox = block.get("bbox", [0, 0, 0, 0])
            
            # Skip header/footer regions
            if bbox[1] < page_height * 0.05 or bbox[3] > page_height * 0.95:
                continue
            
            # Extract text from block
            text = self._extract_block_text(block)
            if not text.strip():
                continue
            
            # Determine column based on x position
            x_center = (bbox[0] + bbox[2]) / 2
            column = int(x_center / (page_width / num_columns))
            column = min(column, num_columns - 1)
            
            text_blocks.append({
                "text": text,
                "x": bbox[0],
                "y": bbox[1],
                "column": column,
                "bbox": bbox
            })
        
        if not text_blocks:
            # Fallback to simple extraction
            return page.get_text("text")
        
        # Sort by column first, then by vertical position
        text_blocks.sort(key=lambda b: (b["column"], b["y"], b["x"]))
        
        # Combine text
        current_column = -1
        parts = []
        
        for block in text_blocks:
            if block["column"] != current_column:
                if current_column >= 0:
                    parts.append("\n---\n")  # Column separator
                current_column = block["column"]
            
            parts.append(block["text"])
        
        text = "\n".join(parts)
        return self._clean_text(text)
    
    def _extract_block_text(self, block: Dict) -> str:
        """Extract text from a text block structure"""
        text_parts = []
        
        for line in block.get("lines", []):
            line_parts = []
            for span in line.get("spans", []):
                span_text = span.get("text", "")
                line_parts.append(span_text)
            
            line_text = "".join(line_parts)
            if line_text.strip():
                text_parts.append(line_text)
        
        return "\n".join(text_parts)
    
    def _find_heading_position(self, text: str, heading: str) -> int:
        """
        Find the position of a heading in text
        
        Args:
            text: Full text to search
            heading: Heading to find
        
        Returns:
            Position of heading, or -1 if not found
        """
        if not heading or not text:
            return -1
        
        # Normalize for comparison
        heading_clean = re.sub(r'[^\w\s]', '', heading.lower()).strip()
        heading_words = heading_clean.split()
        
        # Try exact match first
        pos = text.lower().find(heading.lower())
        if pos >= 0:
            return pos
        
        # Try finding by words
        lines = text.split('\n')
        char_count = 0
        
        for line in lines:
            line_clean = re.sub(r'[^\w\s]', '', line.lower()).strip()
            
            # Check if line contains heading words
            if all(word in line_clean for word in heading_words[:3]):  # First 3 words
                return char_count
            
            char_count += len(line) + 1
        
        return -1
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        from config import TEXT_CLEANING
        
        if not text:
            return ""
        
        # Remove unwanted characters
        for char in TEXT_CLEANING.get("unwanted_chars", []):
            text = text.replace(char, "")
        
        # Normalize whitespace
        if TEXT_CLEANING.get("normalize_whitespace", True):
            # Replace multiple spaces with single space
            text = re.sub(r' +', ' ', text)
            # Replace multiple newlines with double newline
            text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove common header/footer patterns if configured
        if TEXT_CLEANING.get("remove_headers_footers", False):
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                is_header_footer = False
                
                for pattern in TEXT_CLEANING.get("header_patterns", []):
                    if re.match(pattern, line.strip()):
                        is_header_footer = True
                        break
                
                if not is_header_footer:
                    for pattern in TEXT_CLEANING.get("footer_patterns", []):
                        if re.match(pattern, line.strip()):
                            is_header_footer = True
                            break
                
                if not is_header_footer:
                    cleaned_lines.append(line)
            
            text = '\n'.join(cleaned_lines)
        
        return text.strip()
    
    def _extract_special_sections(self, special: Dict, page_offset: int) -> Dict:
        """Extract special sections like index, glossary, etc."""
        extracted = {}
        
        for section_name, section_info in special.items():
            try:
                # Get page numbers
                book_start = self._parse_page_number(
                    section_info.get("book_page_start") or section_info.get("pdf_page")
                )
                book_end = self._parse_page_number(
                    section_info.get("book_page_end") or book_start
                )
                
                if book_start is None:
                    continue
                
                # For special sections, pdf_page might be given directly
                if "pdf_page" in section_info:
                    pdf_start = section_info["pdf_page"] - 1  # Convert to 0-indexed
                else:
                    pdf_start = self._book_to_pdf_page(book_start, page_offset)
                
                pdf_end = pdf_start
                if book_end and book_end != book_start:
                    if "pdf_page" in section_info:
                        pdf_end = pdf_start + (book_end - book_start)
                    else:
                        pdf_end = self._book_to_pdf_page(book_end, page_offset)
                
                # Extract content (single column for special sections usually)
                content = self._extract_page_range(pdf_start, pdf_end, 1)
                
                extracted[section_name] = {
                    "book_page_start": book_start,
                    "book_page_end": book_end,
                    "pdf_page_start": pdf_start,
                    "pdf_page_end": pdf_end,
                    "content_preview": content[:1000] if content else "",
                    "full_content": content
                }
                
            except Exception as e:
                logger.error(f"Error extracting special section '{section_name}': {e}")
        
        return extracted
    
    def extract_by_page_range(self, start_page: int, end_page: int, 
                              num_columns: int = 1) -> str:
        """
        Direct extraction by page range
        
        Args:
            start_page: Start page (1-indexed, as would appear in UI)
            end_page: End page (1-indexed)
            num_columns: Number of columns
        
        Returns:
            Extracted text
        """
        # Convert to 0-indexed
        pdf_start = max(0, start_page - 1)
        pdf_end = min(self.total_pages - 1, end_page - 1)
        
        return self._extract_page_range(pdf_start, pdf_end, num_columns)
    
    def search_text(self, search_term: str, max_results: int = 10) -> List[Dict]:
        """
        Search for text in the PDF
        
        Args:
            search_term: Text to search for
            max_results: Maximum results to return
        
        Returns:
            List of search results with page info and context
        """
        results = []
        
        for page_num in range(self.total_pages):
            if len(results) >= max_results:
                break
            
            page = self.doc[page_num]
            text = page.get_text("text")
            
            # Find matches
            for match in re.finditer(re.escape(search_term), text, re.IGNORECASE):
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                
                results.append({
                    "pdf_page": page_num + 1,
                    "context": f"...{context}...",
                    "position": match.start()
                })
                
                if len(results) >= max_results:
                    break
        
        return results
    
    def get_page_count(self) -> int:
        """Get total page count"""
        return self.total_pages
    
    def close(self):
        """Close the PDF document"""
        if hasattr(self, 'doc') and self.doc:
            self.doc.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
