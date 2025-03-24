#!/bin/bash

# Set up environment for real browser testing
export USE_REAL_BROWSER=true

# Function to check and set up Edge
setup_edge() {
    echo "Trying to use Microsoft Edge..."
    # Install Edge WebDriver if not already installed
    if ! command -v msedgedriver &> /dev/null; then
        echo "EdgeDriver not found, attempting to install..."
        python -c "from webdriver_manager.microsoft import EdgeChromiumDriverManager; EdgeChromiumDriverManager().install()"
        if [ $? -ne 0 ]; then
            echo "Failed to install EdgeDriver automatically."
            return 1
        fi
    fi

    # Check if Edge browser is available
    if ! command -v msedge &> /dev/null && ! [ -d "/Applications/Microsoft Edge.app" ]; then
        echo "Microsoft Edge browser not found."
        return 1
    fi
    
    # Edge is available
    export BROWSER=edge
    return 0
}

# Function to check and set up Chrome
setup_chrome() {
    echo "Trying to use Chrome..."
    # Install Chrome WebDriver if not already installed
    if ! command -v chromedriver &> /dev/null; then
        echo "ChromeDriver not found, attempting to install..."
        python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
        if [ $? -ne 0 ]; then
            echo "Failed to install ChromeDriver automatically."
            return 1
        fi
    fi

    # Check if Chrome browser is available
    if ! command -v google-chrome &> /dev/null && ! command -v google-chrome-stable &> /dev/null && ! [ -d "/Applications/Google Chrome.app" ]; then
        echo "Chrome browser not found."
        return 1
    fi
    
    # Chrome is available
    export BROWSER=chrome
    return 0
}

# Function to check and set up Firefox
setup_firefox() {
    echo "Trying to use Firefox..."
    # Install Firefox WebDriver if not already installed
    if ! command -v geckodriver &> /dev/null; then
        echo "GeckoDriver not found, attempting to install..."
        python -c "from webdriver_manager.firefox import GeckoDriverManager; GeckoDriverManager().install()"
        if [ $? -ne 0 ]; then
            echo "Failed to install GeckoDriver automatically."
            return 1
        fi
    fi

    # Check if Firefox browser is available
    if ! command -v firefox &> /dev/null && ! [ -d "/Applications/Firefox.app" ]; then
        echo "Firefox browser not found."
        return 1
    fi
    
    # Firefox is available
    export BROWSER=firefox
    return 0
}

# Try Edge first, then Chrome, then Firefox
if setup_edge; then
    echo "Using Microsoft Edge for testing."
elif setup_chrome; then
    echo "Using Chrome for testing."
elif setup_firefox; then
    echo "Using Firefox for testing."
else
    echo "No supported browser (Edge, Chrome, Firefox) was found. Please install one of these browsers."
    exit 1
fi

# Run tests
echo "Running tests with real browser ($BROWSER)..."
pytest test_page_functionality.py -v

# Capture the exit code
TEST_EXIT_CODE=$?

# Reset environment variables
unset USE_REAL_BROWSER
unset BROWSER

exit $TEST_EXIT_CODE 