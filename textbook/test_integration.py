"""
Quick Test Script for Enhanced AI Studio Extractor
Tests the integration of working logic from upload_to_gemini.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai_studio_extractor import AIStudioExtractor

def test_driver_setup():
    """Test driver setup"""
    print("\n" + "="*60)
    print("TEST 1: Driver Setup")
    print("="*60)
    
    extractor = AIStudioExtractor()
    try:
        extractor._setup_driver()
        print("✓ Driver setup successful")
        print(f"  Driver type: {type(extractor.driver).__name__}")
        return True
    except Exception as e:
        print(f"❌ Driver setup failed: {e}")
        return False
    finally:
        extractor.close()

def test_pdf_discovery():
    """Test PDF discovery in books directory"""
    print("\n" + "="*60)
    print("TEST 2: PDF Discovery")
    print("="*60)
    
    books_dir = project_root / "books"
    
    if not books_dir.exists():
        print(f"❌ Books directory not found: {books_dir}")
        return False
    
    pdf_files = list(books_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in: {books_dir}")
        return False
    
    print(f"✓ Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
        print(f"    Size: {pdf.stat().st_size / (1024*1024):.2f} MB")
        print(f"    Path: {pdf.absolute()}")
    
    return True

def test_config():
    """Test configuration"""
    print("\n" + "="*60)
    print("TEST 3: Configuration")
    print("="*60)
    
    try:
        from config import GOOGLE_EMAIL, GOOGLE_PASSWORD, config, SELENIUM_CONFIG
        
        print("✓ Config loaded successfully")
        print(f"  Google Email: {GOOGLE_EMAIL[:3]}***@{GOOGLE_EMAIL.split('@')[1] if '@' in GOOGLE_EMAIL else 'not set'}")
        print(f"  Password Set: {'Yes' if GOOGLE_PASSWORD else 'No'}")
        print(f"  AI Studio URL: {config.ai_studio_url}")
        print(f"  Books Directory: {config.books_dir}")
        print(f"  Output Directory: {config.output_dir}")
        print(f"  Headless Mode: {SELENIUM_CONFIG.get('headless', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return False

def test_full_extraction():
    """Test full extraction process (with user confirmation)"""
    print("\n" + "="*60)
    print("TEST 4: Full Extraction (Optional)")
    print("="*60)
    print("\nThis will:")
    print("  1. Open Chrome browser")
    print("  2. Navigate to Google AI Studio")
    print("  3. Attempt auto-login (or prompt for manual login)")
    print("  4. Upload your PDF")
    print("  5. Send extraction prompt")
    print("  6. Wait for and extract JSON response")
    print("\nThis may take 5-10 minutes.")
    
    response = input("\nDo you want to run the full extraction test? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("⊘ Skipping full extraction test")
        return None
    
    books_dir = project_root / "books"
    pdf_files = list(books_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found to test")
        return False
    
    pdf_path = pdf_files[0]
    print(f"\nTesting with: {pdf_path.name}")
    
    extractor = AIStudioExtractor()
    try:
        pdf_info = {
            "title": pdf_path.stem,
            "pages": 100  # Placeholder
        }
        
        structure = extractor.extract_structure(pdf_path, pdf_info)
        
        if structure:
            print("✓ Extraction successful!")
            print(f"  Structure keys: {list(structure.keys())}")
            if "book_info" in structure:
                print(f"  Book title: {structure['book_info'].get('title', 'N/A')}")
            if "structure" in structure:
                print(f"  Sections found: {len(structure.get('structure', []))}")
            return True
        else:
            print("❌ Extraction failed - no structure returned")
            return False
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\nClosing browser...")
        extractor.close()

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ENHANCED AI STUDIO EXTRACTOR - TEST SUITE")
    print("="*60)
    print("Testing integration of working logic from upload_to_gemini.py")
    
    results = {}
    
    # Run tests
    results['driver_setup'] = test_driver_setup()
    results['pdf_discovery'] = test_pdf_discovery()
    results['config'] = test_config()
    results['full_extraction'] = test_full_extraction()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⊘ SKIP"
        
        print(f"  {test_name:20s}: {status}")
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print("\n" + "-"*60)
    print(f"  Total: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print("="*60)
    
    if failed == 0:
        print("\n✓ All tests passed! Ready for extraction.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
    
    print("\nNext steps:")
    print("  1. Run: python main.py --mode auto")
    print("  2. Or: python main.py --mode interactive")
    print("  3. Check output in: output/")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
