#!/bin/bash

# Setup Chrome for Docker container
set -e

# Check if Chrome installation was requested
if [ "${INSTALL_CHROME:-false}" != "true" ]; then
    echo "Skipping Chrome setup (INSTALL_CHROME=${INSTALL_CHROME:-false})"
    exit 0
fi

echo "Setting up Chrome environment for Docker..."

# Start Xvfb for headless display
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting Xvfb..."
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
    sleep 2
fi

# Verify Chrome installation
if command -v google-chrome &> /dev/null; then
    echo "✅ Google Chrome is installed: $(google-chrome --version)"
else
    echo "❌ Google Chrome is not installed!"
    exit 1
fi

# Set proper permissions for Chrome
chmod +x /usr/bin/google-chrome

echo "✅ Chrome setup completed successfully!"
