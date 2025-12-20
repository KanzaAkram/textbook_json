"""
Script to organize PDFs by syllabus subtopics.
Matches PDFs from final_pdfs to syllabus structure in merged_outputs.
"""

import json
import re
import ast
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import logging
from difflib import SequenceMatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFSyllabusOrganizer:
    """Organizes PDFs by matching them to syllabus subtopics."""
    
    def __init__(self, final_pdfs_path: Path, merged_outputs_path: Path, organized_output_path: Path):
        """
        Initialize the organizer.
        
        Args:
            final_pdfs_path: Path to final_pdfs folder
            merged_outputs_path: Path to merged_outputs folder
            organized_output_path: Path to save organized PDFs
        """
        self.final_pdfs_path = Path(final_pdfs_path)
        self.merged_outputs_path = Path(merged_outputs_path)
        self.organized_output_path = Path(organized_output_path)
        self.subject_code_map = {}  # Maps folder names to subject codes
        self.copied_pdfs = set()  # Track source PDFs that have been copied (to avoid duplicates)
    
    def extract_subject_code(self, folder_name: str) -> Optional[str]:
        """
        Extract subject code from folder name.
        Examples: 'chemistry_9701' -> '9701', 'physics_0625' -> '0625'
        
        Args:
            folder_name: Name of the subject folder
            
        Returns:
            Subject code or None if not found
        """
        # Pattern: subject_code at the end (e.g., chemistry_9701, physics_0625)
        match = re.search(r'_(\d{4})$', folder_name)
        if match:
            return match.group(1)
        
        # Alternative: just numbers (e.g., 9701)
        match = re.search(r'(\d{4})', folder_name)
        if match:
            return match.group(1)
        
        return None
    
    def load_syllabus_json(self, prompt_path: Path) -> Optional[Dict]:
        """
        Load syllabus JSON from prompt.py file.
        
        Args:
            prompt_path: Path to prompt.py file
            
        Returns:
            Parsed syllabus dictionary or None
        """
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return None
                
                # Try JSON first
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Try Python dict assignment
                    if content.startswith("syllabus = {") or content.startswith("{"):
                        dict_str = content[content.find('{'):]
                        return ast.literal_eval(dict_str)
                    return None
        except Exception as e:
            logger.warning(f"Error loading syllabus from {prompt_path}: {e}")
            return None
    
    def find_matching_syllabus(self, subject_code: str) -> List[Tuple[str, Path, Dict]]:
        """
        Find matching syllabus files for a subject code across all levels.
        
        Args:
            subject_code: Subject code (e.g., '9701')
            
        Returns:
            List of tuples (level_name, prompt_path, syllabus_data)
        """
        matches = []
        levels = ["AS'Level", "Alevel", "IGCSE", "O'level"]
        
        for level in levels:
            level_path = self.merged_outputs_path / level / subject_code
            prompt_path = level_path / "prompt.py"
            
            if prompt_path.exists():
                syllabus_data = self.load_syllabus_json(prompt_path)
                if syllabus_data:
                    matches.append((level, prompt_path, syllabus_data))
                    logger.info(f"Found syllabus: {level}/{subject_code}")
        
        return matches
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def match_pdf_to_subtopic(self, pdf_heading: str, subtopic_name: str, 
                              learning_objectives: List[Dict] = None) -> float:
        """
        Match a PDF heading to a subtopic name.
        
        Args:
            pdf_heading: PDF heading/title
            subtopic_name: Subtopic name from syllabus
            learning_objectives: Optional learning objectives for additional matching
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Direct match with subtopic name
        similarity = self.calculate_similarity(pdf_heading, subtopic_name)
        
        # Also check learning objectives if available
        if learning_objectives:
            for obj in learning_objectives:
                desc = obj.get('description', '')
                obj_similarity = self.calculate_similarity(pdf_heading, desc)
                similarity = max(similarity, obj_similarity)
        
        # Check for keyword matches
        pdf_keywords = set(re.findall(r'\b\w+\b', pdf_heading.lower()))
        subtopic_keywords = set(re.findall(r'\b\w+\b', subtopic_name.lower()))
        
        if pdf_keywords and subtopic_keywords:
            keyword_overlap = len(pdf_keywords & subtopic_keywords) / len(pdf_keywords | subtopic_keywords)
            similarity = max(similarity, keyword_overlap * 0.8)  # Weight keyword matches slightly less
        
        return similarity
    
    def sanitize_filename(self, text: str) -> str:
        """
        Sanitize text for use in filename.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized filename-safe string
        """
        # Replace spaces and special characters with underscores
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text.strip('_')
    
    def extract_pdf_heading_from_filename(self, pdf_filename: str) -> str:
        """
        Extract heading from PDF filename.
        Removes common suffixes like "Cambridge (CIE) A Level Chemistry Revision Notes 2023"
        
        Args:
            pdf_filename: PDF filename
            
        Returns:
            Cleaned heading
        """
        # Remove .pdf extension
        heading = pdf_filename.replace('.pdf', '')
        
        # Remove common suffixes
        patterns = [
            r'\s*Cambridge\s*\(CIE\)\s*A\s*Level\s*Chemistry\s*Revision\s*Notes\s*\d{4}.*$',
            r'\s*Cambridge\s*\(CIE\)\s*.*Revision\s*Notes.*$',
            r'\s*Revision\s*Note.*$',
            r'\s*\(Cambridge.*\)$',
            r'\s*Cambridge\s*\(CIE\).*$',
        ]
        
        for pattern in patterns:
            heading = re.sub(pattern, '', heading, flags=re.IGNORECASE)
        
        # Remove trailing underscores and numbers (like _1, _2)
        heading = re.sub(r'_\d+$', '', heading)
        
        return heading.strip()
    
    def organize_pdfs_for_subject(self, subject_folder: Path, subject_code: str):
        """
        Organize PDFs for a single subject by matching to syllabus subtopics.
        
        Args:
            subject_folder: Folder containing PDFs for this subject
            subject_code: Subject code (e.g., '9701')
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Organizing PDFs for: {subject_folder.name} (Code: {subject_code})")
        logger.info(f"{'='*60}")
        
        # Find matching syllabi
        syllabi = self.find_matching_syllabus(subject_code)
        
        if not syllabi:
            logger.warning(f"No matching syllabus found for code {subject_code}")
            return
        
        # Get all PDFs
        pdf_files = list(subject_folder.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {subject_folder.name}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        logger.info(f"Found {len(syllabi)} matching syllabus file(s)")
        
        # Process each syllabus level
        for level, prompt_path, syllabus_data in syllabi:
            logger.info(f"\nProcessing level: {level}")
            
            # Extract topics and subtopics
            topics = syllabus_data.get('topics', [])
            if not topics:
                logger.warning(f"No topics found in {level}/{subject_code}")
                continue
            
            # Create organized folder structure
            organized_level_path = self.organized_output_path / level / subject_code
            organized_level_path.mkdir(parents=True, exist_ok=True)
            
            # Match PDFs to subtopics
            matched_pdfs = defaultdict(list)  # subtopic_number -> [pdf_files]
            unmatched_pdfs = []
            
            # Track PDFs already processed for this level to avoid duplicates
            processed_pdfs_this_level = set()
            
            for pdf_file in pdf_files:
                # Skip if this PDF was already processed in this level
                pdf_key = (pdf_file.name, pdf_file.stat().st_size)
                if pdf_key in processed_pdfs_this_level:
                    continue
                processed_pdfs_this_level.add(pdf_key)
                pdf_heading = self.extract_pdf_heading_from_filename(pdf_file.name)
                best_match = None
                best_score = 0.0
                
                # Try to match to each subtopic
                for topic in topics:
                    subtopics = topic.get('sub_topics', []) or topic.get('subtopics', [])
                    
                    for subtopic in subtopics:
                        subtopic_name = subtopic.get('sub_topic_name') or subtopic.get('subtopic_name', '')
                        subtopic_number = subtopic.get('sub_topic_number') or subtopic.get('subtopic_number', '')
                        learning_objectives = subtopic.get('learning_objectives', [])
                        
                        if not subtopic_name or not subtopic_number:
                            continue
                        
                        # Calculate similarity
                        similarity = self.match_pdf_to_subtopic(
                            pdf_heading, 
                            subtopic_name,
                            learning_objectives
                        )
                        
                        if similarity > best_score:
                            best_score = similarity
                            best_match = {
                                'subtopic_number': subtopic_number,
                                'subtopic_name': subtopic_name,
                                'topic_number': topic.get('topic_number', ''),
                                'topic_name': topic.get('topic_name', ''),
                                'similarity': similarity
                            }
                
                # If good match (threshold: 0.25 for broader matching), organize it
                if best_match and best_score >= 0.25:
                    subtopic_key = best_match['subtopic_number']
                    matched_pdfs[subtopic_key].append({
                        'pdf_file': pdf_file,
                        'match_info': best_match
                    })
                    logger.debug(f"  Matched: {pdf_file.name} -> {best_match['subtopic_number']} ({best_score:.2%})")
                else:
                    unmatched_pdfs.append({
                        'pdf_file': pdf_file,
                        'heading': pdf_heading,
                        'best_score': best_score
                    })
            
            # Copy PDFs directly to level/subject folder with renamed filenames
            for subtopic_number, pdf_matches in matched_pdfs.items():
                # Get subtopic name from first match
                subtopic_name = pdf_matches[0]['match_info']['subtopic_name']
                
                # Sanitize subtopic name for filename
                sanitized_subtopic_name = self.sanitize_filename(subtopic_name)
                
                # Copy each PDF with new filename format: subtopic_number_sanitized_name.pdf
                for i, match in enumerate(pdf_matches):
                    try:
                        import shutil
                        
                        # Create filename: 1.1_Particles_in_the_atom.pdf
                        if len(pdf_matches) == 1:
                            # Single PDF for this subtopic
                            new_filename = f"{subtopic_number}_{sanitized_subtopic_name}.pdf"
                        else:
                            # Multiple PDFs for same subtopic - add index
                            new_filename = f"{subtopic_number}_{sanitized_subtopic_name}_{i+1}.pdf"
                        
                        dest_path = organized_level_path / new_filename
                        
                        # Ensure parent folder exists
                        if not organized_level_path.exists():
                            organized_level_path.mkdir(parents=True, exist_ok=True)
                        
                        # Ensure source file exists
                        if not match['pdf_file'].exists():
                            logger.error(f"Source file does not exist: {match['pdf_file']}")
                            continue
                        
                        # Handle filename conflicts
                        counter = 1
                        original_dest_path = dest_path
                        while dest_path.exists():
                            if len(pdf_matches) == 1:
                                new_filename = f"{subtopic_number}_{sanitized_subtopic_name}_{counter}.pdf"
                            else:
                                new_filename = f"{subtopic_number}_{sanitized_subtopic_name}_{i+1}_{counter}.pdf"
                            dest_path = organized_level_path / new_filename
                            counter += 1
                        
                        shutil.copy2(match['pdf_file'], dest_path)
                        logger.info(f"  Copied: {match['pdf_file'].name} -> {level}/{subject_code}/{dest_path.name}")
                    except FileNotFoundError as e:
                        logger.error(f"File not found error copying {match['pdf_file'].name}: {e}")
                        logger.error(f"  Source: {match['pdf_file']}")
                        continue
                    except Exception as e:
                        logger.error(f"Error copying {match['pdf_file'].name}: {e}")
                        logger.error(f"  Source: {match['pdf_file']}")
                        logger.error(f"  Destination: {dest_path}")
                        continue
            
            # Save unmatched PDFs with "_unmatched_" prefix directly in level folder
            if unmatched_pdfs:
                logger.warning(f"\n  {len(unmatched_pdfs)} PDF(s) could not be matched:")
                for unmatched in unmatched_pdfs:
                    try:
                        import shutil
                        # Save with _unmatched_ prefix
                        original_name = unmatched['pdf_file'].stem
                        dest_filename = f"_unmatched_{original_name}.pdf"
                        dest_path = organized_level_path / dest_filename
                        
                        # Handle conflicts
                        counter = 1
                        original_dest_path = dest_path
                        while dest_path.exists():
                            dest_filename = f"_unmatched_{original_name}_{counter}.pdf"
                            dest_path = organized_level_path / dest_filename
                            counter += 1
                        
                        shutil.copy2(unmatched['pdf_file'], dest_path)
                        logger.warning(f"    - {unmatched['pdf_file'].name} -> {dest_path.name} (best score: {unmatched['best_score']:.2%})")
                    except Exception as e:
                        logger.error(f"Error copying unmatched PDF {unmatched['pdf_file'].name}: {e}")
                        continue
        
        logger.info(f"\n✓ Organization complete for {subject_folder.name}")
        
        # Post-process: Remove duplicate files from organized folder
        self.remove_duplicates_from_organized(subject_code)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Error calculating hash for {file_path.name}: {e}")
            return ""
    
    def remove_duplicates_from_organized(self, subject_code: str):
        """
        Remove duplicate PDFs from organized folder by comparing file hashes.
        
        Args:
            subject_code: Subject code to process
        """
        logger.info(f"\nChecking for duplicates in organized folder for {subject_code}...")
        
        # Check all levels
        levels = ["AS'Level", "Alevel", "IGCSE", "O'level"]
        total_removed = 0
        
        for level in levels:
            level_path = self.organized_output_path / level / subject_code
            if not level_path.exists():
                continue
            
            pdf_files = list(level_path.glob("*.pdf"))
            if len(pdf_files) < 2:
                continue
            
            # Group files by hash
            hash_groups = defaultdict(list)
            for pdf_file in pdf_files:
                file_hash = self.calculate_file_hash(pdf_file)
                if file_hash:
                    hash_groups[file_hash].append(pdf_file)
            
            # Remove duplicates (keep first file, remove others)
            duplicates_removed = 0
            for file_hash, files in hash_groups.items():
                if len(files) > 1:
                    # Sort by filename to keep consistent ordering
                    files_sorted = sorted(files, key=lambda x: x.name)
                    file_to_keep = files_sorted[0]
                    files_to_remove = files_sorted[1:]
                    
                    logger.info(f"\n  Found {len(files)} duplicate(s) in {level}/{subject_code}:")
                    logger.info(f"    Keeping: {file_to_keep.name}")
                    
                    for file_to_remove in files_to_remove:
                        try:
                            file_to_remove.unlink()
                            duplicates_removed += 1
                            logger.info(f"    Removed: {file_to_remove.name}")
                        except Exception as e:
                            logger.error(f"    Error removing {file_to_remove.name}: {e}")
            
            if duplicates_removed > 0:
                logger.info(f"  Removed {duplicates_removed} duplicate(s) from {level}/{subject_code}")
                total_removed += duplicates_removed
        
        if total_removed > 0:
            logger.info(f"\n✓ Removed {total_removed} total duplicate(s) for {subject_code}")
        else:
            logger.info(f"\n✓ No duplicates found for {subject_code}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    final_pdfs_path = script_dir / "final_pdfs"
    merged_outputs_path = script_dir.parent / "syllabus_json_structured_pipeline" / "merged_outputs"
    organized_output_path = script_dir / "organized_by_syllabus"
    
    if not final_pdfs_path.exists():
        logger.error(f"final_pdfs path does not exist: {final_pdfs_path}")
        return
    
    if not merged_outputs_path.exists():
        logger.error(f"merged_outputs path does not exist: {merged_outputs_path}")
        return
    
    organizer = PDFSyllabusOrganizer(
        final_pdfs_path,
        merged_outputs_path,
        organized_output_path
    )
    
    # Process each subject folder
    subject_folders = [d for d in final_pdfs_path.iterdir() if d.is_dir()]
    
    if not subject_folders:
        logger.warning("No subject folders found in final_pdfs")
        return
    
    for subject_folder in subject_folders:
        # Extract subject code
        subject_code = organizer.extract_subject_code(subject_folder.name)
        
        if not subject_code:
            logger.warning(f"Could not extract subject code from: {subject_folder.name}")
            continue
        
        organizer.organize_pdfs_for_subject(subject_folder, subject_code)
    
    logger.info(f"\n{'='*60}")
    logger.info("All organization complete!")
    logger.info(f"Organized PDFs saved to: {organized_output_path}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()

