"""
app/showcase/routes.py
================================================================================
SHOWCASE PUBLIC ROUTES & DEMO SERVING
Handles showcase listing, search, project tabs, sandboxed demo delivery with
strict CSP headers, asset downloads, engagement, and the Reference Library.
================================================================================
"""

import os
import mimetypes
from flask import (
    render_template, redirect, url_for, flash, request, abort,
    send_file, current_app, jsonify
)
from flask_login import current_user, login_required
from app.models import (
    db, ShowcaseProject, HackathonEvent, ProjectAsset,
    Upvote, Comment, Report, Notification
)
from app.showcase import showcase_bp
from app.showcase.services import render_markdown_safe, validate_external_embed
import site_config


@showcase_bp.route("/")
def home():
    """Showcase homepage with filters, event chips, and featured projects."""
    event_id = request.args.get("event", type=int)
    year = request.args.get("year", type=int)
    track = request.args.get("track", "").strip()
    tag = request.args.get("tag", "").strip()
    demo_mode = request.args.get("demo_mode", "").strip()
    reference_only = request.args.get("reference", type=int)
    sort_by = request.args.get("sort", "newest")
    page = request.args.get("page", 1, type=int)

    query = ShowcaseProject.query.filter(ShowcaseProject.status.in_(site_config.SHOWCASE_PUBLIC_STATUSES))

    if event_id:
        query = query.filter_by(event_id=event_id)
    if track:
        query = query.filter(ShowcaseProject.track.ilike(f"%{track}%"))
    if tag:
        query = query.filter(ShowcaseProject.tech_tags.ilike(f"%{tag}%"))
    if demo_mode:
        query = query.filter_by(demo_mode=demo_mode)
    if reference_only:
        query = query.filter_by(is_reference=True)
    if year:
        query = query.join(HackathonEvent).filter(HackathonEvent.year == year)

    if sort_by == "upvotes":
        # Sort in Python or by upvote count
        projects = query.all()
        projects.sort(key=lambda p: p.upvote_count, reverse=True)
        total = len(projects)
        paginated_projects = projects[(page - 1) * site_config.ITEMS_PER_PAGE : page * site_config.ITEMS_PER_PAGE]
    else:
        query = query.order_by(ShowcaseProject.created_at.desc())
        total = query.count()
        paginated_projects = query.offset((page - 1) * site_config.ITEMS_PER_PAGE).limit(site_config.ITEMS_PER_PAGE).all()

    # Featured row
    featured_projects = ShowcaseProject.query.filter(
        ShowcaseProject.status.in_(site_config.SHOWCASE_PUBLIC_STATUSES),
        ShowcaseProject.is_featured == True
    ).limit(3).all()

    events = HackathonEvent.query.order_by(HackathonEvent.year.desc(), HackathonEvent.id.desc()).all()

    return render_template(
        "showcase/home.html",
        projects=paginated_projects,
        featured_projects=featured_projects,
        events=events,
        current_event_id=event_id,
        current_track=track,
        current_tag=tag,
        current_demo=demo_mode,
        reference_only=reference_only,
        sort_by=sort_by,
        page=page,
        total_projects=total,
        total_pages=(total + site_config.ITEMS_PER_PAGE - 1) // site_config.ITEMS_PER_PAGE
    )


@showcase_bp.route("/<int:project_id>")
def detail(project_id: int):
    """Detailed view for a showcase project with in-page tabs."""
    project = db.get_or_404(ShowcaseProject, project_id)

    # Only owner, reviewers, or admins can view non-public projects
    if project.status not in site_config.SHOWCASE_PUBLIC_STATUSES:
        can_view = current_user.is_authenticated and (
            project.can_edit(current_user) or current_user.is_reviewer or current_user.is_judge
        )
        if not can_view:
            abort(404)

    # Pre-render markdown notes safely
    rendered_notes = {}
    for note in project.dev_notes:
        rendered_notes[note.section_key] = render_markdown_safe(note.body_markdown)

    # Get active tab from URL hash/query
    active_tab = request.args.get("tab", "demo")

    # Presentation deck assets
    pdf_asset = project.get_asset("presentation_pdf")
    source_deck = project.get_asset("presentation_source")
    download_build = project.get_asset("build_download")
    documents = project.get_assets_by_kind("document")
    screenshots = project.get_assets_by_kind("screenshot")
    videos = project.get_assets_by_kind("video")

    return render_template(
        "showcase/detail.html",
        project=project,
        active_tab=active_tab,
        rendered_notes=rendered_notes,
        pdf_asset=pdf_asset,
        source_deck=source_deck,
        download_build=download_build,
        documents=documents,
        screenshots=screenshots,
        videos=videos,
        rubric=site_config.SHOWCASE_RUBRIC
    )


