# Save My Exams Content Extractor

This pipeline extracts revision notes content from Save My Exams website.

## Features

1. **Automatic Syllabus Detection**: Reads syllabus name from `syllabus_json` file
2. **Google Search**: Automatically searches for Save My Exams revision notes
3. **Content Extraction**: Extracts topic structure and content from Save My Exams pages
4. **Dropdown Expansion**: Automatically expands all collapsible sections
5. **JSON Output**: Creates structured JSON output matching the syllabus format

## Installation

Make sure you have the required dependencies:

```bash
pip install selenium undetected-chromedriver webdriver-manager
```

Or install from the main requirements.txt:

```bash
cd ..
pip install -r requirements.txt
```

## Usage

### Main Extraction

```bash
cd save_my_exam
python main.py
```

### Test Extraction

```bash
cd save_my_exam
python test_extraction.py
```

## How It Works

1. **Load Syllabus**: Reads `books/syllabus_json` to get the syllabus name
2. **Google Search**: Searches Google for "{syllabus_name} save my exam revision note"
3. **Navigate**: Clicks the first Save My Exams revision note link
4. **Expand Dropdowns**: Automatically expands all collapsible sections on the page
5. **Extract Structure**: Identifies topics (1, 2, 3...) and subtopics (1.1, 1.2...)
6. **Extract Content**: Extracts text content for each subtopic
7. **Save JSON**: Creates structured JSON output

## Output

The extracted content is saved to `save_my_exam/output/save_my_exam_content.json` with the following structure:

```json
{
  "syllabus_name": "Cambridge International AS & A Level Chemistry 9701",
  "source_url": "https://www.savemyexams.com/...",
  "extraction_date": "2024-01-01 12:00:00",
  "topics": [
    {
      "topic_number": "1",
      "topic_name": "Atomic structure",
      "sub_topics": [
        {
          "sub_topic_number": "1.1",
          "sub_topic_name": "Particles in the atom and atomic radius",
          "content": "Extracted text content from the page...",
          "sub_subtopics": [
            {
              "name": "Sub-subtopic name",
              "content": "Sub-subtopic content"
            }
          ]
        }
      ]
    }
  ]
}
```

## Notes

- The script will automatically handle Google search and navigation
- All dropdowns are expanded automatically
- Content is extracted for each subtopic and sub-subtopic
- Manual intervention may be required if:
  - Google search doesn't find the right link (you'll be prompted to navigate manually)
  - The page structure is different than expected
  - CAPTCHA or login is required

## Troubleshooting

### Google Search Not Finding Link
If the automatic Google search doesn't find the right link, the script will pause and ask you to manually navigate to the Save My Exams revision notes page. Once you're on the page, press Enter to continue.

### No Topics Extracted
If no topics are found, the script will try alternative extraction methods. You may need to:
- Ensure all dropdowns are expanded (the script does this automatically)
- Check that the page has loaded completely
- Verify the page structure matches expected format

### Content Not Extracted
If content is not extracted for subtopics:
- The script will still save the structure
- You can manually review the output JSON
- Try running the extraction again after ensuring the page is fully loaded

