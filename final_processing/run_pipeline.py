"""
Test Pipeline Runner
Run the final processing pipeline for specific subjects/levels.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from final_processing.main import (
    find_matching_subtopics,
    process_subtopic,
    load_json_file,
    extract_text_from_pdf,
    create_comprehensive_notes_prompt,
    extract_subtopic_number_from_filename
)

# Import AI Studio extractor
try:
    from textbook.ai_studio_extractor import AIStudioExtractor
    from textbook.config import SELENIUM_CONFIG
    EXTRACTOR_AVAILABLE = True
except ImportError as e:
    EXTRACTOR_AVAILABLE = False
    print(f"Error importing AIStudioExtractor: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_processing_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_for_subject(subject_code: str, level: str = None):
    """
    Run pipeline for a specific subject code.
    
    Args:
        subject_code: Subject code (e.g., '9701')
        level: Specific level to process (e.g., "AS'Level", "Alevel"). 
               If None, processes all levels that have this subject.
    """
    script_dir = Path(__file__).parent
    
    # Setup paths
    textbook_path = script_dir.parent / "textbook" / "extracted_subtopics"
    syllabus_path = script_dir.parent / "syllabus_json_structured_pipeline" / "split_subtopics"
    save_my_exam_path = script_dir.parent / "save_my_exam" / "organized_by_syllabus"
    output_path = script_dir / "comprehensive_notes"
    
    logger.info("="*60)
    logger.info(f"Testing Pipeline for Subject: {subject_code}")
    if level:
        logger.info(f"Level: {level}")
    else:
        logger.info("Level: ALL (will process all levels with this subject)")
    logger.info("="*60)
    
    # Determine which levels to process
    if level:
        levels_to_process = [level]
    else:
        # Find all levels that have this subject
        levels_to_process = []
        all_levels = ["AS'Level", "Alevel", "IGCSE", "O'level"]
        for lvl in all_levels:
            textbook_level_path = textbook_path / lvl / subject_code
            syllabus_level_path = syllabus_path / lvl / subject_code
            save_my_exam_level_path = save_my_exam_path / lvl / subject_code
            
            if (textbook_level_path.exists() or 
                syllabus_level_path.exists() or 
                save_my_exam_level_path.exists()):
                levels_to_process.append(lvl)
    
    if not levels_to_process:
        logger.error(f"No data found for subject {subject_code} in any level")
        return
    
    logger.info(f"Will process levels: {', '.join(levels_to_process)}")
    
    # Process each level
    for level in levels_to_process:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Level: {level}")
        logger.info(f"{'='*60}")
        
        # Get paths for this level/subject
        textbook_level_path = textbook_path / level / subject_code
        syllabus_level_path = syllabus_path / level / subject_code
        save_my_exam_level_path = save_my_exam_path / level / subject_code
        
        # Find matching subtopics
        matches = find_matching_subtopics(
            level,
            subject_code,
            textbook_level_path if textbook_level_path.exists() else Path(),
            syllabus_level_path if syllabus_level_path.exists() else Path(),
            save_my_exam_level_path if save_my_exam_level_path.exists() else Path()
        )
        
        if not matches:
            logger.warning(f"  No matching subtopics found for {level}/{subject_code}")
            continue
        
        logger.info(f"  Found {len(matches)} matching subtopics")
        
        # Show what will be processed
        logger.info(f"\n  Subtopics to process:")
        for i, match in enumerate(matches[:10], 1):  # Show first 10
            sources = []
            if match['textbook_file']:
                sources.append("Textbook")
            if match['syllabus_file']:
                sources.append("Syllabus")
            if match['save_my_exam_files']:
                sources.append(f"SaveMyExam({len(match['save_my_exam_files'])})")
            logger.info(f"    {match['subtopic_number']}: {', '.join(sources) if sources else 'No sources'}")
        
        if len(matches) > 10:
            logger.info(f"    ... and {len(matches) - 10} more")
        
        # Ask for confirmation
        response = input(f"\n  Process {len(matches)} subtopics for {level}/{subject_code}? (y/n): ")
        if response.lower() != 'y':
            logger.info(f"  Skipping {level}/{subject_code}")
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
                    import time
                    logger.info(f"    Waiting 10 seconds before next subtopic...")
                    time.sleep(10)
        
        logger.info(f"\n  [OK] Completed processing {level}/{subject_code}")
    
    logger.info("\n" + "="*60)
    logger.info("Test run complete!")
    logger.info(f"Output saved to: {output_path}")
    logger.info("="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run final processing pipeline for specific subjects')
    parser.add_argument('subject_code', help='Subject code (e.g., 9701)')
    parser.add_argument('--level', '-l', 
                       choices=["AS'Level", "Alevel", "IGCSE", "O'level"],
                       help='Specific level to process (optional, processes all if not specified)')
    
    args = parser.parse_args()
    
    if not EXTRACTOR_AVAILABLE:
        logger.error("AIStudioExtractor not available. Cannot proceed.")
        sys.exit(1)
    
    run_for_subject(args.subject_code, args.level)


if __name__ == "__main__":
    # If run without arguments, default to 9701
    if len(sys.argv) == 1:
        logger.info("No arguments provided. Running for subject 9701 (AS'Level and Alevel)...")
        run_for_subject("9701")
    else:
        main()
