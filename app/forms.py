"""
app/forms.py
================================================================================
FORMS DEFINITIONS (Flask-WTF & WTForms)
WTForms handles web form rendering, HTML input validation, and CSRF protection.
CSRF (Cross-Site Request Forgery) prevents unauthorized commands from malicious sites.
================================================================================
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    TextAreaField, SelectField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, ValidationError, Regexp
)
from app.models import User
import site_config


# ==============================================================================
# HELPER VALIDATORS
# ==============================================================================
def check_blocked_words(form, field):
    """Checks if user input contains any blocked spam/profanity words from site_config."""
    if not field.data:
        return
    text = field.data.lower()
    for word in site_config.BLOCKED_WORDS:
        if word in text:
            raise ValidationError(f"Your input contains a restricted phrase ('{word}'). Please keep submissions professional.")


# ==============================================================================
# 1. USER REGISTRATION FORM
# ==============================================================================
class RegistrationForm(FlaskForm):
    name = StringField("Full Name", validators=[
        DataRequired(message="Please enter your full name."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])

    email = StringField("Email Address", validators=[
        DataRequired(message="Email address is required."),
        Email(message="Please provide a valid email address.")
    ])

    department = SelectField("Department", choices=[("", "-- Select Department --")] + [(d, d) for d in site_config.DEPARTMENTS],
                             validators=[Optional()])

    year = SelectField("Academic Year", choices=[("", "-- Select Year --")] + [(y, y) for y in site_config.ACADEMIC_YEARS],
                       validators=[Optional()])

    registration_no = StringField("Registration Number (6-digit)", validators=[
        DataRequired(message="Please enter your 6-digit registration number."),
        Regexp(r"^\d{6}$", message="Registration number must be exactly 6 digits (e.g. 231045).")
    ])
    roll_no = StringField("Roll Number (Optional)", validators=[Optional()])

    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])

    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo("password", message="Passwords must match.")
    ])

    submit = SubmitField("Create Account")

    def validate_email(self, field):
        """Validates email domain and uniqueness."""
        email_val = field.data.strip().lower()

        # Strict domain restriction: aitpune.edu.in
        domain = "@" + (site_config.ALLOWED_EMAIL_DOMAIN or "aitpune.edu.in").lstrip("@").lower()
        if not email_val.endswith(domain):
            raise ValidationError(f"Registration is strictly restricted to {domain} email addresses.")

        # Ensure email is not already registered
        existing_user = User.query.filter_by(email=email_val).first()
        if existing_user:
            raise ValidationError("An account with this email address already exists. Please log in.")


# ==============================================================================
# 2. USER LOGIN FORM
# ==============================================================================
class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[
        DataRequired(message="Email address is required."),
        Email(message="Please enter a valid email address.")
    ])

    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required.")
    ])

    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")


# ==============================================================================
# 2B. EDIT PROFILE DETAILS & PASSWORD FORMS
# ==============================================================================
class EditProfileForm(FlaskForm):
    """Allows users to update their personal and academic details (role is strictly non-editable)."""
    name = StringField("Full Name", validators=[
        DataRequired(message="Please enter your full name."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])

    email = StringField("Email Address", validators=[
        DataRequired(message="Email address is required."),
        Email(message="Please provide a valid email address.")
    ])

    department = SelectField("Department", choices=[("", "-- Select Department --")] + [(d, d) for d in site_config.DEPARTMENTS],
                             validators=[Optional()])

    year = SelectField("Academic Year", choices=[("", "-- Select Year --")] + [(y, y) for y in site_config.ACADEMIC_YEARS],
                       validators=[Optional()])

    registration_no = StringField("Registration Number (6-digit)", validators=[
        Optional(),
        Regexp(r"^\d{6}$", message="Registration number must be exactly 6 digits (e.g. 231045).")
    ])
    roll_no = StringField("Roll Number (Legacy Alias)", validators=[Optional()])
    submit_profile = SubmitField("Save Details")

    def __init__(self, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, field):
        email_val = field.data.strip().lower()
        domain = "@" + (site_config.ALLOWED_EMAIL_DOMAIN or "aitpune.edu.in").lstrip("@").lower()
        if not email_val.endswith(domain):
            raise ValidationError(f"Email must end with {domain}.")
        if self.original_email and email_val != self.original_email.lower():
            existing = User.query.filter_by(email=email_val).first()
            if existing:
                raise ValidationError("This email address is already in use by another account.")


class VerifyOtpForm(FlaskForm):
    """Submits 6-digit email OTP verification code."""
    otp = StringField("Verification Code (6-digit OTP)", validators=[
        DataRequired(message="Please enter the 6-digit verification code sent to your email."),
        Regexp(r"^\d{6}$", message="Verification code must be exactly 6 digits (0-9).")
    ])
    submit = SubmitField("Verify & Complete Registration")


class ChangePasswordForm(FlaskForm):
    """Allows authenticated users to update their password securely."""
    current_password = PasswordField("Current Password", validators=[
        DataRequired(message="Current password is required to verify identity.")
    ])

    new_password = PasswordField("New Password", validators=[
        DataRequired(message="New password is required."),
        Length(min=6, message="New password must be at least 6 characters long.")
    ])

    confirm_new_password = PasswordField("Confirm New Password", validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo("new_password", message="Passwords must match.")
    ])

    submit_password = SubmitField("Update Password")


# ==============================================================================
# 3. CONTRIBUTION SUBMISSION FORM (Shared for all 4 categories)
# ==============================================================================
class SubmissionForm(FlaskForm):
    # Category selection
    category = SelectField("Submission Category", choices=[
        ("idea", site_config.CATEGORIES["idea"]["name"]),
        ("research", site_config.CATEGORIES["research"]["name"]),
        ("correction", site_config.CATEGORIES["correction"]["name"]),
        ("infrastructure", site_config.CATEGORIES["infrastructure"]["name"]),
    ], validators=[DataRequired(message="Please select a category.")])

    # Common fields for all categories
    title = StringField("Title", validators=[
        DataRequired(message="A clear title is required."),
        Length(min=5, max=180, message="Title must be between 5 and 180 characters."),
        check_blocked_words
    ])

    summary = StringField("Short Summary", validators=[
        DataRequired(message="Please provide a 1-2 sentence summary."),
        Length(min=10, max=280, message="Summary must be between 10 and 280 characters."),
        check_blocked_words
    ])

    details = TextAreaField("Full Details / Description", validators=[
        DataRequired(message="Detailed description is required."),
        Length(min=20, message="Please write at least 20 characters explaining your contribution."),
        check_blocked_words
    ])

    tags = StringField("Tags (comma separated, e.g., robotics, wifi, lab)", validators=[
        Optional(),
        Length(max=200)
    ])

    # File attachment (PDF, PNG, JPG)
    attachment = FileField("Supporting File / PDF / Image (Optional)", validators=[
        Optional(),
        FileAllowed(["pdf", "png", "jpg", "jpeg"], "Allowed formats: PDF, PNG, JPG, JPEG only.")
    ])

    anonymous_public = BooleanField("Submit anonymously to public feed (Reviewers still see author)")

    # Category 1: Innovative Idea fields
    idea_impact = TextAreaField("Expected Campus / Community Impact", validators=[Optional(), check_blocked_words])
    idea_resources = StringField("Estimated Resources / Equipment Needed", validators=[Optional(), check_blocked_words])

    # Category 2: Research Finding fields
    research_methodology = TextAreaField("Methodology / Experimental Setup", validators=[Optional(), check_blocked_words])
    research_results = TextAreaField("Key Findings / Quantitative Results", validators=[Optional(), check_blocked_words])
    research_link = StringField("DOI / Code Repo / Paper Link (Optional)", validators=[Optional()])

    # Category 3: Research Correction fields
    correction_item = StringField("Item Being Corrected (Title, Notice No., Lab Manual, URL)",
                                  validators=[Optional(), check_blocked_words])
    correction_wrong = TextAreaField("What is Wrong or Outdated?",
                                     validators=[Optional(), check_blocked_words])
    correction_correct = TextAreaField("What is the Correct Information?",
                                       validators=[Optional(), check_blocked_words])
    correction_evidence = TextAreaField("Evidence / Citation / Source Reference",
                                        validators=[Optional(), check_blocked_words])

    # Category 4: Infrastructure Suggestion fields
    infra_location = StringField("Campus Location / Building / Lab / Hostel",
                                 validators=[Optional(), check_blocked_words])
    infra_problem = TextAreaField("Current Issue / Problem Observed",
                                  validators=[Optional(), check_blocked_words])
    infra_solution = TextAreaField("Proposed Fix / Actionable Improvement",
                                   validators=[Optional(), check_blocked_words])
    infra_priority = SelectField("Priority Level", choices=[
        ("Medium", "Medium (Normal Improvement)"),
        ("Low", "Low (Nice to have)"),
        ("High", "High (Urgent / Safety / Equipment Down)")
    ], default="Medium")

    submit = SubmitField("Submit for Review")

    def validate(self, extra_validators=None):
        """Custom multi-field validation depending on category selected."""
        initial_valid = super().validate(extra_validators=extra_validators)
        if not initial_valid:
            return False

        cat = self.category.data

        # Category-specific strict checks
        if cat == "correction":
            # For corrections, evidence and exact items are mandatory
            if not self.correction_item.data or not self.correction_item.data.strip():
                self.correction_item.errors.append("Please specify the item or document being corrected.")
                return False
            if not self.correction_wrong.data or not self.correction_wrong.data.strip():
                self.correction_wrong.errors.append("Please describe what is currently wrong or inaccurate.")
                return False
            if not self.correction_correct.data or not self.correction_correct.data.strip():
                self.correction_correct.errors.append("Please provide the correct replacement information.")
                return False
            if not self.correction_evidence.data or not self.correction_evidence.data.strip():
                self.correction_evidence.errors.append("Evidence or citation is required for research corrections.")
                return False

        elif cat == "infrastructure":
            if not self.infra_location.data or not self.infra_location.data.strip():
                self.infra_location.errors.append("Please specify the campus location (e.g. Mech Lab 2, D-Hostel).")
                return False

        return True


# ==============================================================================
# 4. REVIEWER TRIAGE & STATUS CHANGE FORM
# ==============================================================================
class StatusChangeForm(FlaskForm):
    to_status = SelectField("Update Status To", choices=[
        ("Submitted", "Submitted"),
        ("Under Review", "Under Review"),
        ("Accepted", "Accepted (Publish to public feed)"),
        ("Needs Changes", "Needs Changes (Send back to student)"),
        ("Rejected", "Rejected"),
        ("Implemented", "Implemented (Completed 🎉)")
    ], validators=[DataRequired()])

    public_comment = TextAreaField("Public Feedback / Official Response (Visible to submitter & community)",
                                   validators=[Optional(), Length(max=1000)])

    internal_note = TextAreaField("Internal Reviewer Notes (Visible ONLY to reviewers and admins)",
                                  validators=[Optional(), Length(max=1000)])

    submit = SubmitField("Save Status & Send Feedback")


# ==============================================================================
# 5. PUBLIC DISCUSSION COMMENT FORM
# ==============================================================================
class CommentForm(FlaskForm):
    body = TextAreaField("Leave a comment or constructive thought...", validators=[
        DataRequired(message="Comment cannot be blank."),
        Length(min=3, max=800, message="Comment must be between 3 and 800 characters."),
        check_blocked_words
    ])
    submit = SubmitField("Post Comment")


# ==============================================================================
# 6. REPORT INAPPROPRIATE CONTENT FORM
# ==============================================================================
class ReportForm(FlaskForm):
    reason = SelectField("Reason for Report", choices=[
        ("Spam / Advertisement", "Spam / Advertisement"),
        ("Inappropriate / Offensive Language", "Inappropriate / Offensive Language"),
        ("False or Inaccurate Information", "False or Inaccurate Information"),
        ("Duplicate Submission", "Duplicate Submission"),
        ("Other", "Other")
    ], validators=[DataRequired()])

    details = TextAreaField("Additional Details (Optional)", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Submit Report to Reviewers")
