# PDF Processing and Organization Pipeline

This pipeline processes PDFs from `revision_notes` by:
1. Removing duplicates and extracting headings
2. Organizing PDFs by syllabus subtopics

## Quick Start

**Run the complete pipeline (recommended):**
```bash
cd save_my_exam
python main.py
```

This will automatically:
- Process all subject folders in `revision_notes/`
- Remove duplicate PDFs
- Extract headings and rename files
- Organize PDFs by syllabus subtopics

## Individual Scripts

**Step 1: Remove duplicates and extract headings**
```bash
cd save_my_exam
python remove_duplicates_and_extract_headings.py
```

**Step 2: Organize by syllabus**
```bash
cd save_my_exam
python organize_pdfs_by_syllabus.py
```

## How It Works

### Step 1: Duplicate Removal
- Compares PDFs by file size first
- Extracts content using `pdfplumber`
- Compares content similarity (95% threshold)
- Removes duplicates, keeping one instance
- Extracts headings from first page
- Renames files based on extracted headings

### Step 2: Syllabus Organization
1. **Extract Subject Code**: From folder names like `chemistry_9701`, extracts the code `9701`
2. **Find Matching Syllabus**: Searches in `merged_outputs` across all levels (AS'Level, Alevel, IGCSE, O'level)
3. **Match PDFs to Subtopics**: Uses fuzzy matching to match PDF headings to subtopic names
4. **Organize by Level**: Creates folders organized by level and subtopic number

## Output Structure

```
organized_by_syllabus/
├── AS'Level/
│   └── 9701/
│       ├── 1.1_Particles_in_the_atom_and_atomic_radius.pdf
│       ├── 1.2_Isotopes.pdf
│       ├── 1.3_Electrons_energy_levels_and_atomic_orbitals.pdf
│       └── _unmatched_Some_PDF_Name.pdf  # PDFs that couldn't be matched
├── Alevel/
│   └── 9701/
│       └── ...
└── ...
```

## Matching Algorithm

- Compares PDF filename (cleaned of common suffixes) with subtopic names
- Uses `SequenceMatcher` for fuzzy string matching
- Also checks learning objectives for additional context
- Threshold: 25% similarity minimum to match

## Notes

- PDFs that can't be matched are saved with `_unmatched_` prefix
- PDFs are saved directly in level/subject folders with format: `{subtopic_number}_{subtopic_name}.pdf`
- The script processes all subject folders automatically
- Duplicates are automatically removed during organization

