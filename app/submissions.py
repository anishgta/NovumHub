"""
app/submissions.py
================================================================================
SUBMISSIONS BLUEPRINT
Handles submission creation, browsing/searching public feed, detailed views,
upvoting, comments, author editing/withdrawing, and student personal dashboard.
================================================================================
"""

import os
import secrets
from datetime import datetime, timezone, timedelta
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, jsonify, abort, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Submission, StatusChange, Comment, Upvote, Report, Notification, User, ShowcaseProject, UserWarning
from app.forms import SubmissionForm, CommentForm, ReportForm
import site_config

submissions_bp = Blueprint("submissions", __name__)


# ==============================================================================
# 1. BROWSE & SEARCH PUBLIC FEED (/browse)
# ==============================================================================
@submissions_bp.route("/browse")
def browse():
    """
    Public feed of accepted and implemented submissions with keyword search,
    category filter, department filter, and newest / most-upvoted sorting.
    """
    search_query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()
    status_filter = request.args.get("status", "").strip()
    department_filter = request.args.get("department", "").strip()
    sort_by = request.args.get("sort", "newest").strip()
    page = request.args.get("page", 1, type=int)

    # Base query: only Accepted or Implemented items are shown publicly
    query = Submission.query.filter(Submission.status.in_(site_config.PUBLIC_STATUSES))

    # Keyword search across title, summary, details, and tags
    if search_query:
        term = f"%{search_query}%"
        query = query.filter(
            (Submission.title.ilike(term)) |
            (Submission.summary.ilike(term)) |
            (Submission.details.ilike(term)) |
            (Submission.tags.ilike(term))
        )

    # Category filter
    if category_filter and category_filter in site_config.CATEGORIES:
        query = query.filter(Submission.category == category_filter)

    # Status filter
    if status_filter and status_filter in site_config.PUBLIC_STATUSES:
        query = query.filter(Submission.status == status_filter)

    # Department filter (join on author)
    if department_filter:
        query = query.join(User, Submission.author_id == User.id).filter(User.department == department_filter)

    # Sorting options
    if sort_by == "upvotes":
        # Sort by number of upvotes descending
        all_matches = query.all()
        all_matches.sort(key=lambda s: s.upvote_count, reverse=True)
        # Manual slice pagination for in-memory sort
        start = (page - 1) * site_config.ITEMS_PER_PAGE
        end = start + site_config.ITEMS_PER_PAGE
        submissions = all_matches[start:end]
        total_items = len(all_matches)
        total_pages = (total_items + site_config.ITEMS_PER_PAGE - 1) // site_config.ITEMS_PER_PAGE
        has_prev = page > 1
        has_next = page < total_pages
    else:
        # Default: newest first
        pagination = query.order_by(Submission.created_at.desc()).paginate(
            page=page, per_page=site_config.ITEMS_PER_PAGE, error_out=False
        )
        submissions = pagination.items
        total_pages = pagination.pages
        has_prev = pagination.has_prev
        has_next = pagination.has_next
        total_items = pagination.total

    # Unified search: Also find matching Showcase Projects
    matching_projects = []
    if search_query:
        term = f"%{search_query}%"
        matching_projects = ShowcaseProject.query.filter(
            ShowcaseProject.status.in_(site_config.SHOWCASE_PUBLIC_STATUSES),
            (ShowcaseProject.title.ilike(term)) |
            (ShowcaseProject.pitch.ilike(term)) |
            (ShowcaseProject.tech_tags.ilike(term))
        ).limit(4).all()

    return render_template(
        "submissions/browse.html",
        submissions=submissions,
        matching_projects=matching_projects,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        has_prev=has_prev,
        has_next=has_next,
        search_query=search_query,
        category_filter=category_filter,
        status_filter=status_filter,
        department_filter=department_filter,
        sort_by=sort_by
    )


