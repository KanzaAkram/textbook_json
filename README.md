# Textbook Processing Pipeline

A robust pipeline to extract structured content from textbook PDFs using Google AI Studio and PyMuPDF.

## Features

- **Automatic Structure Extraction**: Uses Google AI Studio to analyze textbook structure (chapters, sections, subsections)
- **Page Offset Detection**: Automatically detects the difference between PDF page numbers and book's printed page numbers
- **Multi-Column Support**: Handles 2-column layouts common in textbooks
- **Content Extraction**: Uses PyMuPDF to extract actual text content based on detected structure
- **JSON Output**: Produces clean, hierarchical JSON with all content

## Installation

```bash
pip install -r requirements.txt
```

### Requirements

- Python 3.8+
- Google Chrome browser
- Google account for AI Studio

## Usage

### Basic Usage

1. Place your PDF textbooks in the `books/` directory
2. Run the pipeline:

```bash
python main.py
```

3. The browser will open AI Studio - log in if needed
4. The pipeline will upload the PDF and extract structure
5. Output files are saved to `output/` directory

### Command Line Options

```bash
python main.py [options]

Options:
  --books DIR       Directory containing PDFs (default: books)
  --output DIR      Output directory (default: output)
  --mode MODE       Processing mode:
                    - auto: Try automatic, fallback to interactive
                    - interactive: Manual AI Studio interaction
                    - structure_only: Only extract structure
  --force           Force reprocess even if output exists
  --single FILE     Process a single PDF file
  --help-more       Show detailed usage information
```

### Examples

```bash
# Process all books in default directory
python main.py

# Process a single book
python main.py --single "books/chemistry.pdf"

# Use interactive mode (manual AI Studio interaction)
python main.py --mode interactive

# Force reprocessing of all books
python main.py --force
```

## How It Works

### Pipeline Steps

1. **PDF Analysis** (`pdf_analyzer.py`)

   - Analyzes PDF structure
   - Detects page offset (book page vs PDF page)
   - Detects column layout (1 or 2 columns)
   - Extracts embedded TOC if available

2. **AI Structure Extraction** (`ai_studio_extractor.py`)

   - Opens Google AI Studio via Selenium
   - Uploads the PDF
   - Sends a structured prompt asking for book hierarchy
   - Parses JSON response with chapters/sections/subsections

3. **Content Extraction** (`content_extractor.py`)
   - Uses PyMuPDF to extract actual text
   - Converts book page numbers to PDF page indices
   - Handles multi-column layouts correctly
   - Organizes content according to AI-detected structure

### Page Offset Handling

Textbooks often have different page numbering:

- **PDF Page**: The actual page index in the PDF (starts at 0 or 1)
- **Book Page**: The printed page number in the textbook

The pipeline automatically detects this offset by:

1. Looking for printed page numbers in header/footer regions
2. Finding where Chapter 1 or page "1" appears
3. Cross-referencing with embedded TOC if available

Example: If Chapter 1 starts on PDF page 15 but shows "Page 1" printed:

- Page offset = 14
- To find book page 50, look at PDF page 64 (50 + 14)

### Multi-Column Handling

For 2-column textbooks:

1. Pipeline detects column layout by analyzing text block positions
2. During extraction, text blocks are sorted by column first, then vertically
3. Content is extracted in proper reading order (left column top-to-bottom, then right column)

## Output Format

### Structure File (`*_structure.json`)

```json
{
  "book_info": {
    "title": "Chemistry Textbook",
    "authors": ["Author Name"],
    "publisher": "Publisher"
  },
  "page_offset": {
    "detected_offset": 12,
    "explanation": "Front matter pages i-xii before page 1"
  },
  "layout": {
    "columns": 2
  },
  "structure": [
    {
      "type": "chapter",
      "number": "1",
      "title": "Atomic Structure",
      "book_page_start": 1,
      "book_page_end": 45,
      "topics": [
        {
          "type": "section",
          "number": "1.1",
          "title": "The Atom",
          "book_page_start": 2,
          "book_page_end": 15,
          "subtopics": [...]
        }
      ]
    }
  ]
}
```

### Content File (`*_content.json`)

```json
{
  "book_info": {...},
  "page_offset": 12,
  "chapters": [
    {
      "number": "1",
      "title": "Atomic Structure",
      "book_page_start": 1,
      "book_page_end": 45,
      "pdf_page_start": 13,
      "pdf_page_end": 57,
      "topics": [
        {
          "number": "1.1",
          "title": "The Atom",
          "content": "Actual extracted text content...",
          "subtopics": [...]
        }
      ]
    }
  ]
}
```

## Troubleshooting

### "Login Required" Message

- The pipeline will wait for you to log in manually
- Log into your Google account in the browser window
- The script continues automatically after login

### PDF Upload Failed

- If automatic upload fails, you'll be prompted to upload manually
- Drag the PDF into AI Studio and press Enter to continue

### Invalid JSON Response

- Use `--mode interactive` to manually copy/paste the prompt and response
- Ensure AI Studio returns valid JSON (no markdown formatting)

### Page Numbers Wrong

- Check the detected offset in the structure file
- You can manually set offset in `config.py` via `manual_page_offset`

### Multi-Column Extraction Issues

- Verify column detection in the analysis output
- Adjust `column_detection_threshold` in `config.py` if needed

## Configuration

Edit `config.py` to customize:

```python
# Page offset settings
auto_detect_page_offset = True
manual_page_offset = 0  # Use if auto-detect fails

# Column detection
auto_detect_columns = True
default_columns = 1

# AI Studio timeout
ai_studio_timeout = 600  # seconds

# Error handling
continue_on_error = True
save_partial_results = True
```

## File Structure

```
textbook_json/
├── books/                    # Place PDFs here
├── output/                   # Output JSON files
├── cache/                    # Cached data
├── temp/                     # Temporary files
├── main.py                   # Main pipeline script
├── config.py                 # Configuration settings
├── pdf_analyzer.py           # PDF analysis module
├── ai_studio_extractor.py    # AI Studio integration
├── content_extractor.py      # Content extraction
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```
