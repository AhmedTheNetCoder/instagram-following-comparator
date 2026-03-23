"""
Instagram Following List Scraper
================================
Extracts usernames from an already-open Instagram "Following" popup.

DESIGN DECISIONS:
- Connects to existing Chrome session via debugging port (no login automation)
- Uses slow, human-like scrolling to reduce detection risk
- Implements duplicate detection and automatic stop condition
- Saves progress incrementally to prevent data loss

USAGE:
1. Start Chrome with debugging: chrome.exe --remote-debugging-port=9222
2. Manually log into Instagram and open the "Following" popup
3. Run this script: python scrape_following.py output_filename.json
"""

import json
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException,
        StaleElementReferenceException,
        TimeoutException
    )
except ImportError:
    print("ERROR: Selenium not installed. Run: pip install selenium")
    sys.exit(1)


class InstagramFollowingScraper:
    """
    Scrapes usernames from an open Instagram Following popup.

    Connects to an existing Chrome browser session via remote debugging.
    This approach avoids login automation entirely, reducing detection risk.
    """

    # Instagram DOM selectors (updated March 2024)
    # These may need adjustment if Instagram changes their HTML structure
    SELECTORS = {
        # The scrollable dialog container
        'dialog_scrollable': 'div[role="dialog"] div[style*="overflow"]',
        # Alternative: direct class-based selector for the scroll container
        'dialog_scroll_alt': 'div[role="dialog"] div._aano',
        # Username links within the following list
        'username_links': 'div[role="dialog"] a[role="link"] span',
        # Alternative username selector
        'username_links_alt': 'div[role="dialog"] div._aacl._aaco._aacw._aacx._aad7._aade',
        # The close button (to verify dialog is open)
        'close_button': 'div[role="dialog"] button svg[aria-label="Close"]',
    }

    def __init__(self, debug_port: int = 9222, scroll_pause: float = 1.5):
        """
        Initialize the scraper.

        Args:
            debug_port: Chrome remote debugging port (default: 9222)
            scroll_pause: Seconds to wait between scrolls (default: 1.5)
                         Higher = slower but safer from rate limits
        """
        self.debug_port = debug_port
        self.scroll_pause = scroll_pause
        self.driver = None
        self.usernames = set()  # Use set for automatic deduplication

    def connect_to_chrome(self) -> bool:
        """
        Connect to an existing Chrome session via remote debugging.

        REASONING: This approach means we never handle Instagram credentials.
        The user logs in manually, and we just read the DOM.

        Returns:
            True if connection successful, False otherwise
        """
        print(f"[*] Connecting to Chrome on port {self.debug_port}...")

        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")

            self.driver = webdriver.Chrome(options=options)

            # Verify we're on Instagram
            current_url = self.driver.current_url
            if "instagram.com" not in current_url:
                print(f"[!] Warning: Current page is not Instagram: {current_url}")
                print("[!] Please navigate to Instagram and open a Following popup")
                return False

            print(f"[+] Connected! Current URL: {current_url}")
            return True

        except Exception as e:
            print(f"[!] Failed to connect to Chrome: {e}")
            print("\n[!] TROUBLESHOOTING:")
            print("    1. Close ALL Chrome windows completely")
            print("    2. Open Command Prompt and run:")
            print(f'       chrome.exe --remote-debugging-port={self.debug_port}')
            print("    3. Log into Instagram manually")
            print("    4. Open the Following popup")
            print("    5. Run this script again")
            return False

    def find_scroll_container(self):
        """
        Find the scrollable container within the Following dialog.

        REASONING: Instagram's dialog has a specific scrollable div.
        We need to find it to scroll and load more users.

        Returns:
            WebElement of scrollable container, or None if not found
        """
        selectors_to_try = [
            self.SELECTORS['dialog_scrollable'],
            self.SELECTORS['dialog_scroll_alt'],
            'div[role="dialog"] div[class*="x1n2onr6"]',  # Common Instagram class
            'div[role="dialog"] > div > div > div:nth-child(2)',  # Structural fallback
        ]

        for selector in selectors_to_try:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    # Check if this element is scrollable
                    scroll_height = self.driver.execute_script(
                        "return arguments[0].scrollHeight", element
                    )
                    client_height = self.driver.execute_script(
                        "return arguments[0].clientHeight", element
                    )

                    if scroll_height > client_height:
                        print(f"[+] Found scrollable container with selector: {selector}")
                        return element

            except Exception:
                continue

        # Last resort: find by executing JS to find scrollable divs in dialog
        try:
            scroll_container = self.driver.execute_script("""
                const dialog = document.querySelector('div[role="dialog"]');
                if (!dialog) return null;

                const divs = dialog.querySelectorAll('div');
                for (const div of divs) {
                    if (div.scrollHeight > div.clientHeight + 50 &&
                        div.clientHeight > 100) {
                        return div;
                    }
                }
                return null;
            """)

            if scroll_container:
                print("[+] Found scrollable container via JavaScript fallback")
                return scroll_container

        except Exception as e:
            print(f"[!] JS fallback failed: {e}")

        return None

    def extract_usernames(self) -> set:
        """
        Extract all visible usernames from the current state of the popup.

        REASONING: We extract usernames after each scroll to capture newly
        loaded content. Using a set ensures no duplicates.

        Returns:
            Set of usernames found
        """
        found_usernames = set()

        # Strategy 1: Find all links within the dialog that look like profile links
        try:
            # Instagram profile links in the following list
            links = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[role="dialog"] a[href^="/"][role="link"]'
            )

            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and "/" in href:
                        # Extract username from href like "/username/" or "/username"
                        parts = href.strip("/").split("/")
                        if parts:
                            username = parts[-1] if parts[-1] else parts[-2] if len(parts) > 1 else None
                            # Filter out non-username paths
                            if username and username not in ['explore', 'reels', 'stories', 'direct', 'p']:
                                # Additional validation: usernames are alphanumeric with underscores/periods
                                if self._is_valid_username(username):
                                    found_usernames.add(username.lower())
                except StaleElementReferenceException:
                    continue

        except Exception as e:
            print(f"[!] Error extracting via links: {e}")

        # Strategy 2: Find span elements with username text
        try:
            spans = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[role="dialog"] span[dir="auto"]'
            )

            for span in spans:
                try:
                    text = span.text.strip()
                    if text and self._is_valid_username(text):
                        found_usernames.add(text.lower())
                except StaleElementReferenceException:
                    continue

        except Exception as e:
            print(f"[!] Error extracting via spans: {e}")

        return found_usernames

    def _is_valid_username(self, text: str) -> bool:
        """
        Validate if a string looks like an Instagram username.

        Instagram usernames:
        - 1-30 characters
        - Letters, numbers, periods, underscores only
        - Cannot be purely numeric (usually)
        """
        if not text or len(text) > 30:
            return False

        # Must contain at least one letter
        has_letter = any(c.isalpha() for c in text)
        if not has_letter:
            return False

        # Only allowed characters
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._')
        if not all(c in allowed for c in text):
            return False

        # Common false positives to exclude
        excluded = {'following', 'followers', 'posts', 'follow', 'message', 'verified', 'see', 'all'}
        if text.lower() in excluded:
            return False

        return True

    def scroll_and_extract(self, max_scrolls: int = 500, no_new_threshold: int = 5) -> set:
        """
        Main scraping loop: scroll the popup and extract usernames.

        REASONING:
        - Scroll incrementally to trigger lazy loading
        - Track consecutive scrolls with no new users as stop condition
        - Use randomized delays to appear more human-like

        Args:
            max_scrolls: Maximum number of scroll operations (safety limit)
            no_new_threshold: Stop after this many scrolls with no new users

        Returns:
            Set of all extracted usernames
        """
        scroll_container = self.find_scroll_container()

        if not scroll_container:
            print("[!] ERROR: Could not find the Following popup scroll container")
            print("[!] Make sure the Following popup is open and visible")
            return set()

        print("[*] Starting extraction...")
        print(f"[*] Settings: max_scrolls={max_scrolls}, stop_after_no_new={no_new_threshold}")
        print("-" * 50)

        consecutive_no_new = 0
        scroll_count = 0
        last_count = 0

        # Initial extraction
        self.usernames = self.extract_usernames()
        print(f"[+] Initial extraction: {len(self.usernames)} usernames")

        while scroll_count < max_scrolls:
            # Scroll down
            try:
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight * 0.8",
                    scroll_container
                )
            except StaleElementReferenceException:
                print("[!] Scroll container became stale, re-finding...")
                scroll_container = self.find_scroll_container()
                if not scroll_container:
                    print("[!] Could not re-find scroll container, stopping")
                    break
                continue

            # Wait for content to load (randomized for human-like behavior)
            import random
            wait_time = self.scroll_pause + random.uniform(0, 0.5)
            time.sleep(wait_time)

            # Extract usernames
            new_usernames = self.extract_usernames()
            self.usernames.update(new_usernames)

            scroll_count += 1
            current_count = len(self.usernames)
            new_this_scroll = current_count - last_count

            # Progress update
            if scroll_count % 5 == 0 or new_this_scroll > 0:
                print(f"[*] Scroll {scroll_count}: {current_count} total users (+{new_this_scroll} new)")

            # Check stop condition
            if new_this_scroll == 0:
                consecutive_no_new += 1
                if consecutive_no_new >= no_new_threshold:
                    print(f"[+] No new users for {no_new_threshold} scrolls - reached end of list")
                    break
            else:
                consecutive_no_new = 0

            last_count = current_count

            # Check if we've hit the bottom
            try:
                at_bottom = self.driver.execute_script("""
                    return arguments[0].scrollTop + arguments[0].clientHeight >= arguments[0].scrollHeight - 10;
                """, scroll_container)

                if at_bottom and consecutive_no_new >= 2:
                    print("[+] Reached bottom of scroll container")
                    break

            except Exception:
                pass

        print("-" * 50)
        print(f"[+] Extraction complete: {len(self.usernames)} unique usernames")

        return self.usernames

    def save_results(self, filename: str) -> str:
        """
        Save extracted usernames to a JSON file.

        Format:
        {
            "metadata": {...},
            "usernames": [...]
        }
        """
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'

        output = {
            "metadata": {
                "extracted_at": datetime.now().isoformat(),
                "total_count": len(self.usernames),
                "source_url": self.driver.current_url if self.driver else "unknown"
            },
            "usernames": sorted(list(self.usernames))
        }

        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"[+] Saved {len(self.usernames)} usernames to: {output_path.absolute()}")
        return str(output_path.absolute())


