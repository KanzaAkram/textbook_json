"""
Main script to process and organize Save My Exams PDFs.
Combines duplicate removal and syllabus organization into one pipeline.
"""

import os
import hashlib
import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import logging
from difflib import SequenceMatcher
import warnings
import shutil

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


# Import classes from the separate modules
from remove_duplicates_and_extract_headings import PDFDuplicateRemover
from organize_pdfs_by_syllabus import PDFSyllabusOrganizer


def main():
    """Main entry point - runs complete pipeline."""
    script_dir = Path(__file__).parent
    
    logger.info("="*60)
    logger.info("Save My Exams PDF Processing Pipeline")
    logger.info("="*60)
    logger.info("This script will:")
    logger.info("  1. Remove duplicate PDFs and extract headings")
    logger.info("  2. Organize PDFs by syllabus subtopics")
    logger.info("="*60)
    
    # Setup paths
    revision_notes_path = script_dir / "revision_notes"
    final_pdfs_path = script_dir / "final_pdfs"
    merged_outputs_path = script_dir.parent / "syllabus_json_structured_pipeline" / "merged_outputs"
    organized_output_path = script_dir / "organized_by_syllabus"
    results_output_path = script_dir / "output" / "pdf_processing_results.json"
    
    # Validate paths
    if not revision_notes_path.exists():
        logger.error(f"Revision notes path does not exist: {revision_notes_path}")
        return
    
    if not PDFPLUMBER_AVAILABLE:
        logger.error("pdfplumber is required. Install with: pip install pdfplumber")
        return
    
    # ========================================================================
    # STEP 1: Remove duplicates and extract headings
    # ========================================================================
    logger.info("\n" + "="*60)
    logger.info("STEP 1: Remove Duplicates & Extract Headings")
    logger.info("="*60)
    
    subject_folders = [d for d in revision_notes_path.iterdir() if d.is_dir()]
    
    if not subject_folders:
        logger.warning("No subject folders found in revision_notes")
        return
    
    all_results = {}
    
    for subject_folder in subject_folders:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {subject_folder.name}")
        logger.info(f"{'='*60}")
        
        # Create output folder for this subject
        final_pdfs_subject_path = final_pdfs_path / subject_folder.name
        
        remover = PDFDuplicateRemover(
            subject_folder, 
            final_pdfs_subject_path,
            similarity_threshold=0.95
        )
        results = remover.process()
        
        all_results[subject_folder.name] = results
    
    # Save combined results
    results_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Step 1 complete!")
    logger.info(f"Results saved to: {results_output_path}")
    logger.info(f"Final PDFs saved to: {final_pdfs_path}")
    
    # ========================================================================
    # STEP 2: Organize by syllabus
    # ========================================================================
    logger.info("\n" + "="*60)
    logger.info("STEP 2: Organize PDFs by Syllabus")
    logger.info("="*60)
    
    if not merged_outputs_path.exists():
        logger.error(f"merged_outputs path does not exist: {merged_outputs_path}")
        logger.warning("Skipping Step 2. You can run it later when syllabus files are available.")
        return
    
    organizer = PDFSyllabusOrganizer(
        final_pdfs_path,
        merged_outputs_path,
        organized_output_path
    )
    
    # Process each subject folder
    final_subject_folders = [d for d in final_pdfs_path.iterdir() if d.is_dir()]
    
    if not final_subject_folders:
        logger.warning("No subject folders found in final_pdfs")
        return
    
    for subject_folder in final_subject_folders:
        # Extract subject code
        subject_code = organizer.extract_subject_code(subject_folder.name)
        
        if not subject_code:
            logger.warning(f"Could not extract subject code from: {subject_folder.name}")
            continue
        
        organizer.organize_pdfs_for_subject(subject_folder, subject_code)
    
    # ========================================================================
    # STEP 3: Remove duplicate filenames from organized folder
    # ========================================================================
    logger.info("\n" + "="*60)
    logger.info("STEP 3: Remove Duplicate Filenames")
    logger.info("="*60)
    
    remove_duplicate_filenames(organized_output_path)
    
    # ========================================================================
    # Summary
    # ========================================================================
    logger.info("\n" + "="*60)
    logger.info("✓ Pipeline completed successfully!")
    logger.info("="*60)
    logger.info("Results:")
    logger.info(f"  - Deduplicated PDFs: {final_pdfs_path}")
    logger.info(f"  - Organized PDFs: {organized_output_path}")
    logger.info(f"  - Processing results: {results_output_path}")
    logger.info("="*60)


