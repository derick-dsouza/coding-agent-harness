# Specification File Formats

The autonomous coding agent can read specifications in **any text-based format**. The system uses simple string replacement, so the file extension doesn't matter - what matters is that the content is readable by the AI models.

## Supported Formats

### ✅ Recommended Formats

1. **Markdown (.md)** - Best for structured specifications
2. **YAML (.yaml, .yml)** - Great for hierarchical requirements
3. **Plain Text (.txt)** - Simple and universal
4. **reStructuredText (.rst)** - Common in Python projects
5. **AsciiDoc (.adoc)** - Advanced documentation format

### ✅ Also Supported

Any text-based format that can be read as plain text:
- `.json` (though not ideal for long-form specs)
- `.org` (Emacs org-mode)
- `.textile`
- Custom extensions (`.spec`, `.requirements`, etc.)

## Format Examples

### Example 1: Markdown Specification

```markdown
# E-Commerce Platform Specification

## Project Overview
Build a modern e-commerce platform with product management, shopping cart, and checkout.

## Tech Stack
- **Frontend:** React 18 + TypeScript + Tailwind CSS
- **Backend:** Node.js + Express + PostgreSQL
- **Payments:** Stripe integration

## Core Features

### 1. Product Management
- Browse products with search and filters
- Product detail pages with images
- Category navigation
- Inventory tracking

### 2. Shopping Cart
- Add/remove items
- Update quantities
- Save cart for later
- Cart persistence across sessions

### 3. User Authentication
- Sign up / Sign in
- Email verification
- Password reset
- OAuth (Google, GitHub)

### 4. Checkout
- Multi-step checkout flow
- Address management
- Payment processing (Stripe)
- Order confirmation emails

## Database Schema

### Products Table
- id (primary key)
- name (string)
- description (text)
- price (decimal)
- stock_quantity (integer)
- category_id (foreign key)
- created_at (timestamp)

### Orders Table
- id (primary key)
- user_id (foreign key)
- total_amount (decimal)
- status (enum: pending, processing, shipped, delivered)
- created_at (timestamp)

## UI/UX Requirements
- Mobile-first responsive design
- Accessibility (WCAG 2.1 AA)
- Dark mode support
- Loading states for async operations
```

**Usage:**
```bash
python autocode.py --spec-file SPEC.md
```

---

### Example 2: YAML Specification

```yaml
project:
  name: "Task Management API"
  type: "REST API"
  description: "A comprehensive task management system with teams and projects"

tech_stack:
  language: "Python 3.11"
  framework: "FastAPI"
  database: "PostgreSQL 15"
  orm: "SQLAlchemy 2.0"
  auth: "JWT tokens"
  testing: "pytest"

features:
  - name: "User Management"
    priority: 1
    endpoints:
      - method: POST
        path: /api/auth/register
        description: "Register new user"
        auth: false
      - method: POST
        path: /api/auth/login
        description: "Login user, return JWT"
        auth: false
      - method: GET
        path: /api/users/me
        description: "Get current user profile"
        auth: true

  - name: "Task Management"
    priority: 1
    endpoints:
      - method: GET
        path: /api/tasks
        description: "List all tasks (with filters)"
        auth: true
        query_params:
          - status: "pending|in_progress|done"
          - priority: "low|medium|high"
          - assigned_to: "user_id"
      - method: POST
        path: /api/tasks
        description: "Create new task"
        auth: true
      - method: PATCH
        path: /api/tasks/{id}
        description: "Update task"
        auth: true
      - method: DELETE
        path: /api/tasks/{id}
        description: "Delete task"
        auth: true

  - name: "Team Collaboration"
    priority: 2
    endpoints:
      - method: POST
        path: /api/teams
        description: "Create team"
        auth: true
      - method: POST
        path: /api/teams/{id}/members
        description: "Add team member"
        auth: true

database_schema:
  users:
    - id: integer, primary_key
    - email: string, unique
    - password_hash: string
    - name: string
    - created_at: timestamp

  tasks:
    - id: integer, primary_key
    - title: string
    - description: text
    - status: enum(pending, in_progress, done)
    - priority: enum(low, medium, high)
    - assigned_to: integer, foreign_key(users.id)
    - created_by: integer, foreign_key(users.id)
    - due_date: date, nullable
    - created_at: timestamp

  teams:
    - id: integer, primary_key
    - name: string
    - created_by: integer, foreign_key(users.id)
    - created_at: timestamp

testing_requirements:
  - Unit tests for all endpoints (95% coverage)
  - Integration tests for workflows
  - Authentication/authorization tests
  - Database transaction tests

deployment:
  - Docker containerization
  - Environment variables for config
  - Health check endpoint: /api/health
  - Logging with structured JSON
```

**Usage:**
```bash
python autocode.py --spec-file requirements.yaml
```

---

### Example 3: Plain Text Specification

