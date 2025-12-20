"""
Main Pipeline - Orchestrates the textbook processing workflow
Coordinates PDF analysis, AI Studio extraction, and content extraction
"""

import sys
import json
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Fix encoding issues on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from config import config, OUTPUT_FORMATS

# Setup logging
def setup_logging():
    """Configure logging with proper encoding"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Create handlers
    handlers = []
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(
        config.log_file, 
        encoding='utf-8',
        mode='a'
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        handlers=handlers,
        format=log_format
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()


class TextbookPipeline:
    """Main pipeline for processing textbooks"""
    
    def __init__(self, books_dir: Path = None, output_dir: Path = None):
        """
        Initialize the pipeline
        
        Args:
            books_dir: Directory containing PDF files
            output_dir: Directory for output files
        """
        self.books_dir = books_dir or config.books_dir
        self.output_dir = output_dir or config.output_dir
        
        # Ensure directories exist
        self.books_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track processing state
        self.processed_books = []
        self.failed_books = []
        
        logger.info(f"Pipeline initialized: books={self.books_dir}, output={self.output_dir}")
    
    def discover_books(self) -> List[Path]:
        """Discover all PDF files in the books directory"""
        pdf_files = list(self.books_dir.glob("*.pdf"))
        logger.info(f"Discovered {len(pdf_files)} PDF files")
        
        for pdf in pdf_files:
            logger.info(f"  - {pdf.name}")
        
        return pdf_files
    
    def process_book(self, pdf_path: Path, mode: str = "auto", 
                    force_reprocess: bool = False) -> Dict:
        """
        Process a single book through the full pipeline
        
        Args:
            pdf_path: Path to PDF file
            mode: Processing mode
                - "auto": Try automatic, fallback to interactive
                - "interactive": Manual interaction with AI Studio
                - "structure_only": Only extract structure, no content
            force_reprocess: Reprocess even if output exists
        
        Returns:
            Processing result dictionary
        """
        book_name = pdf_path.stem
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {book_name}")
        logger.info(f"{'='*60}")
        
        # Check for existing output
        output_file = self.output_dir / f"{book_name}{OUTPUT_FORMATS['content_suffix']}"
        if output_file.exists() and not force_reprocess:
            logger.info(f"Output already exists: {output_file.name}")
            logger.info("Use --force to reprocess")
            return {"status": "skipped", "reason": "already_processed"}
        
        result = {
            "book_name": book_name,
            "pdf_path": str(pdf_path),
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: Analyze PDF
            logger.info("\nStep 1: Analyzing PDF structure...")
            from pdf_analyzer import PDFAnalyzer
            
            with PDFAnalyzer(pdf_path) as analyzer:
                analysis = analyzer.analyze()
                result["steps"]["analysis"] = "completed"
                result["pdf_analysis"] = analysis
                
                page_offset = analysis["page_offset"]["offset"]
                num_columns = analysis["column_layout"]["num_columns"]
                
                logger.info(f"  - Total pages: {analysis['basic_info']['total_pages']}")
                logger.info(f"  - Detected page offset: {page_offset}")
                logger.info(f"  - Detected columns: {num_columns}")
            
            # Step 2: Extract structure via AI Studio
            logger.info("\nStep 2: Extracting structure via AI Studio...")
            from ai_studio_extractor import AIStudioExtractor
            
            with AIStudioExtractor() as extractor:
                if mode == "interactive":
                    structure = extractor.interactive_extraction(pdf_path, analysis)
                else:
                    try:
                        structure = extractor.extract_structure(pdf_path, analysis)
                    except Exception as e:
                        logger.warning(f"Automatic extraction failed: {e}")
                        logger.info("Falling back to interactive mode...")
                        structure = extractor.interactive_extraction(pdf_path, analysis)
                
                result["steps"]["structure_extraction"] = "completed"
                
                # Use AI-detected offset if available
                if "page_offset" in structure:
                    ai_offset = structure["page_offset"].get("detected_offset")
                    if ai_offset is not None:
                        logger.info(f"Using AI-detected page offset: {ai_offset}")
                        page_offset = ai_offset
                
                # Save structure
                structure_file = self.output_dir / f"{book_name}{OUTPUT_FORMATS['structure_suffix']}"
                self._save_json(structure, structure_file)
                logger.info(f"  - Structure saved: {structure_file.name}")
            
            # Step 3: Extract content
            if mode != "structure_only":
                logger.info("\nStep 3: Extracting content with PyMuPDF...")
                from content_extractor import ContentExtractor
                
                with ContentExtractor(pdf_path) as extractor:
                    content = extractor.extract_from_structure(structure, page_offset)
                    result["steps"]["content_extraction"] = "completed"
                    
                    # Save content
                    self._save_json(content, output_file)
                    logger.info(f"  - Content saved: {output_file.name}")
                    
                    # Log stats
                    stats = content.get("extraction_stats", {})
                    logger.info(f"  - Chapters: {stats.get('total_chapters', 0)}")
                    logger.info(f"  - Topics: {stats.get('total_topics', 0)}")
                    logger.info(f"  - Subtopics: {stats.get('total_subtopics', 0)}")
            
            result["status"] = "success"
            result["completed_at"] = datetime.now().isoformat()
            self.processed_books.append(book_name)
            
            logger.info(f"\n[SUCCESS] Book processed successfully: {book_name}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            self.failed_books.append(book_name)
            
            logger.error(f"\n[ERROR] Failed to process {book_name}: {e}")
            logger.error(traceback.format_exc())
            
            # Save partial results if configured
            if config.save_partial_results:
                error_file = self.output_dir / f"{book_name}{OUTPUT_FORMATS['errors_suffix']}"
                self._save_json(result, error_file)
        
        return result
    
    def process_all_books(self, mode: str = "auto", force_reprocess: bool = False) -> Dict:
        """
        Process all books in the books directory
        
        Args:
            mode: Processing mode for each book
            force_reprocess: Force reprocessing of existing outputs
        
        Returns:
            Summary of processing results
        """
        books = self.discover_books()
        
        if not books:
            logger.warning("No PDF files found in books directory!")
            return {"status": "no_books", "books_found": 0}
        
        results = []
        
        for i, book_path in enumerate(books, 1):
            logger.info(f"\n[{i}/{len(books)}] Processing book...")
            
            try:
                result = self.process_book(book_path, mode, force_reprocess)
                results.append(result)
            except Exception as e:
                logger.error(f"Fatal error processing {book_path.name}: {e}")
                if not config.continue_on_error:
                    raise
        
        # Generate summary
        summary = {
            "total_books": len(books),
            "successful": len(self.processed_books),
            "failed": len(self.failed_books),
            "processed_books": self.processed_books,
            "failed_books": self.failed_books,
            "results": results,
            "completed_at": datetime.now().isoformat()
        }
        
        # Save summary
        summary_file = self.output_dir / "processing_summary.json"
        self._save_json(summary, summary_file)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Successfully processed: {len(self.processed_books)}/{len(books)} books")
        
        if self.failed_books:
            logger.warning(f"Failed books: {', '.join(self.failed_books)}")
        
        logger.info(f"Summary saved to: {summary_file}")
        
        return summary
    
    def _save_json(self, data: Dict, filepath: Path):
        """Save data to JSON file with proper encoding"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def print_usage():
    """Print usage instructions"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           TEXTBOOK PROCESSING PIPELINE                           ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  USAGE:                                                          ║
║    python main.py [options]                                      ║
║                                                                  ║
║  OPTIONS:                                                        ║
║    --books DIR     Directory containing PDF files (default: books)║
║    --output DIR    Output directory (default: output)            ║
║    --mode MODE     Processing mode:                              ║
║                      auto - Try automatic, fallback to manual    ║
║                      interactive - Manual AI Studio interaction   ║
║                      structure_only - Extract structure only      ║
║    --force         Force reprocess existing books                ║
║    --single FILE   Process a single PDF file                     ║
║                                                                  ║
║  WORKFLOW:                                                       ║
║    1. Place PDF textbooks in the 'books' directory               ║
║    2. Run: python main.py                                        ║
║    3. When prompted, interact with AI Studio in the browser      ║
║    4. Results are saved to 'output' directory                    ║
║                                                                  ║
║  OUTPUT FILES:                                                   ║
║    <book>_structure.json - Book structure from AI                ║
║    <book>_content.json   - Extracted content                     ║
║    processing_summary.json - Overall summary                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Textbook Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--books", 
        type=str, 
        default="books",
        help="Directory containing PDF files"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="output",
        help="Output directory"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "interactive", "structure_only"],
        default="auto",
        help="Processing mode"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocess existing books"
    )
    parser.add_argument(
        "--single",
        type=str,
        help="Process a single PDF file"
    )
    parser.add_argument(
        "--help-more",
        action="store_true",
        help="Show detailed usage information"
    )
    
    args = parser.parse_args()
    
    if args.help_more:
        print_usage()
        return
    
    # Initialize pipeline
    pipeline = TextbookPipeline(
        books_dir=Path(args.books),
        output_dir=Path(args.output)
    )
    
    # Process books
    if args.single:
        # Process single file
        pdf_path = Path(args.single)
        if not pdf_path.exists():
            logger.error(f"File not found: {pdf_path}")
            sys.exit(1)
        
        result = pipeline.process_book(pdf_path, args.mode, args.force)
        
        if result.get("status") == "success":
            logger.info("Processing completed successfully!")
        else:
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    else:
        # Process all books
        summary = pipeline.process_all_books(args.mode, args.force)
        
        if summary.get("failed") > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
