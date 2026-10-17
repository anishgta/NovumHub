"""
site_config.py
================================================================================
WELCOME TO HACKREC CONFIGURATION!
This file holds all the editable text, settings, and options for the Hackrec portal.
You DO NOT need to know Python or Flask to change anything here.
Simply edit the text between the quotes, save this file, and refresh your browser.
================================================================================
"""

# ==========================================
# 1. BASIC SITE IDENTITY & BRANDING
# ==========================================

# The main name shown in the navigation bar and page titles
SITE_NAME = "NovumHub"

# The short one-line motto shown under the title and in search previews
SITE_TAGLINE = "Empowering Student Voices & Research at AIT"

# The official name of your institution
COLLEGE_NAME = "Army Institute of Technology (AIT), Pune"

# The short name or acronym used in badges and breadcrumbs
COLLEGE_SHORT_NAME = "AIT Pune"

# Accent colour (hex code) - Violet & Electric Blue accent
ACCENT_COLOR = "#8B5CF6"

# Primary dark navy colour (hex code) for cosmic branding
PRIMARY_COLOR = "#090B2A"

# Contact email shown in the footer and help pages
CONTACT_EMAIL = "novumhub-support@aitpune.edu.in"


# ==========================================
# 2. HERO SECTION TEXT (HOMEPAGE)
# ==========================================

# Big bold title on the home page hero banner
HERO_TITLE = "Empower Campus Innovation"

# Paragraph text under the hero title explaining what Hackrec is
HERO_SUBTITLE = (
    "A transparent, student-first portal for Army Institute of Technology. "
    "Propose innovative ideas, publish research findings, report academic corrections, "
    "or suggest campus infrastructure upgrades. Every voice is heard, triaged, and tracked."
)

# Text on the main call-to-action button
HERO_CTA_TEXT = "Submit a Contribution"

# Text on the secondary button to explore submitted items
HERO_BROWSE_TEXT = "Explore All Contributions"


# ==========================================
# 3. FOOTER & COPYRIGHT
# ==========================================

# Text displayed at the bottom of every page
FOOTER_TEXT = "Developed for Army Institute of Technology students, faculty, and innovators."

# Copyright notice in footer
FOOTER_COPYRIGHT = "© 2026 Army Institute of Technology. Built with pride by AIT students."


# ==========================================
# 4. SUBMISSION CATEGORIES
# ==========================================
# Each category has a key (used internally), a friendly name, an icon, and a description.
# You can update names and descriptions here!

CATEGORIES = {
    "idea": {
        "name": "Innovative Idea",
        "badge_color": "var(--cat-idea)",
        "icon": "icons/icon-idea.svg",
        "icon_svg": "icons/icon-idea.svg",
        "short_desc": "New project, product, event, club, or process idea.",
        "full_desc": (
            "Got an idea for a new hackathon, tech club initiative, robotics build, or software project? "
            "Share your vision, expected impact on the campus community, and what resources you need."
        ),
        "guidelines": "Be specific about what problem your idea solves and what tools/budget it would require."
    },
    "research": {
        "name": "Research Finding",
        "badge_color": "var(--cat-research)",
        "icon": "icons/icon-research.svg",
        "icon_svg": "icons/icon-research.svg",
        "short_desc": "Student experiments, papers, or literature insights.",
        "full_desc": (
            "Have you completed a lab experiment, written a paper draft, or discovered an interesting "
            "algorithmic optimization? Share your methodology, key results, and optionally attach a PDF."
        ),
        "guidelines": "Include your methodology and cite any papers or datasets used. Attach a PDF if available."
    },
    "correction": {
        "name": "Research Correction",
        "badge_color": "var(--cat-correction)",
        "icon": "icons/icon-correction.svg",
        "icon_svg": "icons/icon-correction.svg",
        "short_desc": "Corrections to college research, syllabus, or lab manuals.",
        "full_desc": (
            "Found an error or outdated item in college-published research, syllabus notices, "
            "lab manuals, or the college website? Help maintain academic integrity by submitting verifiable corrections."
        ),
        "guidelines": "You MUST provide the exact item being corrected, what is wrong, what is correct, and verifiable evidence/source."
    },
    "infrastructure": {
        "name": "Infrastructure Suggestion",
        "badge_color": "var(--cat-infrastructure)",
        "icon": "icons/icon-infrastructure.svg",
        "icon_svg": "icons/icon-infrastructure.svg",
        "short_desc": "Proposals for labs, WiFi, library, hostels, or safety.",
        "full_desc": (
            "Spot a problem with hostel WiFi, lab equipment, library seating, canteen cleanliness, "
            "or campus accessibility? Propose actionable improvements with location details."
        ),
        "guidelines": "State the exact building/location, current issue, proposed remedy, and priority level."
    }
}


# ==========================================
# 5. SUBMISSION STATUSES & WORKFLOW
# ==========================================
# The stages a submission passes through from creation to completion.

