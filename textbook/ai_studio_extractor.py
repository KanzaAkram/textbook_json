"""
AI Studio Extractor - Enhanced version with proven working logic from upload_to_gemini.py
Uses Selenium to interact with Google AI Studio
Extracts book structure by uploading PDF and getting AI analysis
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, Optional, List
import logging

# Try to import pyperclip for clipboard access
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("Note: pyperclip not installed. Install with: pip install pyperclip")

logger = logging.getLogger(__name__)


class AIStudioExtractor:
    """Extracts book structure using Google AI Studio via Selenium"""
    
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        
    def _setup_driver(self):
        """Setup Selenium WebDriver with appropriate options to bypass Google's automation detection"""
        from textbook.config import SELENIUM_CONFIG, config
        import tempfile
        
        # Use undetected-chromedriver if available (BETTER for bypassing Google detection)
        try:
            import undetected_chromedriver as uc
            
            logger.info("Using undetected-chromedriver for better Google login bypass...")
            user_data_dir = os.path.join(tempfile.gettempdir(), "chrome_uc_profile")
            os.makedirs(user_data_dir, exist_ok=True)
            
            options = uc.ChromeOptions()
            options.add_argument(f"--user-data-dir={user_data_dir}")
            
            if SELENIUM_CONFIG.get("headless"):
                options.add_argument("--headless")
            
            # Try with explicit version first (matches common Chrome versions)
            try:
                self.driver = uc.Chrome(options=options, version_main=142)
            except Exception as e:
                logger.info(f"Version 142 specification failed, trying auto-detection: {e}")
                # Fallback to auto-detection
                self.driver = uc.Chrome(options=options)
            
            self.driver.maximize_window()
            logger.info("Using undetected-chromedriver")
            
        except ImportError:
            # Fallback to regular selenium with anti-detection measures
            logger.info("Using regular Selenium with anti-detection measures...")
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            
            # CRITICAL: Remove automation flags that Google detects
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Make browser look more normal
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-gpu")
            
            # Use a user data directory to maintain login session
            user_data_dir = os.path.join(tempfile.gettempdir(), "chrome_selenium_profile")
            os.makedirs(user_data_dir, exist_ok=True)
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            
            if SELENIUM_CONFIG.get("headless"):
                chrome_options.add_argument("--headless")
            
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            self.driver.maximize_window()
            logger.info("Using standard Selenium Chrome driver with anti-detection")
        
        # Set timeouts
        self.driver.implicitly_wait(SELENIUM_CONFIG.get("implicit_wait", 15))
        self.driver.set_page_load_timeout(SELENIUM_CONFIG.get("page_load_timeout", 120))
        self.driver.set_script_timeout(SELENIUM_CONFIG.get("script_timeout", 300))
        
        return self.driver
    
    def _wait_for_element(self, by, value, timeout=30, clickable=False):
        """Wait for an element to be present or clickable"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(self.driver, timeout)
        
        if clickable:
            return wait.until(EC.element_to_be_clickable((by, value)))
        else:
            return wait.until(EC.presence_of_element_located((by, value)))
    
    def _wait_for_page_load(self, timeout=30):
        """Wait for page to fully load"""
        from selenium.webdriver.support.ui import WebDriverWait
        
        def page_loaded(driver):
            return driver.execute_script("return document.readyState") == "complete"
        
        WebDriverWait(self.driver, timeout).until(page_loaded)
    
    def extract_structure(self, pdf_path: Path, pdf_info: Dict) -> Dict:
        """
        Extract book structure using AI Studio
        
        Args:
            pdf_path: Path to the PDF file
            pdf_info: Basic PDF info from analyzer
            
        Returns:
            Extracted structure as dictionary
        """
        from textbook.config import AI_STUDIO_PROMPTS, SELENIUM_CONFIG, config
        
        logger.info(f"Starting AI Studio extraction for: {pdf_path.name}")
        
        try:
            # Setup driver if not already done
            if self.driver is None:
                self._setup_driver()
            
            # Navigate to AI Studio
            ai_studio_url = SELENIUM_CONFIG.get("ai_studio_url") or config.ai_studio_url or "https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview"
            
            logger.info(f"Navigating to AI Studio: {ai_studio_url}")
            self.driver.get(ai_studio_url)
            
            self._wait_for_page_load(60)
            time.sleep(5)  # Additional wait for dynamic content
            
            # Check if login is required
            if not self._check_and_handle_login():
                raise Exception("Failed to login to AI Studio")
            
            # Wait for chat interface to load
            logger.info("Waiting for chat interface...")
            time.sleep(5)
            
            # Upload the PDF
            logger.info("Uploading PDF file...")
            if not self._upload_pdf(pdf_path):
                raise Exception("Failed to upload PDF")
            
            # Send the structure extraction prompt
            logger.info("Sending extraction prompt...")
            prompt = AI_STUDIO_PROMPTS["structure_extraction"]
            
            if not self._send_prompt(prompt):
                raise Exception("Failed to send prompt")
            
            # Wait for and extract response
            logger.info("Waiting for AI response...")
            response = self._wait_for_response(timeout=SELENIUM_CONFIG.get("ai_studio_timeout", 600))
            
            if not response:
                raise Exception("No response received from AI Studio")
            
            # Try to copy response using copy button or extract from DOM
            logger.info("Extracting JSON response...")
            json_content = self._extract_json_response()
            
            if json_content:
                # Copy to clipboard if available
                if PYPERCLIP_AVAILABLE:
                    try:
                        pyperclip.copy(json_content)
                        logger.info("AI output copied to clipboard successfully")
                    except Exception as e:
                        logger.warning(f"Failed to copy to clipboard: {e}")
                
                # Save to file
                output_filename = pdf_path.stem + "_ai_response.json"
                output_path = pdf_path.parent / output_filename
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(json_content)
                    logger.info(f"JSON response saved to: {output_path}")
                except Exception as e:
                    logger.warning(f"Failed to save JSON file: {e}")
            
            # Parse JSON from response
            structure = self._parse_json_response(json_content or response)
            
            if structure:
                logger.info("Successfully extracted structure")
                return structure
            else:
                logger.warning("Could not parse JSON from response, saving raw response")
                return {
                    "raw_response": json_content or response,
                    "parse_error": True,
                    "book_info": {"title": pdf_path.stem},
                    "structure": []
                }
                
        except Exception as e:
            logger.error(f"AI Studio extraction failed: {e}")
            raise
    
    def _check_and_handle_login(self) -> bool:
        """Check if logged in and handle login if needed"""
        from selenium.webdriver.common.by import By
        from textbook.config import GOOGLE_EMAIL, GOOGLE_PASSWORD
        
        logger.info("Checking login status...")
        
        try:
            current_url = self.driver.current_url
            
            if "accounts.google.com" in current_url or "signin" in current_url.lower():
                logger.info("Google login page detected")
                
                # Try automatic login if credentials available
                if GOOGLE_EMAIL and GOOGLE_PASSWORD:
                    logger.info("Attempting automatic login...")
                    if self._auto_login(GOOGLE_EMAIL, GOOGLE_PASSWORD):
                        logger.info("Auto-login successful!")
                        self.is_logged_in = True
                        # Navigate to AI Studio if not there yet
                        if "aistudio.google.com" not in self.driver.current_url:
                            from textbook.config import SELENIUM_CONFIG, config
                            ai_studio_url = SELENIUM_CONFIG.get("ai_studio_url") or config.ai_studio_url or "https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview"
                            logger.info(f"Navigating to: {ai_studio_url}")
                            self.driver.get(ai_studio_url)
                            time.sleep(5)
                        return True
                    else:
                        logger.warning("Auto-login failed, falling back to manual login")
                
                # Fall back to manual login
                logger.info("=" * 60)
                logger.info("MANUAL LOGIN REQUIRED")
                logger.info("Please log in to your Google account in the browser window")
                logger.info("The script will continue automatically after login")
                logger.info("=" * 60)
                
                # Wait for redirect back to AI Studio
                from textbook.config import config
                timeout = config.manual_login_timeout
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    current_url = self.driver.current_url
                    if "aistudio.google.com" in current_url and "signin" not in current_url.lower():
                        logger.info("Manual login successful!")
                        self.is_logged_in = True
                        time.sleep(3)
                        return True
                    time.sleep(2)
                
                logger.error("Login timeout - please try again")
                return False
            
            elif "aistudio.google.com" in current_url:
                # Already on AI Studio, verify interface is loaded
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "textarea, input[type='text']")
                    logger.info("✓ Already logged in and ready!")
                    self.is_logged_in = True
                    return True
                except:
                    logger.warning("Could not verify login status. May need manual intervention.")
                    input("Please ensure you're logged in, then press Enter...")
                    return True
            
        except Exception as e:
            logger.error(f"Error checking login: {e}")
        
        return True  # Assume logged in if no login page detected
    
    def _auto_login(self, email: str, password: str, timeout: int = 60) -> bool:
        """
        Attempt automatic Google login with human-like behavior
        
        Args:
            email: Google account email
            password: Google account password
            timeout: Timeout for login process
        
        Returns:
            True if login successful, False otherwise
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            logger.info("="*60)
            logger.info("ATTEMPTING AUTOMATED GOOGLE LOGIN")
            logger.info("="*60)
            logger.info(f"Logging in as {email}...")
            
            wait = WebDriverWait(self.driver, 15)
            
            # Check if already logged in
            try:
                self.driver.find_element(By.CSS_SELECTOR, "textarea, input[type='text']")
                logger.info("✓ Already logged in!")
                return True
            except:
                pass
            
            # Find email input
            email_selectors = [
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name='identifier']"),
                (By.CSS_SELECTOR, "#identifierId"),
                (By.XPATH, "//input[@type='email']"),
            ]
            
            email_input = None
            for selector_type, selector in email_selectors:
                try:
                    email_input = wait.until(EC.presence_of_element_located((selector_type, selector)))
                    if email_input:
                        logger.info(f"Found email input with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_input:
                logger.warning("❌ Could not find email input field")
                return False
            
            # Enter email with human-like typing
            logger.info(f"Entering email: {email}")
            email_input.click()
            time.sleep(0.5)
            
            for char in email:
                email_input.send_keys(char)
                time.sleep(0.05 + (0.1 * (hash(char) % 10) / 10))
            
            time.sleep(1)
            
            # Click Next
            next_button_selectors = [
                (By.XPATH, "//button[contains(., 'Next')]"),
                (By.XPATH, "//button[@type='button']//span[contains(text(), 'Next')]"),
                (By.CSS_SELECTOR, "button[type='button']"),
                (By.ID, "identifierNext"),
            ]
            
            next_button = None
            for selector_type, selector in next_button_selectors:
                try:
                    next_button = self.driver.find_element(selector_type, selector)
                    if next_button and next_button.is_displayed():
                        break
                except:
                    continue
            
            if next_button:
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
            else:
                email_input.send_keys(Keys.RETURN)
                time.sleep(3)
            
            # Find password input
            password_selectors = [
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.XPATH, "//input[@type='password']"),
                (By.CSS_SELECTOR, "#password"),
            ]
            
            password_input = None
            for selector_type, selector in password_selectors:
                try:
                    password_input = wait.until(EC.presence_of_element_located((selector_type, selector)))
                    if password_input:
                        logger.info(f"Found password input with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                logger.warning("❌ Could not find password input field")
                logger.warning("This might be due to CAPTCHA, 2FA, or automation detection")
                return False
            
            # Enter password with human-like typing
            logger.info("Entering password...")
            password_input.click()
            time.sleep(0.5)
            
            for char in password:
                password_input.send_keys(char)
                time.sleep(0.05 + (0.1 * (hash(char) % 10) / 10))
            
            time.sleep(1)
            
            # Click Next/Sign in
            signin_button_selectors = [
                (By.XPATH, "//button[contains(., 'Next')]"),
                (By.XPATH, "//button[contains(., 'Sign in')]"),
                (By.XPATH, "//button[@type='button']//span[contains(text(), 'Next')]"),
                (By.ID, "passwordNext"),
                (By.CSS_SELECTOR, "button[type='button']"),
            ]
            
            signin_button = None
            for selector_type, selector in signin_button_selectors:
                try:
                    signin_button = self.driver.find_element(selector_type, selector)
                    if signin_button and signin_button.is_displayed():
                        break
                except:
                    continue
            
            if signin_button:
                self.driver.execute_script("arguments[0].click();", signin_button)
                time.sleep(5)
            else:
                password_input.send_keys(Keys.RETURN)
                time.sleep(5)
            
            # Wait for redirect
            logger.info("Checking login status...")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                current_url = self.driver.current_url
                if "aistudio.google.com" in current_url and "signin" not in current_url.lower():
                    logger.info("✓ Login successful!")
                    return True
                
                # Check for 2FA
                try:
                    if self.driver.find_elements(By.XPATH, "//*[contains(text(), 'verify') or contains(text(), 'Verify') or contains(text(), '2-Step')]"):
                        logger.warning("⚠️  2-Factor Authentication detected!")
                        logger.warning("Please complete 2FA manually, then press Enter...")
                        input()
                        return True
                except:
                    pass
                
                # Check for CAPTCHA
                page_source = self.driver.page_source.lower()
                if "captcha" in page_source or "unusual traffic" in page_source:
                    logger.warning("⚠️  CAPTCHA or security challenge detected!")
                    logger.warning("Please complete the challenge manually, then press Enter...")
                    input()
                    return True
                
                time.sleep(1)
            
            logger.warning("⚠️  Login status unclear.")
            input("If you're logged in, press Enter. Otherwise, complete login manually and press Enter...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during auto-login: {e}")
            import traceback
            traceback.print_exc()
            logger.info("\nFalling back to manual login...")
            input("Please log in manually, then press Enter to continue...")
            return True
    
    def _upload_pdf(self, pdf_path: Path) -> bool:
        """Upload PDF to AI Studio with enhanced detection"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        logger.info(f"\nUploading PDF: {pdf_path}")
        
        if not pdf_path.exists():
            logger.error(f"ERROR: PDF file not found at: {pdf_path}")
            return False
        
        try:
            wait = WebDriverWait(self.driver, 10)
            file_input = None
            
            # Method 1: Look for file input directly
            try:
                file_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='file']")))
                if file_inputs:
                    file_input = file_inputs[0]
                    logger.info("Found file input element directly")
            except Exception as e:
                logger.debug(f"Method 1 failed: {e}")
            
            # Method 2: Click upload button
            if not file_input:
                logger.info("Looking for upload/attach button...")
                upload_button_xpaths = [
                    "//button[contains(@aria-label, 'Upload')]",
                    "//button[contains(@aria-label, 'Attach')]",
                    "//button[contains(@aria-label, 'file')]",
                    "//button[contains(@title, 'Upload')]",
                    "//button[contains(@title, 'Attach')]",
                    "//div[contains(@role, 'button') and contains(@aria-label, 'Upload')]",
                    "//button[.//*[local-name()='svg']]//ancestor::button[1]",
                ]
                
                for xpath in upload_button_xpaths:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        visible = [e for e in elements if e.is_displayed()]
                        if visible:
                            upload_button = visible[0]
                            logger.info(f"Found upload button: {xpath}")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", upload_button)
                            time.sleep(1)
                            upload_button.click()
                            logger.info("Clicked upload button")
                            time.sleep(2)
                            
                            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                            if file_inputs:
                                file_input = file_inputs[0]
                                break
                    except:
                        continue
            
            # Method 3: Look near prompt area
            if not file_input:
                try:
                    prompt_elements = self.driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text']")
                    if prompt_elements:
                        parent = prompt_elements[0].find_element(By.XPATH, "./..")
                        file_inputs = parent.find_elements(By.CSS_SELECTOR, "input[type='file']")
                        if file_inputs:
                            file_input = file_inputs[0]
                            logger.info("Found file input near prompt")
                except:
                    pass
            
            # Try to make hidden inputs visible
            if not file_input:
                all_file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                for inp in all_file_inputs:
                    try:
                        self.driver.execute_script(
                            "arguments[0].style.display='block'; arguments[0].style.visibility='visible'; arguments[0].style.opacity='1';",
                            inp
                        )
                        file_input = inp
                        break
                    except:
                        continue
            
            # Upload the file
            if file_input:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", file_input)
                    time.sleep(1)
                    file_input.send_keys(str(pdf_path.absolute()))
                    logger.info("✓ File path sent to upload element")
                    
                    logger.info("Waiting for file to be processed...")
                    time.sleep(5)
                    
                    # Wait for overlays to disappear
                    try:
                        wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-backdrop-showing, .dialog-backdrop")))
                        logger.info("✓ Dialogs cleared")
                    except:
                        time.sleep(3)
                    
                    return True
                except Exception as e:
                    logger.error(f"Error sending file path: {e}")
                    return False
            else:
                logger.warning("Could not find file upload element")
                logger.info("\n" + "="*60)
                logger.info("MANUAL UPLOAD REQUIRED")
                logger.info(f"Please upload: {pdf_path}")
                logger.info("="*60)
                input("Press Enter after uploading...")
                return True
                
        except Exception as e:
            logger.error(f"Error uploading PDF: {e}")
            input("Press Enter after manually uploading the PDF...")
            return True
    
    def _send_prompt(self, prompt: str) -> bool:
        """Send prompt to AI Studio chat with improved methods"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            logger.info("\nEntering prompt text...")
            wait = WebDriverWait(self.driver, 15)
            
            # Wait for overlays to clear
            try:
                wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-backdrop-showing")))
            except:
                time.sleep(2)
                # Try to hide overlays with JavaScript
                try:
                    self.driver.execute_script("""
                        var overlays = document.querySelectorAll('.cdk-overlay-backdrop-showing');
                        overlays.forEach(function(overlay) { overlay.style.display = 'none'; });
                    """)
                    time.sleep(1)
                except:
                    pass
            
            # Find prompt input
            input_selectors = [
                (By.CSS_SELECTOR, "textarea[placeholder*='prompt'], textarea[placeholder*='type']"),
                (By.CSS_SELECTOR, "textarea[placeholder='Start typing a prompt']"),
                (By.CSS_SELECTOR, "textarea"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "[contenteditable='true']"),
            ]
            
            prompt_input = None
            for selector_type, selector in input_selectors:
                try:
                    prompt_input = wait.until(EC.presence_of_element_located((selector_type, selector)))
                    if prompt_input:
                        logger.info(f"Found prompt input: {selector}")
                        break
                except:
                    continue
            
            if not prompt_input:
                logger.warning("Could not find prompt input")
                input("Please paste the prompt manually and press Enter...")
                return True
            
            # Try JavaScript to set value (bypasses overlays)
            success = False
            try:
                logger.info("Setting prompt text using JavaScript...")
                self.driver.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, prompt_input, prompt)
                time.sleep(1)
                
                # Verify
                current_value = self.driver.execute_script("return arguments[0].value;", prompt_input)
                if current_value and len(current_value) > 100:
                    logger.info("✓ Prompt text entered via JavaScript")
                    success = True
            except Exception as e:
                logger.debug(f"JavaScript method failed: {e}")
            
            # Fallback: Try regular click and type
            if not success:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", prompt_input)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", prompt_input)
                    time.sleep(0.5)
                    prompt_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.3)
                    prompt_input.send_keys(prompt)
                    time.sleep(1)
                    logger.info("✓ Prompt text entered via typing")
                    success = True
                except Exception as e:
                    logger.warning(f"Typing method failed: {e}")
            
            if not success:
                logger.warning("Could not enter prompt automatically")
                return False
            
            # Send the prompt
            logger.info("\nSending prompt...")
            
            # Look for send button
            send_xpaths = [
                "//button[contains(@aria-label, 'Send')]",
                "//button[contains(@aria-label, 'Run')]",
                "//button[contains(@aria-label, 'Submit')]",
                "//button[contains(text(), 'Send')]",
                "//button[@type='submit']",
                "//textarea/following-sibling::button",
            ]
            
            send_button = None
            for xpath in send_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    visible = [e for e in elements if e.is_displayed() and e.is_enabled()]
                    if visible:
                        send_button = visible[0]
                        logger.info(f"Found send button: {xpath}")
                        break
                except:
                    continue
            
            if send_button:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", send_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", send_button)
                    logger.info("✓ Prompt sent via button click")
                    return True
                except Exception as e:
                    logger.debug(f"Button click failed: {e}")
            
            # Fallback: Use Enter key
            try:
                prompt_input.click()
                time.sleep(0.5)
                prompt_input.send_keys(Keys.RETURN)
                logger.info("✓ Prompt sent via Enter key")
                return True
            except Exception as e:
                logger.error(f"Could not send prompt: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            return False
    
    def _wait_for_response(self, timeout: int = 600) -> Optional[str]:
        """Wait for AI response and extract it"""
        from selenium.webdriver.common.by import By
        
        logger.info(f"\nWaiting for AI response (timeout: {timeout}s)...")
        logger.info("This may take some time depending on the document size...")
        
        start_time = time.time()
        max_wait_time = timeout
        wait_interval = 5
        elapsed_time = 0
        response_generated = False
        
        response_indicators = [
            "//div[contains(@class, 'response')]",
            "//div[contains(@class, 'output')]",
            "//div[contains(@class, 'result')]",
            "//div[contains(@class, 'content')]//pre",
            "//div[contains(@class, 'markdown')]",
        ]
        
        while elapsed_time < max_wait_time:
            try:
                for xpath in response_indicators:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        for elem in elements:
                            text = elem.text
                            if text and len(text) > 100:
                                # Check if still generating
                                loading = self.driver.find_elements(By.XPATH, 
                                    "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(text(), 'Generating')]")
                                if not any(l.is_displayed() for l in loading):
                                    response_generated = True
                                    logger.info("✓ Response appears complete")
                                    break
                        if response_generated:
                            break
                
                if response_generated:
                    break
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                
                if elapsed_time % 30 == 0:
                    logger.info(f"Still waiting... ({elapsed_time}/{max_wait_time} seconds)")
                    
            except Exception as e:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
        
        if not response_generated:
            logger.warning("Could not detect if response is complete. Proceeding anyway...")
        
        time.sleep(3)
        
        # Try to get response text
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            return body.text
        except:
            return None
    
    def _extract_json_response(self) -> Optional[str]:
        """Extract JSON content from the page using copy button or DOM extraction"""
        from selenium.webdriver.common.by import By
        
        logger.info("\nAttempting to extract JSON content...")
        json_content = None
        
        # Method 1: Extract JSON directly from DOM
        try:
            logger.info("Extracting JSON from page DOM...")
            
            # Look for code blocks
            code_selectors = [
                "//pre[contains(@class, 'code') or contains(@class, 'json')]",
                "//code",
                "//div[contains(@class, 'code-block')]",
                "//pre",
            ]
            
            code_block = None
            for selector in code_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    code_block = elements[-1]  # Get most recent
                    text = code_block.text
                    if text and len(text) > 50 and (text.strip().startswith('{') or text.strip().startswith('[')):
                        json_content = text
                        logger.info(f"✓ Extracted JSON from DOM ({len(json_content)} characters)")
                        break
        except Exception as e:
            logger.debug(f"DOM extraction failed: {e}")
        
        # Method 2: Try copy button
        if not json_content:
            try:
                logger.info("Looking for copy button...")
                
                # Find code block first
                code_block = None
                try:
                    code_elements = self.driver.find_elements(By.XPATH, "//pre | //code")
                    if code_elements:
                        code_block = code_elements[-1]
                except:
                    pass
                
                # Look for copy button near code block
                copy_button = None
                if code_block:
                    try:
                        container = code_block.find_element(By.XPATH, "./..")
                        nearby_copy = container.find_elements(By.XPATH, 
                            ".//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy')] | "
                            ".//button[contains(@class, 'copy')]")
                        if nearby_copy:
                            visible = [b for b in nearby_copy if b.is_displayed() and b.is_enabled()]
                            if visible:
                                copy_button = visible[0]
                                logger.info("Found copy button near code block")
                    except:
                        pass
                
                # Try general copy button search
                if not copy_button:
                    copy_xpaths = [
                        "//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy')]",
                        "//button[@aria-label='Copy']",
                        "//button[contains(@class, 'copy')]",
                    ]
                    for xpath in copy_xpaths:
                        try:
                            elements = self.driver.find_elements(By.XPATH, xpath)
                            visible = [e for e in elements if e.is_displayed() and e.is_enabled()]
                            if visible:
                                copy_button = visible[0]
                                logger.info(f"Found copy button: {xpath}")
                                break
                        except:
                            continue
                
                # Click copy button
                if copy_button:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", copy_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", copy_button)
                    time.sleep(3)
                    logger.info("✓ Copy button clicked")
                    
                    # Get from clipboard
                    if PYPERCLIP_AVAILABLE:
                        try:
                            copied_content = pyperclip.paste()
                            if copied_content and len(copied_content) > 50:
                                json_content = copied_content
                                logger.info(f"✓ Content copied from clipboard ({len(copied_content)} characters)")
                        except Exception as e:
                            logger.debug(f"Clipboard read failed: {e}")
                
            except Exception as e:
                logger.debug(f"Copy button method failed: {e}")
        
        return json_content
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from AI response"""
        if not response:
            return None
        
        # Clean up response first
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith('```'):
            # Remove ```json or ``` at start
            response = re.sub(r'^```(?:json)?\s*', '', response, flags=re.IGNORECASE)
            # Remove ``` at end
            response = re.sub(r'\s*```$', '', response)
        
        # Try to find JSON in response
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
            r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
            r'(\{[\s\S]{50,}\})',           # Raw JSON object (at least 50 chars)
        ]
        
        json_str = None
        
        for pattern in patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    json_str = match.strip()
                    # Remove any trailing punctuation or text after closing brace
                    json_str = re.sub(r'(\})\s*[^\}]*$', r'\1', json_str)
                    data = json.loads(json_str)
                    
                    # Accept any valid dict (for page extraction, it has "subtopics", not "structure")
                    if isinstance(data, dict):
                        logger.info("Successfully parsed JSON response")
                        return data
                        
                except json.JSONDecodeError as e:
                    logger.debug(f"Pattern {pattern} matched but failed to parse: {e}")
                    continue
        
        # Try parsing entire response
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                # Clean up any trailing text
                json_str = re.sub(r'(\})\s*[^\}]*$', r'\1', json_str)
                data = json.loads(json_str)
                if isinstance(data, dict):
                    logger.info("Successfully parsed JSON response (direct parse)")
                    return data
        except json.JSONDecodeError as e:
            logger.debug(f"Direct parse failed: {e}")
        
        logger.warning("Could not parse JSON from response")
        # Save failed response for debugging
        try:
            debug_path = Path("temp") / "failed_json_response.txt"
            debug_path.parent.mkdir(exist_ok=True)
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(response)
            logger.info(f"Saved failed response to: {debug_path} (first 500 chars: {response[:500]})")
        except:
            pass
        return None
    
    def interactive_extraction(self, pdf_path: Path, pdf_info: Dict) -> Dict:
        """Semi-interactive extraction with manual assistance"""
        from textbook.config import AI_STUDIO_PROMPTS
        
        logger.info("Starting interactive extraction mode...")
        
        if self.driver is None:
            self._setup_driver()
        
        self.driver.get("https://aistudio.google.com/prompts/new_chat")
        self._wait_for_page_load(60)
        time.sleep(3)
        
        self._check_and_handle_login()
        
        print("\n" + "=" * 70)
        print("INTERACTIVE EXTRACTION MODE")
        print("=" * 70)
        print(f"\n1. Upload this PDF to AI Studio:")
        print(f"   {pdf_path.absolute()}")
        print(f"\n2. Copy and paste this prompt:\n")
        print("-" * 70)
        print(AI_STUDIO_PROMPTS.get("structure_extraction_simple", AI_STUDIO_PROMPTS.get("structure_extraction")))
        print("-" * 70)
        print("\n3. After AI responds with JSON, copy the JSON response")
        print("\n4. Paste the JSON response below (end with an empty line):")
        print("-" * 70)
        
        # Collect multi-line input
        lines = []
        while True:
            try:
                line = input()
                if line == "":
                    break
                lines.append(line)
            except EOFError:
                break
        
        response = "\n".join(lines)
        
        # Parse the response
        structure = self._parse_json_response(response)
        
        if structure:
            logger.info("Successfully parsed manual JSON input")
            return structure
        else:
            logger.error("Could not parse JSON. Please check the format.")
            return {
                "raw_response": response,
                "parse_error": True,
                "book_info": {"title": pdf_path.stem},
                "structure": []
            }
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
