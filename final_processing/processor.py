"""
Final Processing Pipeline - Main Script

This script processes matched subtopics from the staging directory:
1. Reads matched subtopic files (textbook, syllabus, save_my_exam)
2. Combines content according to priority (textbook primary, syllabus fencing, save_my_exam secondary)
3. Sends to AI Studio for comprehensive note generation
4. Saves properly structured output
"""
import logging
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys

# Try to import pyperclip for clipboard access
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("Note: pyperclip not installed. Install with: pip install pyperclip")

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from config import (
    STAGING_PATH, OUTPUT_PATH, LEVELS, AI_PROMPT_TEMPLATE,
    LOG_FORMAT, LOG_FILE
)
from utils import (
    load_json_file, save_json_file, get_subtopic_info,
    extract_text_from_pdf, format_learning_objectives, sanitize_filename
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import AI Studio extractor
try:
    from textbook.ai_studio_extractor import AIStudioExtractor
    from textbook.config import SELENIUM_CONFIG, config
    EXTRACTOR_AVAILABLE = True
except ImportError as e:
    EXTRACTOR_AVAILABLE = False
    logger.error(f"Could not import AIStudioExtractor: {e}")
    AIStudioExtractor = None
    SELENIUM_CONFIG = {}
    config = None


class SubtopicProcessor:
    """Processes a single matched subtopic through AI Studio."""
    
    def __init__(self, extractor):
        self.extractor = extractor
    
    def load_subtopic_data(self, metadata_path: Path) -> Optional[Dict]:
        """
        Load all data for a subtopic from staging directory.
        
        Args:
            metadata_path: Path to _metadata.json file
            
        Returns:
            Dict with all loaded data or None if error
        """
        metadata = load_json_file(metadata_path)
        if not metadata:
            logger.error(f"Could not load metadata from {metadata_path}")
            return None
        
        subtopic_dir = metadata_path.parent
        subtopic_num = metadata['subtopic_number']
        
        logger.info(f"  Loading data for subtopic {subtopic_num}...")
        
        # Load textbook
        textbook_data = None
        textbook_path = metadata['sources'].get('textbook')
        if textbook_path:
            textbook_data = load_json_file(Path(textbook_path))
            if textbook_data:
                logger.info(f"    [OK] Loaded textbook: {Path(textbook_path).name}")
            else:
                logger.warning(f"    [ERROR] Failed to load textbook: {textbook_path}")
        else:
            logger.warning(f"    [WARN] No textbook file for {subtopic_num}")
        
        # Load syllabus
        syllabus_data = None
        syllabus_path = metadata['sources'].get('syllabus')
        if syllabus_path:
            syllabus_data = load_json_file(Path(syllabus_path))
            if syllabus_data:
                logger.info(f"    [OK] Loaded syllabus: {Path(syllabus_path).name}")
            else:
                logger.warning(f"    [ERROR] Failed to load syllabus: {syllabus_path}")
        else:
            logger.warning(f"    [WARN] No syllabus file for {subtopic_num}")
        
        # Load Save My Exam PDFs
        save_my_exam_texts = []
        save_my_exam_paths = metadata['sources'].get('save_my_exam', [])
        if save_my_exam_paths:
            for pdf_path_str in save_my_exam_paths:
                pdf_path = Path(pdf_path_str)
                if pdf_path.exists():
                    text = extract_text_from_pdf(pdf_path)
                    if text:
                        save_my_exam_texts.append(text)
                        logger.info(f"    [OK] Extracted Save My Exam: {pdf_path.name} ({len(text)} chars)")
                    else:
                        logger.warning(f"    [ERROR] Failed to extract: {pdf_path.name}")
                else:
                    logger.warning(f"    [ERROR] File not found: {pdf_path}")
        else:
            logger.info(f"    [WARN] No Save My Exam files for {subtopic_num}")
        
        # Check if we have at least textbook or syllabus
        if not textbook_data and not syllabus_data:
            logger.error(f"    ✗ No textbook or syllabus data available for {subtopic_num}")
            return None
        
        return {
            'metadata': metadata,
            'textbook': textbook_data,
            'syllabus': syllabus_data,
            'save_my_exam_texts': save_my_exam_texts
        }
    
    def create_prompt(self, data: Dict) -> str:
        """
        Create AI Studio prompt from loaded data.
        
        Args:
            data: Dictionary containing all loaded data
            
        Returns:
            Formatted prompt string
        """
        metadata = data['metadata']
        textbook_data = data['textbook']
        syllabus_data = data['syllabus']
        save_my_exam_texts = data['save_my_exam_texts']
        
        # Extract information
        subtopic_num = metadata['subtopic_number']
        subtopic_name = metadata['subtopic_name']
        level = metadata['level']
        subject_code = metadata['subject_code']
        
        # Get learning objectives (prefer syllabus, fallback to textbook)
        learning_objectives = []
        if syllabus_data:
            _, _, objectives = get_subtopic_info(syllabus_data)
            learning_objectives = objectives
        elif textbook_data:
            _, _, objectives = get_subtopic_info(textbook_data)
            learning_objectives = objectives
        
        objectives_text = format_learning_objectives(learning_objectives)
        
        # Get textbook content
        textbook_content = ""
        if textbook_data and 'subtopic' in textbook_data:
            content = textbook_data['subtopic'].get('content', '')
            if content:
                # Limit to reasonable size (AI Studio may have limits)
                if len(content) > 8000:
                    textbook_content = content[:8000] + f"\n\n[Content truncated - showing first 8000 of {len(content)} characters]"
                else:
                    textbook_content = content
            else:
                textbook_content = "No textbook content available"
        else:
            textbook_content = "No textbook content available"
        
        # Format syllabus content (just learning objectives)
        syllabus_content = objectives_text
        
        # Combine Save My Exam texts
        save_my_exam_content = ""
        if save_my_exam_texts:
            combined = "\n\n=== Save My Exam Document ===\n\n".join(save_my_exam_texts)
            # Limit size
            if len(combined) > 5000:
                save_my_exam_content = combined[:5000] + f"\n\n[Content truncated - showing first 5000 of {len(combined)} characters]"
            else:
                save_my_exam_content = combined
        else:
            save_my_exam_content = "No Save My Exam content available"
        
        # Create prompt
        prompt = AI_PROMPT_TEMPLATE.format(
            subtopic_number=subtopic_num,
            subtopic_name=subtopic_name,
            level=level,
            subject_code=subject_code,
            learning_objectives=objectives_text,
            textbook_content=textbook_content,
            syllabus_content=syllabus_content,
            save_my_exam_content=save_my_exam_content
        )
        
        logger.debug(f"  Created prompt ({len(prompt)} chars)")
        return prompt
    
    def extract_json_from_response(self) -> Optional[str]:
        """
        Extract JSON content from the page using copy button or DOM extraction.
        This mirrors the logic from ai_studio_extractor.py
        
        Returns:
            JSON content as string or None if extraction failed
        """
        from selenium.webdriver.common.by import By
        
        logger.info("    Extracting JSON from AI response...")
        json_content = None
        
        # Method 1: Extract JSON directly from DOM
        try:
            logger.info("    Trying DOM extraction...")
            
            # Look for code blocks
            code_selectors = [
                "//pre[contains(@class, 'code') or contains(@class, 'json')]",
                "//code",
                "//div[contains(@class, 'code-block')]",
                "//pre",
            ]
            
            code_block = None
            for selector in code_selectors:
                elements = self.extractor.driver.find_elements(By.XPATH, selector)
                if elements:
                    code_block = elements[-1]  # Get most recent
                    text = code_block.text
                    if text and len(text) > 50 and (text.strip().startswith('{') or text.strip().startswith('[')):
                        json_content = text
                        logger.info(f"      [✓] Extracted JSON from DOM ({len(json_content)} characters)")
                        break
        except Exception as e:
            logger.debug(f"      DOM extraction failed: {e}")
        
        # Method 2: Try copy button to get content from clipboard
        if not json_content:
            try:
                logger.info("    Trying copy button + clipboard method...")
                
                # Find code block first
                code_block = None
                try:
                    code_elements = self.extractor.driver.find_elements(By.XPATH, "//pre | //code")
                    if code_elements:
                        code_block = code_elements[-1]
                except:
                    pass
                
                # Look for copy button near code block
                copy_button = None
                if code_block:
                    try:
                        container = code_block.find_element(By.XPATH, "./..")
                        nearby_copy = container.find_elements(By.XPATH, 
                            ".//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy')] | "
                            ".//button[contains(@class, 'copy')]")
                        if nearby_copy:
                            visible = [b for b in nearby_copy if b.is_displayed() and b.is_enabled()]
                            if visible:
                                copy_button = visible[0]
                                logger.info("      Found copy button near code block")
                    except:
                        pass
                
                # Try general copy button search
                if not copy_button:
                    copy_xpaths = [
                        "//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy')]",
                        "//button[@aria-label='Copy']",
                        "//button[contains(@class, 'copy')]",
                    ]
                    for xpath in copy_xpaths:
                        try:
                            elements = self.extractor.driver.find_elements(By.XPATH, xpath)
                            visible = [e for e in elements if e.is_displayed() and e.is_enabled()]
                            if visible:
                                copy_button = visible[0]
                                logger.info(f"      Found copy button")
                                break
                        except:
                            continue
                
                # Click copy button and get from clipboard
                if copy_button:
                    try:
                        self.extractor.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", copy_button)
                        time.sleep(1)
                        self.extractor.driver.execute_script("arguments[0].click();", copy_button)
                        time.sleep(3)
                        logger.info("      [✓] Copy button clicked")
                        
                        # Get from clipboard
                        if PYPERCLIP_AVAILABLE:
                            try:
                                copied_content = pyperclip.paste()
                                if copied_content and len(copied_content) > 50:
                                    json_content = copied_content
                                    logger.info(f"      [✓] Content copied from clipboard ({len(copied_content)} characters)")
                            except Exception as e:
                                logger.debug(f"      Clipboard read failed: {e}")
                        else:
                            logger.warning("      pyperclip not available, skipping clipboard method")
                    except Exception as e:
                        logger.debug(f"      Failed to click copy button: {e}")
                
            except Exception as e:
                logger.debug(f"      Copy button method failed: {e}")
        
        if not json_content:
            logger.warning("    Could not extract JSON from response")
        
        return json_content
    
    def send_to_ai_studio(self, prompt: str) -> Optional[Dict]:
        """
        Send prompt to AI Studio and get response.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Parsed JSON response or None if error
        """
        try:
            # Check if driver is healthy, restart if needed
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    if self.extractor.driver is None:
                        logger.info("    Setting up WebDriver...")
                        self.extractor._setup_driver()
                    
                    # Test if driver is responsive
                    try:
                        title = self.extractor.driver.title
                        logger.debug(f"    Driver is responsive (title: {title[:50]})")
                    except:
                        logger.warning("    Driver is unresponsive, restarting...")
                        self.extractor.close()
                        self.extractor._setup_driver()
                    
                    # Navigate to AI Studio
                    ai_studio_url = SELENIUM_CONFIG.get("ai_studio_url") or config.ai_studio_url
                    logger.info(f"    Navigating to AI Studio...")
                    self.extractor.driver.get(ai_studio_url)
                    self.extractor._wait_for_page_load(60)
                    time.sleep(5)
                    
                    # Check login
                    logger.info(f"    Checking authentication...")
                    if not self.extractor._check_and_handle_login():
                        raise Exception("Failed to authenticate with AI Studio")
                    
                    time.sleep(3)
                    
                    # Send prompt
                    logger.info(f"    Sending prompt to AI...")
                    if not self.extractor._send_prompt(prompt):
                        raise Exception("Failed to send prompt to AI Studio")
                    
                    # Wait for response with proper timeout
                    logger.info(f"    Waiting for AI response (this may take 1-2 minutes)...")
                    response = self.extractor._wait_for_response(timeout=180)
                    
                    if not response:
                        raise Exception("No response received from AI Studio")
                    
                    logger.info(f"    [OK] Received response ({len(response)} chars)")
                    
                    # Extract and parse JSON with enhanced DOM/clipboard extraction
                    logger.info(f"    Extracting JSON response...")
                    
                    # First try our enhanced extraction with DOM and clipboard copy
                    json_content = self.extract_json_from_response()
                    
                    # If that didn't work, try the extractor's method
                    if not json_content:
                        logger.info("    Trying extractor's extraction method...")
                        json_content = self.extractor._extract_json_response()
                    
                    # Fall back to raw response if all else fails
                    if not json_content:
                        json_content = response
                    
                    result_data = self.extractor._parse_json_response(json_content or response)
                    
                    if not result_data:
                        logger.error(f"    [ERROR] Could not parse JSON from response")
                        logger.debug(f"    Raw response snippet: {response[:200]}...")
                        return None
                    
                    logger.info(f"    [OK] Successfully parsed JSON response")
                    return result_data
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"    Attempt {attempt + 1} failed: {e}. Retrying...")
                        # Close driver before retry
                        try:
                            self.extractor.close()
                        except:
                            pass
                        time.sleep(5)
                        continue
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"    [ERROR] Error communicating with AI Studio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_result(self, result_data: Dict, metadata: Dict, output_dir: Path) -> bool:
        """
        Save the AI-generated result.
        
        Args:
            result_data: The AI-generated data
            metadata: Original metadata
            output_dir: Directory to save to
            
        Returns:
            True if successful
        """
        try:
            subtopic_num = metadata['subtopic_number']
            subtopic_name = metadata['subtopic_name']
            
            # Add metadata to result
            result_data['metadata'] = {
                'level': metadata['level'],
                'subject_code': metadata['subject_code'],
                'subtopic_number': subtopic_num,
                'subtopic_name': subtopic_name,
                'generated_at': datetime.now().isoformat(),
                'sources_used': {
                    'textbook': metadata['sources'].get('textbook') is not None,
                    'syllabus': metadata['sources'].get('syllabus') is not None,
                    'save_my_exam_count': len(metadata['sources'].get('save_my_exam', []))
                }
            }
            
            # Create filename
            safe_name = sanitize_filename(subtopic_name)
            filename = f"{subtopic_num}_{safe_name}.json"
            output_path = output_dir / filename
            
            # Save
            output_dir.mkdir(parents=True, exist_ok=True)
            if save_json_file(result_data, output_path):
                logger.info(f"    [OK] Saved result: {filename}")
                return True
            else:
                logger.error(f"    [ERROR] Failed to save: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"    ✗ Error saving result: {e}")
            return False
    
    def process_subtopic(self, metadata_path: Path, output_dir: Path) -> bool:
        """
        Process a single subtopic: load data, create prompt, get AI response, save result.
        
        Args:
            metadata_path: Path to subtopic's _metadata.json
            output_dir: Output directory for results
            
        Returns:
            True if successful
        """
        # Load data
        data = self.load_subtopic_data(metadata_path)
        if not data:
            return False
        
        subtopic_num = data['metadata']['subtopic_number']
        
        # Create prompt
        logger.info(f"  Creating prompt for {subtopic_num}...")
        prompt = self.create_prompt(data)
        
        # Send to AI Studio
        logger.info(f"  Processing with AI Studio...")
        result_data = self.send_to_ai_studio(prompt)
        if not result_data:
            return False
        
        # Save result
        logger.info(f"  Saving result...")
        success = self.save_result(result_data, data['metadata'], output_dir)
        
        return success


def process_all_staged_subtopics(limit_per_subject: Optional[int] = None, level: Optional[str] = None, subject: Optional[str] = None):
    """
    Process all subtopics from staging directory.
    
    Args:
        limit_per_subject: Optional limit on number of subtopics to process per subject (for testing)
        level: Optional level filter (e.g., "Alevel", "AS'Level", "IGCSE", "O'level")
        subject: Optional subject code filter (e.g., "9701")
    """
    logger.info("="*80)
    logger.info("FINAL PROCESSING PIPELINE - AI Studio Generation")
    logger.info("="*80)
    if level:
        logger.info(f"Filtering to level: {level}")
    if subject:
        logger.info(f"Filtering to subject: {subject}")
    
    if not EXTRACTOR_AVAILABLE:
        logger.error("AIStudioExtractor not available. Cannot proceed.")
        logger.error("Make sure textbook module is available and dependencies are installed.")
        return
    
    total_processed = 0
    total_success = 0
    total_failed = 0
    
    for curr_level in LEVELS:
        # Skip if level filter is set and doesn't match
        if level and curr_level != level:
            continue
            
        level_path = STAGING_PATH / curr_level
        if not level_path.exists():
            logger.info(f"\nNo staging data for level: {curr_level}")
            continue
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing Level: {curr_level}")
        logger.info(f"{'='*80}")
        
        # Find all subject codes
        subject_dirs = [d for d in level_path.iterdir() if d.is_dir()]
        
        for subject_dir in sorted(subject_dirs):
            subject_code = subject_dir.name
            
            # Skip if subject filter is set and doesn't match
            if subject and subject_code != subject:
                continue
                
            logger.info(f"\n{'-'*80}")
            logger.info(f"Subject: {curr_level}/{subject_code}")
            logger.info(f"{'-'*80}")
            
            # Find all subtopic metadata files
            metadata_files = list(subject_dir.glob("*/_metadata.json"))
            
            if not metadata_files:
                logger.warning(f"  No subtopics found in {subject_dir}")
                continue
            
            # Apply limit if specified
            if limit_per_subject and len(metadata_files) > limit_per_subject:
                logger.warning(f"  Limiting to first {limit_per_subject} subtopics for testing")
                metadata_files = metadata_files[:limit_per_subject]
            
            logger.info(f"  Found {len(metadata_files)} subtopics to process")
            
            # Create output directory
            output_dir = OUTPUT_PATH / level / subject_code
            
            # Process each subtopic
            with AIStudioExtractor() as extractor:
                processor = SubtopicProcessor(extractor)
                
                for i, metadata_path in enumerate(metadata_files, 1):
                    subtopic_num = metadata_path.parent.name
                    
                    logger.info(f"\n  [{i}/{len(metadata_files)}] Processing subtopic: {subtopic_num}")
                    logger.info(f"  {'·'*60}")
                    
                    total_processed += 1
                    success = processor.process_subtopic(metadata_path, output_dir)
                    
                    if success:
                        total_success += 1
                        logger.info(f"  [SUCCESS] Subtopic {subtopic_num} completed")
                    else:
                        total_failed += 1
                        logger.error(f"  [FAILED] Subtopic {subtopic_num}")
                    
                    # Wait between requests to avoid overloading
                    if i < len(metadata_files):
                        wait_time = 15
                        logger.info(f"  Waiting {wait_time} seconds before next subtopic...")
                        time.sleep(wait_time)
    
    # Final summary
    logger.info(f"\n{'='*80}")
    logger.info(f"PROCESSING COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"  Total processed: {total_processed}")
    logger.info(f"  Successful: {total_success}")
    logger.info(f"  Failed: {total_failed}")
    logger.info(f"  Success rate: {(total_success/total_processed*100):.1f}%" if total_processed > 0 else "N/A")
    logger.info(f"  Output directory: {OUTPUT_PATH}")
    logger.info(f"{'='*80}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process matched subtopics through AI Studio")
    parser.add_argument('--limit', type=int, help='Limit number of subtopics per subject (for testing)')
    parser.add_argument('--level', type=str, help='Process only specific level (e.g., "Alevel")')
    parser.add_argument('--subject', type=str, help='Process only specific subject code (e.g., "9701")')
    
    args = parser.parse_args()
    
    try:
        process_all_staged_subtopics(limit_per_subject=args.limit, level=args.level, subject=args.subject)
        process_all_staged_subtopics(limit_per_subject=args.limit)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
