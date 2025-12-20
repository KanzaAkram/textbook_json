# Response Detection Fixes - Summary

## Problem Identified
After sending prompts to AI Studio, the pipeline was getting stuck waiting for responses. The logs showed:
- "Prompt sent via button click" (success)
- "Waiting for AI response..." (starts waiting)
- Then hangs with connection errors from Selenium webdriver

## Root Causes
1. **Incorrect DOM Selectors**: The original `_wait_for_response()` method used generic XPath selectors that didn't match Google AI Studio's actual DOM structure
2. **No Response Detection Logic**: Didn't properly detect when AI finished generating (no check for "generating" indicators disappearing)
3. **Single Driver Reuse**: Reusing the same Selenium driver for multiple subtopics caused connection exhaustion and timeouts
4. **No Error Recovery**: When driver became unresponsive, no mechanism to restart it

## Fixes Applied

### 1. **Improved Response Detection** (`ai_studio_extractor.py` - `_wait_for_response()`)
**Changed from:**
- Simple element presence checks
- Timeout without proper detection

**Changed to:**
- Multiple specific XPath selectors: `//pre`, `//code`, `//div[role='article']`, `//article`, etc.
- **Content Stability Detection**: Tracks content length and waits for it to stop growing (2 consecutive checks)
- **Generating Indicator Detection**: Checks for "Generating", "Loading", "spinner" indicators and waits for them to disappear
- **Dual-trigger Detection**: Responds when EITHER:
  - Content found AND no "generating" indicators
  - Content found AND stable (not growing)
- **Error Recovery**: Tracks consecutive connection errors and automatically refreshes page if >3 errors
- **Better Logging**: Shows progress every 15 seconds with current content size

### 2. **Enhanced Extraction Methods** (`ai_studio_extractor.py` - `_extract_json_response()`)
**Improvements:**
- **Multi-method fallback**: Tries 3 different extraction methods:
  1. DOM extraction from `<pre>`, `<code>`, message divs, articles
  2. Copy button method (if available)
  3. Fallback: Extract all visible body text
- **Better element selection**: Finds largest/most recent response element
- **Robust JSON detection**: Checks for `{` and `}` characters instead of strict `.json()` assumption

### 3. **Driver Management** (`final_processing/run_pipeline.py`)
**Changes:**
- **Periodic Driver Restart**: Creates fresh driver every 3 subtopics instead of reusing single driver
- **Explicit Cleanup**: Properly closes driver between batches with `try/finally` block
- **Better Resource Management**: Prevents connection exhaustion from long-running driver sessions

### 4. **Retry Logic in Processor** (`final_processing/processor.py` - `send_to_ai_studio()`)
**Improvements:**
- **Health Check**: Tests driver responsiveness before using it
- **Automatic Restart**: If driver unresponsive, closes and creates new one
- **Retry on Failure**: Up to 2 attempts per subtopic with driver restart between attempts
- **Better Error Messages**: More informative logging for troubleshooting

### 5. **Connection Error Handling** (`ai_studio_extractor.py` - `_wait_for_response()`)
**New Features:**
- **Error Counter**: Tracks consecutive connection errors
- **Page Refresh Recovery**: If >3 consecutive errors, automatically refreshes page
- **Graceful Degradation**: If all else fails, still tries to extract whatever content is available

## Expected Improvements

### Before
```
[INFO] Prompt sent via button click
[INFO] Waiting for AI response (timeout: 180s)...
[WARNING] [Connection refused errors...]
[TIMEOUT] No response received after 180 seconds
[ERROR] Pipeline fails on first subtopic
```

### After
```
[INFO] Prompt sent via button click
[INFO] Waiting for AI response (timeout: 180s)...
[INFO] Response status: generating... (content: 450 chars, elapsed: 15s)
[INFO] Response status: generating... (content: 1250 chars, elapsed: 30s)
[INFO] Response status: generating... (content: 2100 chars, elapsed: 45s)
[OK] Response appears complete (no generating indicator)
[OK] Extracted JSON from DOM
[OK] Successfully parsed JSON response
[OK] Completed subtopic 1.1
```

## Testing the Fixes

Run the pipeline with:
```bash
cd final_processing
python run_pipeline.py 9701 --level "AS'Level"
```

Watch for:
- ✓ "Response status: generating..." messages (content is being detected)
- ✓ "[OK] Response appears complete" (detection worked)
- ✓ "[OK] Extracted JSON from DOM" (extraction successful)
- ✓ "[OK] Successfully parsed JSON response" (parsing worked)

## Files Modified
1. `textbook/ai_studio_extractor.py` (2 methods)
   - `_wait_for_response()` (lines 756-875)
   - `_extract_json_response()` (lines 877-962)

2. `final_processing/processor.py` (1 method)
   - `send_to_ai_studio()` (lines 217-293) with retry logic and health checks

3. `final_processing/run_pipeline.py` (1 section)
   - Driver management loop (lines 120-165) with periodic restart

## Next Steps
1. Run full pipeline: `python run_pipeline.py 9701 --level "AS'Level"`
2. Monitor logs for response detection working
3. Verify JSON extraction and parsing success
4. Process all remaining subtopics
