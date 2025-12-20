# Final Processing Pipeline

Comprehensive note generation pipeline that combines textbook content, syllabus objectives, and Save My Exam notes using AI Studio.

## Overview

This pipeline:

1. **Matches** subtopics across 3 sources (textbook, syllabus, Save My Exam)
2. **Organizes** matched files into a staging directory
3. **Processes** each subtopic through AI Studio to generate comprehensive notes
4. **Saves** properly structured JSON output

## Architecture

### Content Hierarchy (Priority)

1. **TEXTBOOK** (Primary) - Main content source and foundation
2. **SYLLABUS** (Fencing) - Learning objectives define boundaries
3. **SAVE MY EXAM** (Secondary) - Supplementary content (filtered by syllabus)

### File Structure

```
final_processing/
├── config.py              # Configuration and paths
├── utils.py               # Utility functions
├── matcher.py             # Matches subtopics across sources
├── processor.py           # Processes through AI Studio
├── run_pipeline.py        # Master pipeline runner
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── staging/               # Organized matched files (generated)
│   ├── Alevel/
│   │   └── 9701/
│   │       ├── 23.1/
│   │       │   └── _metadata.json
│   │       ├── 23.2/
│   │       └── _manifest.json
│   └── AS'Level/
└── comprehensive_notes/   # Final AI-generated output (generated)
    ├── Alevel/
    │   └── 9701/
    │       ├── 23.1_Lattice_energy_and_Born_Haber_cycles.json
    │       └── 23.2_Enthalpies_of_solution_and_hydration.json
    └── AS'Level/
```

## Components

### 1. Config (`config.py`)

- Defines all paths (sources, staging, output)
- Contains AI prompt template
- Configuration constants

### 2. Utils (`utils.py`)

- `extract_subtopic_number()` - Extract subtopic number from filename
- `normalize_filename()` - Normalize names for matching
- `load_json_file()` / `save_json_file()` - Safe file operations
- `extract_text_from_pdf()` - Extract text from Save My Exam PDFs
- `get_subtopic_info()` - Extract info from JSON files
- `format_learning_objectives()` - Format objectives for prompt

### 3. Matcher (`matcher.py`)

Matches subtopics across all 3 sources by subtopic number (e.g., "1.1", "23.1")

**Process:**

1. Scans textbook/extracted_subtopics/
2. Scans syllabus_json_structured_pipeline/split_subtopics/
3. Scans save_my_exam/organized_by_syllabus/
4. Matches by subtopic number
5. Creates staging directory with metadata for each match
6. Generates manifest files for tracking

**Output:** Organized staging directory

### 4. Processor (`processor.py`)

Processes matched subtopics through AI Studio

**Process:**

1. Reads metadata from staging directory
2. Loads all 3 source files for each subtopic
3. Creates comprehensive prompt with correct hierarchy
4. Sends to AI Studio via Selenium
5. Parses JSON response
6. Saves structured output

**Output:** Comprehensive notes in JSON format

### 5. Pipeline Runner (`run_pipeline.py`)

Master script that runs complete pipeline

## Usage

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure textbook module is available (for AI Studio extractor)
# Should already be in workspace: ../textbook/
```

### Quick Start

```bash
# Navigate to final_processing directory
cd final_processing

# Run complete pipeline
python run_pipeline.py

# Run with test limit (first 2 subtopics per subject)
python run_pipeline.py --limit 2

# Skip matching step (use existing staging)
python run_pipeline.py --skip-matching
```

### Step-by-Step

```bash
# Step 1: Match subtopics (creates staging directory)
python matcher.py

# Step 2: Process through AI Studio (requires staging from step 1)
python processor.py

# With limit for testing
python processor.py --limit 2
```

### Command Line Options

```
run_pipeline.py:
  --skip-matching    Skip matching, use existing staging
  --limit N          Process only first N subtopics per subject

processor.py:
  --limit N          Process only first N subtopics per subject
