"""
Matcher - Matches subtopics across all 3 sources and organizes them for processing.

This script:
1. Scans all 3 source folders (textbook, syllabus, save_my_exam)
2. Matches subtopics by subtopic number
3. Creates organized staging folders with matched files
4. Generates manifest for tracking
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

from config import (
    TEXTBOOK_PATH, SYLLABUS_PATH, SAVE_MY_EXAM_PATH,
    STAGING_PATH, LEVELS, LOG_FORMAT, LOG_FILE
)
from utils import (
    extract_subtopic_number, normalize_filename, load_json_file,
    save_json_file, get_subtopic_info, create_manifest, calculate_similarity
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SubtopicMatcher:
    """Matches subtopics across all 3 source directories."""
    
    def __init__(self, level: str, subject_code: str):
        self.level = level
        self.subject_code = subject_code
        self.textbook_dir = TEXTBOOK_PATH / level / subject_code
        self.syllabus_dir = SYLLABUS_PATH / level / subject_code
        self.save_my_exam_dir = SAVE_MY_EXAM_PATH / level / subject_code
        self.staging_dir = STAGING_PATH / level / subject_code
        
    def find_textbook_files(self) -> Dict[str, Path]:
        """Find all textbook JSON files and index by subtopic number."""
        files = {}
        if not self.textbook_dir.exists():
            logger.warning(f"Textbook directory not found: {self.textbook_dir}")
            return files
        
        for file in self.textbook_dir.glob("*.json"):
            subtopic_num = extract_subtopic_number(file.name)
            if subtopic_num:
                files[subtopic_num] = file
                logger.debug(f"Found textbook: {subtopic_num} - {file.name}")
        
        logger.info(f"Found {len(files)} textbook files for {self.level}/{self.subject_code}")
        return files
    
    def find_syllabus_files(self) -> Dict[str, Path]:
        """Find all syllabus JSON files and index by subtopic number."""
        files = {}
        if not self.syllabus_dir.exists():
            logger.warning(f"Syllabus directory not found: {self.syllabus_dir}")
            return files
        
        for file in self.syllabus_dir.glob("*.json"):
            subtopic_num = extract_subtopic_number(file.name)
            if subtopic_num:
                files[subtopic_num] = file
                logger.debug(f"Found syllabus: {subtopic_num} - {file.name}")
        
        logger.info(f"Found {len(files)} syllabus files for {self.level}/{self.subject_code}")
        return files
    
    def find_save_my_exam_files(self) -> Dict[str, List[Path]]:
        """Find all Save My Exam PDF files and index by subtopic number."""
        files = defaultdict(list)
        if not self.save_my_exam_dir.exists():
            logger.warning(f"Save My Exam directory not found: {self.save_my_exam_dir}")
            return dict(files)
        
        for file in self.save_my_exam_dir.glob("*.pdf"):
            subtopic_num = extract_subtopic_number(file.name)
            if subtopic_num:
                files[subtopic_num].append(file)
                logger.debug(f"Found Save My Exam: {subtopic_num} - {file.name}")
        
        total_files = sum(len(pdfs) for pdfs in files.values())
        logger.info(f"Found {total_files} Save My Exam files across {len(files)} subtopics for {self.level}/{self.subject_code}")
        return dict(files)
    
    def match_subtopics(self) -> List[Dict]:
        """
        Match subtopics across all sources by subtopic number.
        
        Returns:
            List of match dictionaries with keys:
            - subtopic_number: The subtopic number (e.g., "1.1")
            - subtopic_name: Best available name for the subtopic
            - textbook_file: Path to textbook JSON (or None)
            - syllabus_file: Path to syllabus JSON (or None)
            - save_my_exam_files: List of PDF paths
            - confidence: Match confidence score
        """
        textbook_files = self.find_textbook_files()
        syllabus_files = self.find_syllabus_files()
        save_my_exam_files = self.find_save_my_exam_files()
        
        # Get all unique subtopic numbers
        all_subtopic_nums = set(textbook_files.keys()) | set(syllabus_files.keys()) | set(save_my_exam_files.keys())
        
        matches = []
        for subtopic_num in sorted(all_subtopic_nums):
            textbook_file = textbook_files.get(subtopic_num)
            syllabus_file = syllabus_files.get(subtopic_num)
            save_my_exam_pdfs = save_my_exam_files.get(subtopic_num, [])
            
            # Get subtopic name from available sources
            subtopic_name = ""
            if textbook_file:
                data = load_json_file(textbook_file)
                _, name, _ = get_subtopic_info(data)
                subtopic_name = name
            elif syllabus_file:
                data = load_json_file(syllabus_file)
                _, name, _ = get_subtopic_info(data)
                subtopic_name = name
            
            # Calculate confidence
            source_count = sum([
                textbook_file is not None,
                syllabus_file is not None,
                len(save_my_exam_pdfs) > 0
            ])
            confidence = source_count / 3.0
            
            match = {
                'subtopic_number': subtopic_num,
                'subtopic_name': subtopic_name,
                'textbook_file': textbook_file,
                'syllabus_file': syllabus_file,
                'save_my_exam_files': save_my_exam_pdfs,
                'confidence': confidence,
                'source_count': source_count
            }
            matches.append(match)
            
            # Log match details
            sources = []
            if textbook_file:
                sources.append("Textbook")
            if syllabus_file:
                sources.append("Syllabus")
            if save_my_exam_pdfs:
                sources.append(f"SaveMyExam({len(save_my_exam_pdfs)})")
            
            logger.info(f"  Matched {subtopic_num}: {subtopic_name[:50]}... [{', '.join(sources)}]")
        
        logger.info(f"\nTotal matches: {len(matches)}")
        logger.info(f"  - With all 3 sources: {sum(1 for m in matches if m['source_count'] == 3)}")
        logger.info(f"  - With 2 sources: {sum(1 for m in matches if m['source_count'] == 2)}")
        logger.info(f"  - With 1 source: {sum(1 for m in matches if m['source_count'] == 1)}")
        
        return matches
    
    def organize_staging(self, matches: List[Dict]) -> bool:
        """
        Organize matched files into staging directory.
        Creates a folder for each subtopic with all matched files.
        
        Args:
            matches: List of match dictionaries
            
        Returns:
            True if successful
        """
        logger.info(f"\nOrganizing staging directory: {self.staging_dir}")
        
        # Create staging directory
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        
        for match in matches:
            subtopic_num = match['subtopic_number']
            subtopic_dir = self.staging_dir / subtopic_num
            subtopic_dir.mkdir(exist_ok=True)
            
            # Create metadata file
            metadata = {
                'subtopic_number': subtopic_num,
                'subtopic_name': match['subtopic_name'],
                'level': self.level,
                'subject_code': self.subject_code,
                'sources': {
                    'textbook': str(match['textbook_file']) if match['textbook_file'] else None,
                    'syllabus': str(match['syllabus_file']) if match['syllabus_file'] else None,
                    'save_my_exam': [str(f) for f in match['save_my_exam_files']]
                },
                'confidence': match['confidence']
            }
            
            metadata_path = subtopic_dir / "_metadata.json"
            save_json_file(metadata, metadata_path)
            
            # Copy/symlink files (we'll just save paths for now)
            # This makes it easy to see what will be processed
            logger.debug(f"  Organized {subtopic_num} in {subtopic_dir.name}")
        
        # Create manifest
        create_manifest(self.staging_dir, matches, self.level, self.subject_code)
        
        logger.info(f"[OK] Staging complete: {len(matches)} subtopics organized")
        return True


def match_all_levels():
    """Match subtopics for all levels and subject codes."""
    logger.info("="*80)
    logger.info("SUBTOPIC MATCHER - Organizing files for processing")
    logger.info("="*80)
    
    total_matches = 0
    
    for level in LEVELS:
        logger.info(f"\n{'='*80}")
        logger.info(f"Level: {level}")
        logger.info(f"{'='*80}")
        
        # Find all subject codes for this level
        subject_codes = set()
        
        for base_path in [TEXTBOOK_PATH, SYLLABUS_PATH, SAVE_MY_EXAM_PATH]:
            level_path = base_path / level
            if level_path.exists():
                for item in level_path.iterdir():
                    if item.is_dir():
                        subject_codes.add(item.name)
        
        if not subject_codes:
            logger.info(f"  No subject codes found for {level}")
            continue
        
        logger.info(f"  Found {len(subject_codes)} subject codes: {', '.join(sorted(subject_codes))}")
        
        for subject_code in sorted(subject_codes):
            logger.info(f"\n  Processing: {level}/{subject_code}")
            logger.info(f"  {'-'*60}")
            
            matcher = SubtopicMatcher(level, subject_code)
            matches = matcher.match_subtopics()
            
            if matches:
                matcher.organize_staging(matches)
                total_matches += len(matches)
            else:
                logger.warning(f"    No matches found for {level}/{subject_code}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"MATCHING COMPLETE")
    logger.info(f"  Total subtopics matched: {total_matches}")
    logger.info(f"  Staging directory: {STAGING_PATH}")
    logger.info(f"{'='*80}")


def main():
    """Main entry point."""
    try:
        match_all_levels()
    except Exception as e:
        logger.error(f"Error during matching: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
