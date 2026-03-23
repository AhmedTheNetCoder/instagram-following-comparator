#!/bin/bash
# Chrome Debug Mode Launcher for macOS/Linux

echo "=============================================="
echo "Chrome Debug Mode Launcher"
echo "=============================================="
echo

# Kill existing Chrome processes
echo "[*] Closing any existing Chrome instances..."
pkill -f "Google Chrome" 2>/dev/null || pkill chrome 2>/dev/null || true

sleep 1

# Find Chrome
CHROME_PATH=""

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
    # Linux
    for path in /usr/bin/google-chrome /usr/bin/chromium /usr/bin/chromium-browser; do
        if [[ -x "$path" ]]; then
            CHROME_PATH="$path"
            break
        fi
    done
fi

if [[ -z "$CHROME_PATH" || ! -x "$CHROME_PATH" ]]; then
    echo "[ERROR] Chrome not found. Please install Google Chrome."
    exit 1
fi

echo "[OK] Found Chrome at: $CHROME_PATH"
echo
echo "[*] Starting Chrome with remote debugging on port 9222..."

# Start Chrome with debugging
"$CHROME_PATH" --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug &

sleep 2

echo
echo "=============================================="
echo "SUCCESS! Chrome should now be open."
echo "=============================================="
echo
echo "NEXT STEPS:"
echo "  1. Go to instagram.com and log in"
echo "  2. Navigate to a profile and click 'Following'"
echo "  3. Run: python scrape_following.py account1.json"
echo
