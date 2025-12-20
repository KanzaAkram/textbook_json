"""
Final Processing Pipeline
Combines syllabus JSON + textbook notes + Save My Exam notes for each subtopic
and generates comprehensive notes using AI Studio.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available. Install with: pip install PyMuPDF")

try:
    import sys
    from pathlib import Path
    # Add parent directory to path to import textbook module
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from textbook.ai_studio_extractor import AIStudioExtractor
    from textbook.config import SELENIUM_CONFIG
    EXTRACTOR_AVAILABLE = True
except ImportError as e:
    EXTRACTOR_AVAILABLE = False
    logger.error(f"Could not import AIStudioExtractor: {e}")
    logger.error("Make sure textbook module is available and all dependencies are installed.")
    AIStudioExtractor = None  # Define as None for type hints
    SELENIUM_CONFIG = {}


def extract_subtopic_number_from_filename(filename: str) -> Optional[str]:
    """
    Extract subtopic number from filename.
    Examples:
    - "1.1_Particles_in_the_atom.json" -> "1.1"
    - "1.1_Particles in the atom and atomic radius.json" -> "1.1"
    - "23.1_Lattice energy and Born-Haber cycles.json" -> "23.1"
    """
    match = re.match(r'^(\d+\.\d+)', filename)
    if match:
        return match.group(1)
    return None


def normalize_subtopic_name(name: str) -> str:
    """
    Normalize subtopic name for matching (remove special chars, lowercase).
    """
    # Remove special characters, keep only alphanumeric and spaces
    normalized = re.sub(r'[^\w\s]', '', name.lower())
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def find_matching_subtopics(
    level: str,
    subject_code: str,
    textbook_path: Path,
    syllabus_path: Path,
    save_my_exam_path: Path
) -> List[Dict]:
    """
    Find matching subtopics across all 3 sources by subtopic number.
    
    Returns:
        List of dicts with keys: subtopic_number, textbook_file, syllabus_file, save_my_exam_files
    """
    matches = []
    
    # Get all textbook subtopic files
    textbook_files = {}
    if textbook_path.exists():
        for file in textbook_path.glob("*.json"):
            subtopic_num = extract_subtopic_number_from_filename(file.name)
            if subtopic_num:
                textbook_files[subtopic_num] = file
    
    # Get all syllabus subtopic files
    syllabus_files = {}
    if syllabus_path.exists():
        for file in syllabus_path.glob("*.json"):
            subtopic_num = extract_subtopic_number_from_filename(file.name)
            if subtopic_num:
                syllabus_files[subtopic_num] = file
    
    # Get all Save My Exam PDF files
    save_my_exam_files = {}
    if save_my_exam_path.exists():
        for file in save_my_exam_path.glob("*.pdf"):
            subtopic_num = extract_subtopic_number_from_filename(file.name)
            if subtopic_num:
                if subtopic_num not in save_my_exam_files:
                    save_my_exam_files[subtopic_num] = []
                save_my_exam_files[subtopic_num].append(file)
    
    # Find matches (subtopic must exist in at least textbook or syllabus)
    all_subtopic_nums = set(textbook_files.keys()) | set(syllabus_files.keys())
    
    for subtopic_num in sorted(all_subtopic_nums):
        match = {
            'subtopic_number': subtopic_num,
            'textbook_file': textbook_files.get(subtopic_num),
            'syllabus_file': syllabus_files.get(subtopic_num),
            'save_my_exam_files': save_my_exam_files.get(subtopic_num, [])
        }
        matches.append(match)
    
    logger.info(f"Found {len(matches)} matching subtopics for {level}/{subject_code}")
    return matches


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from Save My Exam PDF.
    """
    if not PYMUPDF_AVAILABLE:
        logger.warning(f"PyMuPDF not available. Cannot extract text from {pdf_path.name}")
        return ""
    
    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
        
        doc.close()
        content = "\n\n".join(text_parts)
        logger.debug(f"  Extracted {len(content)} chars from {pdf_path.name}")
        return content
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path.name}: {e}")
        return ""


def load_json_file(file_path: Path) -> Optional[Dict]:
    """Load JSON file safely."""
    if not file_path or not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path.name}: {e}")
        return None


