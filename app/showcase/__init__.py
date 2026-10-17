"""
app/showcase/__init__.py
================================================================================
SHOWCASE BLUEPRINT
Top-level section for hackathon project demonstrations, interactive WebGL/HTML5
builds, presentation decks, developer notes, and judging evaluations.
================================================================================
"""

from flask import Blueprint

# Initialize Showcase blueprint with URL prefix /showcase
showcase_bp = Blueprint("showcase", __name__, url_prefix="/showcase")

# Import route handlers to register endpoints
from app.showcase import routes
from app.showcase import wizard
from app.showcase import judge
from app.showcase import admin