STATUSES = {
    "Submitted": {
        "label": "Submitted",
        "color": "var(--status-submitted)",
        "description": "Your contribution is submitted and awaiting review by the faculty/admin triage team."
    },
    "Under Review": {
        "label": "Under Review",
        "color": "var(--status-review)",
        "description": "A reviewer is currently evaluating the submission and checking feasibility."
    },
    "Accepted": {
        "label": "Accepted",
        "color": "var(--status-accepted)",
        "description": "The submission has been accepted and is now visible on the public feed for community voting!"
    },
    "Needs Changes": {
        "label": "Needs Changes",
        "color": "var(--status-changes)",
        "description": "The reviewer requested further clarification or additional evidence. Submitter can edit."
    },
    "Rejected": {
        "label": "Rejected",
        "color": "var(--status-rejected)",
        "description": "The submission was reviewed but could not be accepted at this time. Feedback is provided."
    },
    "Implemented": {
        "label": "Implemented",
        "color": "var(--status-implemented)",
        "description": "Success! The idea, correction, or campus improvement has been officially implemented."
    }
}

# The statuses that are publicly visible to all visitors (approved / successful)
PUBLIC_STATUSES = ["Accepted", "Implemented"]


# ==========================================
# 6. ACADEMIC DEPARTMENTS & YEARS (AIT)
# ==========================================

DEPARTMENTS = [
    "Computer Engineering",
    "Information Technology",
    "Electronics & Telecommunication Engineering",
    "Mechanical Engineering",
    "Automation & Robotics Engineering"
]

ACADEMIC_YEARS = [
    "First Year (FE)",
    "Second Year (SE)",
    "Third Year (TE)",
    "Final Year (BE)",
    "Faculty / Staff",
    "Alumni"
]

PRIORITY_LEVELS = [
    "Low",
    "Medium",
    "High"
]


# ==========================================
# 7. SECURITY & ACCESS CONTROL SETTINGS
# ==========================================

# Allowed email domain for registrations (e.g., 'aitpune.edu.in').
# Only accounts with this provider can register.
ALLOWED_EMAIL_DOMAIN = "aitpune.edu.in"

# ------------------------------------------------------------------------------
# Real Email (SMTP) Dispatch Settings
# ------------------------------------------------------------------------------
# To send actual verification OTPs to user inboxes, supply your institutional or
# personal SMTP credentials below (e.g. Gmail App Password, Office 365, SendGrid).
# If left blank, NovumHub runs in development mode and displays the code on screen.
SMTP_SERVER = ""              # e.g., "smtp.gmail.com" or "smtp.office365.com"
SMTP_PORT = 587               # Standard TLS port (587) or SSL (465)
SMTP_USERNAME = ""           # e.g., "novumhub@aitpune.edu.in" or your sending email
SMTP_PASSWORD = ""           # Application-specific password or token
SMTP_FROM_EMAIL = ""         # e.g., "novumhub-noreply@aitpune.edu.in"
SMTP_USE_TLS = True

# Maximum upload file size in megabytes (MB)
MAX_UPLOAD_SIZE_MB = 10

# Allowed file extensions for attachments (must include dot)
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

# Rate limit: Maximum submissions a student can make within 1 hour
MAX_SUBMISSIONS_PER_HOUR = 10

# Maximum login attempts before temporary cooldown (in minutes)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_COOLDOWN_MINUTES = 10

# Basic spam and profanity filter word list (lowercase). Submissions containing these will be blocked.
BLOCKED_WORDS = [
    "spam", "scam", "viagra", "casino", "free-money", "hack-test-profane"
]

# Items per page for paginated lists
ITEMS_PER_PAGE = 10


# ==========================================
# 8. HACKATHON SHOWCASE CONFIGURATION
# ==========================================

# Display branding for the Showcase section
SHOWCASE_NAME = "Showcase"
SHOWCASE_NAV_LABEL = "Showcase"
SHOWCASE_TAGLINE = "Interactive Hackathon Project Demonstrations & Reference Library"

# Allowed external host domains for embedded demos (must match domain suffix)
SHOWCASE_ALLOWED_EMBED_HOSTS = [
    "youtube.com",
    "youtu.be",
    "drive.google.com",
    "github.io",
    "itch.io",
    "huggingface.co",
    "streamlit.app"
]

# Interactive Demo Zip Upload Limits
SHOWCASE_DEMO_MAX_ZIP_MB = 50           # Max upload size of the zip bundle
SHOWCASE_MAX_ZIP_MB = 50                # Alias for ease of access
SHOWCASE_DEMO_MAX_UNCOMPRESSED_MB = 150 # Max extracted uncompressed size
SHOWCASE_MAX_UNCOMPRESSED_MB = 150      # Alias
SHOWCASE_DEMO_MAX_FILES = 500           # Max number of files allowed in zip bundle
SHOWCASE_MAX_FILES = 500                # Alias

