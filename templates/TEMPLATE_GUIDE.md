# App Spec Template Guide

## Overview

This guide explains how to use the `app_spec_template.txt` for creating high-quality project specifications that work seamlessly with the autonomous coding agent.

## Template Philosophy

The template is based on deep analysis of the successful Claude.ai Clone specification. It follows these core principles:

### 1. **XML-Style Structure for Clarity**
- Hierarchical organization with semantic tags
- Easy to parse by both humans and AI
- Clear nesting shows relationships between concepts

### 2. **Comprehensive Yet Organized**
- Covers all aspects of a complete application
- Logical flow from high-level to implementation details
- Cross-referenced sections (features → schema → endpoints → UI)

### 3. **Action-Oriented Language**
- Features described with action verbs
- Tasks are atomic and testable
- No ambiguity in requirements

### 4. **Implementation-Ready**
- Explicit technology choices
- Detailed enough for autonomous implementation
- Success criteria for validation

## How to Use This Template

### Step 1: Copy the Template

Use the `autospec` alias to copy the template to your project:

```bash
# Copy to current directory
autospec

# Copy to specific directory
autospec /path/to/your/project
```

This will create `app_spec.txt` in your target directory.

### Step 2: Fill Out Each Section

Work through the template systematically:

#### A. Project Identity
```xml
<project_name>Your Actual Project Name</project_name>
<overview>
  What you're building, why it matters, and who it's for.
  Be specific and comprehensive.
</overview>
```

#### B. Technology Stack
Replace all `[e.g., ...]` placeholders with your actual choices:
```xml
<frontend>
  <framework>React with Vite</framework>  <!-- Not [e.g., React with Vite] -->
  <styling>Tailwind CSS</styling>
  ...
</frontend>
```

**Pro tip:** Be specific with versions and packages when possible.

#### C. Core Features
This is the heart of your spec. For each feature category:

1. **Name it clearly** - e.g., `user_authentication`, `data_visualization`
2. **Describe the purpose** - Brief explanation of what this group does
3. **List specific features** - One per line, action-oriented

Example:
```xml
<user_authentication>
  <name>User Authentication & Authorization</name>
  <description>Secure user login, registration, and permission management</description>
  <features>
    - Email/password registration with validation
    - JWT-based session management
    - Password reset via email
    - OAuth integration (Google, GitHub)
    - Role-based access control (admin, user, guest)
    - Two-factor authentication optional
  </features>
</user_authentication>
```

#### D. Database Schema
Map your features to data structures:

```xml
<users>
  - id INTEGER PRIMARY KEY
  - email TEXT UNIQUE NOT NULL
  - password_hash TEXT NOT NULL
  - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  - role TEXT DEFAULT 'user'
  - is_verified BOOLEAN DEFAULT FALSE
</users>
```

**Pro tip:** Include relationships between tables.

#### E. API Endpoints
Document all endpoints your app needs:

```xml
<authentication>
  <name>Authentication Endpoints</name>
  <endpoints>
    - POST /api/auth/register - Create new user account
    - POST /api/auth/login - Authenticate user and return JWT
    - POST /api/auth/logout - Invalidate user session
    - POST /api/auth/reset-password - Request password reset
    - GET /api/auth/verify/:token - Verify email address
  </endpoints>
</authentication>
```

#### F. UI Layout
Describe your interface structure:

```xml
<main_structure>
  - Single-page application with React Router
  - Top navigation bar with logo and user menu
  - Sidebar for main navigation (collapsible on mobile)
  - Main content area with page-specific components
  - Footer with links and copyright
  - Responsive: mobile-first, breakpoints at 768px and 1024px
</main_structure>
```

#### G. Design System
Define your visual language:

```xml
<color_palette>
  - Primary: #3B82F6 (blue-500) - Primary actions, links
  - Secondary: #6B7280 (gray-500) - Secondary elements
  - Accent: #F59E0B (amber-500) - Highlights, notifications
  - Background: #FFFFFF (light) / #1F2937 (dark)
  - Text: #111827 (light) / #F9FAFB (dark)
  - Error: #EF4444 (red-500)
  - Success: #10B981 (green-500)
</color_palette>
```

