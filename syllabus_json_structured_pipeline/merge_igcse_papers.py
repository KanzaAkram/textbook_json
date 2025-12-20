"""
Pipeline to merge all papers for each IGCSE, O'level, AS'Level, and Alevel subject into a single prompt file.
Excludes the 'changes_for_2023_2025_syllabus' section as requested.

For AS/Alevel: Merges AS papers first, then Alevel papers for the same subject code.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Union
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SyllabusPaperMerger:
    """Merges all papers for each subject into a single prompt file."""
    
    def __init__(self, base_path: str, level_name: str = "IGCSE"):
        """
        Initialize the merger.
        
        Args:
            base_path: Path to the 'Only Syllabus Jsons/Only Syllabus Jsons' directory
            level_name: Name of the level folder ('IGCSE', 'O'level', 'AS'Level', or 'Alevel')
        """
        self.base_path = Path(base_path) / level_name
        self.level_name = level_name
        if not self.base_path.exists():
            raise ValueError(f"Base path does not exist: {self.base_path}")
    
    def find_all_paper_folders(self, subject_path: Path) -> List[Path]:
        """
        Find all paper folders in a subject directory.
        
        Args:
            subject_path: Path to the subject folder (e.g., 0417)
            
        Returns:
            List of paths to paper folders (e.g., paper 1, paper 2, paper 3)
        """
        paper_folders = []
        for item in subject_path.iterdir():
            if item.is_dir() and item.name.startswith("paper"):
                prompt_file = item / "prompt.py"
                if prompt_file.exists():
                    paper_folders.append(item)
        return sorted(paper_folders, key=lambda x: x.name)
    
    def load_prompt_file(self, prompt_path: Path) -> Dict[str, Any]:
        """
        Load and parse a prompt.py file (which contains JSON or Python dict).
        
        Args:
            prompt_path: Path to the prompt.py file
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If file is empty or invalid
        """
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Check if file is empty
            if not content:
                raise ValueError(f"File is empty: {prompt_path}")
            
            # Try parsing as JSON first
            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract Python dict assignment
                # Look for patterns like: syllabus = {...} or data = {...}
                import re
                
                # Try to find dict assignment: variable_name = {...}
                match = re.search(r'(?:syllabus|data|content)\s*=\s*(\{.*\})', content, re.DOTALL)
                if match:
                    dict_str = match.group(1)
                    # Try to parse the dict string as JSON
                    try:
                        data = json.loads(dict_str)
                        return data
                    except json.JSONDecodeError:
                        # If that fails, try using ast.literal_eval for Python dict
                        import ast
                        try:
                            data = ast.literal_eval(dict_str)
                            return data
                        except (ValueError, SyntaxError) as e:
                            raise ValueError(f"Could not parse Python dict from {prompt_path}: {e}")
                
                # If no pattern found, raise original JSON error
                raise ValueError(f"File does not contain valid JSON or Python dict assignment: {prompt_path}")
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error reading {prompt_path}: {e}")
            raise ValueError(f"Error reading {prompt_path}: {e}")
    
    def extract_syllabus_content(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract syllabus content from different JSON structures.
        Handles:
        - {"syllabus": {"topics": [...]}}
        - [{"syllabus_name": ..., "core_content": [...]}]
        - Other variations
        
        Args:
            paper_data: Parsed JSON data from prompt.py
            
        Returns:
            Dictionary containing syllabus content (normalized structure)
        """
        # Handle array format (e.g., 0580)
        if isinstance(paper_data, list) and len(paper_data) > 0:
            paper_data = paper_data[0]
        
        # Handle different structures
        if "syllabus" in paper_data:
            # Format: {"syllabus": {...}}
            syllabus = paper_data["syllabus"]
            return {
                "syllabus_code": syllabus.get("syllabus_code"),
                "level": syllabus.get("level"),
                "title": syllabus.get("title"),
                "syllabus_name": syllabus.get("syllabus_name"),
                "years": syllabus.get("years") or syllabus.get("syllabus_years"),
                "topics": syllabus.get("topics", []),
                "core_content": syllabus.get("core_content", []),
                "extended_content": syllabus.get("extended_content", [])
            }
        elif "syllabus_name" in paper_data:
            # Format: {"syllabus_name": ..., "core_content": [...]}
            return {
                "syllabus_code": paper_data.get("syllabus_code"),
                "level": paper_data.get("level"),
                "title": paper_data.get("title"),
                "syllabus_name": paper_data.get("syllabus_name"),
                "years": paper_data.get("years") or paper_data.get("syllabus_years"),
                "topics": paper_data.get("topics", []),
                "core_content": paper_data.get("core_content", []),
                "extended_content": paper_data.get("extended_content", [])
            }
        else:
            # Unknown format, return as-is
            return paper_data
    
    def are_syllabus_contents_identical(self, content1: Dict[str, Any], content2: Dict[str, Any]) -> bool:
        """
        Check if two syllabus contents are identical (ignoring metadata like years).
        
        Args:
            content1: First syllabus content
            content2: Second syllabus content
            
        Returns:
            True if contents are identical, False otherwise
        """
        # Compare the actual content (topics, core_content, etc.)
        # Create normalized copies without metadata that might differ
        def normalize_content(content):
            normalized = {}
            if "topics" in content and content["topics"]:
                normalized["topics"] = content["topics"]
            if "core_content" in content and content["core_content"]:
                normalized["core_content"] = content["core_content"]
            if "extended_content" in content and content["extended_content"]:
                normalized["extended_content"] = content["extended_content"]
            return normalized
        
        norm1 = normalize_content(content1)
        norm2 = normalize_content(content2)
        
        # Compare JSON strings (ignoring order differences)
        try:
            json1 = json.dumps(norm1, sort_keys=True, ensure_ascii=False)
            json2 = json.dumps(norm2, sort_keys=True, ensure_ascii=False)
            return json1 == json2
        except Exception:
            # If JSON comparison fails, do deep comparison
            return norm1 == norm2
    
    def merge_papers(self, paper_data_list: List[Dict[str, Any]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Merge topics from multiple papers into a single structure.
        Handles different JSON formats.
        
        Args:
            paper_data_list: List of paper data dictionaries
            
        Returns:
            Merged dictionary with combined topics
        """
        if not paper_data_list:
            raise ValueError("No paper data provided for merging")
        
        # Extract syllabus contents
        syllabus_contents = [self.extract_syllabus_content(paper_data) for paper_data in paper_data_list]
        
        # Check if all papers have identical syllabus content
        if len(syllabus_contents) > 1:
            first_content = syllabus_contents[0]
            all_identical = all(
                self.are_syllabus_contents_identical(first_content, content)
                for content in syllabus_contents[1:]
            )
            
            if all_identical:
                logger.info(f"  All papers have identical syllabus content - copying once (no merge needed)")
                # Return the first paper's structure (without changes_for_2023_2025_syllabus)
                base_paper = paper_data_list[0]
                if isinstance(base_paper, list):
                    base_paper = base_paper[0]
                
                # Remove changes_for_2023_2025_syllabus if present
                result = base_paper.copy()
                if "changes_for_2023_2025_syllabus" in result:
                    del result["changes_for_2023_2025_syllabus"]
                
                return result
        
        # Papers have different content - merge them
        logger.info(f"  Papers have different content - merging...")
        base_content = syllabus_contents[0]
        
        # Handle topics structure (e.g., 0417)
        if base_content.get("topics"):
            return self._merge_topics_structure(syllabus_contents, paper_data_list[0])
        
        # Handle core_content structure (e.g., 0580)
        elif base_content.get("core_content"):
            return self._merge_core_content_structure(syllabus_contents, paper_data_list[0])
        
        # Unknown structure - return first paper
        else:
            logger.warning(f"  Unknown structure, returning first paper as-is")
            result = paper_data_list[0].copy()
            if isinstance(result, list):
                result = result[0].copy()
            if "changes_for_2023_2025_syllabus" in result:
                del result["changes_for_2023_2025_syllabus"]
            return result
    
    def _merge_topics_structure(self, syllabus_contents: List[Dict], base_paper: Dict) -> Dict:
        """Merge papers with topics structure."""
        topic_map = {}  # Map topic_number to topic data
        
        for content in syllabus_contents:
            topics = content.get("topics", [])
            for topic in topics:
                topic_number = topic.get("topic_number")
                
                if topic_number in topic_map:
                    # Topic already exists, merge subtopics
                    existing_topic = topic_map[topic_number]
                    existing_subtopics = {st.get("sub_topic_number"): st 
                                        for st in existing_topic.get("sub_topics", [])}
                    
                    # Add new subtopics
                    for subtopic in topic.get("sub_topics", []):
                        subtopic_number = subtopic.get("sub_topic_number")
                        if subtopic_number not in existing_subtopics:
                            existing_topic["sub_topics"].append(subtopic)
                            existing_subtopics[subtopic_number] = subtopic
                else:
                    # New topic, add it
                    topic_map[topic_number] = topic.copy()
        
        # Convert topic_map to sorted list
        merged_topics = sorted(
            topic_map.values(),
            key=lambda x: self._topic_sort_key(x.get("topic_number"))
        )
        
        # Determine base structure
        base_content = self.extract_syllabus_content(base_paper)
        
        # Check if base_paper has "syllabus" key (IGCSE format) or direct keys (O'level format)
        if isinstance(base_paper, list):
            # Array format
            return [{
                "syllabus_name": base_content.get("syllabus_name"),
                "syllabus_years": base_content.get("years"),
                "topics": merged_topics
            }]
        elif "syllabus" in base_paper:
            # IGCSE format: {"syllabus": {...}}
            return {
                "syllabus": {
                    "syllabus_code": base_content.get("syllabus_code"),
                    "level": base_content.get("level"),
                    "title": base_content.get("title"),
                    "years": base_content.get("years"),
                    "topics": merged_topics
                }
            }
        else:
            # O'level format: {"syllabus_name": ..., "topics": [...]}
            return {
                "syllabus_name": base_content.get("syllabus_name") or base_paper.get("syllabus_name"),
                "syllabus_years": base_content.get("years") or base_paper.get("syllabus_years"),
                "topics": merged_topics
            }
    
    def _merge_core_content_structure(self, syllabus_contents: List[Dict], base_paper: Dict) -> Dict:
        """Merge papers with core_content structure."""
        # For core_content, we typically just need to combine if different
        # But if identical, we already handled that
        # For now, return first paper's structure
        base_content = self.extract_syllabus_content(base_paper)
        
        if isinstance(base_paper, list):
            result = base_paper[0].copy()
            if "changes_for_2023_2025_syllabus" in result:
                del result["changes_for_2023_2025_syllabus"]
            return [result]
        else:
            result = base_paper.copy()
            if "changes_for_2023_2025_syllabus" in result:
                del result["changes_for_2023_2025_syllabus"]
            return result
    
    def _topic_sort_key(self, topic_number: str) -> tuple:
        """
        Create a sort key for topic numbers.
        Handles both numeric (e.g., "1", "2") and string (e.g., "17", "20") topic numbers.
        
        Args:
            topic_number: Topic number as string
            
        Returns:
            Tuple for sorting (int, str)
        """
        try:
            return (int(topic_number), "")
        except (ValueError, TypeError):
            return (999999, str(topic_number))
    
    def save_merged_prompt(self, merged_data: Any, output_path: Path):
        """
        Save merged data to a prompt.py file.
        Handles both dict and list formats.
        
        Args:
            merged_data: Merged data to save (dict or list)
            output_path: Path where to save the file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format JSON with proper indentation
        json_str = json.dumps(merged_data, indent=2, ensure_ascii=False)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"  Saved to: {output_path.name}")
    
    def process_subject(self, subject_code: str, output_base_path: Path = None) -> bool:
        """
        Process a single subject by merging all its papers.
        
        Args:
            subject_code: Subject code (e.g., "0417")
            output_base_path: Base path for output (if None, saves in original location)
            
        Returns:
            True if successful, False otherwise
        """
        subject_path = self.base_path / subject_code
        
        if not subject_path.exists():
            logger.warning(f"Subject folder not found: {subject_path}")
            return False
        
        logger.info(f"\nProcessing subject: {subject_code}")
        
        # Find all paper folders
        paper_folders = self.find_all_paper_folders(subject_path)
        
        if not paper_folders:
            logger.warning(f"No paper folders found in {subject_path}")
            return False
        
        logger.info(f"Found {len(paper_folders)} paper folder(s): {[p.name for p in paper_folders]}")
        
        # Load all paper data
        paper_data_list = []
        for paper_folder in paper_folders:
            prompt_file = paper_folder / "prompt.py"
            try:
                paper_data = self.load_prompt_file(prompt_file)
                paper_data_list.append(paper_data)
                logger.info(f"  Loaded: {paper_folder.name}/prompt.py")
            except Exception as e:
                logger.warning(f"  Skipping {paper_folder.name}/prompt.py: {e}")
                # Continue with other papers instead of failing completely
                continue
        
        if not paper_data_list:
            logger.error(f"  No valid papers found for {subject_code}")
            return False
        
        # Merge papers
        try:
            merged_data = self.merge_papers(paper_data_list)
            
            # Count topics/subtopics for logging
            if isinstance(merged_data, list):
                # Array format
                if merged_data and "topics" in merged_data[0]:
                    total_topics = len(merged_data[0].get("topics", []))
                    total_subtopics = sum(
                        len(topic.get("sub_topics", []))
                        for topic in merged_data[0].get("topics", [])
                    )
                    logger.info(f"  Result: {total_topics} topics, {total_subtopics} subtopics")
                elif merged_data and "core_content" in merged_data[0]:
                    total_topics = len(merged_data[0].get("core_content", []))
                    logger.info(f"  Result: {total_topics} core topics")
            elif "syllabus" in merged_data:
                # Object format with syllabus key
                total_topics = len(merged_data["syllabus"].get("topics", []))
                total_subtopics = sum(
                    len(topic.get("sub_topics", []))
                    for topic in merged_data["syllabus"].get("topics", [])
                )
                logger.info(f"  Result: {total_topics} topics, {total_subtopics} subtopics")
            elif "topics" in merged_data:
                total_topics = len(merged_data.get("topics", []))
                total_subtopics = sum(
                    len(topic.get("sub_topics", []))
                    for topic in merged_data.get("topics", [])
                )
                logger.info(f"  Result: {total_topics} topics, {total_subtopics} subtopics")
            
            # Determine output path
            if output_base_path:
                output_path = output_base_path / self.level_name / subject_code / "prompt.py"
            else:
                output_path = subject_path / "prompt.py"
            
            self.save_merged_prompt(merged_data, output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error merging papers for {subject_code}: {e}")
            return False
    
    def process_all_subjects(self, output_base_path: Path = None):
        """
        Process all subjects in the base path.
        
        Args:
            output_base_path: Base path for output (if None, saves in original location)
        """
        if not self.base_path.exists():
            logger.error(f"Base path does not exist: {self.base_path}")
            return
        
        # Find all subject folders (numeric codes)
        subject_folders = [
            item for item in self.base_path.iterdir()
            if item.is_dir() and item.name.isdigit()
        ]
        
        if not subject_folders:
            logger.warning(f"No subject folders found in {self.base_path}")
            return
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {self.level_name} subjects")
        logger.info(f"Found {len(subject_folders)} {self.level_name} subject(s) to process")
        logger.info(f"{'='*60}")
        
        success_count = 0
        failed_count = 0
        
        for subject_folder in sorted(subject_folders):
            subject_code = subject_folder.name
            if self.process_subject(subject_code, output_base_path):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"\n{self.level_name} Processing Summary:")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {failed_count}")


def process_as_alevel_separate(base_path: Path, output_base_path: Path = None):
    """
    Process AS'Level and Alevel separately (NOT merged together).
    For each level:
    1. Check if papers are identical - if so, use only one
    2. If different, merge them
    
    Args:
        base_path: Path to the 'Only Syllabus Jsons/Only Syllabus Jsons' directory
        output_base_path: Base path for output (if None, saves in original location)
    """
    as_path = base_path / "AS'Level"
    alevel_path = base_path / "Alevel"
    
    # Process AS'Level
    if as_path.exists():
        logger.info(f"\n{'='*60}")
        logger.info("Processing AS'Level")
        logger.info(f"{'='*60}")
        
        as_merger = SyllabusPaperMerger(str(base_path), "AS'Level")
        as_merger.process_all_subjects(output_base_path)
    else:
        logger.warning(f"AS'Level path does not exist: {as_path}")
    
    # Process Alevel
    if alevel_path.exists():
        logger.info(f"\n{'='*60}")
        logger.info("Processing Alevel")
        logger.info(f"{'='*60}")
        
        alevel_merger = SyllabusPaperMerger(str(base_path), "Alevel")
        alevel_merger.process_all_subjects(output_base_path)
    else:
        logger.warning(f"Alevel path does not exist: {alevel_path}")


def main():
    """Main entry point."""
    # Path to base folder containing all levels
    script_dir = Path(__file__).parent
    base_path = script_dir / "Only Syllabus Jsons" / "Only Syllabus Jsons"
    
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        logger.error("Please run this script from the syllabus_json_structured_pipeline directory")
        return
    
    # Create output folder for merged results
    output_base_path = script_dir / "merged_outputs"
    output_base_path.mkdir(exist_ok=True)
    logger.info(f"\n{'='*60}")
    logger.info(f"Output folder: {output_base_path}")
    logger.info(f"{'='*60}")
    
    # Process IGCSE
    igcse_path = base_path / "IGCSE"
    if igcse_path.exists():
        logger.info("\n" + "="*60)
        logger.info("Starting IGCSE processing...")
        logger.info("="*60)
        igcse_merger = SyllabusPaperMerger(str(base_path), "IGCSE")
        igcse_merger.process_all_subjects(output_base_path)
    else:
        logger.warning(f"IGCSE path does not exist: {igcse_path}")
    
    # Process O'level
    olevel_path = base_path / "O'level"
    if olevel_path.exists():
        logger.info("\n" + "="*60)
        logger.info("Starting O'level processing...")
        logger.info("="*60)
        olevel_merger = SyllabusPaperMerger(str(base_path), "O'level")
        olevel_merger.process_all_subjects(output_base_path)
    else:
        logger.warning(f"O'level path does not exist: {olevel_path}")
    
    # Process AS'Level and Alevel separately (not merged together)
    process_as_alevel_separate(base_path, output_base_path)
    
    logger.info(f"\n{'='*60}")
    logger.info("All processing complete!")
    logger.info(f"Merged outputs saved in: {output_base_path}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()