def get_base_filename(filename: str) -> str:
    """
    Get base filename without _1, _2, _3 suffixes.
    Example: '1.1_Topic_1.pdf' -> '1.1_Topic.pdf'
             '1.1_Topic_2.pdf' -> '1.1_Topic.pdf'
    
    Args:
        filename: Filename with or without suffix
        
    Returns:
        Base filename without suffix
    """
    # Remove .pdf extension
    base = filename.replace('.pdf', '')
    
    # Remove trailing _1, _2, _3, etc.
    base = re.sub(r'_(\d+)$', '', base)
    
    return base.lower()


def remove_duplicate_filenames(organized_output_path: Path):
    """
    Remove duplicate PDF files based on filename.
    Checks both exact matches and base name matches (ignoring _1, _2 suffixes).
    Keeps the first occurrence and removes others.
    
    Args:
        organized_output_path: Path to organized_by_syllabus folder
    """
    if not organized_output_path.exists():
        logger.warning(f"Organized output path does not exist: {organized_output_path}")
        return
    
    total_removed = 0
    
    # Process all levels
    levels = ["AS'Level", "Alevel", "IGCSE", "O'level"]
    
    for level in levels:
        level_path = organized_output_path / level
        if not level_path.exists():
            continue
        
        # Process each subject folder in this level
        subject_folders = [d for d in level_path.iterdir() if d.is_dir()]
        
        for subject_folder in subject_folders:
            pdf_files = list(subject_folder.glob("*.pdf"))
            
            if len(pdf_files) < 2:
                continue
            
            # Group files by base filename (ignoring _1, _2 suffixes)
            base_filename_groups = defaultdict(list)
            for pdf_file in pdf_files:
                base_name = get_base_filename(pdf_file.name)
                base_filename_groups[base_name].append(pdf_file)
            
            # Remove duplicates (keep first, remove others)
            duplicates_removed = 0
            for base_name, files in base_filename_groups.items():
                if len(files) > 1:
                    # Sort by full path to keep consistent ordering
                    # Prefer files without _1, _2 suffixes
                    files_sorted = sorted(files, key=lambda x: (
                        0 if not re.search(r'_\d+\.pdf$', x.name) else 1,  # Prefer files without _1, _2
                        str(x)
                    ))
                    file_to_keep = files_sorted[0]
                    files_to_remove = files_sorted[1:]
                    
                    logger.info(f"\n  Found {len(files)} files with same base name in {level}/{subject_folder.name}:")
                    logger.info(f"    Base name: {base_name}")
                    logger.info(f"    Keeping: {file_to_keep.name}")
                    
                    for file_to_remove in files_to_remove:
                        try:
                            file_to_remove.unlink()
                            duplicates_removed += 1
                            logger.info(f"    Removed: {file_to_remove.name}")
                        except Exception as e:
                            logger.error(f"    Error removing {file_to_remove.name}: {e}")
            
            if duplicates_removed > 0:
                logger.info(f"  Removed {duplicates_removed} duplicate filename(s) from {level}/{subject_folder.name}")
                total_removed += duplicates_removed
    
    if total_removed > 0:
        logger.info(f"\n✓ Removed {total_removed} total duplicate filename(s)")
    else:
        logger.info(f"\n✓ No duplicate filenames found")


if __name__ == "__main__":
    main()

