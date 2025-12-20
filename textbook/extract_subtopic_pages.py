"""
Extract page numbers for each subtopic from textbooks using Gemini AI Studio.
Matches textbooks with syllabus JSONs and gets start/end pages for each subtopic.
"""

import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available. Install with: pip install pymupdf")

from ai_studio_extractor import AIStudioExtractor
from config import config, SELENIUM_CONFIG


def load_syllabus_json(prompt_path: Path) -> Optional[Dict]:
    """
    Load syllabus JSON from prompt.py file.
    
    Args:
        prompt_path: Path to prompt.py file
        
    Returns:
        Parsed syllabus dictionary or None
    """
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return None
            
            # Try JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try Python dict assignment
                if content.startswith("syllabus = {") or content.startswith("{"):
                    dict_str = content[content.find('{'):]
                    return ast.literal_eval(dict_str)
                return None
    except Exception as e:
        logger.warning(f"Error loading syllabus from {prompt_path}: {e}")
        return None


def create_page_extraction_prompt(syllabus_data: Dict) -> str:
    """
    Create a prompt for Gemini to extract page numbers for each subtopic.
    Includes the full syllabus JSON structure in the prompt.
    
    Args:
        syllabus_data: Syllabus JSON data
        
    Returns:
        Formatted prompt string
    """
    # Convert syllabus to JSON string for inclusion in prompt
    syllabus_json_str = json.dumps(syllabus_data, indent=2, ensure_ascii=False)
    
    # Build prompt
    prompt = f"""Analyze the uploaded PDF textbook and provide the start and end page numbers for each subtopic listed in the syllabus.

The complete syllabus structure is provided below in JSON format:

{syllabus_json_str}

Your task:
1. For each subtopic in the syllabus, find where its content appears in the uploaded PDF textbook
2. Determine the start page and end page for each subtopic
3. Return a JSON response with page numbers for all subtopics

Please provide a JSON response in the following format:
{{
  "syllabus_name": "{syllabus_data.get('syllabus_name', 'Unknown')}",
  "syllabus_years": "{syllabus_data.get('syllabus_years', 'Unknown')}",
  "subtopics": [
    {{
      "subtopic_number": "1.1",
      "subtopic_name": "Particles in the atom and atomic radius",
      "topic_number": "1",
      "topic_name": "Atomic structure",
      "start_page": 10,
      "end_page": 25
    }},
    ...
  ]
}}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
- The PDF may have cover pages, table of contents, etc. that are NOT numbered in the book
- You MUST use the BOOK'S PRINTED PAGE NUMBERS (the numbers actually printed on the pages)
- DO NOT use PDF page numbers (page 1 of PDF might be the cover, not book page 1)
- Look for the actual page numbers printed on the pages (e.g., "Page 1", "1", etc.)
- If book page 1 appears at PDF page 10, then book page 10 = PDF page 19, NOT PDF page 10
- Find where each subtopic content begins and ends using the BOOK'S printed page numbers
- If a subtopic spans multiple sections, use the first occurrence's start page and last occurrence's end page
- If a subtopic is not found in the book, set start_page and end_page to null
- Return ONLY valid JSON, no markdown formatting, no code blocks, no explanations
- Include ALL subtopics from the syllabus in your response
"""
    
    return prompt


