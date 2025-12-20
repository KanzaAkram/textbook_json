"""
Test script to verify automated AI Studio extraction
Tests: login, PDF upload, AI extraction, clipboard copy
"""

import sys
from pathlib import Path
from ai_studio_extractor import AIStudioExtractor
from pdf_analyzer import PDFAnalyzer
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_automation():
    """Test the automated extraction process"""
    
    # Find PDF files in books directory
    books_dir = Path("books")
    pdf_files = list(books_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {books_dir}")
        return False
    
    # Use the first PDF found
    pdf_path = pdf_files[0]
    logger.info(f"Testing with PDF: {pdf_path.name}")
    
    try:
        # Step 1: Analyze PDF
        logger.info("Step 1: Analyzing PDF...")
        with PDFAnalyzer(pdf_path) as analyzer:
            analysis = analyzer.analyze()
            logger.info(f"  - Total pages: {analysis['basic_info']['total_pages']}")
        
        # Step 2: Extract structure via AI Studio (with auto-login and upload)
        logger.info("\nStep 2: Extracting structure via AI Studio...")
        logger.info("  - Will automatically login with credentials from config")
        logger.info("  - Will automatically upload PDF")
        logger.info("  - Will automatically extract AI output and copy to clipboard")
        
        with AIStudioExtractor() as extractor:
            structure = extractor.extract_structure(pdf_path, analysis)
            
            if structure:
                logger.info("\n[SUCCESS] Extraction completed!")
                logger.info(f"  - Book title: {structure.get('book_info', {}).get('title', 'Unknown')}")
                logger.info("  - AI output has been copied to clipboard")
                logger.info("  - Structure extracted successfully")
                return True
            else:
                logger.error("Extraction failed - no structure returned")
                return False
                
    except Exception as e:
        logger.error(f"Error during automation test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_automation()
    sys.exit(0 if success else 1)


