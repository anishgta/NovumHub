"""
app/showcase/wizard.py
================================================================================
SHOWCASE PROJECT SUBMISSION & EDIT WIZARD
A structured, multi-step guide for student teams to submit and update hackathon
projects: Basics -> Demo -> Team -> Assets/Deck -> Dev Notes -> Review & Publish.
================================================================================
"""

import os
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import current_user, login_required
from app.models import db, ShowcaseProject, HackathonEvent, ProjectMember, ProjectAsset, DevNote, Submission, User
from app.showcase import showcase_bp
from app.showcase.forms import (
    ProjectBasicsForm, ProjectDemoForm, ProjectMemberForm,
    ProjectAssetsForm, DevNotesForm
)
from app.showcase.services import extract_demo_zip, save_project_asset, validate_external_embed
import site_config


def check_project_owner(project):
    """Helper to ensure only the owner or an admin/reviewer can edit."""
    if not (project.can_edit(current_user) or current_user.is_admin):
        flash("You do not have permission to edit this project.", "error")
        abort(403)


@showcase_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_project():
    """Step 1: Start a new project submission (Project Basics)."""
    form = ProjectBasicsForm()
    
    # Populate events dropdown (active events first)
    events = HackathonEvent.query.filter_by(is_active=True).all()
    if not events:
        events = HackathonEvent.query.all()
    form.event_id.choices = [(e.id, f"{e.name} ({e.year})") for e in events]

    # Populate optional ideas dropdown from current user's submitted ideas
    user_ideas = Submission.query.filter_by(author_id=current_user.id).all()
    form.linked_submission_id.choices = [(0, "-- None / New Project --")] + [
        (s.id, f"#{s.id}: {s.title[:45]}") for s in user_ideas
    ]

    if form.validate_on_submit():
        linked_id = form.linked_submission_id.data if form.linked_submission_id.data != 0 else None
        project = ShowcaseProject(
            title=form.title.data.strip(),
            pitch=form.pitch.data.strip(),
            description=form.description.data.strip(),
            event_id=form.event_id.data,
            track=form.track.data.strip(),
            team_name=form.team_name.data.strip(),
            tech_tags=form.tech_tags.data.strip() if form.tech_tags.data else "",
            repo_url=form.repo_url.data.strip() if form.repo_url.data else "",
            linked_submission_id=linked_id,
            owner_id=current_user.id,
            demo_mode="screenshot",  # Default placeholder mode
            status="draft"
        )
        db.session.add(project)
        db.session.flush()

        # Add the creator as the first team member automatically
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=current_user.id,
            display_name=current_user.name,
            role="Team Lead / Submitter"
        )
        db.session.add(owner_member)
        db.session.commit()

        flash("Project draft created! Proceed to configure your demo.", "success")
        return redirect(url_for("showcase.step_demo", project_id=project.id))

    return render_template(
        "showcase/form_wizard.html",
        step=1,
        step_name="Basics",
        form=form,
        project=None
    )


@showcase_bp.route("/<int:project_id>/edit")
@login_required
def edit_project(project_id: int):
    """Direct landing for editing an existing project."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)
    return redirect(url_for("showcase.step_basics", project_id=project.id))


@showcase_bp.route("/<int:project_id>/step/basics", methods=["GET", "POST"])
@login_required
def step_basics(project_id: int):
    """Edit Step 1: Basics."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)

    form = ProjectBasicsForm(obj=project)
    events = HackathonEvent.query.all()
    form.event_id.choices = [(e.id, f"{e.name} ({e.year})") for e in events]
    user_ideas = Submission.query.filter_by(author_id=current_user.id).all()
    form.linked_submission_id.choices = [(0, "-- None / New Project --")] + [
        (s.id, f"#{s.id}: {s.title[:45]}") for s in user_ideas
    ]

    if form.validate_on_submit():
        form.populate_obj(project)
        if form.linked_submission_id.data == 0:
            project.linked_submission_id = None
        db.session.commit()
        flash("Project basics updated.", "success")
        return redirect(url_for("showcase.step_demo", project_id=project.id))

    return render_template(
        "showcase/form_wizard.html",
        step=1,
        step_name="Basics",
        form=form,
        project=project
    )


@showcase_bp.route("/<int:project_id>/step/demo", methods=["GET", "POST"])
@login_required
def step_demo(project_id: int):
    """Step 2: Demo configuration (Hosted zip, External embed, Video, Download)."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)

    form = ProjectDemoForm(obj=project)

    if form.validate_on_submit():
        mode = form.demo_mode.data
        project.demo_mode = mode

        # Mode A: Hosted WebGL / HTML5 ZIP
        if mode == "hosted_webgl" and form.demo_zip.data:
            zip_file = form.demo_zip.data
            success, result = extract_demo_zip(project.id, zip_file)
            if not success:
                flash(f"Zip extraction failed: {result}", "error")
                return render_template("showcase/form_wizard.html", step=2, step_name="Demo", form=form, project=project)
            project.demo_entry_path = result
            flash("Hosted interactive demo uploaded & extracted successfully!", "success")

        # Mode B: External Embed URL
        elif mode == "external_embed":
            embed_url = form.demo_external_url.data.strip() if form.demo_external_url.data else ""
            if embed_url:
                is_valid, final_url, err = validate_external_embed(embed_url)
                if not is_valid:
                    flash(f"Embed validation error: {err}", "error")
                    return render_template("showcase/form_wizard.html", step=2, step_name="Demo", form=form, project=project)
                project.demo_external_url = final_url
            else:
                project.demo_external_url = ""

        # Mode C: Video Demo
        elif mode == "video":
            if form.video_url.data:
                project.video_url = form.video_url.data.strip()
            if form.video_file.data:
                save_project_asset(project.id, form.video_file.data, kind="video", title="Video Walkthrough")

        # Mode D: Downloadable Build
        elif mode == "download":
            if form.download_file.data:
                save_project_asset(project.id, form.download_file.data, kind="build_download", title="Downloadable Build")

        db.session.commit()
        flash("Demo configuration saved.", "success")
        return redirect(url_for("showcase.step_team", project_id=project.id))

    return render_template(
        "showcase/form_wizard.html",
        step=2,
        step_name="Demo",
        form=form,
        project=project
    )


@showcase_bp.route("/<int:project_id>/step/team", methods=["GET", "POST"])
@login_required
def step_team(project_id: int):
    """Step 3: Team Members."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)

    form = ProjectMemberForm()
    if form.validate_on_submit():
        user = None
        if form.user_email.data:
            user = User.query.filter_by(email=form.user_email.data.strip().lower()).first()

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id if user else None,
            display_name=form.display_name.data.strip(),
            role=form.role.data.strip() if form.role.data else "Contributor",
            links=form.links.data.strip() if form.links.data else ""
        )
        db.session.add(member)
        db.session.commit()
        flash(f"Added member: {member.display_name}", "success")
        return redirect(url_for("showcase.step_team", project_id=project.id))

    return render_template(
        "showcase/form_wizard.html",
        step=3,
        step_name="Team",
        form=form,
        project=project
    )