#### H. Implementation Steps
Break down the work into sequential phases:

```xml
<step number="1">
  <title>Project Setup and Backend Foundation</title>
  <tasks>
    - Initialize Express.js server with TypeScript
    - Configure PostgreSQL database connection
    - Set up environment variables and configuration
    - Create database migration system
    - Implement logging and error handling middleware
    - Set up JWT authentication middleware
  </tasks>
</step>
```

**Pro tip:** Order steps by dependency - foundational first, polish last.

#### I. Success Criteria
Define what "done" looks like across four dimensions:

1. **Functionality** - Does it work?
2. **User Experience** - Is it pleasant to use?
3. **Technical Quality** - Is the code maintainable?
4. **Design Polish** - Does it look professional?

### Step 3: Review and Refine

Before running the coding agent:

1. **Check completeness** - Did you fill in all `[placeholders]`?
2. **Verify consistency** - Do features, schema, and endpoints align?
3. **Test readability** - Can someone understand what you want built?
4. **Validate technical choices** - Are your technology selections compatible?

## Patterns and Best Practices

### Feature Definition Pattern

✅ **Good:**
```
- User can upload profile photo with drag-and-drop or file picker
- System validates image format (PNG, JPG, max 5MB)
- Uploaded image is automatically resized and optimized
- User receives confirmation when upload completes
```

❌ **Bad:**
```
- Photo upload
- Image handling
- Various formats supported
```

### Database Schema Pattern

✅ **Good:**
```xml
<blog_posts>
  - id UUID PRIMARY KEY
  - author_id UUID REFERENCES users(id) ON DELETE CASCADE
  - title VARCHAR(200) NOT NULL
  - slug VARCHAR(220) UNIQUE NOT NULL
  - content TEXT
  - published_at TIMESTAMP
  - created_at TIMESTAMP DEFAULT NOW()
  - updated_at TIMESTAMP DEFAULT NOW()
  - is_draft BOOLEAN DEFAULT TRUE
</blog_posts>
```

❌ **Bad:**
```xml
<posts>
  - id
  - title
  - content
</posts>
```

### API Endpoint Pattern

✅ **Good:**
```
- GET /api/posts - List all published posts with pagination
- GET /api/posts/:id - Get single post by ID (404 if not found)
- POST /api/posts - Create new post (requires authentication)
- PUT /api/posts/:id - Update post (requires ownership)
- DELETE /api/posts/:id - Delete post (requires ownership)
- POST /api/posts/:id/publish - Publish draft post
```

❌ **Bad:**
```
- /api/posts endpoints
- CRUD operations for posts
```

### Implementation Task Pattern

✅ **Good:**
```
- Create User model with bcrypt password hashing
- Implement POST /api/auth/register endpoint with validation
- Add email uniqueness check before registration
- Generate JWT token on successful registration
- Send welcome email with verification link
```

❌ **Bad:**
```
- Set up user stuff
- Make authentication work
- Add email
```

## Common Sections to Consider

When filling out the template, consider including:

### For Web Applications
- Responsive design requirements
- Accessibility standards (WCAG 2.1)
- Browser compatibility targets
- Performance budgets

### For Data-Heavy Applications
- Data validation rules
- Import/export functionality
- Reporting requirements
- Search and filtering capabilities

### For Collaborative Applications
- Real-time updates mechanism
- Permissions and sharing model
- Notification system
- Activity logging

### For Content Management
- Rich text editing capabilities
- Media upload and management
- Content versioning
- Draft/publish workflow

## Template Customization

The template is comprehensive but flexible. You can:

### Add Custom Sections
```xml
<integrations>
  <stripe>
    - Payment processing for subscriptions
    - Webhook handling for payment events
    - Customer portal for subscription management
  </stripe>
  
  <sendgrid>
    - Transactional email delivery
    - Email templates for notifications
    - Bounce and complaint handling
  </sendgrid>
</integrations>
```

