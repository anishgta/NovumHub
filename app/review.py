"""
app/review.py
================================================================================
REVIEW & ADMIN BLUEPRINT
Handles faculty/admin triage queue, status changes, internal notes, notifications,
content moderation reports, CSV data export, and user role management.
================================================================================
"""

import csv
import io
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    abort, Response
)
from flask_login import login_required, current_user
from app.models import (
    db, Submission, StatusChange, Notification, Report,
    Comment, User, ShowcaseProject, HackathonEvent, JudgeScore,
    UserWarning, Upvote, ProjectMember
)
from app.forms import StatusChangeForm
import site_config

review_bp = Blueprint("review", __name__)


# ==============================================================================
# BEFORE REQUEST HOOK: ROLE ENFORCEMENT
# ==============================================================================
@review_bp.before_request
@login_required
def ensure_reviewer_role():
    """Restricts all routes in this blueprint to Reviewers and Admins only."""
    if not current_user.is_reviewer:
        abort(403)


# ==============================================================================
# 1. REVIEW QUEUE DASHBOARD (/review)
# ==============================================================================
@review_bp.route("/review")
def queue():
    """
    Main triage dashboard for faculty/admins.
    Filterable by status & category, shows metric counters, and open reports.
    """
    status_filter = request.args.get("status", "").strip()
    category_filter = request.args.get("category", "").strip()

    query = Submission.query

    if status_filter:
        query = query.filter(Submission.status == status_filter)
    if category_filter:
        query = query.filter(Submission.category == category_filter)

    submissions = query.order_by(Submission.created_at.desc()).all()

    # Metric counts
    counts_by_status = {s: Submission.query.filter_by(status=s).count() for s in site_config.STATUSES}
    counts_by_cat = {c: Submission.query.filter_by(category=c).count() for c in site_config.CATEGORIES}

    # Open moderation reports
    open_reports = Report.query.filter_by(resolved=False).order_by(Report.created_at.desc()).all()

    return render_template(
        "review/queue.html",
        submissions=submissions,
        counts_by_status=counts_by_status,
        counts_by_cat=counts_by_cat,
        status_filter=status_filter,
        category_filter=category_filter,
        open_reports=open_reports
    )


# ==============================================================================
# 2. SUBMISSION TRIAGE & STATUS CHANGE (/review/<id>)
# ==============================================================================
@review_bp.route("/review/<int:submission_id>", methods=["GET", "POST"])
def triage(submission_id: int):
    """Detailed triage view allowing reviewers to evaluate and update status."""
    submission = db.get_or_404(Submission, submission_id)
    form = StatusChangeForm()

    if request.method == "GET":
        form.to_status.data = submission.status

    if form.validate_on_submit():
        old_status = submission.status
        new_status = form.to_status.data
        public_comment = form.public_comment.data.strip() if form.public_comment.data else ""
        internal_note = form.internal_note.data.strip() if form.internal_note.data else ""

        # Update the submission's current status
        submission.status = new_status

        # Create audit trail record
        timeline_entry = StatusChange(
            submission_id=submission.id,
            actor_id=current_user.id,
            from_status=old_status,
            to_status=new_status,
            public_comment=public_comment or None,
            internal_note=internal_note or None
        )
        db.session.add(timeline_entry)

        # Notify student submitter if status changed
        if old_status != new_status:
            notif = Notification(
                user_id=submission.author_id,
                message=f"Your submission '{submission.title[:35]}...' status was updated to '{new_status}'.",
                link=url_for("submissions.detail", submission_id=submission.id)
            )
            db.session.add(notif)

        db.session.commit()
        flash(f"Submission status successfully updated to '{new_status}'.", "success")
        return redirect(url_for("review.triage", submission_id=submission.id))

    return render_template("review/triage.html", submission=submission, form=form)


# ==============================================================================
# 3. CSV DATA EXPORT (/review/export)
# ==============================================================================
@review_bp.route("/review/export")
def export_csv():
    """Exports all submissions and review statuses to a downloadable CSV file."""
    submissions = Submission.query.order_by(Submission.id.asc()).all()

    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "ID", "Category", "Title", "Summary", "Status",
        "Author Name", "Author Email", "Author Dept", "Author Year", "Roll No",
        "Upvotes", "Created At", "Updated At", "Attachment"
    ])

    for sub in submissions:
        author = sub.author
        writer.writerow([
            sub.id,
            site_config.CATEGORIES.get(sub.category, {}).get("name", sub.category),
            sub.title,
            sub.summary,
            sub.status,
            author.name if author else "N/A",
            author.email if author else "N/A",
            author.department or "N/A",
            author.year or "N/A",
            author.display_registration_no or "N/A",
            sub.upvote_count,
            sub.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            sub.updated_at.strftime("%Y-%m-%d %H:%M:%S") if sub.updated_at else "",
            sub.attachment_path or "None"
        ])

    csv_data = output.getvalue()
    filename = f"hackrec_submissions_{site_config.COLLEGE_SHORT_NAME.lower().replace(' ', '_')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==============================================================================