@showcase_bp.route("/<int:project_id>/step/team/<int:member_id>/delete", methods=["POST"])
@login_required
def delete_member(project_id: int, member_id: int):
    """Removes a team member."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)
    member = ProjectMember.query.filter_by(id=member_id, project_id=project.id).first_or_404()
    db.session.delete(member)
    db.session.commit()
    flash("Team member removed.", "info")
    return redirect(url_for("showcase.step_team", project_id=project.id))


@showcase_bp.route("/<int:project_id>/step/assets", methods=["GET", "POST"])
@login_required
def step_assets(project_id: int):
    """Step 4: Presentation deck (PDF + source PPTX) and files."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)

    form = ProjectAssetsForm()

    if form.validate_on_submit():
        if form.presentation_pdf.data:
            save_project_asset(project.id, form.presentation_pdf.data, kind="presentation_pdf", title="Presentation Deck (PDF)")
            flash("Uploaded presentation PDF.", "success")

        if form.presentation_source.data:
            save_project_asset(project.id, form.presentation_source.data, kind="presentation_source", title="Presentation Source Slides")
            flash("Uploaded original slides.", "success")

        if form.document_file.data:
            label = form.document_title.data.strip() if form.document_title.data else "Supporting Document"
            save_project_asset(project.id, form.document_file.data, kind="document", title=label)
            flash("Uploaded supporting document.", "success")

        if form.screenshot_file.data:
            cap = form.screenshot_caption.data.strip() if form.screenshot_caption.data else "Project Screenshot"
            save_project_asset(project.id, form.screenshot_file.data, kind="screenshot", title=cap)
            flash("Uploaded screenshot.", "success")

        return redirect(url_for("showcase.step_assets", project_id=project.id))

    return render_template(
        "showcase/form_wizard.html",
        step=4,
        step_name="Assets",
        form=form,
        project=project
    )


@showcase_bp.route("/<int:project_id>/step/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
def delete_asset(project_id: int, asset_id: int):
    """Deletes an asset from disk and database."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)
    asset = ProjectAsset.query.filter_by(id=asset_id, project_id=project.id).first_or_404()

    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], asset.file_path)
    if os.path.isfile(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass

    db.session.delete(asset)
    db.session.commit()
    flash("Asset removed.", "info")
    return redirect(url_for("showcase.step_assets", project_id=project.id))


@showcase_bp.route("/<int:project_id>/step/devnotes", methods=["GET", "POST"])
@login_required
def step_devnotes(project_id: int):
    """Step 5: Structured Developer Notes (8 sections)."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)

    form = DevNotesForm()

    # Pre-populate existing notes
    if request.method == "GET":
        for note in project.dev_notes:
            if hasattr(form, note.section_key):
                getattr(form, note.section_key).data = note.body_markdown

    if form.validate_on_submit():
        for key in site_config.SHOWCASE_DEVNOTE_SECTIONS.keys():
            val = getattr(form, key).data
            note = DevNote.query.filter_by(project_id=project.id, section_key=key).first()
            if not note:
                note = DevNote(project_id=project.id, section_key=key, body_markdown=val or "")
                db.session.add(note)
            else:
                note.body_markdown = val or ""

        db.session.commit()
        flash("Developer notes saved.", "success")
        return redirect(url_for("showcase.step_review", project_id=project.id))

    return render_template(
        "showcase/form_wizard.html",
        step=5,
        step_name="Dev Notes",
        form=form,
        project=project,
        sections=site_config.SHOWCASE_DEVNOTE_SECTIONS
    )


@showcase_bp.route("/<int:project_id>/step/review", methods=["GET", "POST"])
@login_required
def step_review(project_id: int):
    """Step 6: Final check and publish."""
    project = db.get_or_404(ShowcaseProject, project_id)
    check_project_owner(project)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "publish":
            project.status = "published"
            db.session.commit()
            flash("Congratulations! Your project is now published in the Showcase.", "success")
            return redirect(url_for("showcase.detail", project_id=project.id))
        elif action == "draft":
            project.status = "draft"
            db.session.commit()
            flash("Project saved as draft.", "info")
            return redirect(url_for("showcase.detail", project_id=project.id))

    return render_template(
        "showcase/form_wizard.html",
        step=6,
        step_name="Review & Publish",
        project=project
    )
