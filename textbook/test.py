#!/usr/bin/env python3
"""
Test Script - Verifies pipeline installation and configuration
"""

import sys
import json
from pathlib import Path


def test_imports():
    """Test all module imports"""
    print("\n" + "="*60)
    print("TESTING IMPORTS")
    print("="*60)
    
    modules_to_test = [
        ("config", "Configuration module"),
        ("pdf_analyzer", "PDF Analyzer"),
        ("ai_studio_extractor", "AI Studio Extractor"),
        ("content_extractor", "Content Extractor"),
        ("utils", "Utilities"),
        ("main", "Main Pipeline"),
    ]
    
    all_passed = True
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"[PASS] {description} ({module_name})")
        except ImportError as e:
            print(f"[FAIL] {description} ({module_name}): {e}")
            all_passed = False
    
    return all_passed


def test_dependencies():
    """Test external dependencies"""
    print("\n" + "="*60)
    print("TESTING DEPENDENCIES")
    print("="*60)
    
    dependencies = [
        ("fitz", "PyMuPDF"),
        ("selenium", "Selenium"),
        ("pathlib", "pathlib"),
    ]
    
    all_passed = True
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"[PASS] {description}")
        except ImportError:
            print(f"[FAIL] {description} - Install with: pip install {module_name}")
            all_passed = False
    
    # Optional dependencies
    optional = [
        ("pyperclip", "pyperclip (optional)"),
        ("undetected_chromedriver", "undetected-chromedriver (optional)"),
    ]
    
    for module_name, description in optional:
        try:
            __import__(module_name)
            print(f"[PASS] {description}")
        except ImportError:
            print(f"[INFO] {description} not installed (optional)")
    
    return all_passed


def test_directories():
    """Test directory structure"""
    print("\n" + "="*60)
    print("TESTING DIRECTORIES")
    print("="*60)
    
    dirs_to_test = [
        ("books", "PDF books directory"),
        ("output", "Output directory"),
        ("cache", "Cache directory"),
        ("temp", "Temporary directory"),
    ]
    
    all_passed = True
    
    for dir_name, description in dirs_to_test:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"[PASS] {description} exists")
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Created {description}")
    
    return all_passed


def test_configuration():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("TESTING CONFIGURATION")
    print("="*60)
    
    try:
        from config import config, GOOGLE_EMAIL, GOOGLE_PASSWORD, PYPERCLIP_AVAILABLE
        
        print("[PASS] Configuration loaded")
        
        # Check settings
        settings = [
            (config.books_dir, "Books directory", str(config.books_dir)),
            (config.output_dir, "Output directory", str(config.output_dir)),
            (config.ai_studio_url, "AI Studio URL", "aistudio.google.com" in config.ai_studio_url),
            (config.auto_detect_page_offset, "Auto page offset detection", config.auto_detect_page_offset),
            (config.auto_detect_columns, "Auto column detection", config.auto_detect_columns),
        ]
        
        for value, description, display in settings:
            if isinstance(display, bool):
                status = "[PASS]" if display else "[INFO]"
            else:
                status = "[PASS]" if value else "[INFO]"
            print(f"{status} {description}")
        
        # Check credentials
        print("\n[CREDENTIALS]")
        if GOOGLE_EMAIL and GOOGLE_PASSWORD:
            print("[PASS] Google credentials configured")
            print(f"  Email: {GOOGLE_EMAIL[:15]}...")
            print(f"  Auto-login: {config.auto_login_enabled}")
        else:
            print("[INFO] No Google credentials configured")
            print("  Run: python setup_credentials.py")
            print("  Or set GOOGLE_EMAIL and GOOGLE_PASSWORD environment variables")
        
        if PYPERCLIP_AVAILABLE:
            print("[PASS] pyperclip available")
        else:
            print("[INFO] pyperclip not available (optional)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Configuration error: {e}")
        return False


def test_pdf_files():
    """Test for PDF files in books directory"""
    print("\n" + "="*60)
    print("TESTING PDF FILES")
    print("="*60)
    
    books_dir = Path("books")
    pdf_files = list(books_dir.glob("*.pdf"))
    
    if pdf_files:
        print(f"[PASS] Found {len(pdf_files)} PDF file(s):")
        for pdf in pdf_files:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  - {pdf.name} ({size_mb:.1f} MB)")
        return True
    else:
        print("[INFO] No PDF files found in books/ directory")
        print("  Place PDF textbooks in the books/ directory to process them")
        return False


def test_pipeline_structure():
    """Test pipeline can be instantiated"""
    print("\n" + "="*60)
    print("TESTING PIPELINE STRUCTURE")
    print("="*60)
    
    try:
        from main import TextbookPipeline
        
        pipeline = TextbookPipeline()
        books = pipeline.discover_books()
        
        print(f"[PASS] Pipeline instantiated")
        print(f"[INFO] Found {len(books)} books to process")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Pipeline error: {e}")
        return False


def test_sample_json():
    """Test if we can parse sample output JSON"""
    print("\n" + "="*60)
    print("TESTING OUTPUT JSON")
    print("="*60)
    
    output_dir = Path("output")
    json_files = list(output_dir.glob("*.json"))
    
    if not json_files:
        print("[INFO] No JSON output files found yet")
        print("  Run: python main.py")
        return True
    
    all_valid = True
    
    for json_file in json_files[:3]:  # Test first 3 files
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check structure
            if "book_info" in data or "chapters" in data:
                print(f"[PASS] {json_file.name} is valid JSON")
            else:
                print(f"[INFO] {json_file.name} has unexpected structure")
                
        except json.JSONDecodeError as e:
            print(f"[FAIL] {json_file.name} is not valid JSON: {e}")
            all_valid = False
    
    return all_valid


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TEXTBOOK PIPELINE - SYSTEM TEST")
    print("="*70)
    
    test_results = []
    
    # Run tests
    test_results.append(("Imports", test_imports()))
    test_results.append(("Dependencies", test_dependencies()))
    test_results.append(("Directories", test_directories()))
    test_results.append(("Configuration", test_configuration()))
    test_results.append(("PDF Files", test_pdf_files()))
    test_results.append(("Pipeline", test_pipeline_structure()))
    test_results.append(("Output JSON", test_sample_json()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in test_results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
    
    passed_count = sum(1 for _, p in test_results if p)
    total_count = len(test_results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n[SUCCESS] All tests passed! Pipeline is ready to use.")
        print("\nNext steps:")
        print("1. Place PDF textbooks in the books/ directory")
        print("2. (Optional) Run: python setup_credentials.py")
        print("3. Run: python main.py")
        return 0
    else:
        print("\n[WARNING] Some tests failed. See above for details.")
        print("\nNext steps:")
        print("1. Fix any [FAIL] items")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Run this test again: python test.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
