# Quick Start Guide - Enhanced AI Studio Extractor

## 🚀 What's New

Your `ai_studio_extractor.py` now includes proven working logic from `upload_to_gemini.py`:

- ✅ Better Google login bypass
- ✅ 4 methods for PDF upload detection
- ✅ Automatic JSON extraction from response
- ✅ Copy button + clipboard integration
- ✅ Human-like typing to avoid detection

## 📋 Prerequisites

```bash
# Install required packages
pip install undetected-chromedriver pyperclip

# Or install all requirements
pip install -r requirements.txt
```

## ⚡ Quick Start

### Option 1: Automated Extraction

```bash
cd c:\Users\kanza\OneDrive\Desktop\textbook_json
python main.py --mode auto
```

### Option 2: Test First

```bash
python test_integration.py
```

### Option 3: Interactive Mode

```bash
python main.py --mode interactive
```

## 🎯 Directory Structure

```
textbook_json/
├── books/
│   └── cambridge...pdf              ← Put PDFs here
├── output/
│   ├── *_content.json              ← Results appear here
│   ├── *_structure.json
│   └── processing_summary.json
├── ai_studio_extractor.py          ← ENHANCED VERSION
├── ai_studio_extractor_old_backup.py ← Original backup
├── config.py                        ← Settings
├── main.py                          ← Run this
└── test_integration.py              ← Test this
```

## 🔐 Credentials Setup

### Quick Setup (Testing)

Credentials are already in `config.py`:

- Email: `kanzamuhammadakram@gmail.com`
- Password: `123456`

### Secure Setup (Production)

```powershell
# Set environment variables (recommended)
[System.Environment]::SetEnvironmentVariable('GOOGLE_EMAIL', 'your-email@gmail.com', 'User')
[System.Environment]::SetEnvironmentVariable('GOOGLE_PASSWORD', 'your-password', 'User')

# Restart PowerShell after setting
```

## 🎬 What Happens During Extraction

```
1. Opens Chrome (hidden or visible)
2. Goes to Google AI Studio
3. Logs in automatically (or waits for you)
4. Finds and clicks upload button
5. Uploads your PDF from books/ folder
6. Sends extraction prompt
7. Waits for AI response (5-10 minutes)
8. Extracts JSON from page
9. Saves to output/ folder
10. Done! 🎉
```

## ✅ Success Indicators

Look for these messages:

```
✓ Using undetected-chromedriver...
✓ Already logged in!
✓ File path sent to upload element
✓ Prompt text entered...
✓ Response appears complete
✓ Extracted JSON from DOM
✓ JSON response saved to: ...
```

## ⚠️ Common Issues

### "Could not find email input"

- **Cause**: Google changed login page
- **Fix**: It will pause for manual login

### "Could not find file input"

- **Cause**: AI Studio UI changed
- **Fix**: It will try 4 methods, then ask for manual upload

### "Login failed"

- **Cause**: 2FA or CAPTCHA
- **Fix**: It will pause for you to complete manually

### "Could not extract JSON"

- **Cause**: Response format changed
- **Fix**: Check `books/*_ai_response.json` for raw response

## 🔧 Configuration Options

Edit `config.py`:

```python
# Timeout for AI response (seconds)
ai_studio_timeout = 600  # 10 minutes

# Run browser in background (may break login)
headless = False

# Manual login timeout (seconds)
manual_login_timeout = 300  # 5 minutes

# AI Studio URL
ai_studio_url = "https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview"
```

## 📊 Output Files

### In `output/` directory:

- `*_content.json` - Full extracted content
- `*_structure.json` - Document structure
- `processing_summary.json` - Processing log

### In `books/` directory:

- `*_ai_response.json` - Raw AI response (new!)

## 🐛 Debugging

### Enable verbose logging:

```python
# In config.py
log_level = "DEBUG"
```

### Run with browser visible:

```python
# In config.py
headless = False
```

### Check Chrome version:

```bash
chrome --version
# Should be ~142.x or similar
```

## 📝 Test Commands

### Test driver setup only:

```python
from ai_studio_extractor import AIStudioExtractor
e = AIStudioExtractor()
e._setup_driver()
print("Driver OK!")
e.close()
```

### Test PDF discovery:

```python
from pathlib import Path
books = list(Path("books").glob("*.pdf"))
print(f"Found {len(books)} PDFs")
for pdf in books:
    print(f"  - {pdf.name}")
```

### Full integration test:

```bash
python test_integration.py
```

## 🎓 Advanced Usage

### Process specific PDF:

```python
from pathlib import Path
from ai_studio_extractor import AIStudioExtractor

pdf = Path("books/your_book.pdf")
extractor = AIStudioExtractor()
try:
    result = extractor.extract_structure(pdf, {"title": pdf.stem})
    print(f"Extracted {len(result.get('structure', []))} sections")
finally:
    extractor.close()
```

### Batch process all PDFs:

```bash
python main.py --mode auto
```

### Interactive with manual control:

```bash
python main.py --mode interactive
```

## 📚 Documentation Files

- `INTEGRATION_SUMMARY.md` - Detailed changes and improvements
- `INTEGRATION_FLOW.md` - Visual flow diagrams
- `QUICKSTART.md` - This file (quick reference)
- `README.md` - Original project documentation

## 🆘 Get Help

### Check logs:

```bash
# View log file
cat pipeline.log

# Or in PowerShell
Get-Content pipeline.log -Tail 50
```

### Run diagnostics:

```bash
python test_integration.py
```

### Manual intervention:

If automation fails, the script will pause and ask you to:

1. Complete the action manually in the browser
2. Press Enter to continue

## ✨ Key Features

| Feature                       | Status      |
| ----------------------------- | ----------- |
| Automatic Google login        | ✅          |
| 2FA/CAPTCHA handling          | ✅ (manual) |
| PDF upload (4 methods)        | ✅          |
| Prompt sending                | ✅          |
| JSON extraction (DOM)         | ✅          |
| JSON extraction (copy button) | ✅          |
| Clipboard integration         | ✅          |
| Auto file saving              | ✅          |
| Error recovery                | ✅          |
| Detailed logging              | ✅          |
| Session persistence           | ✅          |

## 🎯 Next Steps

1. **Test it**: Run `python test_integration.py`
2. **Use it**: Run `python main.py --mode auto`
3. **Check results**: Look in `output/` folder
4. **Enjoy!**: Process all your textbooks automatically! 🎉

---

**Quick Reference Card** | Integration Complete ✅

For detailed information, see:

- `INTEGRATION_SUMMARY.md` - Full documentation
- `INTEGRATION_FLOW.md` - Visual diagrams
- `test_integration.py` - Test suite
