"""
app/showcase/judge.py
===============================================================================
SHOWCASE JUDGING WORKSPACE & EVENT LEADERBOARDS
Allows designated judges and faculty to score hackathon submissions against a
6-criteria rubric, provide private/public feedback, and view leaderboards.
===============================================================================
"""

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.models import db, ShowcaseProject, HackathonEvent, JudgeScore
from app.showcase import showcase_bp
from app.showcase.forms import JudgeScoreForm
import site_config


def require_judge():
    """Ensure the current user is a judge or admin."""
    if not current_user.is_authenticated or not (current_user.is_judge or current_user.is_admin):
        flash("Access restricted to judges and administrators.", "error")
        abort(403)


@showcase_bp.route("/judge")
@login_required
def judge_dashboard():
    """Judge overview: pending projects to evaluate and scored projects."""
    require_judge()
    event_id = request.args.get("event", type=int)

    events = HackathonEvent.query.order_by(HackathonEvent.year.desc()).all()
    selected_event = db.session.get(HackathonEvent, event_id) if event_id else (events[0] if events else None)

    projects = []
    my_scores = {}
    if selected_event:
        projects = ShowcaseProject.query.filter_by(
            event_id=selected_event.id,
            status="published"
        ).order_by(ShowcaseProject.created_at.asc()).all()

        scores = JudgeScore.query.filter_by(judge_id=current_user.id).all()
        my_scores = {s.project_id: s for s in scores}

    return render_template(
        "showcase/judge_workspace.html",
        mode="dashboard",
        events=events,
        selected_event=selected_event,
        projects=projects,
        my_scores=my_scores,
        rubric=site_config.SHOWCASE_RUBRIC
    )


@showcase_bp.route("/judge/<int:project_id>", methods=["GET", "POST"])
@login_required
def judge_project(project_id: int):
    """Side-by-side scoring workspace for a specific project."""
    require_judge()
    project = db.get_or_404(ShowcaseProject, project_id)

    # Find existing score by this judge
    score = JudgeScore.query.filter_by(
        project_id=project.id,
        judge_id=current_user.id
    ).first()

    form = JudgeScoreForm(obj=score)

    if form.validate_on_submit():
        if not score:
            score = JudgeScore(
                project_id=project.id,
                judge_id=current_user.id
            )
            db.session.add(score)

        form.populate_obj(score)
        db.session.commit()
        flash(f"Score for '{project.title}' saved! Total: {score.total_score}/60.", "success")
        return redirect(url_for("showcase.judge_dashboard", event=project.event_id))

    # All judges' scores if user is admin, for consensus viewing
    all_scores = JudgeScore.query.filter_by(project_id=project.id).all() if current_user.is_admin else []

    pdf_asset = project.get_asset("presentation_pdf")
    download_build = project.get_asset("build_download")

    return render_template(
        "showcase/judge_workspace.html",
        mode="score",
        project=project,
        form=form,
        score=score,
        all_scores=all_scores,
        rubric=site_config.SHOWCASE_RUBRIC,
        pdf_asset=pdf_asset,
        download_build=download_build
    )


@showcase_bp.route("/event/<int:event_id>")
def event_detail(event_id: int):
    """Hackathon Event landing page with tracks and leaderboard."""
    event = db.get_or_404(HackathonEvent, event_id)
    track_filter = request.args.get("track", "").strip()

    query = ShowcaseProject.query.filter_by(event_id=event.id, status="published")
    if track_filter:
        query = query.filter_by(track=track_filter)

    projects = query.all()

    # Calculate leaderboard if results published or user is judge/admin
    can_view_leaderboard = event.results_published or (
        current_user.is_authenticated and (current_user.is_judge or current_user.is_admin)
    )

    leaderboard = []
    if can_view_leaderboard:
        scored_projects = []
        for p in projects:
            scored_projects.append({
                "project": p,
                "avg_score": p.average_judge_score,
                "total_evaluations": p.judge_count
            })
        scored_projects.sort(key=lambda x: x["avg_score"], reverse=True)
        leaderboard = scored_projects

    return render_template(
        "showcase/event.html",
        event=event,
        projects=projects,
        leaderboard=leaderboard,
        can_view_leaderboard=can_view_leaderboard,
        current_track=track_filter,
        tracks=event.tracks_list
    )
