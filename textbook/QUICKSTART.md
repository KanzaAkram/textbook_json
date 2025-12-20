# Quick Start Guide

## For First-Time Users

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set Up Automatic Login

```bash
python setup_credentials.py
```

Then follow the prompts to enter your Google credentials.

### 3. Place Your Textbooks

Copy PDF files to the `books/` directory

### 4. Run the Pipeline

```bash
python main.py
```

## Common Commands

```bash
# Process all books in books/ directory
python main.py

# Process a single book
python main.py --single "books/mybook.pdf"

# Interactive mode (manual AI Studio interaction)
python main.py --mode interactive

# Extract structure only (no content extraction)
python main.py --mode structure_only

# Force reprocess existing outputs
python main.py --force

# Show help
python main.py --help-more
```

## Understanding the Output

Each processed book generates:

1. **`<book>_structure.json`** - Hierarchical structure with:

   - Book metadata (title, authors, pages)
   - Page offset information
   - Complete chapter/section hierarchy with page numbers
   - Layout information (1 or 2 columns)

2. **`<book>_content.json`** - Full content with:
   - All chapters with topics and subtopics
   - Actual extracted text for each section
   - Page range mappings
   - Extraction statistics

## Troubleshooting

### "No module named pdf_analyzer"

- Make sure you're in the correct directory
- Try: `python main.py --help`

### Login issues

- If automatic login fails, you'll see a browser window
- Log in manually and the script continues
- Or set up credentials with: `python setup_credentials.py`

### Wrong page numbers

- Check the `_structure.json` file for detected page offset
- If wrong, adjust `manual_page_offset` in `config.py`

### Multi-column extraction looks wrong

- Verify the column detection in the analysis output
- Adjust `column_detection_threshold` in `config.py`

## File Structure

```
textbook_json/
├── books/                    ← Place PDFs here
├── output/                   ← Output files appear here
├── cache/                    ← Cached data
├── temp/                     ← Temporary files
│
├── main.py                   ← Main entry point
├── config.py                 ← Configuration
├── pdf_analyzer.py           ← PDF analysis
├── ai_studio_extractor.py    ← Google AI Studio integration
├── content_extractor.py      ← Content extraction
├── utils.py                  ← Utilities
├── setup_credentials.py      ← Credential setup
│
├── requirements.txt          ← Dependencies
├── README.md                 ← Full documentation
└── QUICKSTART.md             ← This file
```

## Advanced Usage

### Using with Docker

```bash
docker build -t textbook-pipeline .
docker run -it -v $(pwd)/books:/app/books -v $(pwd)/output:/app/output textbook-pipeline
```

### Batch Processing

```bash
# Create a script to process multiple directories
for dir in /path/to/textbooks/*; do
    python main.py --books "$dir" --output "./output/$(basename $dir)"
done
```

### Parallel Processing

Edit `config.py`:

```python
parallel_processing = True
max_workers = 4
```

## Performance Tips

1. **First run may be slow** - PDF analysis and AI processing take time
2. **Use `--force` sparingly** - Reprocessing is computationally expensive
3. **Large books (500+ pages)** - May take 5-10 minutes per book
4. **Disable image extraction** - Set `extract_images = False` in config.py

## Getting Help

1. Check [README.md](README.md) for detailed documentation
2. Run `python main.py --help-more` for command options
3. Check the log file: `textbook_pipeline.log`
4. Review output JSON structure for data validation

## Next Steps

- Explore the JSON output files
- Customize `config.py` for your needs
- Integrate the pipeline into your workflow
- Share feedback and improvements!