### Remove Irrelevant Sections
If your app doesn't have a complex design system, simplify:
```xml
<design_system>
  <colors>Bootstrap 5 default theme</colors>
  <components>Standard Bootstrap components</components>
</design_system>
```

### Adjust Detail Level
For prototypes, less detail is fine:
```xml
<core_features>
  <mvp>
    - User registration and login
    - Create and view posts
    - Basic commenting system
  </mvp>
</core_features>
```

For production apps, be exhaustive.

## Integration with Coding Agent

The autonomous coding agent uses your spec to:

1. **Generate issues** in your task management system (Linear/BEADS/GitHub)
2. **Implement features** systematically based on implementation steps
3. **Validate work** against success criteria
4. **Make decisions** when ambiguities arise

### Tips for Agent-Friendly Specs

1. **Be explicit about ports**: `<port>Only launch on port 3000</port>`
2. **Specify exact package names**: Not "a markdown renderer" but "React Markdown"
3. **Define environment variables**: List all required env vars with examples
4. **Include error handling**: Specify what should happen when things fail
5. **Describe data validation**: What makes data valid/invalid?

## Examples of Well-Specified Features

### Example 1: Search Functionality
```xml
<search_and_filtering>
  <name>Advanced Search</name>
  <description>Full-text search across posts with filters</description>
  <features>
    - Search input with debounced API calls (300ms)
    - Search across post titles and content
    - Filter by author, date range, tags
    - Sort results by relevance, date, or popularity
    - Display result count and search term highlighting
    - "No results" state with suggestions
    - Recent searches history (last 5)
    - Search results pagination (20 per page)
  </features>
</search_and_filtering>
```

### Example 2: Authentication Flow
```xml
<key_interactions>
  <user_registration>
    <name>New User Registration Flow</name>
    <steps>
      1. User clicks "Sign Up" button in header
      2. Registration modal appears with form fields (email, password, confirm password)
      3. Client-side validation runs on each field blur
      4. User submits form
      5. Loading spinner shows on submit button
      6. Server validates email uniqueness and password strength
      7. On success: Account created, verification email sent, user redirected to "Check your email" page
      8. On error: Inline error messages shown, form remains populated
      9. User checks email and clicks verification link
      10. User redirected to app with "Email verified" success message
      11. User can now log in
    </steps>
  </user_registration>
</key_interactions>
```

## Troubleshooting

### "My spec is too vague"
**Solution:** For each feature, ask:
- What exactly does the user see/do?
- What data is involved?
- What happens on success/failure?
- Are there edge cases to handle?

### "My spec is too detailed"
**Solution:** Focus on the "what" not the "how". Let the agent decide:
- ❌ "Use useState hook with useCallback for optimization"
- ✅ "Search input with debounced API calls"

### "Features don't match database schema"
**Solution:** After writing features, explicitly map each feature to:
- Database tables it needs
- API endpoints it uses
- UI components involved

This ensures alignment.

## Quick Start Checklist

- [ ] Copy template to project directory (`autospec`)
- [ ] Fill in project name and overview
- [ ] Choose and document technology stack
- [ ] List all feature categories with specific features
- [ ] Design database schema matching features
- [ ] Document all API endpoints needed
- [ ] Describe UI layout and components
- [ ] Define design system (or reference existing one)
- [ ] Map out key user interaction flows
- [ ] Break work into implementation steps
- [ ] Define success criteria
- [ ] Review for completeness and consistency
- [ ] Run autocode to start implementation!

## Next Steps

Once your spec is complete:

1. Run `autocode` in your project directory
2. The agent will parse your spec and create issues
3. Implementation begins automatically
4. Monitor progress in your task management system
5. Add new features by updating the spec and re-running

---

**Remember:** A great spec is:
- **Clear** - No ambiguity
- **Complete** - All aspects covered
- **Consistent** - Parts align with each other
- **Actionable** - Agent knows what to build

Happy specifying! 🚀
