"""
app/showcase/admin.py
================================================================================
SHOWCASE ADMIN & MODERATION
Management of hackathon events, demo kill switch, featured badges, and reference
library curator controls.
================================================================================
"""

import os
import shutil
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import current_user, login_required
from app.models import (
    db, ShowcaseProject, HackathonEvent, ProjectMember,
    ProjectAsset, DevNote, JudgeScore, Upvote, Comment, StatusChange
)
from app.showcase import showcase_bp
from app.showcase.forms import HackathonEventForm


def require_admin():
    """Ensure current user has administrative permissions."""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash("Administrator access required.", "error")
        abort(403)


@showcase_bp.route("/admin/events")
@login_required
def admin_events():
    """List all hackathon events and project submissions for administrative management."""
    require_admin()
    events = HackathonEvent.query.order_by(HackathonEvent.year.desc(), HackathonEvent.id.desc()).all()
    all_projects = ShowcaseProject.query.order_by(ShowcaseProject.created_at.desc()).all()
    return render_template("showcase/admin_events.html", events=events, all_projects=all_projects)


@showcase_bp.route("/admin/events/new", methods=["GET", "POST"])
@login_required
def admin_event_create():
    """Create a new hackathon event."""
    require_admin()
    form = HackathonEventForm()
    if form.validate_on_submit():
        event = HackathonEvent(
            name=form.name.data.strip(),
            year=form.year.data,
            theme=form.theme.data.strip() if form.theme.data else "",
            organiser=form.organiser.data.strip() if form.organiser.data else "",
            tracks=form.tracks.data.strip() if form.tracks.data else "",
            description=form.description.data.strip() if form.description.data else "",
            is_active=form.is_active.data,
            results_published=form.results_published.data
        )
        db.session.add(event)
        db.session.commit()
        flash(f"Hackathon event '{event.name}' created successfully.", "success")
        return redirect(url_for("showcase.admin_events"))

    return render_template("showcase/admin_events.html", form=form, edit_event=None)


@showcase_bp.route("/admin/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def admin_event_edit(event_id: int):
    """Edit an existing hackathon event."""
    require_admin()
    event = db.get_or_404(HackathonEvent, event_id)
    form = HackathonEventForm(obj=event)

    if form.validate_on_submit():
        form.populate_obj(event)
        db.session.commit()
        flash(f"Event '{event.name}' updated.", "success")
        return redirect(url_for("showcase.admin_events"))

    return render_template("showcase/admin_events.html", form=form, edit_event=event)


@showcase_bp.route("/<int:project_id>/toggle-demo", methods=["POST"])
@login_required
def toggle_demo(project_id: int):
    """Moderator kill switch to disable or re-enable an interactive demo."""
    if not (current_user.is_admin or current_user.is_reviewer):
        abort(403)
    project = db.get_or_404(ShowcaseProject, project_id)
    project.demo_disabled = not project.demo_disabled
    db.session.commit()

    state = "disabled" if project.demo_disabled else "re-enabled"
    flash(f"Interactive demo has been {state}.", "info")
    return redirect(url_for("showcase.detail", project_id=project.id))


@showcase_bp.route("/<int:project_id>/toggle-featured", methods=["POST"])
@login_required
def toggle_featured(project_id: int):
    """Feature or unfeature a project on the showcase homepage."""
    require_admin()
    project = db.get_or_404(ShowcaseProject, project_id)
    project.is_featured = not project.is_featured
    db.session.commit()

    state = "featured" if project.is_featured else "unfeatured"
    flash(f"Project '{project.title}' is now {state}.", "info")
    return redirect(url_for("showcase.detail", project_id=project.id))


@showcase_bp.route("/<int:project_id>/toggle-reference", methods=["POST"])
@login_required
def toggle_reference(project_id: int):
    """Include or exclude project in the Reference Library for future participants."""
    require_admin()
    project = db.get_or_404(ShowcaseProject, project_id)
    project.is_reference = not project.is_reference
    db.session.commit()

    state = "added to" if project.is_reference else "removed from"
    flash(f"Project '{project.title}' {state} the Reference Library.", "info")
    return redirect(url_for("showcase.detail", project_id=project.id))


@showcase_bp.route("/<int:project_id>/status", methods=["POST"])
@login_required
def change_status(project_id: int):
    """Change project status (draft, published, archived)."""
    require_admin()
    project = db.get_or_404(ShowcaseProject, project_id)
    new_status = request.form.get("status")
    if new_status in ("draft", "published", "archived"):
        project.status = new_status
        db.session.commit()
        flash(f"Status changed to {new_status}.", "success")
    return redirect(url_for("showcase.detail", project_id=project.id))


@showcase_bp.route("/<int:project_id>/delete", methods=["POST"])
@showcase_bp.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def admin_project_delete(project_id: int):
    """Permanently delete a hackathon project submission (Admin only)."""
    require_admin()
    project = db.get_or_404(ShowcaseProject, project_id)
    project_title = project.title
    event_id = project.event_id

    # 1. Safely remove physical files on disk
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    if upload_folder:
        for asset in project.assets:
            if asset.file_path:
                full_path = os.path.join(upload_folder, asset.file_path)
                if os.path.isfile(full_path):
                    try:
                        os.remove(full_path)
                    except OSError:
                        pass

        # Remove extracted demos directory for this project if present
        demos_dir = os.path.join(upload_folder, "demos", str(project.id))
        if os.path.isdir(demos_dir):
            try:
                shutil.rmtree(demos_dir, ignore_errors=True)
            except OSError:
                pass

    # 2. Explicitly remove related foreign-key entries to prevent SQLite constraint failures
    try:
        ProjectMember.query.filter_by(project_id=project.id).delete()
        ProjectAsset.query.filter_by(project_id=project.id).delete()
        DevNote.query.filter_by(project_id=project.id).delete()
        JudgeScore.query.filter_by(project_id=project.id).delete()
        Upvote.query.filter_by(showcase_project_id=project.id).delete()
        Comment.query.filter_by(showcase_project_id=project.id).delete()
        StatusChange.query.filter_by(showcase_project_id=project.id).delete()
        db.session.delete(project)
        db.session.commit()
        flash(f"Hackathon submission '{project_title}' has been successfully removed.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing hackathon submission: {str(e)}", "danger")
        return redirect(url_for("showcase.detail", project_id=project_id))

    # 3. Determine safe redirect target
    next_url = request.form.get("next") or request.referrer
    if next_url and ("showcase" in next_url or "admin" in next_url):
        # Don't redirect back to the detail page of the deleted project
        if f"/showcase/{project_id}" not in next_url:
            return redirect(next_url)

    if event_id:
        return redirect(url_for("showcase.event_detail", event_id=event_id))
    return redirect(url_for("showcase.admin_events"))

