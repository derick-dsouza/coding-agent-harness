# Quick Start: Adapter Selection Guide

Choose the right task management adapter for your use case.

## Comparison Matrix

| Feature | Linear | GitHub Issues | BEADS |
|---------|--------|---------------|-------|
| **Authentication** | API Key | OAuth (gh CLI) | Token (bd CLI) |
| **Setup Complexity** | Low | Low | Medium |
| **API/CLI** | MCP/API | CLI (`gh`) | CLI (`bd`) |
| **Production Ready** | ✅ Yes | ✅ Yes | ⚠️ Template |
| **Rate Limits** | Generous | 5K/hour | Unknown |
| **Custom Fields** | Native | Labels | Unknown |
| **Project Management** | Native | Projects v2 | Native |
| **Cost** | Paid plans | Free (public) | Unknown |

## When to Use Each

### Use Linear If...
- ✅ You want **native project management** features
- ✅ Your team already uses Linear
- ✅ You need **advanced issue tracking** (relationships, cycles, etc.)
- ✅ You have a Linear subscription
- ✅ You want **fastest API performance** (MCP-based)

**Setup:**
```bash
export TASK_ADAPTER_TYPE="linear"
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"
```

**Pros:**
- Production-ready and battle-tested
- Rich feature set (cycles, estimates, etc.)
- Fast MCP-based integration
- Excellent UI/UX

**Cons:**
- Requires paid subscription
- API key management needed

---

### Use GitHub Issues If...
- ✅ You're already using **GitHub for code hosting**
- ✅ You want to **keep everything in one place** (code + issues)
- ✅ You prefer **CLI-based tools** (`gh`)
- ✅ You want **zero additional cost** (public repos)
- ✅ Your team is comfortable with GitHub

**Setup:**
```bash
# Install GitHub CLI
brew install gh  # macOS
gh auth login

# Configure adapter
export TASK_ADAPTER_TYPE="github"
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"
```

**Pros:**
- **No API key needed** (uses gh CLI)
- Free for public repositories
- Integrated with code and PRs
- Familiar to developers
- GitHub Actions integration

**Cons:**
- Simpler than dedicated project management tools
- Status/priority via labels (less native)
- Rate limits (5K/hour authenticated)

**Important Setup:** Create status and priority labels first:
```bash
gh label create "priority:urgent" --color "d73a4a" --repo OWNER/REPO
gh label create "priority:high" --color "ff9800" --repo OWNER/REPO
gh label create "priority:medium" --color "ffc107" --repo OWNER/REPO
gh label create "priority:low" --color "4caf50" --repo OWNER/REPO
gh label create "status:todo" --color "e4e669" --repo OWNER/REPO
gh label create "status:in-progress" --color "0366d6" --repo OWNER/REPO
gh label create "status:done" --color "28a745" --repo OWNER/REPO
gh label create "status:canceled" --color "6c757d" --repo OWNER/REPO
```

---

### Use BEADS If...
- ✅ Your organization uses BEADS
- ✅ You want to integrate with existing BEADS workflows
- ✅ You're willing to **customize the adapter** for your BEADS instance

**Setup:**
```bash
# Install BEADS CLI (method depends on your BEADS deployment)
# Example (adjust based on actual BEADS CLI):
npm install -g beads-cli  # or pip install beads-cli

# Authenticate
bd auth login

# Configure adapter
export TASK_ADAPTER_TYPE="beads"
export BEADS_WORKSPACE="my-workspace"  # Optional
```

**Pros:**
- Integrates with existing BEADS setup
- CLI-based (no API key management)
- Potential for custom workflows

**Cons:**
- ⚠️ **Template implementation** - requires customization
- Unknown feature set (depends on BEADS version)
- Less documentation available
- Requires BEADS CLI verification

**Important:** Before using BEADS adapter:
1. Verify BEADS CLI commands (`bd --help`)
2. Update status/priority mappings in `beads_adapter.py`
3. Test with actual BEADS instance
4. Document your customizations

---

## Quick Decision Tree

```
Do you already use Linear?
├─ Yes → Use Linear adapter
└─ No
   ├─ Is your code on GitHub?
   │  ├─ Yes → Use GitHub adapter
   │  └─ No → Continue
   └─ Do you use BEADS?
      ├─ Yes → Use BEADS adapter (customize first)
      └─ No → Choose GitHub (easiest) or Linear (most features)
```

## Migration Between Adapters

All adapters share the same interface, so switching is straightforward:

```python
# Old configuration
export TASK_ADAPTER_TYPE="linear"
export LINEAR_API_KEY="..."

# New configuration
export TASK_ADAPTER_TYPE="github"
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"

# No code changes needed!
python autonomous_agent_demo.py
```

**Data Migration:** Issues/labels are platform-specific. To migrate:
1. Export data from old platform (CSV, API)
2. Transform to new platform format
3. Import to new platform
4. Update `.task_project.json` with new project ID

## Adapter Documentation

- **Linear**: See `task_management/linear_adapter.py`
- **GitHub**: See [task_management/GITHUB_ADAPTER.md](task_management/GITHUB_ADAPTER.md)
- **BEADS**: See [task_management/BEADS_ADAPTER.md](task_management/BEADS_ADAPTER.md)
- **All Adapters**: See [task_management/README.md](task_management/README.md)

## Testing Your Adapter

```python
from task_management import create_adapter

# Create adapter
adapter = create_adapter("github", owner="test", repo="demo")

# Test connection
assert adapter.test_connection(), "Connection failed"

# Create test issue
issue = adapter.create_issue(
    title="Test Issue",
    description="Testing adapter setup"
)

print(f"✅ Successfully created issue: {issue.id}")

# Update status
adapter.update_issue(issue.id, status=IssueStatus.DONE)
print(f"✅ Successfully updated issue status")
```

## Troubleshooting

### Linear: API Key Not Working
```bash
# Verify API key
curl -H "Authorization: Bearer $LINEAR_API_KEY" https://api.linear.app/graphql

# Check environment variable
echo $LINEAR_API_KEY
```

### GitHub: CLI Not Authenticated
```bash
# Check auth status
gh auth status

# Re-authenticate
gh auth login
```

### BEADS: CLI Not Found
```bash
# Check if bd is installed
which bd
bd --version

# Install if missing (adjust based on BEADS distribution)
npm install -g beads-cli
```

## Next Steps

1. Choose your adapter based on the criteria above
2. Follow setup instructions
3. Test connection with sample code
4. Run the autonomous agent demo
5. Monitor progress in your chosen task management system

## Support

- **General Issues**: Open issue on GitHub
- **Adapter-Specific**: See adapter documentation
- **Linear**: [Linear API Docs](https://developers.linear.app/)
- **GitHub**: [GitHub CLI Docs](https://cli.github.com/manual/)
- **BEADS**: Contact BEADS support for CLI documentation
