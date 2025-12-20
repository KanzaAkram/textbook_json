# How to Run the Textbook Pipeline

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd textbook
   pip install -r requirements.txt
   ```

2. **Set Up Google Credentials**
   
   The script needs your Google account credentials to access AI Studio. You have two options:
   
   **Option A: Environment Variables (Recommended)**
   ```powershell
   # Windows PowerShell
   [System.Environment]::SetEnvironmentVariable('GOOGLE_EMAIL', 'your-email@gmail.com', 'User')
   [System.Environment]::SetEnvironmentVariable('GOOGLE_PASSWORD', 'your-password', 'User')
   ```
   
   **Option B: Edit config.py**
   - Open `textbook/config.py`
   - Update the hardcoded credentials (lines ~35-36)

3. **Required Folder Structure**
   ```
   textbook/
   ├── books/
   │   ├── as_alevel/
   │   │   └── 9701/
   │   │       └── [your-textbook].pdf
   │   ├── igcse/
   │   └── olevel/
   └── extract_subtopic_pages.py
   
   syllabus_json_structured_pipeline/
   └── merged_outputs/
       ├── AS'Level/
       │   └── 9701/
       │       └── prompt.py
       ├── Alevel/
       └── ...
   ```

## Running the Pipeline

### Basic Usage

```bash
cd textbook
python extract_subtopic_pages.py
```

### What It Does

1. **Scans** `textbook/books/` for PDF textbooks
2. **Matches** each book with syllabus JSONs from `syllabus_json_structured_pipeline/merged_outputs/`
3. **Uploads** the PDF to Google AI Studio (Gemini)
4. **Extracts** page numbers for each subtopic using AI
5. **Extracts** text content from those pages using PyMuPDF (handles 2-column layouts)
6. **Saves** individual JSON files for each subtopic in `textbook/extracted_subtopics/`

### Output Structure

```
textbook/
└── extracted_subtopics/          # NEW - separate output folder
    ├── AS'Level/
    │   └── 9701/
    │       ├── 1.1_Particles_in_the_atom_and_atomic_radius.json
    │       ├── 1.2_Isotopes.json
    │       └── ...
    └── Alevel/
        └── 9701/
            └── ...
```

### Output JSON Format

Each subtopic JSON file contains:
```json
{
  "subtopic_number": "1.1",
  "subtopic_name": "Particles in the atom and atomic radius",
  "topic_number": "1",
  "topic_name": "Atomic structure",
  "start_page": 10,
  "end_page": 25,
  "content": "Extracted text from pages 10-25...",
  "content_length": 5234,
  "pages_extracted": "10-25",
  "layout_detected": "2 column(s)"
}
```

## Important Notes

- **Browser Window**: The script will open a Chrome browser window (Selenium). Don't close it!
- **Processing Time**: Each book can take 5-10 minutes depending on:
  - Number of subtopics
  - AI Studio response time
  - PDF size
- **Wait Between Requests**: The script waits 5 seconds between syllabus levels to avoid rate limiting
- **2-Column Layouts**: The script automatically detects and handles 2-column PDF layouts
- **Error Handling**: If a subtopic fails, the script continues with the next one

## Troubleshooting

### "No matching syllabus found"
- Check that `syllabus_json_structured_pipeline/merged_outputs/` contains the subject code
- Verify the subject code matches (e.g., `9701` in both places)

### "Failed to login to AI Studio"
- Check your credentials in `config.py` or environment variables
- Make sure 2FA is disabled or handled manually

### "PyMuPDF not available"
- Install: `pip install PyMuPDF`

### Browser Issues
- Make sure Chrome is installed
- The script uses `undetected-chromedriver` to bypass bot detection

## Example Run

```powershell
PS C:\Users\kanza\OneDrive\Desktop\textbook_json> cd textbook
PS C:\Users\kanza\OneDrive\Desktop\textbook_json\textbook> python extract_subtopic_pages.py

============================================================
Textbook Subtopic Page Extraction
============================================================

Processing level folder: as_alevel
Processing: AS'Level/9701
Opening PDF: cambridge international as and a level chemistry coursebook complete.pdf
PDF has 515 pages
Detected layout: 2 column(s)
Extracting content from PDF pages...
  1.1: Extracted 5234 chars from pages 10-25
  1.2: Extracted 3124 chars from pages 26-30
  ...
✓ Completed: AS'Level/9701
```

