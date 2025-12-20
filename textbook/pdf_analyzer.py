"""
PDF Analyzer - Analyzes PDF structure and detects layout
Handles page offset detection and multi-column layouts
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class PageOffset:
    """Represents the offset between PDF page numbers and book page numbers"""
    offset: int  # PDF page - Book page = offset
    confidence: float
    detected_from: str  # How it was detected
    first_content_pdf_page: int  # First PDF page with actual content (page 1)
    

@dataclass
class ColumnLayout:
    """Represents column layout information"""
    num_columns: int
    confidence: float
    gap_positions: List[float]  # X positions of column gaps
    

class PDFAnalyzer:
    """Analyzes PDF structure, layout, and page numbering"""
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(pdf_path)
        self.total_pages = len(self.doc)
        logger.info(f"Opened PDF: {self.pdf_path.name} ({self.total_pages} pages)")
        
    def analyze(self) -> Dict:
        """
        Perform complete PDF analysis
        
        Returns:
            Dictionary with all analysis results
        """
        logger.info("Starting PDF analysis...")
        
        # Basic info
        basic_info = self._get_basic_info()
        
        # Detect page offset
        page_offset = self._detect_page_offset()
        
        # Detect column layout
        column_layout = self._detect_column_layout()
        
        # Detect TOC if available
        toc = self._extract_toc()
        
        # Sample text from key pages
        sample_text = self._get_sample_text()
        
        analysis = {
            "basic_info": basic_info,
            "page_offset": {
                "offset": page_offset.offset,
                "confidence": page_offset.confidence,
                "detected_from": page_offset.detected_from,
                "first_content_pdf_page": page_offset.first_content_pdf_page
            },
            "column_layout": {
                "num_columns": column_layout.num_columns,
                "confidence": column_layout.confidence,
                "gap_positions": column_layout.gap_positions
            },
            "toc": toc,
            "sample_text": sample_text
        }
        
        logger.info(f"Analysis complete. Offset: {page_offset.offset}, Columns: {column_layout.num_columns}")
        return analysis
    
    def _get_basic_info(self) -> Dict:
        """Get basic PDF information"""
        metadata = self.doc.metadata
        
        return {
            "filename": self.pdf_path.name,
            "total_pages": self.total_pages,
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "file_size_mb": round(self.pdf_path.stat().st_size / (1024 * 1024), 2)
        }
    
    def _detect_page_offset(self) -> PageOffset:
        """
        Detect the offset between PDF page numbers and book page numbers
        
        Strategy:
        1. Look for roman numerals in early pages (preface, contents)
        2. Find where Arabic numerals (1, 2, 3...) start
        3. Match detected page numbers to PDF page indices
        """
        logger.info("Detecting page offset...")
        
        # Patterns for page numbers
        arabic_pattern = re.compile(r'\b(\d{1,3})\b')
        roman_pattern = re.compile(r'\b([ivxlcdm]+)\b', re.IGNORECASE)
        
        # Sample pages to check
        sample_range = min(50, self.total_pages)
        
        page_number_detections = []
        first_arabic_page = None
        
        for pdf_page_idx in range(sample_range):
            page = self.doc[pdf_page_idx]
            text = page.get_text("text")
            
            # Get text from typical page number locations (bottom, top)
            blocks = page.get_text("dict")["blocks"]
            page_height = page.rect.height
            page_width = page.rect.width
            
            # Look for page numbers in header/footer regions
            for block in blocks:
                if block.get("type") != 0:  # Not text
                    continue
                    
                bbox = block.get("bbox", [0, 0, 0, 0])
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("text", "")
                
                block_text = block_text.strip()
                
                # Check if in header (top 10%) or footer (bottom 10%)
                is_header = bbox[1] < page_height * 0.1
                is_footer = bbox[3] > page_height * 0.9
                is_centered = abs((bbox[0] + bbox[2]) / 2 - page_width / 2) < page_width * 0.2
                
                if (is_header or is_footer) and is_centered:
                    # Try to extract page number
                    arabic_match = arabic_pattern.search(block_text)
                    if arabic_match and len(block_text) < 10:  # Short text, likely page number
                        detected_num = int(arabic_match.group(1))
                        if 1 <= detected_num <= self.total_pages:
                            page_number_detections.append({
                                "pdf_page": pdf_page_idx,
                                "detected_number": detected_num,
                                "location": "footer" if is_footer else "header"
                            })
                            
                            if first_arabic_page is None and detected_num <= 10:
                                first_arabic_page = (pdf_page_idx, detected_num)
        
        # Calculate offset from detections
        if page_number_detections:
            # Use most common offset
            offsets = [d["pdf_page"] - d["detected_number"] + 1 for d in page_number_detections]
            offset_counter = Counter(offsets)
            most_common_offset, count = offset_counter.most_common(1)[0]
            confidence = count / len(offsets)
            
            logger.info(f"Detected offset: {most_common_offset} (confidence: {confidence:.2f})")
            
            return PageOffset(
                offset=most_common_offset,
                confidence=confidence,
                detected_from="page_number_detection",
                first_content_pdf_page=most_common_offset
            )
        
        # Fallback: Look for "Chapter 1" or similar
        for pdf_page_idx in range(sample_range):
            page = self.doc[pdf_page_idx]
            text = page.get_text("text").lower()
            
            if re.search(r'chapter\s*1[^\d]', text) or re.search(r'\b1\.\s+\w+', text):
                logger.info(f"Found Chapter 1 on PDF page {pdf_page_idx}")
                return PageOffset(
                    offset=pdf_page_idx,
                    confidence=0.6,
                    detected_from="chapter_detection",
                    first_content_pdf_page=pdf_page_idx
                )
        
        # Default: assume small offset for front matter
        logger.warning("Could not detect page offset, assuming offset of 10")
        return PageOffset(
            offset=10,
            confidence=0.3,
            detected_from="default_assumption",
            first_content_pdf_page=10
        )
    
    def _detect_column_layout(self) -> ColumnLayout:
        """
        Detect if the PDF uses single or multi-column layout
        
        Strategy:
        1. Analyze text block positions on sample pages
        2. Look for vertical gaps in the middle of pages
        3. Check consistency across pages
        """
        logger.info("Detecting column layout...")
        
        from config import COLUMN_DETECTION
        
        sample_pages = [p for p in COLUMN_DETECTION["sample_pages"] if p < self.total_pages]
        if not sample_pages:
            sample_pages = list(range(min(10, self.total_pages)))
        
        column_votes = []
        gap_positions_all = []
        
        for page_idx in sample_pages:
            page = self.doc[page_idx]
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Get text blocks
            blocks = page.get_text("dict")["blocks"]
            
            # Filter text blocks and get their x positions
            x_positions = []
            for block in blocks:
                if block.get("type") != 0:  # Not text
                    continue
                    
                bbox = block.get("bbox", [0, 0, 0, 0])
                
                # Ignore headers/footers
                if bbox[1] < page_height * 0.08 or bbox[3] > page_height * 0.92:
                    continue
                    
                # Ignore edge blocks
                if bbox[0] < page_width * 0.05 or bbox[2] > page_width * 0.95:
                    continue
                
                x_center = (bbox[0] + bbox[2]) / 2
                x_positions.append(x_center)
            
            if len(x_positions) < COLUMN_DETECTION["text_block_threshold"]:
                continue
            
            # Analyze distribution
            page_center = page_width / 2
            left_count = sum(1 for x in x_positions if x < page_center - 20)
            right_count = sum(1 for x in x_positions if x > page_center + 20)
            center_count = sum(1 for x in x_positions if page_center - 20 <= x <= page_center + 20)
            
            # If most blocks are on left AND right sides with few in center = 2 columns
            if left_count > 5 and right_count > 5 and center_count < max(left_count, right_count) * 0.3:
                column_votes.append(2)
                gap_positions_all.append(page_center)
            else:
                column_votes.append(1)
        
        if not column_votes:
            return ColumnLayout(num_columns=1, confidence=0.5, gap_positions=[])
        
        # Vote for column count
        vote_counter = Counter(column_votes)
        num_columns, vote_count = vote_counter.most_common(1)[0]
        confidence = vote_count / len(column_votes)
        
        # Average gap position
        gap_positions = []
        if num_columns == 2 and gap_positions_all:
            avg_gap = sum(gap_positions_all) / len(gap_positions_all)
            gap_positions = [avg_gap]
        
        logger.info(f"Detected {num_columns} column(s) (confidence: {confidence:.2f})")
        
        return ColumnLayout(
            num_columns=num_columns,
            confidence=confidence,
            gap_positions=gap_positions
        )
    
    def _extract_toc(self) -> List[Dict]:
        """Extract Table of Contents if embedded in PDF"""
        toc = self.doc.get_toc()
        
        if not toc:
            logger.info("No embedded TOC found")
            return []
        
        logger.info(f"Found embedded TOC with {len(toc)} entries")
        
        toc_entries = []
        for level, title, page in toc:
            toc_entries.append({
                "level": level,
                "title": title,
                "pdf_page": page  # This is already 1-indexed in PyMuPDF TOC
            })
        
        return toc_entries
    
    def _get_sample_text(self, num_pages: int = 5) -> Dict:
        """Get sample text from key pages for AI analysis"""
        samples = {}
        
        # First few pages (cover, preface, contents)
        for i in range(min(10, self.total_pages)):
            page = self.doc[i]
            samples[f"page_{i+1}"] = page.get_text("text")[:2000]  # Limit text
        
        # Middle page (content sample)
        mid_page = self.total_pages // 2
        samples[f"page_{mid_page+1}"] = self.doc[mid_page].get_text("text")[:2000]
        
        return samples
    
    def get_page_text(self, pdf_page: int) -> str:
        """Get text from a specific PDF page (0-indexed)"""
        if 0 <= pdf_page < self.total_pages:
            return self.doc[pdf_page].get_text("text")
        return ""
    
    def book_page_to_pdf_page(self, book_page: int, offset: int) -> int:
        """
        Convert book page number to PDF page index (0-indexed)
        
        Args:
            book_page: The page number as printed in the book
            offset: The page offset (detected or configured)
            
        Returns:
            PDF page index (0-indexed)
        """
        pdf_page = book_page + offset - 1  # -1 because PDF is 0-indexed
        return max(0, min(pdf_page, self.total_pages - 1))
    
    def pdf_page_to_book_page(self, pdf_page: int, offset: int) -> int:
        """
        Convert PDF page index to book page number
        
        Args:
            pdf_page: PDF page index (0-indexed)
            offset: The page offset
            
        Returns:
            Book page number as it would appear printed
        """
        return pdf_page - offset + 1
    
    def close(self):
        """Close the PDF document"""
        if hasattr(self, 'doc'):
            self.doc.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