```
PROJECT: Personal Finance Tracker
================================

OVERVIEW:
A web application to track income, expenses, and budgets.
Users can categorize transactions, set monthly budgets, and view spending reports.

TECH STACK:
- Frontend: Vue.js 3 + Vuetify 3
- Backend: Django 4.2 + Django REST Framework
- Database: PostgreSQL
- Charts: Chart.js

FEATURES:

1. TRANSACTION MANAGEMENT
   - Add income/expense transactions
   - Fields: date, amount, category, description, payment method
   - Edit and delete transactions
   - Bulk import from CSV
   - Search and filter transactions

2. CATEGORIES
   - Predefined categories (Food, Transport, Utilities, etc.)
   - Custom user-defined categories
   - Category icons and colors
   - Subcategories support

3. BUDGETS
   - Set monthly budget per category
   - Visual progress bars (spent vs budget)
   - Notifications when approaching budget limit
   - Budget vs actual comparison charts

4. REPORTS
   - Monthly spending summary (pie chart)
   - Spending trends over time (line chart)
   - Category breakdown (bar chart)
   - Export reports as PDF

5. USER AUTHENTICATION
   - Email/password registration
   - Email verification
   - Password reset
   - Session management

DATABASE SCHEMA:

Users:
  - id, email, password, name, created_at

Transactions:
  - id, user_id, type (income/expense), amount, category_id, 
    description, date, payment_method, created_at

Categories:
  - id, user_id, name, type, color, icon, parent_category_id

Budgets:
  - id, user_id, category_id, month, year, amount

UI REQUIREMENTS:
- Mobile responsive
- Dashboard with key metrics (total income, expenses, balance)
- Calendar view for transactions
- Dark/light theme toggle
- Smooth animations
```

**Usage:**
```bash
python autocode.py --spec-file PROJECT_SPEC.txt
```

---

### Example 4: JSON Specification (Less Common)

```json
{
  "project": {
    "name": "Weather Dashboard",
    "type": "Web Application",
    "description": "Real-time weather dashboard with forecasts and alerts"
  },
  "tech_stack": {
    "frontend": "React + TypeScript",
    "backend": "Node.js + Express",
    "api": "OpenWeather API",
    "database": "MongoDB"
  },
  "features": [
    {
      "name": "Current Weather",
      "description": "Display current weather for user's location",
      "details": [
        "Temperature, humidity, wind speed",
        "Weather icon and description",
        "Sunrise/sunset times",
        "UV index"
      ]
    },
    {
      "name": "7-Day Forecast",
      "description": "Show week-ahead weather forecast",
      "details": [
        "Daily high/low temperatures",
        "Precipitation probability",
        "Weather icons",
        "Hourly breakdown"
      ]
    },
    {
      "name": "Multiple Locations",
      "description": "Track weather for multiple cities",
      "details": [
        "Add/remove locations",
        "Set default location",
        "Quick location switching",
        "Search cities by name"
      ]
    }
  ]
}
```

**Usage:**
```bash
python autocode.py --spec-file app_spec.json
```

---

## Best Practices

### 1. **Be Detailed and Specific**

✅ Good:
```markdown
### User Registration
- Form fields: email (required, validated), password (min 8 chars, 1 uppercase, 1 number), confirm password
- Email verification: Send confirmation email with unique token
- Password hashing: Use bcrypt with cost factor 12
- Error messages: Display inline validation errors
```

❌ Too Vague:
```
User registration with email and password
```

### 2. **Include Tech Stack and Database Schema**

The initializer agent needs to know:
- Programming language and framework
- Database type and ORM
- Frontend framework (if applicable)
- Key libraries and dependencies

### 3. **Specify 40-60 Distinct Features**

The initializer creates ~50 Linear issues. Make sure your spec has enough features to fill those issues:
- 5-10 core features (authentication, main functionality)
- 15-25 secondary features (UI components, additional pages)
- 10-15 polish features (styling, error handling, edge cases)
- 10-15 testing and deployment features

### 4. **Provide UI/UX Guidance**

Include:
- Responsive design requirements
- Accessibility standards
- Color scheme / theme
- Layout descriptions
- User flow diagrams (in text)

### 5. **Test Steps for Features**

Where possible, include how to verify each feature:
```markdown
### Shopping Cart Feature

**Test Steps:**
1. Navigate to product listing page
2. Click "Add to Cart" on product
3. Cart icon shows item count (1)
4. Click cart icon
5. See product in cart with quantity, price
6. Click "Remove" button
7. Cart becomes empty
```

This helps both the coding agent (knows what to test) and audit agent (knows what to verify).

---

## Configuration

### In .autocode-config.json

```json
{
  "spec_file": "SPEC.md",
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101"
}
```

### Via CLI

```bash
python autocode.py --spec-file requirements.yaml
```

### Default Behavior

If no spec file is specified:
1. Checks `.autocode-config.json` for `spec_file` key
2. Falls back to `app_spec.txt` (default)

---

## Format Recommendation

**For most projects: Use Markdown (.md)**

Why:
- ✅ Human-readable and AI-friendly
- ✅ Supports headings, lists, code blocks
- ✅ GitHub/GitLab render it beautifully
- ✅ Easy to version control and review
- ✅ Can include diagrams (mermaid)
- ✅ Widely understood format

**For API projects: Consider YAML (.yaml)**

Why:
- ✅ Structured endpoint definitions
- ✅ Easy to parse hierarchies
- ✅ Compact for large API specs
- ✅ Similar to OpenAPI/Swagger

**For simple projects: Plain text (.txt) works fine**

---

## How It Works Internally

The system uses simple string replacement in prompts:

```python
# In prompts.py
def load_prompt(name: str, spec_file: Path | None = None) -> str:
    prompt = load_template(name)
    if spec_file:
        # Replace all occurrences of "app_spec.txt" with your file
        prompt = prompt.replace("app_spec.txt", str(spec_file))
    return prompt
```

So when agents see:
```markdown
Read `app_spec.txt` in your working directory
```

It becomes:
```markdown
Read `requirements.yaml` in your working directory
```

The agent then uses standard file reading (which works for all text formats).

---

## Summary

✅ **Any text-based format works** (.md, .yaml, .txt, .json, .rst, .adoc, etc.)  
✅ **Recommended: Markdown** (best balance of structure and readability)  
✅ **Specify via:** `--spec-file` CLI arg or `spec_file` in config  
✅ **Default:** `app_spec.txt` if nothing specified  

**The format doesn't matter - what matters is clear, detailed specifications!**
