@echo off
SETLOCAL EnableDelayedExpansion

REM =====================================================
REM Chrome Debug Mode Launcher for Instagram Scraper
REM =====================================================

title Chrome Debug Launcher

echo =====================================================
echo Chrome Debug Mode Launcher
echo =====================================================
echo.

REM Try to find Chrome
set "CHROME_PATH="

REM Check common locations
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
    goto :found
)

if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    goto :found
)

if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    goto :found
)

REM Chrome not found
echo [ERROR] Chrome not found in standard locations.
echo.
echo Please enter your Chrome path manually, or press ENTER to exit:
echo (Example: C:\Program Files\Google\Chrome\Application\chrome.exe)
echo.
set /p CHROME_PATH="Chrome path: "

if "!CHROME_PATH!"=="" (
    echo Exiting...
    pause
    exit /b 1
)

if not exist "!CHROME_PATH!" (
    echo [ERROR] File not found: !CHROME_PATH!
    pause
    exit /b 1
)

:found
echo [OK] Found Chrome at:
echo     !CHROME_PATH!
echo.

REM Warn if Chrome might be running
echo [INFO] Checking for running Chrome processes...
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I "chrome.exe" >NUL
if %ERRORLEVEL%==0 (
    echo.
    echo [WARNING] Chrome appears to be running!
    echo For best results, close ALL Chrome windows first.
    echo.
    echo Press any key to continue anyway, or close this window to cancel...
    pause >NUL
)

echo.
echo [INFO] Starting Chrome with remote debugging on port 9222...
echo.

REM Start Chrome with debugging enabled
start "" "!CHROME_PATH!" --remote-debugging-port=9222

REM Give Chrome a moment to start
timeout /t 2 /nobreak >NUL

echo =====================================================
echo SUCCESS! Chrome should now be open.
echo =====================================================
echo.
echo NEXT STEPS:
echo   1. In the Chrome window, go to: instagram.com
echo   2. Log into your Instagram account
echo   3. Navigate to a profile and click "Following"
echo   4. Open Command Prompt in this folder
echo   5. Run: python scrape_following.py account1.json
echo.
echo -----------------------------------------------------
echo TIP: Keep this window open while scraping.
echo      You can close it after you're done.
echo -----------------------------------------------------
echo.
pause
