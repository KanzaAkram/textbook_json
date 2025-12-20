# How to Run the Full Pipeline

## Quick Start

### Option 1: Test with a Few Subtopics (Recommended First)
```bash
cd final_processing
python auto_test.py
```
This will:
- Process first 3 subtopics from AS'Level/9701
- Create fresh drivers for each batch
- Show response detection working
- Generate test log: `pipeline_auto_test.log`

### Option 2: Full Pipeline Run
```bash
cd final_processing
python run_pipeline.py 9701 --level "AS'Level"
```
This will:
- Show all 51 subtopics to process
- Ask for confirmation (type 'y')
- Process all subtopics with fresh drivers every 3 subtopics
- Save results to: `output/AS'Level/9701/`

## What to Expect

### During Processing
You'll see logs like:
```
[1/51] Processing subtopic 1.1...
  Using undetected-chromedriver
  Navigating to AI Studio...
  Sending prompt to AI...
  Waiting for AI response (timeout: 180s)...
  Starting response wait loop...
  Response status: generating... (content: 450 chars, elapsed: 15s)
  Response status: generating... (content: 1250 chars, elapsed: 30s)
  [OK] Response appears complete
  [OK] Extracted JSON from DOM
  [OK] Successfully parsed JSON response
[OK] Completed subtopic 1.1
Waiting 10 seconds before next subtopic...

[2/51] Processing subtopic 1.2...
...
```

### Key Success Indicators
- ✓ "Response status: generating..." appears
- ✓ "[OK] Response appears complete" message
- ✓ "[OK] Extracted JSON from DOM"
- ✓ "[OK] Successfully parsed JSON"
- ✓ No "Waiting... (timeout: 180s)" hanging

### Output Files
After processing, you'll find:
```
final_processing/output/
├── AS'Level/
│   ├── 9701/
│   │   ├── 1.1_Particles.json
│   │   ├── 1.2_Isotopes.json
│   │   ├── 1.3_Relative.json
│   │   └── ... (51 subtopics total)
│   ├── 9700/
│   ├── 9702/
│   └── ...
└── Alevel/
    ├── 9701/
    └── ...
```

Each JSON file contains:
```json
{
  "metadata": {
    "level": "AS'Level",
    "subject_code": "9701",
    "subtopic_number": "1.1"
  },
  "comprehensive_notes": "...",
  "structure": {
    "introduction": "...",
    "key_concepts": [...],
    "definitions": {...},
    "examples": [...],
    "practice_questions": [...]
  }
}
```

## Processing Timeline

### For Testing (3 subtopics)
- **Subtopic 1**: ~2-3 minutes
- **Subtopic 2**: ~2-3 minutes  
- **Subtopic 3**: ~2-3 minutes
- **Total**: ~6-9 minutes

### For Full Run (51 subtopics - AS'Level/9701)
- **Driver setup**: ~2 min per batch × 17 batches = ~34 minutes
- **Processing**: ~2.5-3 min per subtopic × 51 = ~2-2.5 hours
- **Wait time**: ~10 seconds × 50 = ~8 minutes
- **Total**: ~2.5-3 hours per subject

### All 1088 Subtopics (estimate)
- Multiple batches across all levels
- With periodic driver restarts: ~4-5 hours for full processing

## Troubleshooting

### If hanging on response wait:
```
Problem: Pipeline stuck at "Waiting for AI response..."
Solution: 
1. The improved detection should handle this now
2. If still stuck after 180s, Ctrl+C and check logs
3. Run with python auto_test.py first to verify detection works
```

### If driver crashes:
```
Problem: UndetectedChromedriverError or connection refused
Solution:
1. This triggers automatic restart (happens every 3 subtopics)
2. If persistent, the retry logic will restart the driver
3. Check Windows chromedriver processes: Get-Process chrome
```

### If JSON parsing fails:
```
Problem: "Could not parse JSON from response"
Solution:
1. Raw response is saved to temp/failed_json_response.txt
2. Rerun that specific subtopic
3. Check if AI returned valid JSON structure
```

## Advanced Usage

### Process Only Specific Level
```bash
python run_pipeline.py 9701 --level "Alevel"
```

### Process Specific Subject Code
```bash
python run_pipeline.py 0417  # IGCSE Chemistry
python run_pipeline.py 2058  # O'level Mathematics
```

### Restart Failed Batch
The driver restart every 3 subtopics means if batch fails:
1. Identify which subtopic failed in logs
2. Re-run pipeline - it will skip completed ones (checks output directory)
3. Resume from failed subtopic

### Monitor Progress
```bash
# In another terminal
Get-Content final_processing_test.log -Wait  # Windows
tail -f final_processing_test.log            # Linux/Mac
```

## Success Criteria

✅ **Pipeline is working when you see**:
1. Prompt successfully sent to AI
2. "Response status: generating..." messages appear
3. Content size increases (e.g., "content: 450 chars → 1250 chars → 2100 chars")
4. "[OK] Response appears complete" message
5. JSON extracted and parsed without errors
6. Comprehensive notes saved to output directory

❌ **Pipeline is stuck if you see**:
1. No "Response status" messages for >30 seconds
2. Connection refused errors in log (should auto-recover)
3. Same content size for >60 seconds AND still shows "generating..."
4. Timeout after 180 seconds

## Next Steps After Full Processing

1. **Validate Output**: Check a few generated JSONs for quality
2. **Aggregate Results**: Combine all subject outputs
3. **Quality Assurance**: Spot-check comprehensive notes
4. **Deploy**: Move output files to final location
5. **Archive**: Backup original staging directory

## Key Files

- **Pipeline Entry**: `final_processing/run_pipeline.py`
- **Test Entry**: `final_processing/auto_test.py`
- **Main Logic**: `final_processing/processor.py`
- **Matcher**: `final_processing/matcher.py`
- **AI Integration**: `textbook/ai_studio_extractor.py`
- **Config**: `final_processing/config.py`

## Getting Help

If issues occur:
1. Check `final_processing.log` for detailed error messages
2. Check `pipeline_auto_test.log` for test-specific logs
3. Review `temp/failed_json_response.txt` for failed responses
4. Check AI Studio logs in browser console (F12)

---

**Last Updated**: December 21, 2025
**Status**: Response detection fixes deployed and tested
**Ready For**: Full production run of 1088 subtopics