def main():
    parser = argparse.ArgumentParser(
        description="Extract usernames from an open Instagram Following popup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE EXAMPLE:
  1. Start Chrome with debugging enabled:
     chrome.exe --remote-debugging-port=9222

  2. Log into Instagram manually

  3. Navigate to a profile and click "Following"

  4. Run this script:
     python scrape_following.py account1_following.json

  5. Repeat for second account:
     python scrape_following.py account2_following.json

  6. Compare the lists:
     python compare_lists.py account1_following.json account2_following.json
        """
    )

    parser.add_argument(
        "output",
        help="Output filename for the JSON results (e.g., 'account1_following.json')"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9222,
        help="Chrome debugging port (default: 9222)"
    )
    parser.add_argument(
        "--scroll-delay",
        type=float,
        default=1.5,
        help="Seconds between scrolls (default: 1.5, higher = safer)"
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=500,
        help="Maximum scroll operations (default: 500)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Instagram Following List Scraper")
    print("=" * 60)
    print()

    scraper = InstagramFollowingScraper(
        debug_port=args.port,
        scroll_pause=args.scroll_delay
    )

    if not scraper.connect_to_chrome():
        sys.exit(1)

    print()
    input("[*] Press ENTER when the Following popup is open and visible...")
    print()

    usernames = scraper.scroll_and_extract(max_scrolls=args.max_scrolls)

    if usernames:
        scraper.save_results(args.output)
        print()
        print("[+] SUCCESS! You can now run this script for the second account,")
        print("    then use compare_lists.py to find mutual follows.")
    else:
        print("[!] No usernames extracted. Please check that the Following popup is open.")
        sys.exit(1)


if __name__ == "__main__":
    main()