# ==============================================================================
# 2. CREATE NEW CONTRIBUTION (/submit)
# ==============================================================================
@submissions_bp.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    """Form to submit an Idea, Research Finding, Correction, or Infrastructure Suggestion."""
    # Submission rate limit per user
    one_hour_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    recent_count = Submission.query.filter(
        Submission.author_id == current_user.id,
        Submission.created_at >= one_hour_ago
    ).count()

    if recent_count >= site_config.MAX_SUBMISSIONS_PER_HOUR:
        flash(f"Rate limit exceeded: You can make at most {site_config.MAX_SUBMISSIONS_PER_HOUR} submissions per hour.", "danger")
        return redirect(url_for("submissions.dashboard"))

    form = SubmissionForm()
    # Pre-select category if passed in URL query param
    if request.method == "GET" and request.args.get("category"):
        form.category.data = request.args.get("category")

    if form.validate_on_submit():
        attachment_filename = None
        # Handle optional file upload
        if form.attachment.data:
            uploaded_file = form.attachment.data
            ext = os.path.splitext(uploaded_file.filename)[1].lower()
            if ext in site_config.ALLOWED_EXTENSIONS:
                # Generate safe random filename to prevent overwrites or security exploits
                safe_name = f"{secrets.token_hex(8)}{ext}"
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                uploaded_file.save(os.path.join(upload_folder, safe_name))
                attachment_filename = safe_name

        # Package category-specific dynamic fields
        extra_data = {}
        cat = form.category.data
        if cat == "idea":
            extra_data = {
                "expected_impact": form.idea_impact.data or "",
                "resources_needed": form.idea_resources.data or ""
            }
        elif cat == "research":
            extra_data = {
                "methodology": form.research_methodology.data or "",
                "key_results": form.research_results.data or "",
                "link_or_doi": form.research_link.data or ""
            }
        elif cat == "correction":
            extra_data = {
                "item_corrected": form.correction_item.data or "",
                "what_is_wrong": form.correction_wrong.data or "",
                "what_is_correct": form.correction_correct.data or "",
                "evidence_source": form.correction_evidence.data or ""
            }
        elif cat == "infrastructure":
            extra_data = {
                "location": form.infra_location.data or "",
                "problem": form.infra_problem.data or "",
                "solution": form.infra_solution.data or "",
                "priority": form.infra_priority.data or "Medium"
            }

        submission = Submission(
            author_id=current_user.id,
            category=cat,
            title=form.title.data.strip(),
            summary=form.summary.data.strip(),
            details=form.details.data.strip(),
            tags=form.tags.data.strip() if form.tags.data else "",
            attachment_path=attachment_filename,
            anonymous_public=form.anonymous_public.data,
            status="Submitted"
        )
        submission.extra_fields = extra_data
        db.session.add(submission)
        db.session.flush()  # Generate submission.id

        # Record initial status timeline entry
        timeline_entry = StatusChange(
            submission_id=submission.id,
            actor_id=current_user.id,
            from_status="None",
            to_status="Submitted",
            public_comment="Contribution created and submitted for triage review."
        )
        db.session.add(timeline_entry)
        db.session.commit()

        flash("Your contribution has been successfully submitted! The review team will evaluate it shortly.", "success")
        return redirect(url_for("submissions.detail", submission_id=submission.id))

    return render_template("submissions/submit.html", form=form)


# ==============================================================================
# 3. SUBMISSION DETAIL VIEW (/submissions/<id>)
# ==============================================================================
@submissions_bp.route("/submissions/<int:submission_id>")
def detail(submission_id: int):
    """Full detail view with status timeline, attachments, upvoting, and comments."""
    submission = db.get_or_404(Submission, submission_id)

    # Access control: Private statuses are only visible to the author and reviewers/admins
    if submission.status not in site_config.PUBLIC_STATUSES:
        if not current_user.is_authenticated or (
            current_user.id != submission.author_id and not current_user.is_reviewer
        ):
            abort(403)

    comment_form = CommentForm()
    report_form = ReportForm()

    return render_template(
        "submissions/detail.html",
        submission=submission,
        comment_form=comment_form,
        report_form=report_form
    )


