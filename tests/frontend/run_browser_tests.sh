#!/bin/bash

# Set up environment for real browser testing
export USE_REAL_BROWSER=true

# Install Chrome WebDriver if not already installed
if ! command -v chromedriver &> /dev/null; then
    echo "ChromeDriver not found, attempting to install..."
    python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
    if [ $? -ne 0 ]; then
        echo "Failed to install ChromeDriver automatically."
        echo "Please install ChromeDriver manually or ensure Chrome browser is installed."
        exit 1
    fi
fi

# Check if Chrome browser is available
if ! command -v google-chrome &> /dev/null && ! command -v google-chrome-stable &> /dev/null && ! [ -d "/Applications/Google Chrome.app" ]; then
    echo "Chrome browser not found. Please install Chrome browser first."
    exit 1
fi

echo "Running tests with real browser..."
pytest test_page_functionality.py -v

# Capture the exit code
TEST_EXIT_CODE=$?

# Reset environment variable
unset USE_REAL_BROWSER

exit $TEST_EXIT_CODE 