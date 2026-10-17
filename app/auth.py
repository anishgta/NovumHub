"""
app/auth.py
================================================================================
AUTHENTICATION BLUEPRINT
Handles user registration, login, logout, and login attempt rate limiting.
================================================================================
"""

import random
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from app.forms import RegistrationForm, LoginForm, EditProfileForm, ChangePasswordForm, VerifyOtpForm
from app.email_service import send_otp_email, is_smtp_configured
import site_config

# Create a Flask Blueprint named 'auth'
auth_bp = Blueprint("auth", __name__)

# In-memory dictionary to track failed login attempts for basic rate limiting
# Format: { 'ip_or_email': [timestamp1, timestamp2, ...] }
FAILED_LOGIN_ATTEMPTS = {}


def is_rate_limited(identifier: str) -> bool:
    """Checks if a user/IP has exceeded MAX_LOGIN_ATTEMPTS within LOGIN_COOLDOWN_MINUTES."""
    now = datetime.now(timezone.utc)
    cooldown_cutoff = now - timedelta(minutes=site_config.LOGIN_COOLDOWN_MINUTES)
    
    attempts = FAILED_LOGIN_ATTEMPTS.get(identifier, [])
    # Keep only recent attempts
    valid_attempts = [t for t in attempts if t > cooldown_cutoff]
    FAILED_LOGIN_ATTEMPTS[identifier] = valid_attempts

    return len(valid_attempts) >= site_config.MAX_LOGIN_ATTEMPTS


def record_failed_attempt(identifier: str):
    """Records a failed login timestamp."""
    attempts = FAILED_LOGIN_ATTEMPTS.setdefault(identifier, [])
    attempts.append(datetime.now(timezone.utc))


def reset_failed_attempts(identifier: str):
    """Resets attempts on successful login."""
    FAILED_LOGIN_ATTEMPTS.pop(identifier, None)


# ==============================================================================
# REGISTER ROUTE (/register)
# ==============================================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Allows new AIT students, faculty/staff, and alumni to register directly with @aitpune.edu.in."""
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for("main.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email_clean = form.email.data.strip().lower()
        if not email_clean.endswith("@aitpune.edu.in"):
            flash("Registration is strictly restricted to @aitpune.edu.in email addresses.", "danger")
            return render_template("auth/register.html", form=form)

        year_val = (form.year.data or "").strip()
        # Role assignment logic:
        # Faculty / Staff -> 'staff'
        # Alumni -> 'alumni'
        # Others (FE, SE, TE, BE, etc.) -> 'student'
        if year_val == "Faculty / Staff":
            assigned_role = "staff"
        elif year_val == "Alumni":
            assigned_role = "alumni"
        else:
            assigned_role = "student"

        reg_no = (form.registration_no.data or "").strip() or (form.roll_no.data or "").strip() or None

        user = User(
            name=form.name.data.strip(),
            email=email_clean,
            department=form.department.data or None,
            year=year_val or None,
            registration_no=reg_no,
            roll_no=reg_no,
            role=assigned_role
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Automatically log in the user after successful registration
        login_user(user)
        flash(f"Welcome to {site_config.SITE_NAME}, {user.name}! Your account has been created successfully.", "success")
        return redirect(url_for("submissions.dashboard"))

    return render_template("auth/register.html", form=form)


# ==============================================================================
# LOGIN ROUTE (/login)
# ==============================================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Logs in an existing student, reviewer, or administrator."""
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    client_ip = request.remote_addr or "unknown"

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Check rate limiting for this email or IP
        if is_rate_limited(email) or is_rate_limited(client_ip):
            flash(
                f"Too many failed login attempts. Please wait {site_config.LOGIN_COOLDOWN_MINUTES} minutes before trying again.",
                "danger"
            )
            return render_template("auth/login.html", form=form)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            if user.is_banned:
                reason = user.ban_reason or "Account suspended by administration."
                flash(f"Account Suspended: Your access to {site_config.SITE_NAME} has been revoked by administration. Notice / Reason: {reason}", "danger")
                return render_template("auth/login.html", form=form)

            # Password is correct! Clear failed attempts
            reset_failed_attempts(email)
            reset_failed_attempts(client_ip)
            login_user(user, remember=form.remember_me.data)

            flash(f"Welcome back, {user.name}!", "success")

            # Check if there was a redirected page the user originally wanted to visit
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)

            # Redirect reviewers/admins to review queue, students to their dashboard
            if user.is_reviewer:
                return redirect(url_for("review.queue"))
            return redirect(url_for("submissions.dashboard"))
        else:
            # Login failed
            record_failed_attempt(email)
            record_failed_attempt(client_ip)
            flash("Invalid email address or password. Please double-check your credentials.", "danger")

    return render_template("auth/login.html", form=form)


# ==============================================================================
# LOGOUT ROUTE (/logout)
# ==============================================================================
@auth_bp.route("/logout")
@login_required
def logout():
    """Logs out the current user."""
    logout_user()
    flash("You have been successfully logged out. See you next time!", "info")
    return redirect(url_for("main.home"))


# ==============================================================================
# PROFILE & ACCOUNT SETTINGS ROUTE (/profile)
# ==============================================================================
@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Allows authenticated users to update their personal/academic details and password (role is strictly non-editable)."""
    profile_form = EditProfileForm(original_email=current_user.email, prefix="profile")
    password_form = ChangePasswordForm(prefix="password")

    # If saving profile details
    if "profile-submit_profile" in request.form:
        if profile_form.validate_on_submit():
            current_user.name = profile_form.name.data.strip()
            current_user.email = profile_form.email.data.strip().lower()
            current_user.department = profile_form.department.data or None
            current_user.year = profile_form.year.data or None
            reg_val = (profile_form.registration_no.data or "").strip() or (profile_form.roll_no.data or "").strip() or None
            current_user.registration_no = reg_val
            current_user.roll_no = reg_val
            # ROLE IS STRICTLY UNTOUCHED - role can only be assigned by campus administration!
            db.session.commit()
            flash("Your profile information has been successfully updated.", "success")
            return redirect(url_for("auth.profile"))

    # If updating password
    elif "password-submit_password" in request.form:
        if password_form.validate_on_submit():
            if not current_user.check_password(password_form.current_password.data):
                flash("Current password verification failed. Please try again.", "danger")
            else:
                current_user.set_password(password_form.new_password.data)
                db.session.commit()
                flash("Your password has been securely updated. Please use your new password next time you sign in.", "success")
                return redirect(url_for("auth.profile"))

    # Pre-populate details on initial GET
    if request.method == "GET":
        profile_form.name.data = current_user.name
        profile_form.email.data = current_user.email
        profile_form.department.data = current_user.department or ""
        profile_form.year.data = current_user.year or ""
        profile_form.registration_no.data = current_user.display_registration_no or ""
        profile_form.roll_no.data = current_user.display_registration_no or ""

    return render_template(
        "auth/profile.html",
        profile_form=profile_form,
        password_form=password_form
    )

