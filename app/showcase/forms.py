"""
app/showcase/forms.py
================================================================================
SHOWCASE FORMS (Flask-WTF)
Forms for project submission wizards, asset uploads, dev notes, judging rubrics,
and event administration.
================================================================================
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, FileField,
    IntegerField, BooleanField, SubmitField
)
from wtforms.validators import DataRequired, Length, Optional, URL, NumberRange
import site_config


class ProjectBasicsForm(FlaskForm):
    """Step 1: Project Metadata & Event Selection"""
    title = StringField("Project Title", validators=[DataRequired(), Length(max=200)])
    pitch = StringField("One-Line Pitch", validators=[DataRequired(), Length(max=300)])
    description = TextAreaField("Project Overview", validators=[DataRequired()])
    event_id = SelectField("Hackathon Event", coerce=int, validators=[DataRequired()])
    track = StringField("Track / Theme", validators=[DataRequired(), Length(max=100)])
    team_name = StringField("Team Name", validators=[DataRequired(), Length(max=150)])
    tech_tags = StringField("Tech Stack Tags (comma-separated)", validators=[Optional(), Length(max=255)])
    repo_url = StringField("Repository URL (GitHub / GitLab)", validators=[Optional(), Length(max=255)])
    linked_submission_id = SelectField("Started as a Hackrec Idea? (Optional)", coerce=int, validators=[Optional()])
    submit = SubmitField("Save & Continue")


class ProjectDemoForm(FlaskForm):
    """Step 2: Live Demo Configuration (Interactive Build, External, Video, etc.)"""
    demo_mode = SelectField(
        "Select Demo Type",
        choices=[(k, v) for k, v in site_config.SHOWCASE_DEMO_MODES.items()],
        validators=[DataRequired()]
    )
    demo_zip = FileField("Interactive Build (.zip containing index.html)")
    demo_external_url = StringField("External Embed URL (HuggingFace, Streamlit, itch.io, YouTube)", validators=[Optional()])
    video_url = StringField("Recorded Video Link (YouTube / Drive)", validators=[Optional()])
    video_file = FileField("Video File (.mp4, .webm)")
    download_file = FileField("Downloadable Build (.zip, .exe, .apk)")
    submit = SubmitField("Save & Continue")


class ProjectMemberForm(FlaskForm):
    """Step 3: Team Member Management"""
    display_name = StringField("Member Name", validators=[DataRequired(), Length(max=120)])
    role = StringField("Role (e.g. Lead Dev, UI/UX, Hardware)", validators=[Optional(), Length(max=100)])
    user_email = StringField("Linked Account Email (Optional)", validators=[Optional()])
    links = StringField("Portfolio / GitHub / LinkedIn", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Add Member")


class ProjectAssetsForm(FlaskForm):
    """Step 4: Presentation Decks & Supporting Files"""
    presentation_pdf = FileField("Presentation Deck (PDF - Required for inline preview)")
    presentation_source = FileField("Original Slides (.pptx, .key - Optional download)")
    document_file = FileField("Supporting Document (SRS, Report, Poster, Dataset)")
    document_title = StringField("Document Label (e.g. Architecture Blueprint)", validators=[Optional()])
    screenshot_file = FileField("Project Screenshot (.png, .jpg, .webp)")
    screenshot_caption = StringField("Screenshot Caption", validators=[Optional()])
    submit = SubmitField("Upload Asset")


class DevNotesForm(FlaskForm):
    """Step 5: Structured Developer Notes (8 Fixed Markdown Sections)"""
    problem = TextAreaField("1. Problem We Tackled", validators=[Optional()])
    how_it_works = TextAreaField("2. How It Works (Architecture)", validators=[Optional()])
    tech_stack = TextAreaField("3. Tech Stack & Why We Chose It", validators=[Optional()])
    run_locally = TextAreaField("4. How to Run Locally (Step-by-Step)", validators=[Optional()])
    challenges = TextAreaField("5. Challenges & How We Solved Them", validators=[Optional()])
    differently = TextAreaField("6. What We Would Do Differently", validators=[Optional()])
    time_breakdown = TextAreaField("7. Time Breakdown", validators=[Optional()])
    resources = TextAreaField("8. Useful Resources & Links", validators=[Optional()])
    submit = SubmitField("Save Developer Notes")


class JudgeScoreForm(FlaskForm):
    """Judge Evaluation Rubric Form"""
    innovation = IntegerField("Innovation & Originality (0-10)", validators=[DataRequired(), NumberRange(min=0, max=10)])
    technical_depth = IntegerField("Technical Depth (0-10)", validators=[DataRequired(), NumberRange(min=0, max=10)])
    completeness = IntegerField("Completeness & Functionality (0-10)", validators=[DataRequired(), NumberRange(min=0, max=10)])
    design_ux = IntegerField("Design & UX (0-10)", validators=[DataRequired(), NumberRange(min=0, max=10)])
    presentation = IntegerField("Presentation & Docs (0-10)", validators=[DataRequired(), NumberRange(min=0, max=10)])
    impact = IntegerField("Impact & Viability (0-10)", validators=[DataRequired(), NumberRange(min=0, max=10)])
    private_feedback = TextAreaField("Private Feedback (Only visible to fellow judges & admins)")
    public_feedback = TextAreaField("Public Constructive Feedback (Visible to the team)")
    submit = SubmitField("Submit Evaluation")


class HackathonEventForm(FlaskForm):
    """Admin Event Management Form"""
    name = StringField("Event Name (e.g. HackAIT 2026)", validators=[DataRequired(), Length(max=150)])
    year = IntegerField("Year", validators=[DataRequired()])
    theme = StringField("Theme / Motto", validators=[Optional(), Length(max=255)])
    organiser = StringField("Organising Club / Dept", validators=[Optional(), Length(max=150)])
    tracks = StringField("Tracks (comma-separated, e.g. AI, Web3, Campus Tech)", validators=[Optional()])
    description = TextAreaField("Event Details & Rules", validators=[Optional()])
    is_active = BooleanField("Active for Submissions", default=True)
    results_published = BooleanField("Publish Leaderboard & Results", default=False)
    submit = SubmitField("Save Event")
