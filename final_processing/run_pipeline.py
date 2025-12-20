"""
Master Pipeline Runner

Runs the complete final processing pipeline:
1. Matcher: Matches subtopics across all 3 sources
2. Processor: Processes matched subtopics through AI Studio
"""
import logging
import sys
from pathlib import Path
import argparse

from config import LOG_FORMAT, LOG_FILE
from matcher import match_all_levels
from processor import process_all_staged_subtopics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),  # Overwrite log each run
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline(skip_matching: bool = False, limit_per_subject: int = None, level: str = None, subject: str = None):
    """
    Run the complete pipeline.
    
    Args:
        skip_matching: If True, skip matching step (use existing staging)
        limit_per_subject: Limit number of subtopics per subject (for testing)
        level: Process only specific level (e.g., "Alevel", "AS'Level", "IGCSE", "O'level")
        subject: Process only specific subject code (e.g., "9701")
    """
    logger.info("="*80)
    logger.info("FINAL PROCESSING PIPELINE - MASTER RUNNER")
    logger.info("="*80)
    if level:
        logger.info(f"Filtering to level: {level}")
    if subject:
        logger.info(f"Filtering to subject: {subject}")
    
    try:
        # Step 1: Match subtopics
        if not skip_matching:
            logger.info("\n" + "="*80)
            logger.info("STEP 1: MATCHING SUBTOPICS")
            logger.info("="*80)
            match_all_levels()
        else:
            logger.info("\n" + "="*80)
            logger.info("STEP 1: MATCHING SUBTOPICS (SKIPPED)")
            logger.info("="*80)
            logger.info("Using existing staging directory")
        
        # Step 2: Process through AI Studio
        logger.info("\n" + "="*80)
        logger.info("STEP 2: PROCESSING WITH AI STUDIO")
        logger.info("="*80)
        process_all_staged_subtopics(limit_per_subject=limit_per_subject, level=level, subject=subject)
        
        logger.info("\n" + "="*80)
        logger.info("PIPELINE COMPLETE!")
        logger.info("="*80)
        
    except KeyboardInterrupt:
        logger.warning("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nPipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point with CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Final Processing Pipeline - Comprehensive Note Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python run_pipeline.py
  
  # Run with test limit (first 2 subtopics per subject)
  python run_pipeline.py --limit 2
  
  # Skip matching step (use existing staging)
  python run_pipeline.py --skip-matching
  
  # Process specific level and subject
  python run_pipeline.py --level "AS'Level" --subject 9701
  
  # Process specific subject with limit
  python run_pipeline.py --subject 9701 --limit 5
  
  # Just run matching (no AI processing)
  python matcher.py
  
  # Just run processing (requires existing staging)
  python processor.py
        """
    )
    
    parser.add_argument(
        '--skip-matching',
        action='store_true',
        help='Skip matching step and use existing staging directory'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit processing to first N subtopics per subject (for testing)'
    )
    
    parser.add_argument(
        '--level',
        type=str,
        help='Process only specific level (e.g., "Alevel", "AS\'Level", "IGCSE", "O\'level")'
    )
    
    parser.add_argument(
        '--subject',
        type=str,
        help='Process only specific subject code (e.g., "9701")'
    )
    
    args = parser.parse_args()
    
    run_pipeline(
        skip_matching=args.skip_matching,
        limit_per_subject=args.limit,
        level=args.level,
        subject=args.subject
    )


if __name__ == "__main__":
    main()
