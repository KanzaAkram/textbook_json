# Clipboard Response Extraction Implementation

## Overview

Copied response extraction and clipboard logic from `ai_studio_extractor.py` into `processor.py` to enable copying generated AI responses directly from the DOM using pyperclip.

## Changes Made

### 1. **processor.py - Added Imports**

- Added `import traceback` for error handling
- Added `pyperclip` import with fallback handling
- Set `PYPERCLIP_AVAILABLE` flag to check if pyperclip is installed

```python
# Try to import pyperclip for clipboard access
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("Note: pyperclip not installed. Install with: pip install pyperclip")
```

### 2. **processor.py - New Method: `extract_json_from_response()`**

Added a new method to the `SubtopicProcessor` class that extracts JSON content from AI Studio responses using two methods:

#### Method 1: DOM Extraction

- Searches for code blocks in the page DOM using multiple selectors
- Looks for `<pre>`, `<code>`, and code-block divs
- Extracts text that looks like JSON (starts with `{` or `[`)
- Returns the most recent code block found

#### Method 2: Copy Button + Clipboard

- Finds the copy button near the code block
- Searches with XPath selectors for button elements with "copy" in their aria-label or class
- Clicks the copy button to copy content to clipboard
- Uses `pyperclip.paste()` to retrieve the copied content
- Verifies content is valid (> 50 characters) before returning

### 3. **processor.py - Updated `send_to_ai_studio()` Method**

Enhanced the response extraction flow:

```python
# Extract and parse JSON with enhanced DOM/clipboard extraction
logger.info(f"    Extracting JSON response...")

# First try our enhanced extraction with DOM and clipboard copy
json_content = self.extract_json_from_response()

# If that didn't work, try the extractor's method
if not json_content:
    logger.info("    Trying extractor's extraction method...")
    json_content = self.extractor._extract_json_response()

# Fall back to raw response if all else fails
if not json_content:
    json_content = response

result_data = self.extractor._parse_json_response(json_content or response)
```

### 4. **requirements.txt - Added Dependency**

```
pyperclip>=1.8.0
```

## How It Works

1. **When AI Studio generates a response:**

   - The new `extract_json_from_response()` method is called
   - It first tries to extract JSON directly from the page DOM

2. **If DOM extraction fails:**

   - It looks for a copy button near the code block
   - Clicks the button to copy content to clipboard
   - Uses pyperclip to retrieve the copied content

3. **If both methods fail:**
   - Falls back to the original extractor method
   - Then falls back to raw response text
   - Content is parsed as JSON

## Benefits

✅ **More reliable response extraction** - Two methods ensure better success rate
✅ **Leverages browser's native copy** - Copy button directly copies what user would copy
✅ **Clipboard access** - Uses pyperclip for cross-platform clipboard operations
✅ **Graceful degradation** - Falls back through multiple extraction methods
✅ **Better logging** - Detailed logs show which extraction method succeeded

## Dependencies

Make sure to install the new dependency:

```bash
pip install pyperclip>=1.8.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Notes

- pyperclip is optional - if not installed, the method will log a warning and continue
- The clipboard method requires the copy button to be visible and clickable on the page
- All extraction attempts are logged for debugging purposes
- The method includes proper waits between DOM manipulations for reliability
