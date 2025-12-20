"""
Non-interactive test runner for the pipeline.
Bypasses confirmation prompts.
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from textbook.ai_studio_extractor import AIStudioExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_auto_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def auto_run_pipeline():
    """Run pipeline without user confirmation."""
    subject_code = "9701"
    level = "AS'Level"
    
    logger.info("=" * 60)
    logger.info(f"AUTO-RUN PIPELINE TEST: {level}/{subject_code}")
    logger.info("=" * 60)
    
    # Find matches
    from final_processing.main import find_matching_subtopics
    
    textbook_path = Path("../textbook/extracted_subtopics") / level / subject_code
    syllabus_path = Path("../syllabus_json_structured_pipeline/split_subtopics") / level / subject_code
    save_my_exam_path = Path("../save_my_exam/organized_by_syllabus") / level / subject_code
    
    matches = find_matching_subtopics(level, subject_code, textbook_path, syllabus_path, save_my_exam_path)
    
    logger.info(f"\nFound {len(matches)} subtopics")
    if not matches:
        logger.error("No matches found!")
        return False
    
    # Show first few
    logger.info("Sample subtopics:")
    for match in matches[:5]:
        logger.info(f"  - {match['subtopic_number']}")
    
    # Process with fresh driver for each batch
    output_dir = Path("output") / level / subject_code
    output_dir.mkdir(parents=True, exist_ok=True)
    
    restart_interval = 3
    extractor = None
    processed_count = 0
    failed_count = 0
    
    try:
        for i, match in enumerate(matches[:3], 1):  # Test with first 3 subtopics
            # Restart driver every restart_interval
            if (i - 1) % restart_interval == 0:
                if extractor:
                    logger.info(f"Closing driver for cleanup...")
                    extractor.close()
                    import time
                    time.sleep(2)
                
                logger.info(f"Starting fresh driver for batch...")
                extractor = AIStudioExtractor()
            
            logger.info(f"\n[{i}/3] Processing subtopic {match['subtopic_number']}...")
            
            # Import here to avoid circular imports
            from final_processing.run_pipeline import process_subtopic
            success = process_subtopic(match, level, subject_code, output_dir, extractor)
            
            if success:
                logger.info(f"  [OK] Completed {match['subtopic_number']}")
                processed_count += 1
            else:
                logger.error(f"  [FAILED] {match['subtopic_number']}")
                failed_count += 1
            
            # Wait between subtopics
            if i < len(matches):
                import time
                logger.info(f"  Waiting 5 seconds before next subtopic...")
                time.sleep(5)
    
    finally:
        if extractor:
            try:
                extractor.close()
            except:
                pass
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"RESULTS: {processed_count} completed, {failed_count} failed out of 3 tested")
    logger.info("=" * 60)
    
    return processed_count > 0

if __name__ == "__main__":
    success = auto_run_pipeline()
    sys.exit(0 if success else 1)