def extract_subtopic_pages_for_book(
    book_path: Path,
    syllabus_data: Dict,
    output_base_dir: Path,
    level: str,
    subject_code: str,
    extractor: AIStudioExtractor
) -> bool:
    """
    Extract page numbers for subtopics from a book using Gemini AI Studio.
    
    Args:
        book_path: Path to the PDF book
        syllabus_data: Syllabus JSON data
        output_base_dir: Base directory for output (will create level/subject_code subfolder)
        level: Level name (e.g., "AS'Level", "Alevel")
        subject_code: Subject code (e.g., "9701")
        extractor: AIStudioExtractor instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {book_path.name}")
    logger.info(f"{'='*60}")
    
    try:
        # Create prompt
        prompt = create_page_extraction_prompt(syllabus_data)
        
        # Setup extractor if needed
        if extractor.driver is None:
            extractor._setup_driver()
        
        # Navigate to AI Studio
        ai_studio_url = SELENIUM_CONFIG.get("ai_studio_url") or config.ai_studio_url
        logger.info(f"Navigating to AI Studio: {ai_studio_url}")
        extractor.driver.get(ai_studio_url)
        extractor._wait_for_page_load(60)
        time.sleep(5)
        
        # Check login
        if not extractor._check_and_handle_login():
            raise Exception("Failed to login to AI Studio")
        
        time.sleep(5)
        
        # Upload PDF
        logger.info("Uploading PDF...")
        if not extractor._upload_pdf(book_path):
            raise Exception("Failed to upload PDF")
        
        # Optionally upload syllabus JSON as a file (if supported)
        # For now, we include it in the prompt text
        # If you want to upload as file, we can add that functionality
        
        # Send prompt (includes full syllabus JSON)
        logger.info("Sending prompt (with syllabus JSON included)...")
        if not extractor._send_prompt(prompt):
            raise Exception("Failed to send prompt")
        
        # Wait for response
        logger.info("Waiting for AI response...")
        response = extractor._wait_for_response(timeout=SELENIUM_CONFIG.get("ai_studio_timeout", 600))
        
        if not response:
            raise Exception("No response received from AI Studio")
        
        # Extract JSON
        logger.info("Extracting JSON response...")
        json_content = extractor._extract_json_response()
        
        if not json_content:
            json_content = response
        
        # Parse JSON
        result_data = extractor._parse_json_response(json_content or response)
        
        if not result_data:
            logger.error("Could not parse JSON response")
            return False
        
        # Extract content from PDF pages using PyMuPDF
        logger.info("\nExtracting content from PDF pages...")
        subtopics_with_content = extract_content_from_pages(book_path, result_data.get('subtopics', []))
        
        # Create output directory structure: output_base_dir/level/subject_code/
        output_dir = output_base_dir / level / subject_code
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_count = 0
        
        for subtopic in subtopics_with_content:
            subtopic_num = subtopic.get('subtopic_number', '')
            subtopic_name = subtopic.get('subtopic_name', 'Unknown')
            
            if not subtopic_num:
                continue
            
            # Sanitize filename
            sanitized_name = subtopic_name.replace('/', '_').replace('\\', '_')
            filename = f"{subtopic_num}_{sanitized_name}.json"
            filename = re.sub(r'[<>:"|?*]', '', filename)  # Remove invalid chars
            
            output_path = output_dir / filename
            
            # Create subtopic JSON with content
            subtopic_json = {
                "syllabus_info": {
                    "syllabus_name": result_data.get('syllabus_name'),
                    "syllabus_years": result_data.get('syllabus_years')
                },
                "subtopic": subtopic
            }
            
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(subtopic_json, f, indent=2, ensure_ascii=False)
                saved_count += 1
                content_length = len(subtopic.get('content', ''))
                logger.info(f"  Saved: {filename} (content: {content_length} chars)")
            except Exception as e:
                logger.error(f"  Error saving {filename}: {e}")
        
        logger.info(f"\n✓ Saved {saved_count} subtopic JSON files to {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {book_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def detect_page_layout(page) -> int:
    """
    Detect if page has 1 or 2 columns by analyzing text block positions.
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        Number of columns detected (1 or 2)
    """
    try:
        blocks = page.get_text("dict")["blocks"]
        if not blocks:
            return 1
        
        # Get x-coordinates of text blocks
        x_coords = []
        for block in blocks:
            if block.get("type") == 0:  # Text block
                bbox = block.get("bbox", [])
                if len(bbox) >= 4:
                    x_center = (bbox[0] + bbox[2]) / 2
                    x_coords.append(x_center)
        
        if not x_coords:
            return 1
        
        # Check if there's a clear separation (gap) indicating 2 columns
        page_width = page.rect.width
        mid_point = page_width / 2
        
        # Count blocks on left and right sides
        left_blocks = sum(1 for x in x_coords if x < mid_point - 50)
        right_blocks = sum(1 for x in x_coords if x > mid_point + 50)
        
        # If significant blocks on both sides, likely 2 columns
        if left_blocks > 3 and right_blocks > 3:
            return 2
        
        return 1
    except:
        return 1


def extract_multicolumn_text(page, num_columns: int) -> str:
    """
    Extract text from multi-column page in correct reading order.
    
    Args:
        page: PyMuPDF page object
        num_columns: Number of columns (1 or 2)
        
    Returns:
        Extracted text in reading order
    """
    if num_columns == 1:
        return page.get_text("text")
    
    try:
        page_width = page.rect.width
        blocks = page.get_text("dict")["blocks"]
        
        # Categorize text blocks by column
        text_blocks = []
        for block in blocks:
            if block.get("type") == 0:  # Text block
                bbox = block.get("bbox", [])
                if len(bbox) >= 4:
                    x_center = (bbox[0] + bbox[2]) / 2
                    y_top = bbox[1]
                    
                    # Determine column
                    column = int(x_center / (page_width / num_columns))
                    column = min(column, num_columns - 1)
                    
                    # Get text from block
                    block_text = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            block_text += span.get("text", "")
                        block_text += "\n"
                    
                    if block_text.strip():
                        text_blocks.append({
                            'column': column,
                            'y': y_top,
                            'text': block_text.strip()
                        })
        
        # Sort by column first, then by vertical position
        text_blocks.sort(key=lambda b: (b['column'], b['y']))
        
        # Combine text in reading order
        content_parts = []
        current_column = -1
        for block in text_blocks:
            if block['column'] != current_column:
                if current_column >= 0:
                    content_parts.append("\n")  # Column separator
                current_column = block['column']
            content_parts.append(block['text'])
        
        return "\n".join(content_parts)
        
    except Exception as e:
        logger.warning(f"Error in multi-column extraction, falling back to simple extraction: {e}")
        return page.get_text("text")


def detect_page_offset(doc) -> int:
    """
    Detect the offset between PDF page indices and book page numbers.
    
    Searches for where book page 1 actually appears in the PDF.
    Many PDFs have cover pages, TOC, etc. before the actual book content starts.
    
    Args:
        doc: PyMuPDF document object
        
    Returns:
        Offset (e.g., if book page 1 is at PDF page 10, returns 9)
    """
    logger.info("Detecting page offset (book page 1 location)...")
    
    # Search first 50 pages for book page 1
    search_range = min(50, len(doc))
    
    for pdf_page_idx in range(search_range):
        try:
            page = doc[pdf_page_idx]
            text = page.get_text().lower()
            
            # Look for indicators that this is book page 1
            # Common patterns: "page 1", "1", chapter 1, etc.
            patterns = [
                r'\bpage\s+1\b',
                r'^\s*1\s*$',  # Just "1" as a standalone number
                r'\bchapter\s+1\b',
                r'\btopic\s+1\b',
            ]
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Also check if this looks like actual content (not TOC)
                    # TOC usually has "contents" or "table of contents"
                    if 'contents' not in text and 'table of' not in text:
                        offset = pdf_page_idx  # Book page 1 is at PDF page pdf_page_idx
                        logger.info(f"  Detected: Book page 1 appears at PDF page {pdf_page_idx + 1} (offset: {offset})")
                        return offset
            
            # Alternative: Look for first page with substantial content and a page number
            # This is a fallback if explicit "page 1" isn't found
            if pdf_page_idx > 5:  # Skip first few pages (likely covers)
                # Check if page has a page number in footer/header
                words = page.get_text("words")
                for word in words:
                    word_text = word[4].lower()  # Word text
                    # Look for standalone "1" or "page 1" in footer area (bottom 20% of page)
                    if word[1] > page.rect.height * 0.8:  # Bottom 20%
                        if word_text.strip() == '1' or 'page 1' in word_text:
                            offset = pdf_page_idx
                            logger.info(f"  Detected (fallback): Book page 1 appears at PDF page {pdf_page_idx + 1} (offset: {offset})")
                            return offset
        
        except Exception as e:
            logger.debug(f"  Error checking PDF page {pdf_page_idx + 1}: {e}")
            continue
    
    # Default: assume no offset (book starts at PDF page 1)
    logger.info("  No offset detected, assuming book starts at PDF page 1")
    return 0


def extract_content_from_pages(book_path: Path, subtopics: List[Dict]) -> List[Dict]:
    """
    Extract text content from PDF pages for each subtopic using PyMuPDF.
    Handles 2-column layouts and other formatting properly.
    
    Args:
        book_path: Path to the PDF book
        subtopics: List of subtopic dictionaries with start_page and end_page
        
    Returns:
        List of subtopics with added 'content' field
    """
    if not PYMUPDF_AVAILABLE:
        logger.warning("PyMuPDF not available. Skipping content extraction.")
        return subtopics
    
    if not book_path.exists():
        logger.error(f"Book file not found: {book_path}")
        return subtopics
    
    try:
        logger.info(f"Opening PDF: {book_path.name}")
        doc = fitz.open(book_path)
        total_pages = len(doc)
        logger.info(f"PDF has {total_pages} pages")
        
        # CRITICAL: Detect page offset (where book page 1 appears in PDF)
        page_offset = detect_page_offset(doc)
        
        # Detect layout from first few pages
        sample_pages = [0, min(5, total_pages - 1), min(10, total_pages - 1)]
        detected_columns = []
        for sample_page in sample_pages:
            try:
                page = doc[sample_page]
                cols = detect_page_layout(page)
                detected_columns.append(cols)
            except:
                pass
        
        # Use most common column count, default to 2 if mixed
        num_columns = 2 if 2 in detected_columns else (detected_columns[0] if detected_columns else 1)
        logger.info(f"Detected layout: {num_columns} column(s)")
        
        subtopics_with_content = []
        
        for subtopic in subtopics:
            start_page = subtopic.get('start_page')
            end_page = subtopic.get('end_page')
            
            # Skip if pages are not available
            if start_page is None or end_page is None:
                logger.warning(f"  {subtopic.get('subtopic_number')}: No page numbers, skipping content extraction")
                subtopic['content'] = ""
                subtopics_with_content.append(subtopic)
                continue
            
            # Convert BOOK page numbers to PDF page indices (0-indexed)
            # Gemini returns BOOK page numbers, but we need PDF page indices
            # Formula: PDF_page_index = page_offset + (book_page_number - 1)
            try:
                start_page_int = int(start_page)
                end_page_int = int(end_page)
                
                # Convert book page numbers to PDF page indices
                # Book page 1 is at PDF page (page_offset + 0)
                # Book page N is at PDF page (page_offset + N - 1)
                pdf_start = page_offset + (start_page_int - 1)
                pdf_end = page_offset + (end_page_int - 1)
                
                # Clamp to valid PDF page range
                pdf_start = max(0, min(pdf_start, total_pages - 1))
                pdf_end = max(0, min(pdf_end, total_pages - 1))
                
                # Ensure valid range
                if pdf_start >= total_pages:
                    logger.warning(f"  {subtopic.get('subtopic_number')}: Start page {start_page} exceeds PDF pages ({total_pages})")
                    subtopic['content'] = ""
                    subtopics_with_content.append(subtopic)
                    continue
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"  {subtopic.get('subtopic_number')}: Invalid page numbers ({start_page}-{end_page}): {e}")
                subtopic['content'] = ""
                subtopics_with_content.append(subtopic)
                continue
            
            if pdf_start > pdf_end:
                logger.warning(f"  {subtopic.get('subtopic_number')}: Invalid page range ({start_page}-{end_page})")
                subtopic['content'] = ""
                subtopics_with_content.append(subtopic)
                continue
            
            # Extract content from pages with proper column handling
            content_parts = []
            for page_num in range(pdf_start, pdf_end + 1):
                try:
                    page = doc[page_num]
                    
                    # Detect layout for this specific page (may vary)
                    page_columns = detect_page_layout(page)
                    
                    # Extract text with proper column handling
                    page_text = extract_multicolumn_text(page, page_columns)
                    
                    if page_text and page_text.strip():
                        content_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"  Error extracting page {page_num + 1}: {e}")
                    continue
            
            # Combine all pages
            content = "\n\n--- Page Break ---\n\n".join(content_parts)
            
            # Clean up content
            content = re.sub(r'\n{3,}', '\n\n', content)  # Remove excessive newlines
            content = content.strip()
            
            subtopic['content'] = content
            subtopic['content_length'] = len(content)
            subtopic['pages_extracted'] = f"{pdf_start + 1}-{pdf_end + 1}"
            subtopic['layout_detected'] = f"{num_columns} column(s)"
            
            logger.info(f"  {subtopic.get('subtopic_number')}: Extracted {len(content)} chars from book pages {start_page}-{end_page} (PDF pages {pdf_start + 1}-{pdf_end + 1})")
            subtopics_with_content.append(subtopic)
        
        doc.close()
        return subtopics_with_content
        
    except Exception as e:
        logger.error(f"Error extracting content from PDF: {e}")
        import traceback
        traceback.print_exc()
        return subtopics


def find_matching_syllabi(subject_code: str, merged_outputs_path: Path) -> List[tuple]:
    """
    Find matching syllabus files for a subject code across all levels.
    
    Args:
        subject_code: Subject code (e.g., '9701')
        merged_outputs_path: Path to merged_outputs folder
        
    Returns:
        List of tuples (level_name, prompt_path, syllabus_data)
    """
    matches = []
    levels = ["AS'Level", "Alevel", "IGCSE", "O'level"]
    
    for level in levels:
        level_path = merged_outputs_path / level / subject_code
        prompt_path = level_path / "prompt.py"
        
        if prompt_path.exists():
            syllabus_data = load_syllabus_json(prompt_path)
            if syllabus_data:
                matches.append((level, prompt_path, syllabus_data))
                logger.info(f"Found syllabus: {level}/{subject_code}")
    
    return matches


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    books_path = script_dir / "books"
    merged_outputs_path = script_dir.parent / "syllabus_json_structured_pipeline" / "merged_outputs"
    
    if not books_path.exists():
        logger.error(f"Books path does not exist: {books_path}")
        return
    
    if not merged_outputs_path.exists():
        logger.error(f"Merged outputs path does not exist: {merged_outputs_path}")
        return
    
    # Level mapping: folder names to level names
    level_mapping = {
        "as_alevel": ["AS'Level", "Alevel"],
        "igcse": ["IGCSE"],
        "olevel": ["O'level"],
    }
    
    logger.info("="*60)
    logger.info("Textbook Subtopic Page Extraction")
    logger.info("="*60)
    
    # Process each level folder
    for level_folder_name, target_levels in level_mapping.items():
        level_folder = books_path / level_folder_name
        
        if not level_folder.exists():
            continue
        
        logger.info(f"\nProcessing level folder: {level_folder_name}")
        
        # Process each subject code folder
        subject_folders = [d for d in level_folder.iterdir() if d.is_dir()]
        
        for subject_folder in subject_folders:
            subject_code = subject_folder.name
            
            # Find PDF
            pdf_files = list(subject_folder.glob("*.pdf"))
            if not pdf_files:
                logger.warning(f"No PDF found in {subject_folder}")
                continue
            
            book_path = pdf_files[0]  # Take first PDF
            
            # Find matching syllabi
            syllabi = find_matching_syllabi(subject_code, merged_outputs_path)
            
            if not syllabi:
                logger.warning(f"No matching syllabus found for {subject_code}")
                continue
            
            # Process each matching syllabus
            with AIStudioExtractor() as extractor:
                for level, prompt_path, syllabus_data in syllabi:
                    if level not in target_levels:
                        continue
                    
                    logger.info(f"\nProcessing: {level}/{subject_code}")
                    
                    # Extract pages (output will be saved to separate folder)
                    output_base = script_dir / "extracted_subtopics"  # Separate output folder
                    success = extract_subtopic_pages_for_book(
                        book_path,
                        syllabus_data,
                        output_base,
                        level,
                        subject_code,
                        extractor
                    )
                    
                    if success:
                        logger.info(f"✓ Completed: {level}/{subject_code}")
                    else:
                        logger.error(f"✗ Failed: {level}/{subject_code}")
                    
                    # Wait between requests
                    time.sleep(5)
    
    logger.info("\n" + "="*60)
    logger.info("All processing complete!")
    logger.info("="*60)


if __name__ == "__main__":
    main()

