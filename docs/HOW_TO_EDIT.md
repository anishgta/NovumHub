# 📘 Hackrec: Beginner's Guide on How to Edit Frontend & Settings

Welcome! If you are a first-year student with C++/Python/Git knowledge and **zero web development experience**, this guide was written especially for you.

You can modify almost everything on this website without knowing advanced Flask or JavaScript.

---

## 📖 Mini Glossary (What do these web words mean?)

Before you start editing, here are four fundamental concepts:

1. **Route (Python function in `app/*.py`):**
   - Think of a route like a `switch` statement for web URLs. When someone types `http://127.0.0.1:5000/browse`, the `@submissions_bp.route("/browse")` function in Python decides what database records to fetch and which template to show.
2. **Template (`templates/*.html`):**
   - An HTML file with special placeholders using Jinja2 syntax (e.g., `{{ config_data.SITE_NAME }}` or `{% for item in list %}`). It is like a print format string (`printf` in C or f-strings in Python) that Flask fills in before sending to the browser.
3. **Static File (`static/css/` & `static/js/`):**
   - Files that do not change based on user accounts. CSS styles your pages (colors, spacing), images provide visuals, and JavaScript handles interactions (like the upvote button).
4. **CSS Variable (`static/css/custom.css`):**
   - A variable defined in CSS starting with `--` (like `--primary-color: #1a2b49;`). Just like a `#define` or `const` in C++, changing it once at the top automatically changes that color everywhere on the entire website!

---

## 🎨 1. How to Change Colors, Fonts, & Look

All visual styling is governed by variables at the very top of:
📂 `static/css/custom.css`

### Example: Changing the Primary Color & Olive Accent

```css
/* Open static/css/custom.css and look at the first 25 lines: */
:root {
  /* EDIT HERE: Change hex colors below */
  --primary-color: #1a2b49;   /* Change this to your favorite navy or maroon */
  --accent-color: #4b5320;    /* Military olive / khaki accent for AIT */
  --card-bg: #ffffff;         /* Background color for cards */
  --radius-md: 10px;          /* Roundness of cards (increase for rounder) */
}
```

1. Open `static/css/custom.css`.
2. Change `--accent-color: #4b5320;` to another hex code (for example, `#15803d` for bright green or `#b45309` for amber).
3. Save the file.
4. Refresh your browser (`CTRL + F5` to clear browser cache). You will see the new accent color immediately!

---

## 📝 2. How to Change Site Name, Tagline, College Name, & Text

You **never** have to search through HTML templates to change text!
Everything is centralized in:
📂 `site_config.py`