# ==============================================================================
# 4. EDIT SUBMISSION (/submissions/<id>/edit)
# ==============================================================================
@submissions_bp.route("/submissions/<int:submission_id>/edit", methods=["GET", "POST"])
@login_required
def edit(submission_id: int):
    """Authors can edit their submission only while in 'Submitted' or 'Needs Changes' status."""
    submission = db.get_or_404(Submission, submission_id)

    if submission.author_id != current_user.id and not current_user.is_admin:
        abort(403)

    if submission.status not in ("Submitted", "Needs Changes") and not current_user.is_admin:
        flash("This submission cannot be edited because it is already under active review or accepted.", "warning")
        return redirect(url_for("submissions.detail", submission_id=submission.id))

    form = SubmissionForm(obj=submission)

    if request.method == "GET":
        # Pre-fill category dynamic fields
        extra = submission.extra_fields
        form.category.data = submission.category
        if submission.category == "idea":
            form.idea_impact.data = extra.get("expected_impact", "")
            form.idea_resources.data = extra.get("resources_needed", "")
        elif submission.category == "research":
            form.research_methodology.data = extra.get("methodology", "")
            form.research_results.data = extra.get("key_results", "")
            form.research_link.data = extra.get("link_or_doi", "")
        elif submission.category == "correction":
            form.correction_item.data = extra.get("item_corrected", "")
            form.correction_wrong.data = extra.get("what_is_wrong", "")
            form.correction_correct.data = extra.get("what_is_correct", "")
            form.correction_evidence.data = extra.get("evidence_source", "")
        elif submission.category == "infrastructure":
            form.infra_location.data = extra.get("location", "")
            form.infra_problem.data = extra.get("problem", "")
            form.infra_solution.data = extra.get("solution", "")
            form.infra_priority.data = extra.get("priority", "Medium")

    if form.validate_on_submit():
        submission.title = form.title.data.strip()
        submission.summary = form.summary.data.strip()
        submission.details = form.details.data.strip()
        submission.tags = form.tags.data.strip() if form.tags.data else ""
        submission.anonymous_public = form.anonymous_public.data

        # Update dynamic extra fields
        cat = submission.category
        extra = {}
        if cat == "idea":
            extra = {"expected_impact": form.idea_impact.data or "", "resources_needed": form.idea_resources.data or ""}
        elif cat == "research":
            extra = {"methodology": form.research_methodology.data or "", "key_results": form.research_results.data or "", "link_or_doi": form.research_link.data or ""}
        elif cat == "correction":
            extra = {"item_corrected": form.correction_item.data or "", "what_is_wrong": form.correction_wrong.data or "", "what_is_correct": form.correction_correct.data or "", "evidence_source": form.correction_evidence.data or ""}
        elif cat == "infrastructure":
            extra = {"location": form.infra_location.data or "", "problem": form.infra_problem.data or "", "solution": form.infra_solution.data or "", "priority": form.infra_priority.data or "Medium"}

        submission.extra_fields = extra

        # If it was in "Needs Changes", moving it back to "Submitted" signals reviewer that updates are done
        if submission.status == "Needs Changes":
            submission.status = "Submitted"
            change = StatusChange(
                submission_id=submission.id,
                actor_id=current_user.id,
                from_status="Needs Changes",
                to_status="Submitted",
                public_comment="Student updated the submission with requested changes."
            )
            db.session.add(change)

        db.session.commit()
        flash("Your submission has been updated successfully.", "success")
        return redirect(url_for("submissions.detail", submission_id=submission.id))

    return render_template("submissions/edit.html", form=form, submission=submission)


# ==============================================================================
# 5. WITHDRAW SUBMISSION (/submissions/<id>/withdraw)
# ==============================================================================
@submissions_bp.route("/submissions/<int:submission_id>/withdraw", methods=["POST"])
@login_required
def withdraw(submission_id: int):
    """Students can withdraw their own submission while it is still 'Submitted'."""
    submission = db.get_or_404(Submission, submission_id)
    if submission.author_id != current_user.id and not current_user.is_admin:
        abort(403)

    if submission.status != "Submitted" and not current_user.is_admin:
        flash("Only submissions in 'Submitted' status can be withdrawn.", "warning")
        return redirect(url_for("submissions.detail", submission_id=submission.id))

    db.session.delete(submission)
    db.session.commit()
    flash("Your contribution has been withdrawn and deleted.", "info")
    return redirect(url_for("submissions.dashboard"))


