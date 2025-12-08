#!/bin/bash
# Linear Query Runner
# This script runs the query_linear.py script to query Linear project state

# Check if LINEAR_API_KEY is set
if [ -z "$LINEAR_API_KEY" ]; then
    echo "ERROR: LINEAR_API_KEY environment variable is not set"
    echo ""
    echo "Get your API key from: https://linear.app/YOUR-TEAM/settings/api"
    echo "Then set it:"
    echo "  export LINEAR_API_KEY='lin_api_xxxxxxxxxxxxx'"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python script
python3 "$SCRIPT_DIR/query_linear.py"