### Visual Screenshot-in-Words (Navbar & Hero Header)
```
+-----------------------------------------------------------------------------------+
|  🎖️ [SITE_NAME]  [COLLEGE_SHORT_NAME]              Browse  Stats  About  + Submit |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|     [HERO_TITLE]                                                                  |
|     Share Ideas, Advance Research, Improve Campus                                 |
|                                                                                   |
|     [HERO_SUBTITLE]                                                               |
|     A transparent, student-first portal for Army Institute of Technology...      |
|                                                                                   |
|     [HERO_CTA_TEXT]  [HERO_BROWSE_TEXT]                                           |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Steps to Change:
1. Open `site_config.py`.
2. Find `SITE_NAME`, `COLLEGE_NAME`, or `HERO_TITLE`.
3. Change the string inside the quotes:
   ```python
   # Change this:
   SITE_NAME = "Hackrec"
   # To:
   SITE_NAME = "AIT Innovate"
   ```
4. Save the file. Refresh your browser page.

---

## 🏷️ 3. How to Change or Add a Category

Categories are defined in `site_config.py` under the dictionary `CATEGORIES`.

### Modifying an Existing Category:
In `site_config.py`, locate:
```python
CATEGORIES = {
    "idea": {
        "name": "Innovative Idea",
        "icon": "icons/icon-idea.svg",
        "short_desc": "New project, product, event, club, or process idea.",
        ...
    }
}
```
You can change the icon file path, the friendly name, or the description.

### Adding a 5th Category (e.g., "Sports & Fitness"):
1. In `site_config.py`, add a new entry to `CATEGORIES`:
   ```python
   "sports": {
       "name": "Sports & Fitness",
       "badge_color": "var(--cat-idea)",
       "icon": "icons/icon-trophy.svg",
       "short_desc": "Proposals for gym equipment, tournaments, and sports grounds.",
       "full_desc": "Suggest new tournaments, equipment upgrades, or fitness initiatives.",
       "guidelines": "Specify the sport, equipment needed, and estimated player participation."
   }
   ```
2. In `app/forms.py`, add `("sports", "Sports & Fitness")` to the `category` SelectField choices.
3. That's it! The homepage cards, filter dropdowns, and submission badges will now automatically recognize your new category!

---

## 🖼️ 4. How to Change or Replace SVG Icons

All emojis have been replaced with dedicated, standard SVG image files located in:
📂 `static/icons/`

### How It Works:
Every icon on the website is a standalone SVG file referenced via:
```html
<img src="{{ url_for('static', filename='icons/icon-name.svg') }}" class="site-icon" alt="">
```

### 3 Ways to Swap or Customize Icons:
1. **Drop-in Replace:** Simply save your new `.svg` file over the existing file in `static/icons/` with the same name (e.g., replace `static/icons/icon-idea.svg` with your own SVG).
2. **Add a New SVG File:** Put your new icon file into `static/icons/` (e.g., `static/icons/my-new-icon.svg`), then in `site_config.py` update `"icon": "icons/my-new-icon.svg"`.
3. **Change in HTML Templates:** Search for `icons/` in the template and change the filename.

### Complete List of Available Icons:
- `logo.svg` - Main AIT shield / star brand mark in the navbar
- `icon-idea.svg` - Lightbulb for Innovative Ideas
- `icon-research.svg` - Microscope / flask for Research Findings
- `icon-correction.svg` - Pen & document for Academic Corrections
- `icon-infrastructure.svg` - Classical building for Infrastructure Suggestions
- `icon-user.svg` - User avatar for authors & accounts
- `icon-calendar.svg` - Date picker and submission timestamps
- `icon-department.svg` - Department / academic branch
- `icon-comment.svg` - Discussion bubble for community comments
- `icon-attachment.svg` - Paperclip for uploaded PDF/image attachments
- `icon-edit.svg` - Edit pencil for updating submissions
- `icon-trash.svg` - Trash bin for withdrawing or deleting
- `icon-search.svg` - Magnifying glass for Under Review triage status
- `icon-check.svg` - Checkmark for Accepted contributions
- `icon-alert.svg` - Warning triangle for Needs Changes feedback
- `icon-cross.svg` - X mark for Rejected submissions
- `icon-clock.svg` - Clock for Submitted / pending status
- `icon-flag.svg` - Flag for moderation reports
- `icon-bell.svg` - Bell for notifications
- `icon-trophy.svg` - Trophy for Implemented status and top community upvoted contributions
- `icon-upload.svg` - Upward arrow for file uploads
- `icon-download.svg` - Downward arrow for CSV export and file downloads
- `icon-mail.svg` - Envelope for support contact email
- `icon-lock.svg` - Lock for internal triage notes
- `icon-vote.svg` - Upvote indicator for student contributions

---

## ➕ 4. How to Add a New Page to the Website

Want to create an `FAQ` or `Sponsors` page? Follow these 3 easy steps:

### Step 1: Create a Route in Python
Open `app/main.py` and add this code at the bottom:
```python
@main_bp.route("/faq")
def faq():
    """Frequently Asked Questions page."""
    return render_template("main/faq.html")
```

### Step 2: Create the Template File
Create a new file `templates/main/faq.html` with this starter code:
```html
{% extends 'base.html' %}

{% block title %}FAQ - {{ config_data.SITE_NAME }}{% endblock %}

{% block content %}
<div style="max-width: 800px; margin: 1rem auto;">
  <article style="background: var(--card-bg); padding: 2rem; border-radius: var(--radius-md);">
    <h1>Frequently Asked Questions</h1>
    
    <h3>Who can submit?</h3>
    <p>Any registered student at Army Institute of Technology!</p>

    <h3>How long does review take?</h3>
    <p>Submissions are typically triaged within 3 to 5 business days.</p>
  </article>
</div>
{% endblock %}
```

### Step 3: Add a Link in the Navigation Bar
Open `templates/partials/navbar.html`. Under `<!-- Main Navigation Links -->`, add:
```html
<li><a href="{{ url_for('main.faq') }}">FAQ</a></li>
```
Visit `http://127.0.0.1:5000/faq` in your browser!

---

## 🛠️ 5. How to Add a Field to the Submission Form

Suppose you want to add a field asking: *"Estimated Budget (in INR)"* for Innovative Ideas:

### Step 1: Add Field to Form (`app/forms.py`)
In `app/forms.py`, under `# Category 1: Innovative Idea fields`:
```python
idea_budget = StringField("Estimated Budget (INR)", validators=[Optional(), check_blocked_words])
```

### Step 2: Display Field in HTML (`templates/submissions/submit.html`)
Find `<div id="group-idea">` in `templates/submissions/submit.html` and add:
```html
<label for="idea_budget">
  Estimated Budget (INR)
  {{ form.idea_budget(placeholder="e.g. ₹5,000 for sensors and cabling") }}
</label>
```

### Step 3: Save Field in Route (`app/submissions.py`)
In `app/submissions.py` inside `submit()`:
```python
if cat == "idea":
    extra_data = {
        "expected_impact": form.idea_impact.data or "",
        "resources_needed": form.idea_resources.data or "",
        "budget": form.idea_budget.data or ""  # <-- Added here
    }
```

