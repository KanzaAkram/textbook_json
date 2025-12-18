"""
Configuration for Textbook Processing Pipeline
Centralized settings for robustness and flexibility
"""

import os
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


class ExtractionStrategy(Enum):
    """Extraction strategy for content"""
    HYBRID = "hybrid"  # AI Studio structure + PyMuPDF content (RECOMMENDED)
    AI_ONLY = "ai_only"  # Full content from AI Studio
    PAGE_REFS = "page_refs"  # Page numbers only, then PyMuPDF extraction


@dataclass
class PipelineConfig:
    """Main pipeline configuration"""
    
    # Directories
    books_dir: Path = field(default_factory=lambda: Path("books"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    temp_dir: Path = field(default_factory=lambda: Path("temp"))
    
    # AI Studio settings
    ai_studio_url: str = "https://aistudio.google.com/prompts/new_chat"
    ai_studio_timeout: int = 600  # seconds - increased for large books
    ai_studio_max_retries: int = 3
    ai_studio_wait_between_retries: int = 10
    
    # Extraction strategy
    extraction_strategy: ExtractionStrategy = ExtractionStrategy.HYBRID
    
    # PDF Processing
    max_file_size_mb: int = 500
    min_pages: int = 5
    max_pages: int = 3000
    
    # Page number offset detection
    auto_detect_page_offset: bool = True
    manual_page_offset: int = 0  # If auto-detect fails, use this offset
    page_offset_sample_pages: List[int] = field(default_factory=lambda: [5, 10, 15, 20])
    
    # Content extraction settings
    extract_images: bool = False  # Set True to extract images
    extract_tables: bool = True
    extract_equations: bool = True
    preserve_formatting: bool = True
    
    # Multi-column detection
    auto_detect_columns: bool = True
    default_columns: int = 1
    column_detection_threshold: float = 0.6
    column_gap_threshold: int = 30  # pixels
    
    # Text extraction quality
    min_text_length: int = 50  # Minimum characters per topic
    remove_headers_footers: bool = True
    clean_whitespace: bool = True
    
    # Performance
    parallel_processing: bool = False
    max_workers: int = 2
    chunk_size: int = 50  # Pages per chunk for large books
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "textbook_pipeline.log"
    verbose: bool = True
    
    # Error handling
    continue_on_error: bool = True
    save_partial_results: bool = True
    max_errors_per_book: int = 10
    
    def __post_init__(self):
        """Create directories if they don't exist"""
        # Convert strings to Path if needed
        if isinstance(self.books_dir, str):
            self.books_dir = Path(self.books_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)
        if isinstance(self.temp_dir, str):
            self.temp_dir = Path(self.temp_dir)
            
        for dir_path in [self.books_dir, self.output_dir, self.cache_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


# AI Studio Prompts - Optimized for structure extraction
AI_STUDIO_PROMPTS = {
    "structure_extraction": """
You are analyzing a textbook PDF. Your task is to extract the COMPLETE hierarchical structure.

CRITICAL INSTRUCTIONS:
1. Extract ALL chapters, sections, and subsections from the Table of Contents
2. For EACH item, provide:
   - Exact title as it appears
   - The BOOK'S page number (printed on the page, NOT PDF page number)
   - Hierarchy level

3. IMPORTANT: Books often have a page offset - the PDF page number differs from the printed page number.
   - Look at the first few pages to identify this offset
   - Report the offset you detected

4. For 2-column layouts, note if topics span columns

Return ONLY valid JSON (no markdown, no explanation) with this structure:
{
  "book_info": {
    "title": "Full book title",
    "authors": ["Author 1", "Author 2"],
    "publisher": "Publisher name",
    "edition": "Edition if visible",
    "isbn": "ISBN if visible",
    "total_pages": 500
  },
  "page_offset": {
    "detected_offset": 12,
    "explanation": "PDF page 1 shows 'xii' (preface), actual content starts at PDF page 13 which shows page 1",
    "toc_pdf_page": 5
  },
  "layout": {
    "columns": 2,
    "has_headers": true,
    "has_footers": true
  },
  "structure": [
    {
      "type": "chapter",
      "number": "1",
      "title": "Chapter Title",
      "book_page_start": 1,
      "book_page_end": 45,
      "topics": [
        {
          "type": "section",
          "number": "1.1",
          "title": "Section Title",
          "book_page_start": 2,
          "book_page_end": 15,
          "subtopics": [
            {
              "type": "subsection", 
              "number": "1.1.1",
              "title": "Subsection Title",
              "book_page_start": 2,
              "book_page_end": 8
            }
          ]
        }
      ]
    }
  ],
  "special_sections": {
    "preface": {"book_page_start": "ix", "pdf_page": 9},
    "contents": {"pdf_page": 5},
    "index": {"book_page_start": 450, "book_page_end": 480},
    "glossary": {"book_page_start": 440, "book_page_end": 449},
    "answers": {"book_page_start": 420, "book_page_end": 439}
  }
}

Be PRECISE. Use the BOOK'S printed page numbers. Report the page offset accurately.
""",

    "structure_extraction_simple": """
Analyze this textbook and extract its structure. Return ONLY valid JSON.

Find:
1. Book title, authors
2. Page offset (difference between PDF page number and book's printed page number)
3. All chapters and their sections with page numbers (use BOOK page numbers, not PDF)
4. Whether it's 1-column or 2-column layout

JSON format:
{
  "book_info": {"title": "", "authors": []},
  "page_offset": {"detected_offset": 0, "toc_pdf_page": 0},
  "layout": {"columns": 1},
  "structure": [
    {
      "type": "chapter",
      "number": "1", 
      "title": "",
      "book_page_start": 1,
      "book_page_end": 50,
      "topics": [
        {
          "type": "section",
          "number": "1.1",
          "title": "",
          "book_page_start": 1,
          "book_page_end": 10,
          "subtopics": []
        }
      ]
    }
  ]
}
""",

    "validate_structure": """
Review the extracted structure and verify:
1. All page numbers are sequential and valid
2. No overlapping page ranges
3. All topics have clear boundaries
4. Page offset is correctly identified

Return corrections if needed as JSON.
"""
}


# Selenium settings
SELENIUM_CONFIG = {
    "headless": False,  # Keep False to see what's happening
    "window_size": (1920, 1080),
    "implicit_wait": 15,
    "page_load_timeout": 120,
    "script_timeout": 300,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "download_dir": str(Path("temp/downloads").absolute()),
    "chrome_options": [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--start-maximized",
    ]
}


# Column detection parameters
COLUMN_DETECTION = {
    "min_gap_width": 30,  # Minimum pixels between columns
    "text_block_threshold": 15,  # Minimum text blocks to analyze
    "confidence_threshold": 0.6,
    "sample_pages": [5, 10, 15, 20, 30, 50],  # Pages to sample for detection
    "page_margin_percent": 0.1,  # Ignore blocks within this margin
}


# Text cleaning patterns
TEXT_CLEANING = {
    "header_patterns": [
        r"^\s*\d+\s*$",  # Page numbers only
        r"^Chapter\s+\d+\s*$",  # Chapter headers without title
        r"^\s*[A-Z][a-z]+\s+\d+\s*$",  # "Chemistry 1" style headers
    ],
    "footer_patterns": [
        r"^\s*\d+\s*$",  # Page numbers
        r"^\s*www\..+$",  # URLs
        r"^\s*©.*$",  # Copyright
        r"^\s*Cambridge\s+.*$",  # Publisher footers
    ],
    "unwanted_chars": ["\x00", "\ufffd", "\u2028", "\u2029"],
    "normalize_whitespace": True,
}


# Output formats
OUTPUT_FORMATS = {
    "metadata_suffix": "_metadata.json",
    "content_suffix": "_content.json", 
    "structure_suffix": "_structure.json",
    "errors_suffix": "_errors.json",
    "summary_suffix": "_summary.json",
}


# JSON Schema for validation
STRUCTURE_SCHEMA = {
    "required_fields": ["book_info", "structure"],
    "book_info_fields": ["title"],
    "structure_item_fields": ["type", "title", "book_page_start"],
}


# Default configuration instance
config = PipelineConfig()
