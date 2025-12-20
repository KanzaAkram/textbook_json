"""
Utility functions for Final Processing Pipeline
"""
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_subtopic_number(filename: str) -> Optional[str]:
    """
    Extract subtopic number from filename.
    
    Examples:
        - "1.1_Particles_in_the_atom.json" -> "1.1"
        - "23.1_Lattice energy and Born-Haber cycles.json" -> "23.1"
        - "23.1_Lattice_energy_and_Born_Haber_cycles_1.pdf" -> "23.1"
    
    Args:
        filename: The filename to extract from
        
    Returns:
        Subtopic number (e.g., "1.1", "23.1") or None if not found
    """
    match = re.match(r'^(\d+\.\d+)', filename)
    if match:
        return match.group(1)
    return None


def normalize_filename(filename: str) -> str:
    """
    Normalize filename for matching (lowercase, remove special chars, underscores to spaces).
    
    Args:
        filename: Filename to normalize
        
    Returns:
        Normalized filename
    """
    # Remove extension
    name = Path(filename).stem
    
    # Remove subtopic number prefix
    name = re.sub(r'^\d+\.\d+_', '', name)
    
    # Remove trailing numbers like "_1"
    name = re.sub(r'_\d+$', '', name)
    
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    
    # Remove special characters except spaces
    name = re.sub(r'[^\w\s]', '', name)
    
    # Lowercase and remove extra spaces
    name = re.sub(r'\s+', ' ', name.lower()).strip()
    
    return name


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two names (0.0 to 1.0).
    Uses simple word overlap.
    
    Args:
        name1: First name
        name2: Second name
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    words1 = set(name1.lower().split())
    words2 = set(name2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0


def load_json_file(file_path: Path) -> Optional[Dict]:
    """
    Load JSON file safely.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data or None if error
    """
    if not file_path or not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path.name}: {e}")
        return None


def save_json_file(data: Dict, file_path: Path) -> bool:
    """
    Save data to JSON file safely.
    
    Args:
        data: Data to save
        file_path: Path to save to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path.name}: {e}")
        return False


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from PDF using PyMuPDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
        
        doc.close()
        content = "\n\n".join(text_parts)
        logger.debug(f"Extracted {len(content)} chars from {pdf_path.name}")
        return content
        
    except ImportError:
        logger.warning("PyMuPDF not available. Install with: pip install PyMuPDF")
        return ""
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path.name}: {e}")
        return ""


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        name: String to sanitize
        max_length: Maximum length for filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # Replace spaces and multiple underscores
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    
    return sanitized


def format_learning_objectives(objectives: List[Dict]) -> str:
    """
    Format learning objectives for display in prompt.
    
    Args:
        objectives: List of learning objective dicts
        
    Returns:
        Formatted string
    """
    if not objectives:
        return "No specific objectives listed"
    
    formatted = []
    for obj in objectives:
        obj_num = obj.get('objective_number', '')
        desc = obj.get('description', '')
        if obj_num and desc:
            formatted.append(f"{obj_num}. {desc}")
        elif desc:
            formatted.append(f"• {desc}")
    
    return "\n".join(formatted)


def get_subtopic_info(json_data: Dict) -> Tuple[str, str, List[Dict]]:
    """
    Extract subtopic info from JSON data (works for both textbook and syllabus format).
    
    Args:
        json_data: JSON data from textbook or syllabus
        
    Returns:
        Tuple of (subtopic_number, subtopic_name, learning_objectives)
    """
    if not json_data:
        return "", "", []
    
    subtopic = json_data.get('subtopic', {})
    
    # Try different field names
    number = (subtopic.get('sub_topic_number') or 
              subtopic.get('subtopic_number') or 
              subtopic.get('number') or '')
    
    name = (subtopic.get('sub_topic_name') or 
            subtopic.get('subtopic_name') or 
            subtopic.get('name') or '')
    
    objectives = subtopic.get('learning_objectives', [])
    
    return str(number), name, objectives


def create_manifest(staging_dir: Path, matches: List[Dict], level: str, subject_code: str) -> None:
    """
    Create a manifest file documenting all matched subtopics.
    
    Args:
        staging_dir: Directory to save manifest
        matches: List of matched subtopic dicts
        level: Education level
        subject_code: Subject code
    """
    manifest = {
        "level": level,
        "subject_code": subject_code,
        "generated_at": datetime.now().isoformat(),
        "total_matches": len(matches),
        "matches": []
    }
    
    for match in matches:
        manifest["matches"].append({
            "subtopic_number": match['subtopic_number'],
            "subtopic_name": match.get('subtopic_name', ''),
            "has_textbook": match['textbook_file'] is not None,
            "has_syllabus": match['syllabus_file'] is not None,
            "save_my_exam_count": len(match['save_my_exam_files']),
            "textbook_file": str(match['textbook_file']) if match['textbook_file'] else None,
            "syllabus_file": str(match['syllabus_file']) if match['syllabus_file'] else None,
            "save_my_exam_files": [str(f) for f in match['save_my_exam_files']]
        })
    
    manifest_path = staging_dir / "_manifest.json"
    save_json_file(manifest, manifest_path)
    logger.info(f"Created manifest: {manifest_path}")
