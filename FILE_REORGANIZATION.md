# File Reorganization - Config Files Moved to Demo Project

## What Changed

All demo project-specific configuration files have been moved from the harness root to the demo project folder.

### Files Moved

From: `/Users/derickdsouza/Projects/development/coding-agent-harness/`  
To: `/Users/derickdsouza/Projects/development/coding-agent-harness/generations/autonomous_demo_project/`

| File | Purpose | Moved |
|------|---------|-------|
| `.task_project.json` | Task management project state (Linear) | ✅ |
| `.autocode-config.json` | Autocode configuration for demo project | ✅ |
| `.claude_settings.json` | Claude security settings for demo | ✅ |
| `.linear_project.json` | Legacy Linear project state | Already there |
| `app_spec.txt` | Application specification | Already there |

### Files Remaining in Root

These files are harness-wide and stay in root:

| File | Purpose | Location |
|------|---------|----------|
| `.autocode-config.example.json` | Example config template | Root |
| `autocode-defaults.json` | Default settings for harness | Root |
| `.gitignore` | Git ignore patterns | Root |
| `.venv/` | Python virtual environment | Root |

## Directory Structure Now

```
coding-agent-harness/                    # Harness root
├── .autocode-config.example.json        # Example (stays)
├── autocode-defaults.json               # Defaults (stays)
├── .gitignore                           # Git config (stays)
├── .venv/                               # Venv (stays)
├── prompts/
│   └── app_spec.txt                     # Source spec (stays)
├── work-on-project.sh                   # Wrapper script (updated)
├── autocode.py                          # Main script
├── detect_spec_changes.py               # Spec detector
└── generations/
    └── autonomous_demo_project/         # Demo project
        ├── .task_project.json           # ✅ Moved here
        ├── .autocode-config.json        # ✅ Moved here  
        ├── .claude_settings.json        # ✅ Moved here
        ├── .linear_project.json         # Was already here
        ├── app_spec.txt                 # Copy (used by demo)
        ├── server/                      # Application code
        ├── src/                         # Application code
        └── [other generated files]
```

## Why This Change?

1. **Cleaner root directory** - Harness root now only has harness files
2. **Project isolation** - Each generated project has its own config
3. **Easier management** - All project files in one place
4. **Better organization** - Clear separation between harness and projects

## Impact on Workflow

**No impact!** All commands work the same:

```bash
# Still works exactly the same
autocode
code-agent-update
./work-on-project.sh both
```

The scripts automatically look for config files in the demo folder now.

## For New Projects

When you create a new project, configs will be created in the project directory:

```bash
mkdir my-new-project
cd my-new-project
autospec                    # Copy spec here
python ../autocode.py       # Creates .task_project.json here
```

## Legacy Support

If you have `.task_project.json` in the root (old location), the script will still read it for backward compatibility.

## Updated Scripts

- ✅ `work-on-project.sh` - Checks demo folder first
- ✅ `autocode.py` - Uses --project-dir argument
- ✅ `detect_spec_changes.py` - Uses --project-dir argument

All scripts are backward compatible!

## Relative Paths Fixed

When moving config files to the demo project, relative paths were updated:

**`.task_project.json`:**
- ❌ Before: `"project_directory": "generations/autonomous_demo_project"`
- ✅ After: `"project_directory": "."`
- Reason: File is now IN the project directory

**`.autocode-config.json`:**
- ❌ Before: `"spec_file": "prompts/app_spec.txt"`
- ✅ After: `"spec_file": "app_spec.txt"`
- Reason: Spec file is in same directory as config file now

**`.claude_settings.json`:**
- ✅ `./**` patterns - Still valid (relative to current directory)

**Note:** The temporary `prompts/` subdirectory in the demo project was removed to avoid duplication. The demo project uses `app_spec.txt` in its root directory.