### Step 4: Display on Detail Page (`templates/submissions/detail.html`)
Find the `{% if submission.category == 'idea' ... %}` section in `templates/submissions/detail.html` and add:
```html
{% if extra.get('budget') %}
  <p><strong>Estimated Budget:</strong> {{ extra.get('budget') }}</p>
{% endif %}
```

---

## 🔄 6. How to Restart the Server

When you edit Python files (`run.py`, `app/*.py`, `site_config.py`), Flask automatically reloads itself if `debug=True`.

However, if you ever need to stop and restart manually:

1. In your terminal/console window, press **`CTRL + C`** to stop the server.
2. Run:
   ```powershell
   python run.py
   ```
3. Look for the message:
   ```
   * Running on http://127.0.0.1:5000
   ```
4. Refresh your browser tab.

---

## 🛡️ 7. Useful CLI Management Commands

Hackrec comes with built-in command-line tools:

- **Create Demo Data:**
  ```bash
  flask seed-demo
  ```
  *(Creates 5 users and 12 sample contributions across all categories and statuses)*

- **Promote Any User to Administrator:**
  ```bash
  flask make-admin student@aitpune.edu.in
  ```

- **Run Automated Tests:**
  ```bash
  pytest
  ```

---

## 🚀 8. How to Configure the Showcase & Judging System

The **Showcase** section is where AIT student teams upload interactive hackathon project demonstrations, presentation decks, and developer notes.

### A. Changing Showcase Name & Upload Limits (`site_config.py`)
Open `site_config.py` and scroll down to **Section 8 (Showcase Configuration)**:
```python
SHOWCASE_NAME = "Showcase"
SHOWCASE_DEMO_MAX_ZIP_MB = 50           # Max upload size of interactive builds
SHOWCASE_DEMO_MAX_UNCOMPRESSED_MB = 150 # Max extracted uncompressed size
SHOWCASE_DEMO_MAX_FILES = 500           # Max files in a zip
```
To allow 100MB zip builds instead of 50MB, simply change `SHOWCASE_DEMO_MAX_ZIP_MB = 100`!

### B. Customizing the Judging Rubric
Judges evaluate hackathon builds on a 0-10 scale across configurable criteria in `SHOWCASE_RUBRIC`:
```python
SHOWCASE_RUBRIC = {
    "innovation": {
        "label": "Innovation & Originality",
        "desc": "How novel and creative is the idea compared to existing solutions?",
        "max": 10,
        "weight": 1.0
    },
    "technical_depth": {
        "label": "Technical Depth & Complexity",
        "desc": "Demonstrated engineering skill, architecture quality, and challenge.",
        "max": 10,
        "weight": 1.0
    },
    # ...
}
```
You can edit the labels, descriptions, and weights anytime in `site_config.py` without touching any database schemas!

### C. Adding or Modifying Developer Note Sections
Student teams document their builds across 8 fixed sections in `SHOWCASE_DEVNOTE_SECTIONS`:
1. `problem`: Problem We Tackled
2. `how_it_works`: How It Works (Architecture)
3. `tech_stack`: Tech Stack & Why We Chose It
4. `run_locally`: How to Run Locally (Step-by-Step)
5. `challenges`: Challenges & How We Solved Them
6. `differently`: What We Would Do Differently
7. `time_breakdown`: Time Breakdown
8. `resources`: Useful Resources & Links

To add a new section, say `"future_scope"`:
1. Add it to `SHOWCASE_DEVNOTE_SECTIONS` in `site_config.py`:
   ```python
   "future_scope": {
       "title": "Future Scope & Production Roadmap",
       "description": "What features will be added in phase 2?"
   }
   ```
2. Add a `future_scope = TextAreaField(...)` to `DevNotesForm` in `app/showcase/forms.py`.

### D. New Showcase CLI Commands
- **Promote a user to Hackathon Judge:**
  ```bash
  flask make-judge professor@aitpune.edu.in
  ```
- **Seed sample HackAIT events, WebGL builds, decks, and scores:**
  ```bash
  flask seed-showcase
  ```
- **Run non-destructive database upgrade:**
  ```bash
  flask migrate-showcase
  ```

### E. Sandboxed Demo Security & The Kill Switch
Interactive WebGL builds and HTML5 games run inside sandboxed `<iframe>` tags:
- **Sandbox Security:** The browser prevents the demo from reading your cookies, accessing user sessions, or modifying the parent page (`sandbox allow-scripts allow-pointer-lock allow-fullscreen`).
- **Reviewer Kill Switch:** If an uploaded script causes browser freezes, memory leaks, or contains objectionable material, any Reviewer or Admin can click **`Disable Demo (Kill Switch)`** on the project page. This immediately returns an HTTP 403 response on the demo route while keeping slides, code links, and notes accessible for review.

Happy building! You now have full control over Hackrec and the Showcase arena. 🎖️
