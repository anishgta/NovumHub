"""
app/main.py
================================================================================
MAIN BLUEPRINT
Handles public, informative pages: Home, Public Stats, and About/Guidelines.
================================================================================
"""

import os
import json
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, current_app, url_for
from sqlalchemy import func
from app import csrf
from app.models import db, Submission, User, ShowcaseProject, HackathonEvent, JudgeScore
import site_config

main_bp = Blueprint("main", __name__)


# ==============================================================================
# HOMEPAGE ROUTE (/)
# ==============================================================================
@main_bp.route("/")
def home():
    """
    Renders the main landing page with hero banner, 4 category cards,
    recent accepted contributions, latest showcase projects, and how-it-works overview.
    """
    # Fetch recent accepted or implemented submissions for the showcase
    recent_submissions = (
        Submission.query.filter(Submission.status.in_(site_config.PUBLIC_STATUSES))
        .order_by(Submission.created_at.desc())
        .limit(6)
        .all()
    )

    # Fetch recent published hackathon showcase projects
    showcase_projects = (
        ShowcaseProject.query.filter(ShowcaseProject.status.in_(site_config.SHOWCASE_PUBLIC_STATUSES))
        .order_by(ShowcaseProject.created_at.desc())
        .limit(4)
        .all()
    )

    # Quick overview metrics
    total_accepted = Submission.query.filter_by(status="Accepted").count()
    total_implemented = Submission.query.filter_by(status="Implemented").count()
    total_contributors = db.session.query(func.count(func.distinct(Submission.author_id))).scalar() or 0

    # Check for active custom 3D header model
    models_dir = os.path.join(current_app.static_folder, "models")
    model_info_path = os.path.join(models_dir, "model_info.json")
    header_model_info = None
    if os.path.exists(model_info_path):
        try:
            with open(model_info_path, "r", encoding="utf-8") as f:
                header_model_info = json.load(f)
        except Exception:
            header_model_info = None

    return render_template(
        "home.html",
        recent_submissions=recent_submissions,
        showcase_projects=showcase_projects,
        total_accepted=total_accepted,
        total_implemented=total_implemented,
        total_contributors=total_contributors,
        header_model_info=header_model_info
    )


# ==============================================================================
# 3D MODEL API (Header 3D Model Upload & Info)
# ==============================================================================
ALLOWED_3D_EXTENSIONS = {".glb", ".gltf"}

@main_bp.route("/api/header-model-info", methods=["GET"])
def get_header_model_info():
    """Returns metadata for the currently active 3D header model."""
    models_dir = os.path.join(current_app.static_folder, "models")
    model_info_path = os.path.join(models_dir, "model_info.json")
    model_file_path = os.path.join(models_dir, "active_header_model.glb")

    if os.path.exists(model_file_path) and os.path.exists(model_info_path):
        try:
            with open(model_info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
                info["active"] = True
                return jsonify(info)
        except Exception as e:
            return jsonify({"active": False, "error": str(e)})

    return jsonify({"active": False, "filename": "default_origami_model"})


@main_bp.route("/api/upload-header-model", methods=["POST"])
@csrf.exempt
def upload_header_model():
    """
    Accepts an uploaded .glb or .gltf file and saves it as the active 3D header model.
    """
    if "model_file" not in request.files:
        return jsonify({"success": False, "error": "No model file provided"}), 400

    file = request.files["model_file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Empty file uploaded"}), 400

    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_3D_EXTENSIONS:
        return jsonify({
            "success": False,
            "error": f"Invalid format '{ext}'. Only .glb and .gltf 3D models are supported."
        }), 400

    models_dir = os.path.join(current_app.static_folder, "models")
    os.makedirs(models_dir, exist_ok=True)

    dest_filename = f"active_header_model{ext}"
    dest_path = os.path.join(models_dir, dest_filename)
    file.save(dest_path)
    file_size = os.path.getsize(dest_path)

    original_name = secure_filename(file.filename) or f"custom_model{ext}"
    model_info = {
        "active": True,
        "filename": original_name,
        "stored_file": dest_filename,
        "url": url_for("static", filename=f"models/{dest_filename}"),
        "size_bytes": file_size,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }

    model_info_path = os.path.join(models_dir, "model_info.json")
    with open(model_info_path, "w", encoding="utf-8") as f:
        json.dump(model_info, f, indent=2)

    return jsonify({
        "success": True,
        "message": f"Successfully activated 3D model '{original_name}'!",
        "model": model_info
    })


@main_bp.route("/api/reset-header-model", methods=["POST"])
@csrf.exempt
def reset_header_model():
    """Resets the header model back to the default procedural 3D model."""
    models_dir = os.path.join(current_app.static_folder, "models")
    for f in ["active_header_model.glb", "active_header_model.gltf", "model_info.json"]:
        p = os.path.join(models_dir, f)
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

    return jsonify({
        "success": True,
        "message": "Reset to default origami 3D model."
    })


# ==============================================================================
# PUBLIC STATISTICS ROUTE (/stats)
# ==============================================================================
@main_bp.route("/stats")
def stats():
    """
    Displays aggregated campus metrics: counts per category,
    progress bars, and top-upvoted submissions.
    """
    total_submissions = Submission.query.count()

    # Category counts
    category_counts = {}
    for cat_key, cat_info in site_config.CATEGORIES.items():
        count = Submission.query.filter_by(category=cat_key).count()
        category_counts[cat_key] = {
            "name": cat_info["name"],
            "icon": cat_info["icon"],
            "count": count,
            "percentage": round((count / total_submissions * 100) if total_submissions > 0 else 0)
        }

    # Status counts
    status_counts = {}
    for status_key, status_info in site_config.STATUSES.items():
        count = Submission.query.filter_by(status=status_key).count()
        status_counts[status_key] = {
            "label": status_info["label"],
            "count": count,
            "percentage": round((count / total_submissions * 100) if total_submissions > 0 else 0)
        }

    # Top upvoted contributions (Accepted or Implemented)
    all_public = Submission.query.filter(Submission.status.in_(site_config.PUBLIC_STATUSES)).all()
    top_submissions = sorted(all_public, key=lambda s: s.upvote_count, reverse=True)[:5]

    # Showcase metrics
    total_showcase_projects = ShowcaseProject.query.filter_by(status="published").count()
    total_judge_scores = JudgeScore.query.count()
    total_reference_projects = ShowcaseProject.query.filter_by(is_reference=True, status="published").count()

    return render_template(
        "main/stats.html",
        total_submissions=total_submissions,
        category_counts=category_counts,
        status_counts=status_counts,
        top_submissions=top_submissions,
        total_showcase_projects=total_showcase_projects,
        total_judge_scores=total_judge_scores,
        total_reference_projects=total_reference_projects
    )


# ==============================================================================
# ABOUT & SUBMISSION GUIDELINES ROUTE (/about)
# ==============================================================================
@main_bp.route("/about")
def about():
    """
    Detailed about page explaining the purpose of Hackrec, submission guidelines,
    peer review process, and contact info.
    """
    return render_template("main/about.html")