def create_comprehensive_notes_prompt(
    syllabus_data: Dict,
    textbook_data: Dict,
    save_my_exam_texts: List[str]
) -> str:
    """
    Create prompt for AI Studio to generate comprehensive notes.
    """
    # Extract key information
    subtopic_info = syllabus_data.get('subtopic', {}) or textbook_data.get('subtopic', {})
    subtopic_number = subtopic_info.get('sub_topic_number') or subtopic_info.get('subtopic_number', '')
    subtopic_name = subtopic_info.get('sub_topic_name') or subtopic_info.get('subtopic_name', '')
    learning_objectives = subtopic_info.get('learning_objectives', [])
    
    # Format learning objectives
    objectives_text = ""
    if learning_objectives:
        objectives_text = "\n".join([
            f"  {obj.get('objective_number', '')}. {obj.get('description', '')}"
            for obj in learning_objectives
        ])
    
    # Combine Save My Exam texts
    save_my_exam_content = "\n\n--- Save My Exam Note ---\n\n".join([
        text for text in save_my_exam_texts if text.strip()
    ])
    
    # Get textbook content
    textbook_content = ""
    if textbook_data and 'subtopic' in textbook_data:
        textbook_content = textbook_data['subtopic'].get('content', '')
    
    prompt = f"""You are creating comprehensive, extensive study notes for a subtopic in Chemistry.

SUBTopic Information:
- Subtopic Number: {subtopic_number}
- Subtopic Name: {subtopic_name}

Learning Objectives (from Syllabus):
{objectives_text if objectives_text else "Not specified"}

Your task:
1. Use the TEXTBOOK CONTENT as the PRIMARY source and foundation for the notes
2. Use the SYLLABUS LEARNING OBJECTIVES to ensure all required topics are covered (as a "fence" to stay within syllabus boundaries)
3. Use the SAVE MY EXAM NOTES as a SECONDARY source to supplement and enhance the textbook content
4. Create comprehensive, well-structured notes that:
   - Cover all learning objectives from the syllabus
   - Are based primarily on the textbook content
   - Are enhanced with relevant information from Save My Exam notes (but only if it's within syllabus scope)
   - Are well-organized with clear headings and subheadings
   - Include key concepts, definitions, examples, and explanations
   - Are suitable for exam preparation

IMPORTANT GUIDELINES:
- The textbook is the PRIMARY context - use it as the main source
- The syllabus learning objectives are your "fence" - ensure all are covered, but don't go beyond them
- Save My Exam notes are SECONDARY - use them to supplement, but ignore any content that goes outside the syllabus scope
- If Save My Exam content contradicts the textbook, prioritize the textbook
- If Save My Exam content is outside the syllabus scope, ignore it

TEXTBOOK CONTENT (PRIMARY):
{textbook_content[:5000] if len(textbook_content) > 5000 else textbook_content}
{f"[Content truncated - showing first 5000 chars of {len(textbook_content)} total]" if len(textbook_content) > 5000 else ""}

SAVE MY EXAM NOTES (SECONDARY):
{save_my_exam_content[:3000] if len(save_my_exam_content) > 3000 else save_my_exam_content}
{f"[Content truncated - showing first 3000 chars of {len(save_my_exam_content)} total]" if len(save_my_exam_content) > 3000 else ""}

Please create comprehensive notes in JSON format:
{{
  "subtopic_number": "{subtopic_number}",
  "subtopic_name": "{subtopic_name}",
  "comprehensive_notes": {{
    "introduction": "...",
    "key_concepts": [
      {{
        "concept": "...",
        "explanation": "...",
        "examples": ["...", "..."]
      }}
    ],
    "detailed_content": {{
      "section_1": {{
        "heading": "...",
        "content": "..."
      }},
      "section_2": {{
        "heading": "...",
        "content": "..."
      }}
    }},
    "summary": "...",
    "important_points": ["...", "..."],
    "exam_tips": ["...", "..."]
  }},
  "learning_objectives_coverage": {{
    "objective_1": "covered",
    "objective_2": "covered"
  }}
}}

Return ONLY valid JSON, no markdown formatting, no code blocks, no explanations.
"""
    
    return prompt


