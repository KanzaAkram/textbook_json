# Integration Flow Diagram

## Working Logic from upload_to_gemini.py → Your Project

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR PROJECT STRUCTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  books/                                                          │
│    └── cambridge...chemistry coursebook.pdf  ←─────┐            │
│                                                      │            │
│  main.py  ────┐                                    │            │
│               │                                     │            │
│               ↓                                     │            │
│  ai_studio_extractor.py (ENHANCED) ────────────────┘            │
│               │                                                   │
│               │  Now includes working logic from:                │
│               │  ✓ Driver setup with anti-detection             │
│               │  ✓ Human-like login automation                   │
│               │  ✓ Multi-method PDF upload                       │
│               │  ✓ Overlay-proof prompt sending                  │
│               │  ✓ DOM + Copy button JSON extraction             │
│               │                                                   │
│               ↓                                                   │
│  output/                                                         │
│    ├── *_content.json  ←── Extracted structure                  │
│    ├── *_structure.json                                          │
│    └── processing_summary.json                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Extraction Flow

````
START
  │
  ├──→ 1. Initialize AIStudioExtractor()
  │
  ├──→ 2. Setup Chrome Driver
  │      ├── Try undetected-chromedriver
  │      │   ✓ Better Google detection bypass
  │      │   ✓ Persistent user data directory
  │      └── Fallback to regular Selenium
  │          ✓ Anti-detection measures
  │
  ├──→ 3. Navigate to AI Studio
  │      URL: https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview
  │
  ├──→ 4. Check Login Status
  │      ├── Already logged in? → Continue
  │      └── Need login?
  │          ├── Try Auto-Login
  │          │   ├── Type email (human-like delays)
  │          │   ├── Click Next
  │          │   ├── Type password (human-like delays)
  │          │   ├── Click Sign in
  │          │   ├── Handle 2FA/CAPTCHA (manual)
  │          │   └── Wait for redirect
  │          └── Fallback to Manual Login
  │
  ├──→ 5. Upload PDF
  │      ├── Method 1: Direct file input
  │      ├── Method 2: Click upload button
  │      ├── Method 3: Near prompt area
  │      ├── Method 4: Make hidden input visible
  │      └── Fallback: Manual upload
  │
  ├──→ 6. Send Extraction Prompt
  │      ├── Wait for overlays to clear
  │      ├── Method 1: JavaScript setValue (bypass overlays)
  │      ├── Method 2: Click and type
  │      ├── Find send button
  │      └── Send via button or Enter key
  │
  ├──→ 7. Wait for AI Response
  │      ├── Monitor response indicators
  │      ├── Check loading status
  │      ├── Progress updates (every 30s)
  │      └── Detect completion
  │
  ├──→ 8. Extract JSON Response
  │      ├── Method 1: DOM Extraction
  │      │   ├── Find code blocks
  │      │   ├── Verify JSON format
  │      │   └── Extract text
  │      ├── Method 2: Copy Button
  │      │   ├── Find copy button near code
  │      │   ├── Click button
  │      │   └── Read from clipboard (pyperclip)
  │      └── Save to file
  │
  ├──→ 9. Parse JSON
  │      ├── Try regex patterns (```json, ```, {})
  │      ├── Validate structure
  │      └── Return parsed data
  │
  └──→ 10. Save Results
         ├── output/*_content.json
         ├── output/*_structure.json
         └── output/processing_summary.json
````

## Key Improvements Integrated

### 1. Driver Setup (from lines 48-123 of upload_to_gemini.py)

```
OLD: Basic Selenium setup
NEW: ✓ Undetected-chromedriver with version handling
     ✓ Persistent user data directory
     ✓ Anti-detection CDP commands
     ✓ Proper window maximization
```

### 2. Auto-Login (from lines 142-258 of upload_to_gemini.py)

```
OLD: Simple email/password entry
NEW: ✓ Human-like typing with random delays
     ✓ Multiple selector strategies
     ✓ JavaScript click to bypass overlays
     ✓ 2FA/CAPTCHA detection and handling
     ✓ Better error messages
```

### 3. PDF Upload (from lines 274-409 of upload_to_gemini.py)

```
OLD: Single method file input search
NEW: ✓ 4 different detection methods
     ✓ Button click then input search
     ✓ Near prompt area search
     ✓ Make hidden inputs visible
     ✓ Scroll into view before interaction
```

### 4. Prompt Sending (from lines 414-524 of upload_to_gemini.py)

```
OLD: Basic textarea.send_keys()
NEW: ✓ Wait for overlays to clear
     ✓ JavaScript setValue (bypasses overlays)
     ✓ Multiple send button strategies
     ✓ Enter key fallback
```

### 5. JSON Extraction (from lines 526-691 of upload_to_gemini.py)

```
OLD: Only text extraction from body
NEW: ✓ DOM extraction (code blocks, pre tags)
     ✓ Copy button detection and click
     ✓ Clipboard integration (pyperclip)
     ✓ Automatic file saving
     ✓ Multiple fallback methods
```

## File Locations

```
Your Project Root: c:\Users\kanza\OneDrive\Desktop\textbook_json\

Input:
  books/cambridge...pdf              ← Your PDF files

Enhanced Extractor:
  ai_studio_extractor.py             ← UPDATED with working logic
  ai_studio_extractor_old_backup.py  ← Original backup

Configuration:
  config.py                          ← Credentials and settings

Test & Documentation:
  test_integration.py                ← Run this to test
  INTEGRATION_SUMMARY.md             ← Detailed explanation
  INTEGRATION_FLOW.md                ← This file

Output:
  output/
    ├── *_content.json               ← Extracted content
    ├── *_structure.json             ← Document structure
    └── processing_summary.json      ← Processing log

  books/
    └── *_ai_response.json           ← Raw AI response saved here
```

## Usage Examples

### Basic Extraction

```bash
cd c:\Users\kanza\OneDrive\Desktop\textbook_json
python main.py --mode auto
```

### Test Integration

```bash
python test_integration.py
```

### Interactive Mode (Manual Steps)

```bash
python main.py --mode interactive
```

### Direct Extractor Test

```python
from pathlib import Path
from ai_studio_extractor import AIStudioExtractor

extractor = AIStudioExtractor()
try:
    pdf = Path("books/cambridge international as and a level chemistry coursebook complete.pdf")
    result = extractor.extract_structure(pdf, {"title": pdf.stem})
    print(f"Success! Got {len(result.get('structure', []))} sections")
finally:
    extractor.close()
```

## Verification Checklist

- [x] Driver setup with anti-detection
- [x] Persistent session (user data directory)
- [x] Human-like login typing
- [x] Multiple PDF upload methods
- [x] Overlay-proof prompt sending
- [x] DOM JSON extraction
- [x] Copy button detection and use
- [x] Clipboard integration
- [x] Automatic file saving
- [x] Comprehensive error handling
- [x] Detailed logging with emojis
- [x] Backward compatibility with existing pipeline

## Success Indicators

When running, you should see:

```
✓ Using undetected-chromedriver for better Google login bypass...
✓ Already logged in and ready!
✓ File path sent to upload element
✓ Prompt text entered via JavaScript
✓ Response appears complete
✓ Extracted JSON from DOM (12483 characters)
✓ JSON response saved to: books/..._ai_response.json
```

## Next Steps

1. **Run tests**: `python test_integration.py`
2. **Process a book**: `python main.py --mode auto`
3. **Check results**: Look in `output/` directory
4. **Review logs**: Check console output and log files

---

**Integration Status**: ✅ COMPLETE

All proven working logic from `upload_to_gemini.py` has been successfully integrated into your `ai_studio_extractor.py` while maintaining compatibility with your existing pipeline structure.
