"""
AI Studio Extractor - Uses Selenium to interact with Google AI Studio
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
        from config import SELENIUM_CONFIG
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
        from config import AI_STUDIO_PROMPTS, SELENIUM_CONFIG, config
        
        logger.info(f"Starting AI Studio extraction for: {pdf_path.name}")
        
        try:
            # Setup driver if not already done
            if self.driver is None:
                self._setup_driver()
            
            # Navigate to AI Studio
            # Use URL from config, fallback to default with model parameter
            ai_studio_url = SELENIUM_CONFIG.get("ai_studio_url") or config.ai_studio_url or "https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview"
            
            logger.info(f"Navigating to AI Studio: {ai_studio_url}")
            self.driver.get(ai_studio_url)
            
            self._wait_for_page_load(60)
            time.sleep(3)  # Additional wait for dynamic content
            
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
            
            # Copy response to clipboard using pyperclip
            if PYPERCLIP_AVAILABLE:
                try:
                    pyperclip.copy(response)
                    logger.info("AI output copied to clipboard successfully")
                except Exception as e:
                    logger.warning(f"Failed to copy to clipboard: {e}")
            else:
                logger.info("pyperclip not available - skipping clipboard copy")
            
            # Parse JSON from response
            structure = self._parse_json_response(response)
            
            if structure:
                logger.info("Successfully extracted structure")
                return structure
            else:
                logger.warning("Could not parse JSON from response, saving raw response")
                return {
                    "raw_response": response,
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
        from config import GOOGLE_EMAIL, GOOGLE_PASSWORD, PYPERCLIP_AVAILABLE
        
        logger.info("Checking login status...")
        
        # Check for common login indicators
        try:
            # Look for sign-in button or Google account button
            current_url = self.driver.current_url
            
            if "accounts.google.com" in current_url:
                logger.info("Google login page detected")
                
                # Try automatic login if credentials available
                if GOOGLE_EMAIL and GOOGLE_PASSWORD:
                    logger.info("Attempting automatic login...")
                    if self._auto_login(GOOGLE_EMAIL, GOOGLE_PASSWORD):
                        logger.info("Auto-login successful!")
                        self.is_logged_in = True
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
                from config import config
                timeout = config.manual_login_timeout
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    current_url = self.driver.current_url
                    if "aistudio.google.com" in current_url:
                        logger.info("Manual login successful!")
                        self.is_logged_in = True
                        time.sleep(3)
                        return True
                    time.sleep(2)
                
                logger.error("Login timeout - please try again")
                return False
            
            elif "aistudio.google.com" in current_url:
                # Already on AI Studio, check if interface is loaded
                time.sleep(3)
                self.is_logged_in = True
                return True
            
        except Exception as e:
            logger.error(f"Error checking login: {e}")
        
        return True  # Assume logged in if no login page detected
    
    def _auto_login(self, email: str, password: str, timeout: int = 60) -> bool:
        """
        Attempt automatic Google login
        
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
            logger.info(f"Logging in as {email}...")
            
            # Wait for email field
            wait = WebDriverWait(self.driver, timeout)
            
            # Find and fill email field
            email_selectors = [
                "input[type='email']",
                "#identifierId",
                "input[name='email']"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        email_field = elements[0]
                        break
                except:
                    pass
            
            if not email_field:
                logger.warning("Could not find email field")
                return False
            
            # Clear and enter email
            email_field.clear()
            time.sleep(0.5)
            email_field.send_keys(email)
            time.sleep(0.5)
            
            # Find and click Next button
            next_selectors = [
                "button:contains('Next')",
                "button[aria-label='Next']",
                "#identifierNext",
                "button[jsname='x8hlje']"
            ]
            
            next_button = None
            for selector in next_selectors:
                try:
                    if "contains" in selector:
                        # Can't use :contains in CSS, try XPath
                        elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), 'Next')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            next_button = elem
                            break
                except:
                    pass
                
                if next_button:
                    break
            
            if not next_button:
                logger.warning("Could not find Next button, trying Enter key")
                email_field.send_keys(Keys.RETURN)
            else:
                next_button.click()
            
            time.sleep(2)
            
            # Find and fill password field
            pass_selectors = [
                "input[type='password']",
                "#password",
                "input[name='password']"
            ]
            
            password_field = None
            for selector in pass_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        password_field = elements[0]
                        break
                except:
                    pass
            
            if not password_field:
                logger.warning("Could not find password field")
                return False
            
            # Clear and enter password
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(password)
            time.sleep(0.5)
            
            # Find and click Next button for password
            next_button = None
            for selector in next_selectors:
                try:
                    if "contains" in selector:
                        elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), 'Next')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            next_button = elem
                            break
                except:
                    pass
                
                if next_button:
                    break
            
            if not next_button:
                logger.warning("Could not find Next button for password, trying Enter key")
                password_field.send_keys(Keys.RETURN)
            else:
                next_button.click()
            
            # Wait for redirect to AI Studio
            start_time = time.time()
            while time.time() - start_time < timeout:
                current_url = self.driver.current_url
                if "aistudio.google.com" in current_url:
                    logger.info("Successfully logged in!")
                    time.sleep(3)
                    return True
                
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'invalid') or contains(text(), 'error')]")
                    if error_elements:
                        logger.error("Login error detected")
                        return False
                except:
                    pass
                
                time.sleep(1)
            
            logger.warning("Login timeout - redirect to AI Studio did not occur")
            return False
            
        except Exception as e:
            logger.error(f"Error during auto-login: {e}")
            return False
    
    def _upload_pdf(self, pdf_path: Path) -> bool:
        """Upload PDF to AI Studio"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            # Look for file upload button/area
            # AI Studio typically has an attachment/upload button
            
            # Try different selectors for upload button
            upload_selectors = [
                "input[type='file']",
                "[aria-label*='upload']",
                "[aria-label*='Upload']",
                "[aria-label*='attach']",
                "[aria-label*='Attach']",
                "button[aria-label*='file']",
                ".upload-button",
                "[data-testid='upload-button']"
            ]
            
            file_input = None
            
            # First, try to find hidden file input
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_input = file_inputs[0]
                    logger.info("Found file input element")
            except:
                pass
            
            if file_input is None:
                # Try to click an upload button first
                for selector in upload_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                elem.click()
                                time.sleep(1)
                                # After click, look for file input again
                                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                                if file_inputs:
                                    file_input = file_inputs[0]
                                    break
                    except:
                        continue
                    if file_input:
                        break
            
            if file_input is None:
                # Try using keyboard shortcut to open file dialog
                logger.info("Trying keyboard shortcut for file upload...")
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.CONTROL + 'o')
                time.sleep(1)
                
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_input = file_inputs[0]
            
            if file_input:
                # Make the input visible if hidden
                self.driver.execute_script(
                    "arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';",
                    file_input
                )
                time.sleep(0.5)
                
                # Send the file path
                file_input.send_keys(str(pdf_path.absolute()))
                logger.info(f"File path sent: {pdf_path.absolute()}")
                
                # Wait for upload to complete
                time.sleep(10)  # Wait for upload
                
                # Check for upload confirmation
                logger.info("PDF upload initiated")
                return True
            else:
                logger.warning("Could not find file input. Manual upload may be required.")
                logger.info("=" * 60)
                logger.info("MANUAL UPLOAD REQUIRED")
                logger.info(f"Please manually upload the file: {pdf_path.absolute()}")
                logger.info("Press Enter in the console after uploading...")
                logger.info("=" * 60)
                input("Press Enter after uploading the PDF manually...")
                return True
                
        except Exception as e:
            logger.error(f"Error uploading PDF: {e}")
            logger.info("=" * 60)
            logger.info("MANUAL UPLOAD REQUIRED")
            logger.info(f"Please manually upload the file: {pdf_path.absolute()}")
            logger.info("Press Enter in the console after uploading...")
            logger.info("=" * 60)
            input("Press Enter after uploading the PDF manually...")
            return True
    
    def _send_prompt(self, prompt: str) -> bool:
        """Send prompt to AI Studio chat"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        
        try:
            # Find the text input area
            input_selectors = [
                "textarea",
                "[contenteditable='true']",
                "input[type='text']",
                ".chat-input",
                "[aria-label*='message']",
                "[aria-label*='Message']",
                "[aria-label*='prompt']",
                "[aria-label*='Prompt']",
                "[data-testid='chat-input']"
            ]
            
            text_input = None
            
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            text_input = elem
                            logger.info(f"Found text input: {selector}")
                            break
                except:
                    continue
                if text_input:
                    break
            
            if text_input is None:
                logger.warning("Could not find text input automatically")
                logger.info("=" * 60)
                logger.info("MANUAL INPUT REQUIRED")
                logger.info("Please paste the following prompt into AI Studio:")
                logger.info("-" * 60)
                print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
                logger.info("-" * 60)
                logger.info("Press Enter after sending the prompt...")
                logger.info("=" * 60)
                input("Press Enter after sending the prompt manually...")
                return True
            
            # Click on the input area
            text_input.click()
            time.sleep(0.5)
            
            # Clear any existing text
            text_input.clear()
            time.sleep(0.3)
            
            # Send the prompt
            # For long prompts, use JavaScript to set value
            if len(prompt) > 1000:
                self.driver.execute_script(
                    "arguments[0].value = arguments[1];",
                    text_input, prompt
                )
                # Trigger input event
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                    text_input
                )
            else:
                text_input.send_keys(prompt)
            
            time.sleep(1)
            
            # Find and click send button
            send_selectors = [
                "button[aria-label*='send']",
                "button[aria-label*='Send']",
                "button[aria-label*='submit']",
                "button[aria-label*='Submit']",
                "[data-testid='send-button']",
                "button.send-button",
                "button[type='submit']"
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            send_button = elem
                            break
                except:
                    continue
                if send_button:
                    break
            
            if send_button:
                send_button.click()
                logger.info("Prompt sent via button click")
            else:
                # Try sending with Enter key
                text_input.send_keys(Keys.RETURN)
                logger.info("Prompt sent via Enter key")
            
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            return False
    
    def _wait_for_response(self, timeout: int = 600) -> Optional[str]:
        """Wait for AI response and extract it"""
        from selenium.webdriver.common.by import By
        
        logger.info(f"Waiting for response (timeout: {timeout}s)...")
        
        start_time = time.time()
        last_response_length = 0
        stable_count = 0
        
        # Response selectors to try
        response_selectors = [
            ".response-content",
            ".message-content",
            "[data-testid='response']",
            ".ai-response",
            ".assistant-message",
            ".model-response",
            "div[class*='response']",
            "div[class*='message']"
        ]
        
        while time.time() - start_time < timeout:
            try:
                # Try to find response elements
                response_text = ""
                
                for selector in response_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if len(text) > len(response_text):
                            response_text = text
                
                # Also try getting all text from main content area
                if not response_text:
                    try:
                        main_content = self.driver.find_element(By.TAG_NAME, "main")
                        response_text = main_content.text
                    except:
                        pass
                
                # Check if response is complete (stable for a few iterations)
                if response_text and "{" in response_text:
                    if len(response_text) == last_response_length:
                        stable_count += 1
                        if stable_count >= 5:  # Response stable for 5 checks
                            logger.info("Response appears complete")
                            return response_text
                    else:
                        stable_count = 0
                        last_response_length = len(response_text)
                        logger.info(f"Response growing: {len(response_text)} chars")
                
                time.sleep(2)
                
            except Exception as e:
                logger.debug(f"Error checking response: {e}")
                time.sleep(2)
        
        # Timeout - try to get whatever response we have
        logger.warning("Response timeout - attempting to get partial response")
        
        try:
            # Get all text from page
            body = self.driver.find_element(By.TAG_NAME, "body")
            return body.text
        except:
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from AI response"""
        if not response:
            return None
        
        # Try to find JSON in response
        # Look for JSON block between ``` or just raw JSON
        
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
            r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
            r'(\{[\s\S]*\})',                # Raw JSON object
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    # Clean up the match
                    json_str = match.strip()
                    
                    # Try to parse
                    data = json.loads(json_str)
                    
                    # Validate it has expected structure
                    if isinstance(data, dict) and ("structure" in data or "book_info" in data):
                        logger.info("Successfully parsed JSON response")
                        return data
                        
                except json.JSONDecodeError:
                    continue
        
        # Try parsing the entire response
        try:
            # Find the outermost { }
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                if isinstance(data, dict):
                    return data
        except:
            pass
        
        logger.warning("Could not parse JSON from response")
        return None
    
    def interactive_extraction(self, pdf_path: Path, pdf_info: Dict) -> Dict:
        """
        Semi-interactive extraction with manual assistance
        Use this when automatic extraction fails
        """
        from config import AI_STUDIO_PROMPTS
        
        logger.info("Starting interactive extraction mode...")
        
        if self.driver is None:
            self._setup_driver()
        
        # Open AI Studio
        self.driver.get("https://aistudio.google.com/prompts/new_chat")
        self._wait_for_page_load(60)
        time.sleep(3)
        
        # Handle login
        self._check_and_handle_login()
        
        print("\n" + "=" * 70)
        print("INTERACTIVE EXTRACTION MODE")
        print("=" * 70)
        print(f"\n1. Upload this PDF to AI Studio:")
        print(f"   {pdf_path.absolute()}")
        print(f"\n2. Copy and paste this prompt:\n")
        print("-" * 70)
        print(AI_STUDIO_PROMPTS["structure_extraction_simple"])
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