# 3B. SHOWCASE DATA & JUDGE EVALUATIONS CSV EXPORT (/review/export-showcase)
# ==============================================================================
@review_bp.route("/review/export-showcase")
def export_showcase_csv():
    """Exports all showcase projects, events, teams, and judge scores to CSV."""
    projects = ShowcaseProject.query.order_by(ShowcaseProject.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Project ID", "Event", "Year", "Track", "Title", "Pitch",
        "Team Name", "Demo Mode", "Status", "Upvotes", "Judge Count",
        "Average Judge Score (out of 60)", "Is Featured", "Is Reference",
        "Repo URL", "Owner Name", "Owner Email"
    ])

    for p in projects:
        owner = p.owner
        writer.writerow([
            p.id,
            p.event.name if p.event else "N/A",
            p.event.year if p.event else "N/A",
            p.track,
            p.title,
            p.pitch,
            p.team_name,
            p.demo_mode_label,
            p.status,
            p.upvote_count,
            p.judge_count,
            p.average_judge_score,
            "Yes" if p.is_featured else "No",
            "Yes" if p.is_reference else "No",
            p.repo_url or "None",
            owner.name if owner else "N/A",
            owner.email if owner else "N/A"
        ])

    csv_data = output.getvalue()
    filename = f"hackrec_showcase_projects_{site_config.COLLEGE_SHORT_NAME.lower().replace(' ', '_')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==============================================================================
# 4. RESOLVE MODERATION REPORT (/review/reports/<id>/resolve)
# ==============================================================================
@review_bp.route("/review/reports/<int:report_id>/resolve", methods=["POST"])
def resolve_report(report_id: int):
    """Marks a student/visitor moderation report as resolved."""
    report = db.get_or_404(Report, report_id)
    report.resolved = True
    db.session.commit()
    flash("Report marked as resolved.", "info")
    return redirect(url_for("review.queue"))


# ==============================================================================
# 5. MODERATE / DELETE COMMENT (/review/comments/<id>/delete)
# ==============================================================================
@review_bp.route("/review/comments/<int:comment_id>/delete", methods=["POST"])
def delete_comment(comment_id: int):
    """Soft-deletes an offensive or spam comment."""
    comment = db.get_or_404(Comment, comment_id)
    comment.is_deleted = True
    db.session.commit()
    flash("Comment has been deleted by reviewer.", "info")
    return redirect(url_for("submissions.detail", submission_id=comment.submission_id))


# ==============================================================================
# 6. ADMIN USER MANAGEMENT & MODERATION (/admin/users)
# ==============================================================================
@review_bp.route("/admin/users")
def manage_users():
    """Allows administrators to view users, manage roles, issue warnings, ban, and remove accounts."""
    if not current_user.is_admin:
        abort(403)

    query = User.query
    search_q = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "").strip()
    status_filter = request.args.get("status", "").strip()

    if search_q:
        query = query.filter(
            (User.name.ilike(f"%{search_q}%")) |
            (User.email.ilike(f"%{search_q}%")) |
            (User.registration_no.ilike(f"%{search_q}%")) |
            (User.roll_no.ilike(f"%{search_q}%"))
        )

    if role_filter in ("student", "staff", "alumni", "reviewer", "judge", "admin"):
        query = query.filter(User.role == role_filter)

    if status_filter == "banned":
        query = query.filter(User.is_banned == True)
    elif status_filter == "active":
        query = query.filter(User.is_banned == False)
    elif status_filter == "warned":
        query = query.join(UserWarning, User.id == UserWarning.user_id).distinct()

    users = query.order_by(User.created_at.desc()).all()

    total_users = User.query.count()
    banned_count = User.query.filter_by(is_banned=True).count()
    warned_count = db.session.query(UserWarning.user_id).distinct().count()

    return render_template(
        "review/users.html",
        users=users,
        total_users=total_users,
        banned_count=banned_count,
        warned_count=warned_count,
        search_q=search_q,
        role_filter=role_filter,
        status_filter=status_filter
    )