@showcase_bp.route("/<int:project_id>/demo/<path:filename>")
def serve_demo(project_id: int, filename: str):
    """
    Dedicated sandboxed demo route serving interactive WebGL / HTML5 builds.
    Strictly isolated with Content-Security-Policy sandbox and nosniff headers.
    """
    project = db.get_or_404(ShowcaseProject, project_id)

    if project.demo_disabled:
        return "Interactive demo has been disabled by a reviewer.", 403

    if not project.demo_entry_path:
        abort(404)

    base_dir = current_app.config["UPLOAD_FOLDER"]
    demo_root = os.path.dirname(os.path.join(base_dir, project.demo_entry_path))
    file_path = os.path.normpath(os.path.join(demo_root, filename))

    # Path traversal protection
    if not file_path.startswith(os.path.normpath(demo_root)) or not os.path.isfile(file_path):
        abort(404)

    # Content-Type mapping
    mime_type, encoding = mimetypes.guess_type(file_path)
    if file_path.endswith(".wasm"):
        mime_type = "application/wasm"
    elif file_path.endswith(".data"):
        mime_type = "application/octet-stream"
    elif file_path.endswith(".unityweb"):
        mime_type = "application/octet-stream"

    response = send_file(file_path, mimetype=mime_type or "application/octet-stream")

    # Handle Unity WebGL compression headers (.br or .gz)
    if file_path.endswith(".br") or file_path.endswith(".unityweb") and ".br." in file_path:
        response.headers["Content-Encoding"] = "br"
    elif file_path.endswith(".gz") or file_path.endswith(".unityweb") and ".gz." in file_path:
        response.headers["Content-Encoding"] = "gzip"

    # STRICT ISOLATION HEADERS: No cookies, no parent page access, no forms to main site
    response.headers["Content-Security-Policy"] = "sandbox allow-scripts allow-pointer-lock allow-fullscreen;"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@showcase_bp.route("/assets/<int:asset_id>/download")
def download_asset(asset_id: int):
    """Secure asset download route with proper Content-Disposition."""
    asset = db.get_or_404(ProjectAsset, asset_id)
    base_dir = current_app.config["UPLOAD_FOLDER"]
    full_path = os.path.normpath(os.path.join(base_dir, asset.file_path))

    if not os.path.isfile(full_path):
        abort(404)

    # Preview inline for PDFs and screenshots; force download for builds/sources
    is_inline = asset.kind in ("presentation_pdf", "screenshot")
    return send_file(
        full_path,
        as_attachment=not is_inline,
        download_name=asset.title or os.path.basename(full_path)
    )


@showcase_bp.route("/library")
def library():
    """Reference Library view with technical snippets for future participants."""
    tag = request.args.get("tag", "").strip()
    query = ShowcaseProject.query.filter(
        ShowcaseProject.status.in_(site_config.SHOWCASE_PUBLIC_STATUSES),
        ShowcaseProject.is_reference == True
    )

    if tag:
        query = query.filter(ShowcaseProject.tech_tags.ilike(f"%{tag}%"))

    projects = query.order_by(ShowcaseProject.created_at.desc()).all()
    all_published = ShowcaseProject.query.filter(ShowcaseProject.status.in_(site_config.SHOWCASE_PUBLIC_STATUSES)).all()

    # Extract popular tags
    tags_count = {}
    for p in all_published:
        if p.tech_tags:
            for t in p.tech_tags.split(","):
                t_clean = t.strip()
                if t_clean:
                    tags_count[t_clean] = tags_count.get(t_clean, 0) + 1

    sorted_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:15]

    return render_template(
        "showcase/library.html",
        projects=projects,
        current_tag=tag,
        popular_tags=sorted_tags
    )


@showcase_bp.route("/<int:project_id>/upvote", methods=["POST"])
@login_required
def upvote(project_id: int):
    """Toggles community upvote on a showcase project (AJAX & Form)."""
    project = db.get_or_404(ShowcaseProject, project_id)
    existing = Upvote.query.filter_by(showcase_project_id=project.id, user_id=current_user.id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        upvoted = False
    else:
        new_vote = Upvote(showcase_project_id=project.id, user_id=current_user.id)
        db.session.add(new_vote)
        db.session.commit()
        upvoted = True

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "upvoted": upvoted, "upvote_count": project.upvote_count})

    flash("Vote updated!" if upvoted else "Vote removed.", "info")
    return redirect(url_for("showcase.detail", project_id=project.id, tab="discussion"))


@showcase_bp.route("/<int:project_id>/comment", methods=["POST"])
@login_required
def comment(project_id: int):
    """Adds a constructive discussion comment to a showcase project."""
    project = db.get_or_404(ShowcaseProject, project_id)
    body = request.form.get("body", "").strip()

    if not body:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("showcase.detail", project_id=project.id, tab="discussion"))

    new_comment = Comment(
        showcase_project_id=project.id,
        author_id=current_user.id,
        body=body
    )
    db.session.add(new_comment)

    # Notify project owner if someone else comments
    if project.owner_id != current_user.id:
        notif = Notification(
            user_id=project.owner_id,
            message=f"{current_user.name} commented on your showcase project '{project.title}'",
            link=url_for("showcase.detail", project_id=project.id, tab="discussion")
        )
        db.session.add(notif)

    db.session.commit()
    flash("Your comment has been posted.", "success")
    return redirect(url_for("showcase.detail", project_id=project.id, tab="discussion"))


@showcase_bp.route("/<int:project_id>/report", methods=["POST"])
def report(project_id: int):
    """Reports a showcase project to moderators."""
    project = db.get_or_404(ShowcaseProject, project_id)
    reason = request.form.get("reason", "").strip()

    if not reason:
        flash("Please provide a reason for reporting.", "error")
        return redirect(url_for("showcase.detail", project_id=project.id))

    new_report = Report(
        target_type="showcase_project",
        target_id=project.id,
        reporter_id=current_user.id if current_user.is_authenticated else None,
        reason=reason
    )
    db.session.add(new_report)
    db.session.commit()
    flash("Thank you. This project has been submitted for moderation review.", "info")
    return redirect(url_for("showcase.detail", project_id=project.id))
