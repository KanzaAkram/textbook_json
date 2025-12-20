# Testing the Pipeline

## Quick Test for Subject 9701

To test the pipeline on subject 9701 only:

```bash
cd final_processing
python run_pipeline.py 9701
```

This will:
1. Find all levels (AS'Level, Alevel) that have subject 9701
2. Show you how many subtopics will be processed
3. Ask for confirmation before processing
4. Process each subtopic one by one

## Test Specific Level

To test only AS'Level for 9701:

```bash
python run_pipeline.py 9701 --level "AS'Level"
```

Or for Alevel:

```bash
python run_pipeline.py 9701 --level Alevel
```

## What It Does

1. **Matches subtopics** across all 3 sources:
   - Textbook notes from `textbook/extracted_subtopics/`
   - Syllabus JSON from `syllabus_json_structured_pipeline/split_subtopics/`
   - Save My Exam PDFs from `save_my_exam/organized_by_syllabus/`

2. **Shows preview** of what will be processed (first 10 subtopics)

3. **Asks for confirmation** before starting

4. **Processes each subtopic**:
   - Loads data from all available sources
   - Extracts text from Save My Exam PDFs
   - Sends to AI Studio to generate comprehensive notes
   - Saves output to `comprehensive_notes/Level/SubjectCode/`

5. **Waits 10 seconds** between subtopics to avoid rate limiting

## Output

Results are saved in:
```
final_processing/comprehensive_notes/
├── AS'Level/
│   └── 9701/
│       ├── 1.1_Particles_in_the_atom_and_atomic_radius.json
│       └── ...
└── Alevel/
    └── 9701/
        └── ...
```

## Example Run

```bash
PS C:\Users\kanza\OneDrive\Desktop\textbook_json\final_processing> python run_pipeline.py 9701

============================================================
Testing Pipeline for Subject: 9701
Level: ALL (will process all levels with this subject)
============================================================
Will process levels: AS'Level, Alevel

============================================================
Processing Level: AS'Level
============================================================
  Found 51 matching subtopics

  Subtopics to process:
    1.1: Textbook, Syllabus, SaveMyExam(1)
    1.2: Textbook, Syllabus, SaveMyExam(1)
    ...

  Process 51 subtopics for AS'Level/9701? (y/n): y

  [1/51] Processing subtopic 1.1...
    [OK] Completed subtopic 1.1
    Waiting 10 seconds before next subtopic...
  ...
```

## Tips

- Start with a small test (maybe just 1-2 subtopics) to make sure everything works
- The script will show you which sources are available for each subtopic
- You can interrupt with Ctrl+C if needed
- Check the log file `final_processing_test.log` for detailed information

