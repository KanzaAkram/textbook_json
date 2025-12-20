"""
Quick validation script to check setup before running pipeline
"""
import sys
from pathlib import Path

print("="*80)
print("FINAL PROCESSING PIPELINE - SETUP VALIDATION")
print("="*80)

errors = []
warnings = []

# Check Python version
print(f"\n1. Python Version: {sys.version}")
if sys.version_info < (3, 7):
    errors.append("Python 3.7+ required")

# Check dependencies
print("\n2. Checking Dependencies...")
try:
    import fitz
    print("   ✓ PyMuPDF installed")
except ImportError:
    errors.append("PyMuPDF not installed (pip install PyMuPDF)")

try:
    import selenium
    print("   ✓ Selenium installed")
except ImportError:
    errors.append("Selenium not installed (pip install selenium)")

# Check source directories
print("\n3. Checking Source Directories...")
script_dir = Path(__file__).parent
workspace = script_dir.parent

textbook_path = workspace / "textbook" / "extracted_subtopics"
syllabus_path = workspace / "syllabus_json_structured_pipeline" / "split_subtopics"
save_my_exam_path = workspace / "save_my_exam" / "organized_by_syllabus"

if textbook_path.exists():
    count = sum(1 for _ in textbook_path.rglob("*.json"))
    print(f"   ✓ Textbook path exists ({count} JSON files)")
else:
    warnings.append(f"Textbook path not found: {textbook_path}")

if syllabus_path.exists():
    count = sum(1 for _ in syllabus_path.rglob("*.json"))
    print(f"   ✓ Syllabus path exists ({count} JSON files)")
else:
    warnings.append(f"Syllabus path not found: {syllabus_path}")

if save_my_exam_path.exists():
    count = sum(1 for _ in save_my_exam_path.rglob("*.pdf"))
    print(f"   ✓ Save My Exam path exists ({count} PDF files)")
else:
    warnings.append(f"Save My Exam path not found: {save_my_exam_path}")

# Check textbook module
print("\n4. Checking Textbook Module...")
try:
    parent_dir = script_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from textbook.ai_studio_extractor import AIStudioExtractor
    from textbook.config import SELENIUM_CONFIG, config
    print("   ✓ AIStudioExtractor available")
    print(f"   ✓ AI Studio URL: {SELENIUM_CONFIG.get('ai_studio_url') or config.ai_studio_url}")
except ImportError as e:
    errors.append(f"Cannot import textbook module: {e}")

# Check config files
print("\n5. Checking Configuration Files...")
if (script_dir / "config.py").exists():
    print("   ✓ config.py exists")
else:
    errors.append("config.py not found")

if (script_dir / "utils.py").exists():
    print("   ✓ utils.py exists")
else:
    errors.append("utils.py not found")

if (script_dir / "matcher.py").exists():
    print("   ✓ matcher.py exists")
else:
    errors.append("matcher.py not found")

if (script_dir / "processor.py").exists():
    print("   ✓ processor.py exists")
else:
    errors.append("processor.py not found")

if (script_dir / "run_pipeline.py").exists():
    print("   ✓ run_pipeline.py exists")
else:
    errors.append("run_pipeline.py not found")

# Summary
print("\n" + "="*80)
print("VALIDATION SUMMARY")
print("="*80)

if errors:
    print(f"\n❌ ERRORS ({len(errors)}):")
    for error in errors:
        print(f"   - {error}")

if warnings:
    print(f"\n⚠ WARNINGS ({len(warnings)}):")
    for warning in warnings:
        print(f"   - {warning}")

if not errors and not warnings:
    print("\n✅ All checks passed! Ready to run pipeline.")
    print("\nNext steps:")
    print("   1. python matcher.py          # Match subtopics (creates staging/)")
    print("   2. python processor.py        # Process through AI Studio")
    print("   OR")
    print("   python run_pipeline.py        # Run complete pipeline")
    print("   python run_pipeline.py --limit 2  # Test with 2 subtopics per subject")
elif not errors:
    print("\n⚠ Setup OK with warnings. Can proceed but check warnings.")
else:
    print("\n❌ Setup incomplete. Fix errors before running pipeline.")

print("="*80)