@review_bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
def change_role(user_id: int):
    """Admin endpoint to promote or demote a user's role."""
    if not current_user.is_admin:
        abort(403)
    target_user = db.get_or_404(User, user_id)
    new_role = request.form.get("role")
    if new_role in ("student", "staff", "alumni", "reviewer", "judge", "admin"):
        target_user.role = new_role
        db.session.commit()
        flash(f"Updated {target_user.name}'s role to {new_role.capitalize()}.", "success")
    return redirect(url_for("review.manage_users"))


@review_bp.route("/admin/users/<int:user_id>/ban", methods=["POST"])
def ban_user(user_id: int):
    """Admin endpoint to ban or unban an account with an official notice."""
    if not current_user.is_admin:
        abort(403)
    target_user = db.get_or_404(User, user_id)

    if target_user.id == current_user.id:
        flash("Action denied: You cannot ban your own administrative account.", "danger")
        return redirect(url_for("review.manage_users"))

    action = request.form.get("action", "ban").strip().lower()

    if action == "unban":
        target_user.is_banned = False
        target_user.ban_reason = None
        target_user.banned_at = None
        db.session.add(Notification(
            user_id=target_user.id,
            message="Your account suspension has been lifted by administration.",
            link=url_for("submissions.dashboard")
        ))
        db.session.commit()
        flash(f"Account for {target_user.name} ({target_user.email}) has been reinstated.", "success")
    else:
        reason = request.form.get("ban_reason", "").strip() or "Violation of community standards and campus guidelines."
        target_user.is_banned = True
        target_user.ban_reason = reason
        target_user.banned_at = datetime.now(timezone.utc)
        db.session.add(Notification(
            user_id=target_user.id,
            message=f"ACCOUNT SUSPENDED: {reason}",
            link=url_for("auth.login")
        ))
        db.session.commit()
        flash(f"Account for {target_user.name} ({target_user.email}) has been banned. Notice: {reason}", "warning")

    return redirect(url_for("review.manage_users"))


@review_bp.route("/admin/users/<int:user_id>/warn", methods=["POST"])
def warn_user(user_id: int):
    """Admin endpoint to issue an official notice/warning to a student (spam, policy violation, etc.)."""
    if not current_user.is_admin:
        abort(403)
    target_user = db.get_or_404(User, user_id)

    if target_user.id == current_user.id:
        flash("Action denied: You cannot issue an administrative warning to your own account.", "danger")
        return redirect(url_for("review.manage_users"))

    category = request.form.get("category", "Spam / Low Quality").strip()
    notice_text = request.form.get("message", "").strip()

    if not notice_text:
        flash("Warning notice message cannot be empty. Please explain the issue to the student.", "warning")
        return redirect(url_for("review.manage_users"))

    warning = UserWarning(
        user_id=target_user.id,
        admin_id=current_user.id,
        category=category,
        message=notice_text,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(warning)

    # Deliver high-priority notice to student notifications
    db.session.add(Notification(
        user_id=target_user.id,
        message=f"OFFICIAL WARNING [{category}]: {notice_text[:120]}",
        link=url_for("submissions.dashboard")
    ))
    db.session.commit()

    flash(f"Official warning for '{category}' issued to {target_user.name}. Notice has been delivered.", "success")
    return redirect(url_for("review.manage_users"))


@review_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id: int):
    """Admin endpoint to permanently remove an account and clean up associations."""
    if not current_user.is_admin:
        abort(403)
    target_user = db.get_or_404(User, user_id)

    if target_user.id == current_user.id:
        flash("Action denied: You cannot delete your own administrative account.", "danger")
        return redirect(url_for("review.manage_users"))

    user_name = target_user.name
    user_email = target_user.email

    # Safe cascade cleanup
    Upvote.query.filter_by(user_id=target_user.id).delete()
    Comment.query.filter_by(author_id=target_user.id).delete()
    ProjectMember.query.filter_by(user_id=target_user.id).delete()
    JudgeScore.query.filter_by(judge_id=target_user.id).delete()
    Report.query.filter_by(reporter_id=target_user.id).update({"reporter_id": None})
    StatusChange.query.filter_by(actor_id=target_user.id).update({"actor_id": current_user.id})

    # Delete authored submissions & showcase projects
    for proj in ShowcaseProject.query.filter_by(owner_id=target_user.id).all():
        db.session.delete(proj)
    for sub in Submission.query.filter_by(author_id=target_user.id).all():
        db.session.delete(sub)

    # Delete user (UserWarning and Notification cascade automatically)
    db.session.delete(target_user)
    db.session.commit()

    flash(f"Account for {user_name} ({user_email}) and all associated records have been removed.", "info")
    return redirect(url_for("review.manage_users"))