# ==============================================================================
# 6. ASYNC UPVOTE TOGGLE (/submissions/<id>/upvote)
# ==============================================================================
@submissions_bp.route("/submissions/<int:submission_id>/upvote", methods=["POST"])
def upvote(submission_id: int):
    """Toggles upvote for the current logged-in user."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Please log in to upvote."}), 401

    submission = db.get_or_404(Submission, submission_id)
    existing_upvote = Upvote.query.filter_by(submission_id=submission.id, user_id=current_user.id).first()

    if existing_upvote:
        db.session.delete(existing_upvote)
        db.session.commit()
        upvoted = False
    else:
        new_upvote = Upvote(submission_id=submission.id, user_id=current_user.id)
        db.session.add(new_upvote)
        db.session.commit()
        upvoted = True

    return jsonify({
        "success": True,
        "upvoted": upvoted,
        "upvote_count": submission.upvote_count
    })


# ==============================================================================
# 7. ADD COMMENT (/submissions/<id>/comment)
# ==============================================================================
@submissions_bp.route("/submissions/<int:submission_id>/comment", methods=["POST"])
@login_required
def add_comment(submission_id: int):
    """Logged-in students can participate in constructive discussion."""
    submission = db.get_or_404(Submission, submission_id)
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(
            submission_id=submission.id,
            author_id=current_user.id,
            body=form.body.data.strip()
        )
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been posted.", "success")
    else:
        for err in form.body.errors:
            flash(err, "danger")

    return redirect(url_for("submissions.detail", submission_id=submission.id))


# ==============================================================================
# 8. REPORT SUBMISSION OR COMMENT
# ==============================================================================
@submissions_bp.route("/submissions/<int:submission_id>/report", methods=["POST"])
def report(submission_id: int):
    """Flags inappropriate content for reviewer attention."""
    submission = db.get_or_404(Submission, submission_id)
    form = ReportForm()

    if form.validate_on_submit():
        new_report = Report(
            target_type="submission",
            target_id=submission.id,
            reporter_id=current_user.id if current_user.is_authenticated else None,
            reason=f"{form.reason.data}: {form.details.data or ''}".strip(": ")
        )
        db.session.add(new_report)
        db.session.commit()
        flash("Thank you for your report. The review team has been notified.", "info")
    return redirect(url_for("submissions.detail", submission_id=submission.id))


# ==============================================================================
# 9. STUDENT DASHBOARD (/dashboard)
# ==============================================================================
@submissions_bp.route("/dashboard")
@login_required
def dashboard():
    """Personal student dashboard showing user's submissions, statuses, and alerts."""
    my_submissions = Submission.query.filter_by(author_id=current_user.id).order_by(Submission.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(15).all()

    return render_template(
        "dashboard/student.html",
        my_submissions=my_submissions,
        notifications=notifications
    )


# ==============================================================================
# 10. NOTIFICATIONS READ HELPER
# ==============================================================================
@submissions_bp.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    """Marks all notifications as read for current user."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("Notifications marked as read.", "info")
    return redirect(url_for("submissions.dashboard"))


# ==============================================================================
# 11. SAFE FILE SERVING (/uploads/<filename>)
# ==============================================================================
@submissions_bp.route("/uploads/<filename>")
def uploaded_file(filename: str):
    """Safely serves uploaded attachments."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


# ==============================================================================
# 12. WARNING NOTICE ACKNOWLEDGMENT
# ==============================================================================
@submissions_bp.route("/warnings/<int:warning_id>/acknowledge", methods=["POST"])
@login_required
def acknowledge_warning(warning_id: int):
    """Allows a student to formally acknowledge an administrative notice/warning."""
    from datetime import datetime, timezone
    warning = db.get_or_404(UserWarning, warning_id)
    if warning.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    warning.is_acknowledged = True
    warning.acknowledged_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("You have acknowledged this official notice. Please ensure all future contributions follow guidelines.", "info")
    return redirect(request.referrer or url_for("submissions.dashboard"))

