# Developer Guide

## Architecture Overview

The pipeline consists of 4 main components:

```
PDF File
   ↓
[PDF Analyzer] → Detect page offset, column layout, TOC
   ↓
[AI Studio Extractor] → Get hierarchical structure from AI
   ↓
[Content Extractor] → Extract text using page numbers
   ↓
JSON Output
```

## Core Components

### 1. PDF Analyzer (`pdf_analyzer.py`)

**Purpose**: Analyze PDF structure without extracting content

**Key Methods**:

- `analyze()` - Full PDF analysis
- `_detect_page_offset()` - Detect book vs PDF page numbering
- `_detect_column_layout()` - Detect 1 or 2 column layout
- `_extract_toc()` - Get embedded table of contents

**Output**: Analysis dict with:

- Basic info (pages, metadata)
- Page offset information
- Column layout detection
- Embedded TOC

### 2. AI Studio Extractor (`ai_studio_extractor.py`)

**Purpose**: Use Google AI Studio to extract book structure

**Key Methods**:

- `extract_structure()` - Main extraction via AI Studio
- `interactive_extraction()` - Manual mode with user assistance
- `_setup_driver()` - Initialize Selenium WebDriver
- `_check_and_handle_login()` - Handle authentication
- `_auto_login()` - Automatic Google login (NEW)
- `_upload_pdf()` - Upload PDF to AI Studio
- `_send_prompt()` - Send AI prompt
- `_wait_for_response()` - Get AI response
- `_parse_json_response()` - Extract JSON from response

**Requires**: Google account, Chrome browser, Selenium

### 3. Content Extractor (`content_extractor.py`)

**Purpose**: Extract actual text content from PDF

**Key Methods**:

- `extract_from_structure()` - Main extraction method
- `_extract_chapter()` - Extract chapter content
- `_extract_topic()` - Extract section content
- `_extract_page_range()` - Get text from pages
- `_extract_multicolumn_page()` - Handle 2-column layout
- `_book_to_pdf_page()` - Convert page numbers

**Features**:

- Handles page offset conversion
- Supports multi-column extraction
- Cleans and normalizes text

### 4. Configuration (`config.py`)

**Purpose**: Centralized settings and prompts

**Key Settings**:

- `GOOGLE_EMAIL`, `GOOGLE_PASSWORD` - Credentials (env vars)
- `ai_studio_url` - AI Studio endpoint
- `auto_detect_page_offset` - Auto offset detection
- `auto_detect_columns` - Auto column detection
- `auto_login_enabled` - Enable automatic login
- AI Studio prompts for structure extraction

## Data Flow

### Input: PDF File

```
mybook.pdf (600 pages, 2 columns)
```

### Step 1: PDF Analysis

```python
with PDFAnalyzer(pdf_path) as analyzer:
    analysis = analyzer.analyze()
    # Output:
    # - total_pages: 600
    # - page_offset: 10 (PDF page = book page + 10)
    # - num_columns: 2
    # - toc: [...]
```

### Step 2: AI Structure Extraction

```python
with AIStudioExtractor() as extractor:
    structure = extractor.extract_structure(pdf_path, analysis)
    # Output:
    # {
    #   "book_info": {...},
    #   "page_offset": {"detected_offset": 10, ...},
    #   "structure": [
    #     {
    #       "type": "chapter",
    #       "title": "Chapter 1",
    #       "book_page_start": 1,
    #       "book_page_end": 50,
    #       "topics": [...]
    #     }
    #   ]
    # }
```

### Step 3: Content Extraction

```python
with ContentExtractor(pdf_path) as extractor:
    content = extractor.extract_from_structure(structure, page_offset)
    # Output:
    # {
    #   "book_info": {...},
    #   "chapters": [
    #     {
    #       "title": "Chapter 1",
    #       "topics": [
    #         {
    #           "title": "Section 1",
    #           "content": "Actual text...",
    #           "book_page_start": 1,
    #           "pdf_page_start": 11,
    #           "subtopics": [...]
    #         }
    #       ]
    #     }
    #   ]
    # }
```

### Output: JSON Files

```
output/
├── mybook_structure.json (AI-generated structure)
└── mybook_content.json   (Extracted content)
```

## Key Algorithms

### Page Offset Detection

**Goal**: Find the difference between PDF page index and book's printed page number

**Approaches**:

1. **Page Number Detection** (Primary)

   - Look for Arabic numerals in header/footer regions
   - Most common, most reliable
   - Confidence score based on detections

