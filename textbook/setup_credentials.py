#!/usr/bin/env python3
"""
Setup Script - Configure Google credentials for automatic AI Studio login

This script helps you set up environment variables for the pipeline
to automatically log in to Google AI Studio.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def setup_windows():
    """Setup credentials on Windows"""
    print("\n" + "="*70)
    print("WINDOWS SETUP")
    print("="*70)
    print("\nEnter your Google account credentials:")
    print("(These will be stored as system environment variables)")
    
    email = input("\nGoogle Email: ").strip()
    password = input("Google Password: ").strip()
    
    if not email or not password:
        print("Error: Email and password are required")
        return False
    
    try:
        # Use PowerShell to set environment variables permanently
        print("\nSetting environment variables (requires admin privileges)...")
        
        # For current user (no admin required)
        subprocess.run([
            "powershell", "-Command",
            f"[System.Environment]::SetEnvironmentVariable('GOOGLE_EMAIL', '{email}', 'User')"
        ], check=True)
        
        subprocess.run([
            "powershell", "-Command",
            f"[System.Environment]::SetEnvironmentVariable('GOOGLE_PASSWORD', '{password}', 'User')"
        ], check=True)
        
        print("\n[SUCCESS] Environment variables set for current user")
        print("Note: You may need to restart your terminal for changes to take effect")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting environment variables: {e}")
        print("\nAlternative: Set manually in Environment Variables:")
        print(f"  GOOGLE_EMAIL = {email}")
        print(f"  GOOGLE_PASSWORD = {password}")
        return False


def setup_linux_mac():
    """Setup credentials on Linux/Mac"""
    print("\n" + "="*70)
    print("LINUX/MAC SETUP")
    print("="*70)
    print("\nEnter your Google account credentials:")
    
    email = input("\nGoogle Email: ").strip()
    password = input("Google Password: ").strip()
    
    if not email or not password:
        print("Error: Email and password are required")
        return False
    
    shell_rc = ".bashrc"  # default
    if "zsh" in os.getenv("SHELL", "").lower():
        shell_rc = ".zshrc"
    
    print(f"\nAdd the following lines to your ~/{shell_rc}:")
    print("-" * 70)
    print(f"export GOOGLE_EMAIL=\"{email}\"")
    print(f"export GOOGLE_PASSWORD=\"{password}\"")
    print("-" * 70)
    
    print(f"\nThen run: source ~/{shell_rc}")
    
    return True


def test_credentials():
    """Test if credentials are properly set"""
    print("\n" + "="*70)
    print("TESTING CREDENTIALS")
    print("="*70)
    
    from config import GOOGLE_EMAIL, GOOGLE_PASSWORD, PYPERCLIP_AVAILABLE
    
    if GOOGLE_EMAIL and GOOGLE_PASSWORD:
        print("[SUCCESS] Credentials found!")
        print(f"  Email: {GOOGLE_EMAIL[:10]}...{GOOGLE_EMAIL[-10:]}")
        print(f"  Password: {'*' * len(GOOGLE_PASSWORD)}")
    else:
        print("[WARNING] Credentials not found")
        print("  GOOGLE_EMAIL not set")
        print("  GOOGLE_PASSWORD not set")
    
    if PYPERCLIP_AVAILABLE:
        print("[SUCCESS] pyperclip is installed")
    else:
        print("[WARNING] pyperclip not installed. Install with: pip install pyperclip")
    
    return bool(GOOGLE_EMAIL and GOOGLE_PASSWORD)


def main():
    """Main setup function"""
    print("\n" + "="*70)
    print("TEXTBOOK PIPELINE - CREDENTIAL SETUP")
    print("="*70)
    print("\nThis script configures automatic Google login for AI Studio")
    print("Credentials are stored securely as environment variables")
    
    system = platform.system()
    
    if system == "Windows":
        success = setup_windows()
    elif system in ["Darwin", "Linux"]:
        success = setup_linux_mac()
    else:
        print(f"Unsupported system: {system}")
        return
    
    if success:
        print("\n" + "="*70)
        input("Press Enter to test credentials...")
        test_credentials()
    else:
        print("\nSetup failed. You can still use the pipeline with manual login.")
        print("When running the pipeline, you'll be prompted to log in manually.")
    
    print("\n" + "="*70)
    print("SETUP COMPLETE")
    print("="*70)
    print("\nYou can now run the pipeline:")
    print("  python main.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