def process_subtopic(
    match: Dict,
    level: str,
    subject_code: str,
    output_dir: Path,
    extractor  # AIStudioExtractor type, but can be None if import failed
) -> bool:
    """
    Process a single subtopic: combine all sources and generate comprehensive notes.
    """
    subtopic_num = match['subtopic_number']
    logger.info(f"\n  Processing subtopic {subtopic_num}...")
    
    # Load data from all sources
    syllabus_data = load_json_file(match['syllabus_file']) if match['syllabus_file'] else {}
    textbook_data = load_json_file(match['textbook_file']) if match['textbook_file'] else {}
    
    # Extract text from Save My Exam PDFs
    save_my_exam_texts = []
    for pdf_file in match['save_my_exam_files']:
        text = extract_text_from_pdf(pdf_file)
        if text:
            save_my_exam_texts.append(text)
    
    # Check if we have at least one source
    if not syllabus_data and not textbook_data:
        logger.warning(f"    No syllabus or textbook data for {subtopic_num}, skipping")
        return False
    
    # Create prompt
    prompt = create_comprehensive_notes_prompt(syllabus_data, textbook_data, save_my_exam_texts)
    
    # Send to AI Studio
    try:
        # Setup extractor if needed
        if extractor.driver is None:
            extractor._setup_driver()
        
        # Navigate to AI Studio
        from textbook.config import config
        ai_studio_url = SELENIUM_CONFIG.get("ai_studio_url") or config.ai_studio_url
        logger.info(f"    Navigating to AI Studio...")
        extractor.driver.get(ai_studio_url)
        extractor._wait_for_page_load(60)
        time.sleep(5)
        
        # Check login
        if not extractor._check_and_handle_login():
            raise Exception("Failed to login to AI Studio")
        
        time.sleep(5)
        
        # Send prompt (no PDF upload needed, just text prompt)
        logger.info(f"    Sending prompt to AI Studio...")
        if not extractor._send_prompt(prompt):
            raise Exception("Failed to send prompt")
        
        # Wait for response
        logger.info(f"    Waiting for AI to generate response...")
        response = extractor._wait_for_response(timeout=120)
        
        if not response:
            raise Exception("No response received from AI Studio")
        
        # Extract JSON
        logger.info(f"    Extracting JSON from response...")
        json_content = extractor._extract_json_response()
        if not json_content:
            json_content = response
        
        # Parse JSON
        result_data = extractor._parse_json_response(json_content or response)
        
        if not result_data:
            logger.error(f"    Could not parse JSON response for {subtopic_num}")
            return False
        
        # Save result
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get subtopic name for filename
        subtopic_info = syllabus_data.get('subtopic', {}) or textbook_data.get('subtopic', {})
        subtopic_name = subtopic_info.get('sub_topic_name') or subtopic_info.get('subtopic_name', '')
        
        # Sanitize filename
        safe_name = re.sub(r'[^\w\s-]', '', subtopic_name).strip()
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        filename = f"{subtopic_num}_{safe_name}.json"
        output_path = output_dir / filename
        
        # Add metadata
        result_data['metadata'] = {
            'level': level,
            'subject_code': subject_code,
            'subtopic_number': subtopic_num,
            'sources_used': {
                'syllabus': match['syllabus_file'] is not None,
                'textbook': match['textbook_file'] is not None,
                'save_my_exam': len(match['save_my_exam_files']) > 0
            }
        }
        
        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"    [OK] Saved: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"    ✗ Error processing {subtopic_num}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    
    # Setup paths
    textbook_path = script_dir.parent / "textbook" / "extracted_subtopics"
    syllabus_path = script_dir.parent / "syllabus_json_structured_pipeline" / "split_subtopics"
    save_my_exam_path = script_dir.parent / "save_my_exam" / "organized_by_syllabus"
    output_path = script_dir / "comprehensive_notes"
    
    logger.info("="*60)
    logger.info("Final Processing Pipeline - Comprehensive Notes Generation")
    logger.info("="*60)
    
    if not EXTRACTOR_AVAILABLE:
        logger.error("AIStudioExtractor not available. Cannot proceed.")
        return
    
    if not PYMUPDF_AVAILABLE:
        logger.warning("PyMuPDF not available. Save My Exam PDF extraction will be skipped.")
    
    # Process each level
    levels = ["AS'Level", "Alevel", "IGCSE", "O'level"]
    
    for level in levels:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Level: {level}")
        logger.info(f"{'='*60}")
        
        # Get subject folders
        textbook_level_path = textbook_path / level
        syllabus_level_path = syllabus_path / level
        save_my_exam_level_path = save_my_exam_path / level
        
        if not textbook_level_path.exists() and not syllabus_level_path.exists():
            logger.info(f"  No files found for {level}, skipping...")
            continue
        
        # Get all subject codes
        subject_codes = set()
        if textbook_level_path.exists():
            subject_codes.update([d.name for d in textbook_level_path.iterdir() if d.is_dir()])
        if syllabus_level_path.exists():
            subject_codes.update([d.name for d in syllabus_level_path.iterdir() if d.is_dir()])
        if save_my_exam_level_path.exists():
            subject_codes.update([d.name for d in save_my_exam_level_path.iterdir() if d.is_dir()])
        
        for subject_code in sorted(subject_codes):
            logger.info(f"\n  Processing Subject: {subject_code}")
            
            # Find matching subtopics
            matches = find_matching_subtopics(
                level,
                subject_code,
                textbook_level_path / subject_code if textbook_level_path.exists() else Path(),
                syllabus_level_path / subject_code if syllabus_level_path.exists() else Path(),
                save_my_exam_level_path / subject_code if save_my_exam_level_path.exists() else Path()
            )
            
            if not matches:
                logger.info(f"    No matching subtopics found for {level}/{subject_code}")
                continue
            
            # Process each subtopic
            output_dir = output_path / level / subject_code
            
            with AIStudioExtractor() as extractor:
                for i, match in enumerate(matches, 1):
                    logger.info(f"\n  [{i}/{len(matches)}] Processing subtopic {match['subtopic_number']}...")
                    
                    success = process_subtopic(match, level, subject_code, output_dir, extractor)
                    
                    if success:
                        logger.info(f"    [OK] Completed subtopic {match['subtopic_number']}")
                    else:
                        logger.error(f"    [FAILED] Failed subtopic {match['subtopic_number']}")
                    
                    # Wait between requests
                    if i < len(matches):
                        logger.info(f"    Waiting 10 seconds before next subtopic...")
                        time.sleep(10)
    
    logger.info("\n" + "="*60)
    logger.info("All processing complete!")
    logger.info(f"Output saved to: {output_path}")
    logger.info("="*60)


if __name__ == "__main__":
    main()

