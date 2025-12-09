#!/bin/bash
# Convenience script to work on the generated project
# This script should be run from the harness root directory

# Activate virtual environment
source .venv/bin/activate

# Default project directory
PROJECT_DIR="generations/autonomous_demo_project"

# Try to get project directory from .task_project.json in the demo folder
if [ -f "$PROJECT_DIR/.task_project.json" ]; then
    # Already using the right directory
    :
elif [ -f ".task_project.json" ]; then
    # Old location - read from root (legacy support)
    PROJECT_DIR=$(python3 -c "import json; print(json.load(open('.task_project.json'))['project_directory'])" 2>/dev/null || echo "generations/autonomous_demo_project")
fi

case "$1" in
  "detect")
    echo "🔍 Detecting spec changes..."
    echo "   Spec: prompts/app_spec.txt"
    echo "   Project: $PROJECT_DIR"
    echo ""
    
    # Copy spec to project directory temporarily for detector
    cp prompts/app_spec.txt "$PROJECT_DIR/app_spec.txt"
    
    # Run detector on project directory
    python detect_spec_changes.py --project-dir "$PROJECT_DIR"
    ;;
    
  "run")
    echo "🤖 Running coding agent..."
    echo "   Spec: prompts/app_spec.txt"
    echo "   Project: $PROJECT_DIR"
    echo ""
    
    # Ensure spec is in project directory
    cp prompts/app_spec.txt "$PROJECT_DIR/app_spec.txt"
    
    # Run agent on project directory
    python autocode.py --project-dir "$PROJECT_DIR"
    ;;
    
  "both")
    echo "🔍 Detecting spec changes..."
    echo "   Spec: prompts/app_spec.txt"
    echo "   Project: $PROJECT_DIR"
    echo ""
    
    # Copy spec to project directory
    cp prompts/app_spec.txt "$PROJECT_DIR/app_spec.txt"
    
    # Run detector
    python detect_spec_changes.py --project-dir "$PROJECT_DIR"
    
    echo ""
    echo "🤖 Running coding agent..."
    python autocode.py --project-dir "$PROJECT_DIR"
    ;;
    
  *)
    echo "Usage: $0 {detect|run|both}"
    echo ""
    echo "Run this script from the harness root directory."
    echo ""
    echo "  detect - Run spec change detector only"
    echo "  run    - Run coding agent only"
    echo "  both   - Run detector then agent"
    echo ""
    echo "This script:"
    echo "  - Reads spec from: prompts/app_spec.txt"
    echo "  - Copies to project directory: $PROJECT_DIR/"
    echo "  - Runs detector/agent on: $PROJECT_DIR/"
    exit 1
    ;;
esac


