"""
Script to:
1. Find and remove duplicate PDF files (compare by size, then content similarity)
2. Extract the heading/title from each PDF
3. Save final PDFs with correct filenames in a new folder
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import logging
from difflib import SequenceMatcher
import warnings
import re

# Suppress pdfplumber font warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pdfplumber')

# Require pdfplumber for content extraction
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("ERROR: pdfplumber is required. Install with: pip install pdfplumber")
    raise ImportError("pdfplumber is required for this script")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFDuplicateRemover:
    """Removes duplicate PDF files and extracts headings."""
    
    def __init__(self, revision_notes_path: Path, output_path: Path, similarity_threshold: float = 0.95):
        """
        Initialize the duplicate remover.
        
        Args:
            revision_notes_path: Path to revision_notes folder
            output_path: Path to save final PDFs
            similarity_threshold: Similarity threshold (0.95 = 95%)
        """
        self.revision_notes_path = Path(revision_notes_path)
        self.output_path = Path(output_path)
        self.similarity_threshold = similarity_threshold
        self.duplicates_removed = []
        self.filename_mappings = {}
        self.final_pdfs = []
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_pdf_content(self, pdf_path: Path) -> str:
        """
        Extract all text content from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        content = ""
        
        try:
            # Suppress warnings for this operation
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                content += page_text + "\n"
                        except Exception as e:
                            logger.debug(f"Error extracting text from page in {pdf_path.name}: {e}")
                            continue
        except Exception as e:
            logger.warning(f"Error extracting content from {pdf_path.name}: {e}")
        
        return content.strip()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def extract_pdf_heading(self, pdf_path: Path) -> str:
        """
        Extract heading/title from PDF.
        Looks for the blue highlighted heading (usually in metadata or first page).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted heading or empty string
        """
        heading = ""
        
        try:
            # Suppress warnings for this operation
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with pdfplumber.open(pdf_path) as pdf:
                    # Try metadata first
                    if pdf.metadata and pdf.metadata.get('Title'):
                        heading = pdf.metadata['Title']
                    
                    # Try first page - look for the blue highlighted heading
                    if not heading and len(pdf.pages) > 0:
                        first_page = pdf.pages[0]
                        text = first_page.extract_text()
                        
                        if text:
                            lines = text.split('\n')
                            # Look for heading patterns (usually appears early in the page)
                            for i, line in enumerate(lines[:15]):  # Check first 15 lines
                                line = line.strip()
                                # Heading is usually: medium length, appears before "Contents"
                                if line and 10 < len(line) < 100:
                                    # Check if next line contains "Contents" (indicates this is the heading)
                                    if i + 1 < len(lines) and 'contents' in lines[i + 1].lower():
                                        heading = line
                                        break
                                    # Or check if it looks like a topic heading
                                    if any(keyword in line.lower() for keyword in [
                                        'particles', 'atomic', 'structure', 'isotopes', 'bonding', 
                                        'reaction', 'energy', 'equilibrium', 'acid', 'base', 'organic',
                                        'mechanism', 'spectroscopy', 'ionisation', 'electronic'
                                    ]):
                                        heading = line
                                        break
                            
                            # If still no heading, use first substantial line
                            if not heading:
                                for line in lines:
                                    line = line.strip()
                                    if line and len(line) > 10 and len(line) < 150:
                                        heading = line
                                        break
            
        except Exception as e:
            logger.debug(f"Error extracting heading from {pdf_path.name}: {e}")
        
        # Fallback: use filename without extension
        if not heading:
            heading = pdf_path.stem.replace('(Cambridge (CIE) A Level Chemistry)-Revision Note', '').strip()
        
        return heading
    
    def sanitize_filename(self, text: str) -> str:
        """
        Sanitize text to create a valid filename.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized filename-safe string
        """
        import re
        # Replace invalid filename characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace & with and
        text = text.replace('&', 'and')
        # Remove extra spaces
        text = ' '.join(text.split())
        # Limit length
        if len(text) > 200:
            text = text[:200]
        return text.strip()
    
    def find_duplicates(self) -> List[Tuple[Path, List[Path]]]:
        """
        Find duplicate PDF files by comparing size and content similarity.
        
        Returns:
            List of tuples: (file_to_keep, list_of_duplicates_to_remove)
        """
        logger.info("Scanning PDF files...")
        
        # Group files by size first (with tolerance for small differences)
        size_groups = defaultdict(list)
        pdf_files = list(self.revision_notes_path.rglob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            try:
                file_size = pdf_file.stat().st_size
                # Group by size with 1% tolerance (for minor PDF variations)
                size_key = round(file_size / 100) * 100
                size_groups[size_key].append(pdf_file)
            except Exception as e:
                logger.warning(f"Error reading {pdf_file}: {e}")
        
        duplicates_to_remove = []
        processed_files = set()
        
        # For files with similar size, compare content
        for size_key, files in size_groups.items():
            if len(files) > 1:
                logger.info(f"Found {len(files)} files with similar size (~{size_key:,} bytes), checking content similarity...")
                
                # Compare each pair of files
                for i, file1 in enumerate(files):
                    if file1 in processed_files:
                        continue
                    
                    try:
                        logger.debug(f"  Extracting content from {file1.name}...")
                        content1 = self.extract_pdf_content(file1)
                        if not content1:
                            logger.warning(f"  Could not extract content from {file1.name}, skipping comparison")
                            continue
                        
                        similar_files = [file1]
                        
                        for j, file2 in enumerate(files[i+1:], start=i+1):
                            if file2 in processed_files:
                                continue
                            
                            try:
                                logger.debug(f"    Comparing with {file2.name}...")
                                content2 = self.extract_pdf_content(file2)
                                if not content2:
                                    logger.debug(f"    Could not extract content from {file2.name}, skipping")
                                    continue
                                
                                similarity = self.calculate_similarity(content1, content2)
                                
                                if similarity >= self.similarity_threshold:
                                    logger.info(f"  ✓ Similarity {similarity:.2%} - {file1.name} <-> {file2.name}")
                                    similar_files.append(file2)
                                    processed_files.add(file2)
                                else:
                                    logger.debug(f"    Similarity {similarity:.2%} (below threshold)")
                            
                            except Exception as e:
                                logger.warning(f"    Error comparing {file2.name}: {e}")
                        
                        if len(similar_files) > 1:
                            # Keep the first file (alphabetically), remove others
                            sorted_files = sorted(similar_files, key=lambda x: x.name)
                            file_to_keep = sorted_files[0]
                            files_to_remove = sorted_files[1:]
                            
                            duplicates_to_remove.append((file_to_keep, files_to_remove))
                            processed_files.add(file_to_keep)
                            for f in files_to_remove:
                                processed_files.add(f)
                    
                    except Exception as e:
                        logger.warning(f"Error processing {file1.name}: {e}")
        
        return duplicates_to_remove
    
    def remove_duplicates(self, duplicates: List[Tuple[Path, List[Path]]]) -> int:
        """
        Remove duplicate files.
        
        Args:
            duplicates: List of tuples (file_to_keep, files_to_remove)
            
        Returns:
            Number of files removed
        """
        removed_count = 0
        
        for file_to_keep, files_to_remove in duplicates:
            logger.info(f"\nKeeping: {file_to_keep.name}")
            logger.info(f"Removing {len(files_to_remove)} duplicate(s):")
            
            for file_to_remove in files_to_remove:
                try:
                    logger.info(f"  - {file_to_remove.name}")
                    file_to_remove.unlink()
                    self.duplicates_removed.append(str(file_to_remove))
                    removed_count += 1
                except Exception as e:
                    logger.error(f"  Error removing {file_to_remove.name}: {e}")
        
        return removed_count
    
    def get_base_filename(self, filename: str) -> str:
        """
        Get base filename without _1, _2, _3 suffixes.
        
        Args:
            filename: Filename with or without suffix
            
        Returns:
            Base filename without suffix
        """
        import re
        # Remove _1, _2, _3, etc. before .pdf
        base = re.sub(r'_(\d+)\.pdf$', '.pdf', filename)
        return base
    
    def get_base_filename(self, filename: str) -> str:
        """
        Get base filename without _1, _2, _3 suffixes.
        
        Args:
            filename: Filename with or without suffix
            
        Returns:
            Base filename without suffix
        """
        # Remove _1, _2, _3, etc. before .pdf
        base = re.sub(r'_(\d+)\.pdf$', '.pdf', filename)
        return base
    
    def remove_duplicate_filenames(self) -> int:
        """
        Remove duplicate PDFs in final_pdfs folder that have same base name.
        Compares content similarity and keeps only one (prefers file without suffix).
        
        Returns:
            Number of files removed
        """
        if not self.output_path.exists():
            return 0
        
        logger.info("\nChecking for duplicate filenames in final_pdfs...")
        
        pdf_files = list(self.output_path.rglob("*.pdf"))
        
        if not pdf_files:
            return 0
        
        # Group files by base name (without _1, _2 suffixes)
        base_name_groups = defaultdict(list)
        for pdf_file in pdf_files:
            base_name = self.get_base_filename(pdf_file.name)
            base_name_groups[base_name].append(pdf_file)
        
        duplicates_to_remove = []
        processed_files = set()
        
        # For files with same base name, compare content
        for base_name, files in base_name_groups.items():
            if len(files) > 1:
                logger.info(f"Found {len(files)} files with base name: {base_name}")
                
                # Compare each pair
                for i, file1 in enumerate(files):
                    if file1 in processed_files:
                        continue
                    
                    try:
                        content1 = self.extract_pdf_content(file1)
                        if not content1:
                            logger.warning(f"  Could not extract content from {file1.name}")
                            continue
                        
                        similar_files = [file1]
                        
                        for file2 in files[i+1:]:
                            if file2 in processed_files:
                                continue
                            
                            try:
                                content2 = self.extract_pdf_content(file2)
                                if not content2:
                                    continue
                                
                                similarity = self.calculate_similarity(content1, content2)
                                
                                if similarity >= self.similarity_threshold:
                                    logger.info(f"  ✓ Similarity {similarity:.2%} - {file1.name} <-> {file2.name}")
                                    similar_files.append(file2)
                                    processed_files.add(file2)
                            
                            except Exception as e:
                                logger.warning(f"  Error comparing {file2.name}: {e}")
                        
                        if len(similar_files) > 1:
                            # Keep the one without suffix (or first alphabetically)
                            sorted_files = sorted(similar_files, key=lambda x: (
                                0 if not re.search(r'_\d+\.pdf$', x.name) else 1,  # Prefer files without _1, _2
                                x.name
                            ))
                            file_to_keep = sorted_files[0]
                            files_to_remove = sorted_files[1:]
                            
                            duplicates_to_remove.append((file_to_keep, files_to_remove))
                            processed_files.add(file_to_keep)
                            for f in files_to_remove:
                                processed_files.add(f)
                    
                    except Exception as e:
                        logger.warning(f"  Error processing {file1.name}: {e}")
        
        # Remove duplicates
        removed_count = 0
        for file_to_keep, files_to_remove in duplicates_to_remove:
            logger.info(f"\nKeeping: {file_to_keep.name}")
            logger.info(f"Removing {len(files_to_remove)} duplicate(s):")
            
            for file_to_remove in files_to_remove:
                try:
                    logger.info(f"  - {file_to_remove.name}")
                    file_to_remove.unlink()
                    removed_count += 1
                except Exception as e:
                    logger.error(f"  Error removing {file_to_remove.name}: {e}")
        
        return removed_count
    
    def remove_duplicate_filenames_in_final(self) -> int:
        """
        Remove duplicate PDFs in final_pdfs folder that have same base name.
        Compares content similarity and keeps only one (prefers file without suffix).
        
        Returns:
            Number of files removed
        """
        if not self.output_path.exists():
            return 0
        
        logger.info("\nChecking for duplicate filenames in final_pdfs...")
        
        pdf_files = list(self.output_path.rglob("*.pdf"))
        
        if not pdf_files:
            return 0
        
        # Group files by base name (without _1, _2 suffixes)
        base_name_groups = defaultdict(list)
        for pdf_file in pdf_files:
            base_name = self.get_base_filename(pdf_file.name)
            base_name_groups[base_name].append(pdf_file)
        
        duplicates_to_remove = []
        processed_files = set()
        
        # For files with same base name, compare content
        for base_name, files in base_name_groups.items():
            if len(files) > 1:
                logger.info(f"Found {len(files)} files with base name: {base_name}")
                
                # Compare each pair
                for i, file1 in enumerate(files):
                    if file1 in processed_files:
                        continue
                    
                    try:
                        logger.debug(f"  Extracting content from {file1.name}...")
                        content1 = self.extract_pdf_content(file1)
                        if not content1:
                            logger.warning(f"  Could not extract content from {file1.name}")
                            continue
                        
                        similar_files = [file1]
                        
                        for file2 in files[i+1:]:
                            if file2 in processed_files:
                                continue
                            
                            try:
                                logger.debug(f"    Comparing with {file2.name}...")
                                content2 = self.extract_pdf_content(file2)
                                if not content2:
                                    continue
                                
                                similarity = self.calculate_similarity(content1, content2)
                                
                                if similarity >= self.similarity_threshold:
                                    logger.info(f"  ✓ Similarity {similarity:.2%} - {file1.name} <-> {file2.name}")
                                    similar_files.append(file2)
                                    processed_files.add(file2)
                            
                            except Exception as e:
                                logger.warning(f"    Error comparing {file2.name}: {e}")
                        
                        if len(similar_files) > 1:
                            # Keep the one without suffix (or first alphabetically)
                            sorted_files = sorted(similar_files, key=lambda x: (
                                0 if not re.search(r'_\d+\.pdf$', x.name) else 1,  # Prefer files without _1, _2
                                x.name
                            ))
                            file_to_keep = sorted_files[0]
                            files_to_remove = sorted_files[1:]
                            
                            duplicates_to_remove.append((file_to_keep, files_to_remove))
                            processed_files.add(file_to_keep)
                            for f in files_to_remove:
                                processed_files.add(f)
                    
                    except Exception as e:
                        logger.warning(f"  Error processing {file1.name}: {e}")
        
        # Remove duplicates
        removed_count = 0
        for file_to_keep, files_to_remove in duplicates_to_remove:
            logger.info(f"\nKeeping: {file_to_keep.name}")
            logger.info(f"Removing {len(files_to_remove)} duplicate(s):")
            
            for file_to_remove in files_to_remove:
                try:
                    logger.info(f"  - {file_to_remove.name}")
                    file_to_remove.unlink()
                    removed_count += 1
                except Exception as e:
                    logger.error(f"  Error removing {file_to_remove.name}: {e}")
        
        return removed_count
    
    def copy_pdfs_with_correct_names(self) -> Dict[str, str]:
        """
        Copy remaining PDFs to output folder with correct filenames based on headings.
        
        Returns:
            Dictionary mapping original filename to new filename
        """
        logger.info("\nCopying PDFs with correct filenames...")
        
        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        pdf_files = list(self.revision_notes_path.rglob("*.pdf"))
        filename_mappings = {}
        
        for pdf_file in pdf_files:
            try:
                # Extract heading
                heading = self.extract_pdf_heading(pdf_file)
                
                # Create new filename
                sanitized_heading = self.sanitize_filename(heading)
                new_filename = f"{sanitized_heading}.pdf"
                new_filepath = self.output_path / new_filename
                
                # Handle filename conflicts - but we'll clean duplicates later
                counter = 1
                original_new_filepath = new_filepath
                while new_filepath.exists():
                    new_filename = f"{sanitized_heading}_{counter}.pdf"
                    new_filepath = self.output_path / new_filename
                    counter += 1
                
                # Copy file
                import shutil
                shutil.copy2(pdf_file, new_filepath)
                
                filename_mappings[pdf_file.name] = {
                    "heading": heading,
                    "new_filename": new_filepath.name,
                    "original_path": str(pdf_file)
                }
                
                self.final_pdfs.append(str(new_filepath))
                logger.debug(f"  {pdf_file.name} -> {new_filepath.name}")
            
            except Exception as e:
                logger.warning(f"Error processing {pdf_file.name}: {e}")
                filename_mappings[pdf_file.name] = {
                    "heading": pdf_file.stem,
                    "new_filename": pdf_file.name,
                    "error": str(e)
                }
        
        return filename_mappings
    
    def process(self) -> Dict[str, any]:
        """
        Main processing function.
        
        Returns:
            Dictionary with processing results
        """
        logger.info("="*60)
        logger.info("PDF Duplicate Removal and Heading Extraction")
        logger.info(f"Similarity threshold: {self.similarity_threshold*100:.0f}%")
        logger.info("="*60)
        
        # Step 1: Find duplicates
        duplicates = self.find_duplicates()
        
        if duplicates:
            logger.info(f"\nFound {len(duplicates)} groups of duplicate files")
            total_duplicates = sum(len(files_to_remove) for _, files_to_remove in duplicates)
            logger.info(f"Total duplicate files to remove: {total_duplicates}")
            
            removed_count = self.remove_duplicates(duplicates)
            logger.info(f"\n✓ Removed {removed_count} duplicate file(s)")
        else:
            logger.info("\n✓ No duplicate files found")
            removed_count = 0
        
        # Step 2: Copy PDFs with correct filenames
        filename_mappings = self.copy_pdfs_with_correct_names()
        self.filename_mappings = filename_mappings
        
        logger.info(f"\n✓ Copied {len(filename_mappings)} PDF files to {self.output_path}")
        
        # Step 3: Remove duplicate filenames in final_pdfs (files with _1, _2 suffixes)
        final_duplicates_removed = self.remove_duplicate_filenames()
        
        if final_duplicates_removed > 0:
            logger.info(f"\n✓ Removed {final_duplicates_removed} duplicate filename(s) from final_pdfs")
        
        # Update final_pdfs list after cleanup
        self.final_pdfs = [str(f) for f in self.output_path.rglob("*.pdf")]
        
        return {
            "duplicates_removed": removed_count,
            "duplicate_files": self.duplicates_removed,
            "filename_mappings": filename_mappings,
            "final_duplicates_removed": final_duplicates_removed,
            "final_pdfs_count": len(self.final_pdfs),
            "output_folder": str(self.output_path)
        }
    
    def save_results(self, output_path: Path, results: Dict[str, any]):
        """
        Save processing results to JSON file.
        
        Args:
            output_path: Path to save results JSON
            results: Results dictionary
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✓ Results saved to: {output_path}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    revision_notes_path = script_dir / "revision_notes"
    results_output_path = script_dir / "output" / "pdf_processing_results.json"
    
    if not revision_notes_path.exists():
        logger.error(f"Revision notes path does not exist: {revision_notes_path}")
        return
    
    if not PDFPLUMBER_AVAILABLE:
        logger.error("pdfplumber is required. Install with: pip install pdfplumber")
        return
    
    # Process each subject folder
    subject_folders = [d for d in revision_notes_path.iterdir() if d.is_dir()]
    
    if not subject_folders:
        logger.warning("No subject folders found")
        return
    
    all_results = {}
    
    for subject_folder in subject_folders:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {subject_folder.name}")
        logger.info(f"{'='*60}")
        
        # Create output folder for this subject
        final_pdfs_path = script_dir / "final_pdfs" / subject_folder.name
        
        remover = PDFDuplicateRemover(
            subject_folder, 
            final_pdfs_path,
            similarity_threshold=0.95
        )
        results = remover.process()
        
        all_results[subject_folder.name] = results
    
    # Save combined results
    results_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n{'='*60}")
    logger.info("All processing complete!")
    logger.info(f"Results saved to: {results_output_path}")
    logger.info(f"Final PDFs saved to: {script_dir / 'final_pdfs'}")
    logger.info(f"{'='*60}")
    
    # Optionally run organization by syllabus
    logger.info("\n" + "="*60)
    logger.info("Next step: Run organize_pdfs_by_syllabus.py to organize PDFs by subtopics")
    logger.info("="*60)


if __name__ == "__main__":
    main()

