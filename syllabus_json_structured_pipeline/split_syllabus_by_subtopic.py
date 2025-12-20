"""
Pipeline to split merged syllabus files into separate files for each subtopic.
Each subtopic gets its own JSON file named with subtopic number and name.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SyllabusSplitter:
    """Splits syllabus files into separate files for each subtopic."""
    
    def __init__(self, input_base_path: Path, output_base_path: Path):
        """
        Initialize the splitter.
        
        Args:
            input_base_path: Path to merged_outputs folder
            output_base_path: Path where split files will be saved
        """
        self.input_base_path = Path(input_base_path)
        self.output_base_path = Path(output_base_path)
        self.output_base_path.mkdir(parents=True, exist_ok=True)
    
    def sanitize_filename(self, text: str) -> str:
        """
        Sanitize text to create a valid filename.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized filename-safe string
        """
        # Replace spaces with underscores
        text = text.replace(" ", "_")
        # Remove or replace invalid filename characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Remove commas and other punctuation
        text = re.sub(r'[,;:!?\'"()]', '', text)
        # Replace multiple underscores with single underscore
        text = re.sub(r'_+', '_', text)
        # Remove leading/trailing underscores
        text = text.strip('_')
        return text
    
    def extract_syllabus_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract syllabus metadata from different JSON structures.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            Dictionary with syllabus metadata
        """
        syllabus_info = {}
        
        # Handle different structures
        if "syllabus" in data:
            # Format: {"syllabus": {...}}
            syllabus = data["syllabus"]
            syllabus_info = {
                "syllabus_code": syllabus.get("syllabus_code"),
                "level": syllabus.get("level"),
                "title": syllabus.get("title"),
                "syllabus_name": syllabus.get("syllabus_name"),
                "years": syllabus.get("years") or syllabus.get("syllabus_years")
            }
        elif "syllabus_name" in data:
            # Format: {"syllabus_name": ..., "topics": [...]}
            syllabus_info = {
                "syllabus_code": data.get("syllabus_code"),
                "level": data.get("level"),
                "title": data.get("title"),
                "syllabus_name": data.get("syllabus_name"),
                "years": data.get("years") or data.get("syllabus_years")
            }
        
        return syllabus_info
    
    def get_topics(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract topics array from different JSON structures.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            List of topics
        """
        if "syllabus" in data:
            return data["syllabus"].get("topics", [])
        elif "topics" in data:
            return data.get("topics", [])
        elif "core_content" in data:
            return data.get("core_content", [])
        else:
            return []
    
    def create_subtopic_file(self, subtopic: Dict[str, Any], topic: Dict[str, Any], 
                            syllabus_info: Dict[str, Any], output_dir: Path) -> bool:
        """
        Create a JSON file for a single subtopic.
        
        Args:
            subtopic: Subtopic data
            topic: Parent topic data
            syllabus_info: Syllabus metadata
            output_dir: Directory where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get subtopic number and name
            subtopic_number = subtopic.get("sub_topic_number") or subtopic.get("subtopic_number") or ""
            subtopic_name = subtopic.get("sub_topic_name") or subtopic.get("subtopic_name") or "Unknown"
            
            # Create filename
            if subtopic_number:
                filename = f"{subtopic_number}_{self.sanitize_filename(subtopic_name)}.json"
            else:
                filename = f"{self.sanitize_filename(subtopic_name)}.json"
            
            # Create subtopic JSON structure
            subtopic_data = {
                "syllabus_info": syllabus_info,
                "topic": {
                    "topic_number": topic.get("topic_number"),
                    "topic_name": topic.get("topic_name")
                },
                "subtopic": subtopic.copy()
            }
            
            # Save file
            output_path = output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(subtopic_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"  Created: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"  Error creating file for subtopic {subtopic.get('sub_topic_number', 'unknown')}: {e}")
            return False
    
    def split_syllabus_file(self, prompt_file: Path, output_dir: Path) -> int:
        """
        Split a single syllabus file into subtopic files.
        
        Args:
            prompt_file: Path to the prompt.py file to split
            output_dir: Directory where to save split files
            
        Returns:
            Number of subtopic files created
        """
        try:
            # Load the syllabus file
            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract syllabus info and topics
            syllabus_info = self.extract_syllabus_info(data)
            topics = self.get_topics(data)
            
            if not topics:
                logger.warning(f"  No topics found in {prompt_file.name}")
                return 0
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each topic and its subtopics
            subtopic_count = 0
            for topic in topics:
                topic_number = topic.get("topic_number", "unknown")
                topic_name = topic.get("topic_name", "Unknown")
                
                # Get subtopics
                subtopics = topic.get("sub_topics", []) or topic.get("subtopics", [])
                
                if not subtopics:
                    logger.debug(f"  Topic {topic_number} ({topic_name}) has no subtopics")
                    continue
                
                logger.info(f"  Processing topic {topic_number}: {topic_name} ({len(subtopics)} subtopics)")
                
                # Create file for each subtopic
                for subtopic in subtopics:
                    if self.create_subtopic_file(subtopic, topic, syllabus_info, output_dir):
                        subtopic_count += 1
            
            return subtopic_count
            
        except json.JSONDecodeError as e:
            logger.error(f"  Error parsing JSON from {prompt_file}: {e}")
            return 0
        except Exception as e:
            logger.error(f"  Error processing {prompt_file}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def process_level(self, level_name: str):
        """
        Process all subjects in a level folder.
        
        Args:
            level_name: Name of the level folder (IGCSE, O'level, AS'Level, Alevel)
        """
        level_path = self.input_base_path / level_name
        
        if not level_path.exists():
            logger.warning(f"Level path does not exist: {level_path}")
            return
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {level_name}")
        logger.info(f"{'='*60}")
        
        # Find all subject folders
        subject_folders = [
            item for item in level_path.iterdir()
            if item.is_dir() and item.name.isdigit()
        ]
        
        if not subject_folders:
            logger.warning(f"No subject folders found in {level_path}")
            return
        
        logger.info(f"Found {len(subject_folders)} subject(s)")
        
        total_subtopics = 0
        success_count = 0
        failed_count = 0
        
        for subject_folder in sorted(subject_folders):
            subject_code = subject_folder.name
            prompt_file = subject_folder / "prompt.py"
            
            if not prompt_file.exists():
                logger.warning(f"  {subject_code}: prompt.py not found")
                failed_count += 1
                continue
            
            logger.info(f"\nProcessing {level_name}/{subject_code}")
            
            # Create output directory for this subject
            output_dir = self.output_base_path / level_name / subject_code
            
            # Split the file
            subtopic_count = self.split_syllabus_file(prompt_file, output_dir)
            
            if subtopic_count > 0:
                logger.info(f"  ✓ Created {subtopic_count} subtopic file(s)")
                total_subtopics += subtopic_count
                success_count += 1
            else:
                logger.warning(f"  ✗ No subtopics created")
                failed_count += 1
        
        logger.info(f"\n{level_name} Summary:")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"  Total subtopic files: {total_subtopics}")
    
    def process_all_levels(self):
        """Process all levels in the input folder."""
        if not self.input_base_path.exists():
            logger.error(f"Input path does not exist: {self.input_base_path}")
            return
        
        # Process each level
        levels = ["IGCSE", "O'level", "AS'Level", "Alevel"]
        
        for level_name in levels:
            level_path = self.input_base_path / level_name
            if level_path.exists():
                self.process_level(level_name)
            else:
                logger.debug(f"Skipping {level_name} (folder does not exist)")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    
    # Input: merged_outputs folder
    input_base_path = script_dir / "merged_outputs"
    
    # Output: split_subtopics folder
    output_base_path = script_dir / "split_subtopics"
    
    if not input_base_path.exists():
        logger.error(f"Input path does not exist: {input_base_path}")
        logger.error("Please run the merge script first to create merged_outputs")
        return
    
    logger.info(f"\n{'='*60}")
    logger.info("Syllabus Subtopic Splitter")
    logger.info(f"{'='*60}")
    logger.info(f"Input: {input_base_path}")
    logger.info(f"Output: {output_base_path}")
    logger.info(f"{'='*60}")
    
    splitter = SyllabusSplitter(input_base_path, output_base_path)
    splitter.process_all_levels()
    
    logger.info(f"\n{'='*60}")
    logger.info("All processing complete!")
    logger.info(f"Split files saved in: {output_base_path}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()