```

## Matching Logic

### Subtopic Number Matching

Files are matched by subtopic number extracted from filename:

**Textbook:**

- `23.1_Lattice energy and Born-Haber cycles.json` → **23.1**

**Syllabus:**

- `23.1_Lattice_energy_and_Born-Haber_cycles.json` → **23.1**

**Save My Exam:**

- `23.1_Lattice_energy_and_Born_Haber_cycles_1.pdf` → **23.1**
- `23.1_Lattice_energy_and_Born_Haber_cycles_2.pdf` → **23.1** (multiple PDFs supported)

### Match Quality

- **Perfect (3/3):** All 3 sources available
- **Good (2/3):** Textbook + Syllabus OR Textbook + Save My Exam
- **Acceptable (1/3):** Only one source (will process but with warnings)

## Output Format

### Comprehensive Notes JSON Structure

```json
{
  "subtopic_number": "23.1",
  "subtopic_name": "Lattice energy and Born-Haber cycles",
  "level": "Alevel",
  "subject_code": "9701",
  "comprehensive_notes": {
    "introduction": "Brief introduction...",
    "key_concepts": [
      {
        "concept": "Lattice Energy",
        "explanation": "Detailed explanation...",
        "examples": ["Example 1", "Example 2"]
      }
    ],
    "detailed_content": {
      "section_1": {
        "heading": "Defining Lattice Energy",
        "content": "...",
        "key_points": ["...", "..."]
      }
    },
    "important_definitions": [
      {
        "term": "Lattice Energy",
        "definition": "..."
      }
    ],
    "formulas_and_equations": [
      {
        "name": "Born-Haber Cycle",
        "formula": "...",
        "explanation": "..."
      }
    ],
    "summary": "Concise summary...",
    "exam_tips": ["Tip 1", "Tip 2"],
    "common_mistakes": ["Mistake 1", "Mistake 2"]
  },
  "learning_objectives_coverage": {
    "objective_1": "covered - explanation",
    "objective_2": "covered - explanation"
  },
  "metadata": {
    "level": "Alevel",
    "subject_code": "9701",
    "subtopic_number": "23.1",
    "subtopic_name": "Lattice energy and Born-Haber cycles",
    "generated_at": "2025-12-20T10:30:00",
    "sources_used": {
      "textbook": true,
      "syllabus": true,
      "save_my_exam_count": 1
    }
  }
}
```

## Logging

All operations are logged to:

- **Console:** Real-time progress
- **File:** `final_processing.log` (detailed log)

Log levels:

- `INFO` - Progress updates, matches found, files processed
- `WARNING` - Missing files, partial matches
- `ERROR` - Processing failures, API errors
- `DEBUG` - Detailed operation info (file operations, text extraction)

## Troubleshooting

### No Matches Found

**Problem:** Matcher finds no subtopics
**Solution:**

- Check source directories exist and contain files
- Verify filenames follow pattern: `X.X_Name.json` or `X.X_Name.pdf`
- Check log for specific directory issues

### AI Studio Errors

**Problem:** Failed to communicate with AI Studio
**Solutions:**

- Check internet connection
- Verify AI Studio URL in textbook/config.py
- Check Selenium driver setup
- Verify login credentials

### JSON Parse Errors

**Problem:** Cannot parse AI response
**Solutions:**

- Check AI prompt (may be too long)
- Verify AI Studio is responding with JSON
- Check log for raw response
- Try with smaller content (reduce text in prompt)

### Missing Dependencies

**Problem:** Import errors
**Solutions:**

```bash
pip install -r requirements.txt
# Make sure textbook module is in parent directory
```

## Performance

### Processing Time

- **Matching:** ~1-5 seconds per subject
- **AI Processing:** ~60-120 seconds per subtopic
- **Complete Pipeline:** Depends on number of subtopics

### Optimization Tips

1. Use `--limit` for testing before full run
2. Run matching once, then process in batches
3. Monitor AI Studio rate limits
4. Check log file for bottlenecks

## Validation

### Checking Results

```powershell
# Count total matches
python -c "from pathlib import Path; print(sum(1 for p in Path('staging').rglob('_metadata.json')))"

# Count successful outputs
python -c "from pathlib import Path; print(len(list(Path('comprehensive_notes').rglob('*.json'))))"

# View manifest for a subject
python -c "import json; print(json.dumps(json.load(open('staging/Alevel/9701/_manifest.json')), indent=2))"
```

### Quality Checks

1. Check `_manifest.json` in staging directories
2. Verify match confidence scores
3. Review log for warnings/errors
4. Spot-check generated JSON files
5. Validate learning objectives coverage

## Next Steps

After pipeline completes:

1. Review `comprehensive_notes/` output
2. Check `final_processing.log` for any errors
3. Validate JSON structure
4. Verify learning objectives coverage
5. Use generated notes for application/API

## Support

For issues:

1. Check `final_processing.log`
2. Review this README
3. Check source file formats
4. Verify AI Studio configuration in `../textbook/config.py`