# Allowed file extensions inside an interactive demo zip bundle
SHOWCASE_DEMO_ALLOWED_EXTENSIONS = {
    "html", "htm", "js", "css", "wasm", "json", "png", "jpg", "jpeg",
    "webp", "svg", "gif", "mp3", "ogg", "wav", "ttf", "woff", "woff2",
    "data", "txt", "mem", "unityweb", "br", "gz"
}

# Allowed file extensions for project documents & presentation decks
SHOWCASE_DOCS_ALLOWED_EXTENSIONS = {
    "pdf", "png", "jpg", "jpeg", "webp", "pptx", "ppt", "key",
    "zip", "tar", "gz", "csv", "txt", "ipynb", "apk", "exe"
}

# Maximum file size for individual uploaded documents/videos (in MB)
SHOWCASE_MAX_FILE_MB = 30

# Maximum aggregate storage per project across all assets (in MB)
SHOWCASE_PROJECT_STORAGE_LIMIT_MB = 250

# Showcase Project Status Workflow
SHOWCASE_STATUSES = {
    "Draft": {"label": "Draft", "color": "#64748B"},
    "Submitted": {"label": "Submitted", "color": "#4D7CFF"},
    "Under Review": {"label": "Under Review", "color": "#8B5CF6"},
    "Published": {"label": "Published", "color": "#10B981"},
    "Needs Changes": {"label": "Needs Changes", "color": "#F59E0B"},
    "Archived": {"label": "Archived", "color": "#94A3B8"}
}

# Publicly visible showcase statuses (supports both TitleCase and lowercase)
SHOWCASE_PUBLIC_STATUSES = ["Published", "published"]

# Fixed Developer Note Sections (ordered)
SHOWCASE_DEVNOTE_SECTIONS = {
    "problem": "Problem We Tackled",
    "how_it_works": "How It Works (Architecture)",
    "tech_stack": "Tech Stack & Why We Chose It",
    "run_locally": "How to Run Locally (Step-by-Step)",
    "challenges": "Challenges & How We Solved Them",
    "differently": "What We Would Do Differently",
    "time_breakdown": "Time Breakdown",
    "resources": "Useful Resources & Links"
}

SHOWCASE_DEV_NOTE_SECTIONS = {
    "problem": {
        "title": "Problem We Tackled",
        "description": "What problem does this project solve, and why does it matter?"
    },
    "how_it_works": {
        "title": "How It Works (Architecture)",
        "description": "High-level architecture, key components, and data flow."
    },
    "tech_stack": {
        "title": "Tech Stack & Why We Chose It",
        "description": "Languages, frameworks, libraries, APIs, and the rationale behind each choice."
    },
    "run_locally": {
        "title": "How to Run Locally (Step-by-Step)",
        "description": "Clear copy-paste instructions to clone, configure, and execute the project."
    },
    "challenges": {
        "title": "Challenges & How We Solved Them",
        "description": "Technical roadblocks, bugs, teamwork hurdles, and how they were overcome."
    },
    "differently": {
        "title": "What We Would Do Differently",
        "description": "Retrospective takeaways, architectural regrets, and future improvements."
    },
    "time_breakdown": {
        "title": "Time Breakdown",
        "description": "Rough schedule of what was built during each phase or hour of the hackathon."
    },
    "resources": {
        "title": "Useful Resources & Links",
        "description": "Helpful tutorials, documentation, datasets, and GitHub references."
    }
}

# Configurable Hackathon Evaluation Rubric (Default: 6 criteria, 0 to 10 scale)
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
    "completeness": {
        "label": "Completeness & Functionality",
        "desc": "Does the demo work as claimed without critical crashes?",
        "max": 10,
        "weight": 1.0
    },
    "design_ux": {
        "label": "Design & User Experience",
        "desc": "Visual polish, user interface clarity, and intuitive interaction.",
        "max": 10,
        "weight": 1.0
    },
    "presentation": {
        "label": "Presentation & Documentation",
        "desc": "Clarity of presentation deck, developer notes, and demo walkthrough.",
        "max": 10,
        "weight": 1.0
    },
    "impact": {
        "label": "Potential Impact & Viability",
        "desc": "Practical usefulness for the target audience or campus community.",
        "max": 10,
        "weight": 1.0
    }
}

# Are judge score totals publicly visible before the admin publishes the event results?
SHOWCASE_JUDGE_SCORES_PUBLIC_DEFAULT = False

# Demo modes
SHOWCASE_DEMO_MODES = {
    "hosted_build": "Hosted Interactive Build (WebGL / HTML5 zip)",
    "external_embed": "External Embed (Hugging Face, Streamlit, itch.io, YouTube)",
    "video_demo": "Recorded Video Demo",
    "screenshot_gallery": "Screenshot Gallery",
    "downloadable_build": "Downloadable Build Only (.exe, .apk, .zip)"
}