2. **Chapter Detection** (Secondary)

   - Find "Chapter 1" or "1. " pattern
   - Less reliable but good fallback

3. **TOC Matching** (Tertiary)
   - Cross-reference with embedded TOC
   - Used by AI Studio for verification

**Formula**:

```
offset = pdf_page_index - book_page_number
book_page = pdf_page_index - offset
pdf_page = book_page + offset
```

### Column Layout Detection

**Goal**: Determine if layout is 1-column or 2-column

**Algorithm**:

1. Sample multiple pages (5, 10, 15, 20, 30, 50)
2. Extract text block positions
3. Analyze horizontal distribution
4. If blocks heavily on left AND right with gap in middle → 2 columns
5. Vote based on sample pages
6. Return most common result with confidence

### Multi-Column Text Extraction

**Goal**: Extract text in correct reading order from 2-column pages

**Algorithm**:

1. Get all text blocks with positions
2. Determine page center
3. Assign each block to column (left=0, right=1)
4. Sort by: column first, then vertical position
5. Combine: left column top-to-bottom, then right column

## Extending the Pipeline

### Adding New Extraction Strategies

```python
# In config.py
class ExtractionStrategy(Enum):
    HYBRID = "hybrid"         # Current
    AI_ONLY = "ai_only"       # Current
    PAGE_REFS = "page_refs"    # Current
    CUSTOM = "custom"          # Your new strategy
```

### Customizing AI Prompts

```python
# In config.py
AI_STUDIO_PROMPTS["custom_extraction"] = """
Your custom prompt here...
Return valid JSON with this structure:
{...}
"""
```

### Adding New Content Processors

```python
# Create new_processor.py
class CustomProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def process(self, structure):
        # Your processing logic
        return processed_data
```

## Testing

### Run All Tests

```bash
python test.py
```

### Test Specific Module

```bash
python -m pytest tests/test_pdf_analyzer.py -v
```

### Manual Testing

```bash
# Test PDF analysis
python -c "
from pdf_analyzer import PDFAnalyzer
with PDFAnalyzer('books/test.pdf') as a:
    print(a.analyze())
"

# Test configuration
python -c "
from config import config
print(config.books_dir)
"
```

## Performance Considerations

### Optimization Tips

1. **PDF Analysis**

   - Sample fewer pages for large PDFs
   - Cache analysis results

2. **AI Processing**

   - Batch multiple PDFs for efficiency
   - Use timeout to prevent hangs

3. **Content Extraction**

   - Process chapters in parallel (if enabled)
   - Skip image extraction for speed

4. **Memory**
   - Close PDF handles properly
   - Use context managers (with statements)

### Benchmarks

For a typical 500-page 2-column textbook:

- PDF Analysis: 2-3 seconds
- AI Processing: 2-5 minutes
- Content Extraction: 10-15 seconds
- **Total**: 3-6 minutes per book

## Error Handling

### Common Issues and Solutions

**Issue**: `ModuleNotFoundError: No module named 'pdf_analyzer'`

- **Solution**: Run from correct directory, ensure Python path is set

**Issue**: Login timeout

- **Solution**: Set GOOGLE_EMAIL and GOOGLE_PASSWORD, or log in manually

**Issue**: JSON parsing failed

- **Solution**: Use `--mode interactive` for manual JSON input

**Issue**: Wrong page numbers

- **Solution**: Check detected offset in structure JSON, adjust if needed

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all functions

### Adding Features

1. Create new module or update existing
2. Add configuration options to `config.py`
3. Update `main.py` to use new feature
4. Add tests
5. Update documentation

### Testing Before Submit

```bash
python test.py  # All tests pass
pylint *.py     # Code style check
python main.py  # Pipeline runs successfully
```

## Troubleshooting Development

### Enable Debug Logging

```python
# In config.py
log_level = "DEBUG"
```

### Inspect Intermediate Data

```python
# Save intermediate results
json.dump(analysis, open("debug_analysis.json", "w"), indent=2)
json.dump(structure, open("debug_structure.json", "w"), indent=2)
```

### Profile Performance

```bash
python -m cProfile -s cumtime main.py
```

## Future Enhancements

- [ ] Multi-language support
- [ ] OCR for scanned PDFs
- [ ] Database storage option
- [ ] Web UI for management
- [ ] Parallel PDF processing
- [ ] Advanced table extraction
- [ ] Equation recognition
- [ ] Citation extraction
