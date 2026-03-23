# Instagram Following Comparator

Compare Instagram "Following" lists between two accounts and find mutual follows.

**No login automation. No API keys. No risk of account bans.**

## How It Works

```
You manually open Instagram → Script reads the visible "Following" popup → Saves usernames to JSON
```

The script connects to your browser via Chrome's debugging protocol. You stay in control - just open the Following popup and run the script.

## Features

- Extracts usernames from Instagram Following lists
- Finds mutual follows between two accounts
- Handles large lists (1000+ users) with auto-scrolling
- Exports to JSON and CSV
- No credentials stored or transmitted

## Requirements

- Python 3.8+
- Google Chrome
- Windows (macOS/Linux scripts coming soon)

## Quick Start

### 1. Install

```bash
git clone https://github.com/AhmedTheNetCoder/instagram-following-comparator.git
cd instagram-following-comparator
pip install -r requirements.txt
```

### 2. Start Chrome with Debugging

**Windows (PowerShell):**
```powershell
# Close ALL Chrome windows first, then:
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=C:\temp\chrome_debug"
```

**macOS/Linux:**
```bash
# Close all Chrome windows first, then:
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug
```

Or double-click `start_chrome_debug.bat` on Windows.

### 3. Extract First Account's Following List

1. In the Chrome window, go to **instagram.com** and log in
2. Navigate to the first profile
3. Click **"Following"** to open the popup
4. Run:

```bash
python scrape_following.py account1.json
```

Press Enter when the popup is visible. Wait for extraction to complete.

### 4. Extract Second Account's Following List

1. Close the popup, navigate to the second profile
2. Click **"Following"**
3. Run:

```bash
python scrape_following.py account2.json
```

### 5. Compare and Find Mutual Follows

```bash
python compare_lists.py account1.json account2.json --csv
```

**Output:**
```
MUTUAL FOLLOWS: 156
  12.5% of List 1 follows these accounts
  17.5% of List 2 follows these accounts
```

Results saved to `mutual_follows.json` and `mutual_follows.csv`.

## Command Reference

### Scraper

```bash
python scrape_following.py OUTPUT_FILE [OPTIONS]

Options:
  --port INT          Chrome debugging port (default: 9222)
  --scroll-delay SEC  Seconds between scrolls (default: 1.5, increase for safety)
  --max-scrolls INT   Maximum scrolls (default: 500)
```

### Comparator

```bash
python compare_lists.py FILE1 FILE2 [OPTIONS]

Options:
  -o, --output FILE   Output filename (default: mutual_follows.json)
  --csv               Also export to CSV
  --show-all          Print all mutual follows
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to Chrome" | Close ALL Chrome windows, restart with `--remote-debugging-port=9222` |
| "Could not find scroll container" | Make sure the Following popup is open and visible |
| Script hangs at connecting | ChromeDriver mismatch - delete old chromedriver and retry |
| Extraction stops early | Increase `--scroll-delay` to 2.0 or 3.0 |

### Verify Chrome Debugging is Working

```powershell
# PowerShell
Invoke-WebRequest http://127.0.0.1:9222/json/version

# Bash/CMD
curl http://127.0.0.1:9222/json/version
```

Should return JSON with Chrome version info.

## How It Stays Safe

| Approach | Why It's Safer |
|----------|----------------|
| No login automation | Your credentials are never handled by the script |
| Manual navigation | You control what pages are accessed |
| Slow scrolling | Mimics human behavior, avoids rate limits |
| Browser attachment | Uses your existing session, no cookie manipulation |
| Local only | No data sent to external servers |

## Output Formats

### JSON (account1.json)
```json
{
  "metadata": {
    "extracted_at": "2024-03-20T14:30:00",
    "total_count": 1247
  },
  "usernames": ["user1", "user2", "user3"]
}
```

### Comparison JSON (mutual_follows.json)
```json
{
  "statistics": {
    "mutual_count": 156,
    "mutual_pct_of_first": 12.5,
    "jaccard_similarity": 7.86
  },
  "mutual_follows": ["user1", "user2"],
  "only_in_first": ["user3"],
  "only_in_second": ["user4"]
}
```

### CSV (mutual_follows.csv)
```csv
username,profile_url
user1,https://instagram.com/user1
user2,https://instagram.com/user2
```

## License

MIT License - Use responsibly and respect Instagram's Terms of Service.

## Disclaimer

This tool is for personal/educational use. The authors are not responsible for any misuse or account restrictions. Use at your own risk.
