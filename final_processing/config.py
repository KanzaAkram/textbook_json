"""
Configuration for Final Processing Pipeline
"""
from pathlib import Path

# Base paths
SCRIPT_DIR = Path(__file__).parent
WORKSPACE_ROOT = SCRIPT_DIR.parent

# Source paths
TEXTBOOK_PATH = WORKSPACE_ROOT / "textbook" / "extracted_subtopics"
SYLLABUS_PATH = WORKSPACE_ROOT / "syllabus_json_structured_pipeline" / "split_subtopics"
SAVE_MY_EXAM_PATH = WORKSPACE_ROOT / "save_my_exam" / "organized_by_syllabus"

# Output paths
STAGING_PATH = SCRIPT_DIR / "staging"  # Organized matched files
OUTPUT_PATH = SCRIPT_DIR / "comprehensive_notes"  # Final AI-generated notes

# Processing configuration
LEVELS = ["AS'Level", "Alevel", "IGCSE", "O'level"]

# AI Studio configuration
AI_PROMPT_TEMPLATE = """You are creating comprehensive, extensive study notes for a subtopic.

SUBTOPIC Information:
- Number: {subtopic_number}
- Name: {subtopic_name}
- Level: {level}
- Subject Code: {subject_code}

Learning Objectives (from Syllabus):
{learning_objectives}

CONTENT HIERARCHY:
1. TEXTBOOK (PRIMARY) - Use as the main foundation and source
2. SYLLABUS (FENCING) - Use to ensure coverage and stay within boundaries
3. SAVE MY EXAM (SECONDARY) - Use to supplement and enhance, but only within syllabus scope

GUIDELINES:
✓ Base notes primarily on textbook content
✓ Cover ALL learning objectives from syllabus
✓ Use Save My Exam to supplement ONLY if within syllabus scope
✓ If Save My Exam contradicts textbook, prioritize textbook
✓ Ignore any Save My Exam content outside syllabus boundaries
✓ Create well-structured, comprehensive notes suitable for exam preparation

---

TEXTBOOK CONTENT (PRIMARY SOURCE):
{textbook_content}

---

SYLLABUS LEARNING OBJECTIVES (BOUNDARIES):
{syllabus_content}

---

SAVE MY EXAM NOTES (SUPPLEMENTARY):
{save_my_exam_content}

---

Create comprehensive notes in JSON format:
{{
  "subtopic_number": "{subtopic_number}",
  "subtopic_name": "{subtopic_name}",
  "level": "{level}",
  "subject_code": "{subject_code}",
  "comprehensive_notes": {{
    "introduction": "Brief introduction to the subtopic",
    "key_concepts": [
      {{
        "concept": "Concept name",
        "explanation": "Detailed explanation",
        "examples": ["Example 1", "Example 2"]
      }}
    ],
    "detailed_content": {{
      "section_1": {{
        "heading": "Section heading",
        "content": "Detailed content",
        "key_points": ["Point 1", "Point 2"]
      }}
    }},
    "important_definitions": [
      {{
        "term": "Term",
        "definition": "Definition"
      }}
    ],
    "formulas_and_equations": [
      {{
        "name": "Formula name",
        "formula": "Mathematical expression",
        "explanation": "When and how to use"
      }}
    ],
    "summary": "Concise summary of main points",
    "exam_tips": ["Tip 1", "Tip 2"],
    "common_mistakes": ["Mistake 1", "Mistake 2"]
  }},
  "learning_objectives_coverage": {{
    "objective_1": "covered/detailed explanation",
    "objective_2": "covered/detailed explanation"
  }},
  "metadata": {{
    "sources": {{
      "textbook": true,
      "syllabus": true,
      "save_my_exam": true
    }},
    "generated_date": "ISO format date"
  }}
}}

Return ONLY valid JSON. No markdown formatting, no code blocks, no explanations outside JSON.
"""

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = SCRIPT_DIR / "final_processing.log"
