"""
tests/test_showcase.py
================================================================================
SHOWCASE AUTOMATED TEST SUITE
Tests security isolation, sandboxed iframe headers, zip slip defenses,
file extension filters, external embed allow-lists, markdown sanitization,
judge scoring permissions, and unified browse search.
================================================================================
"""

import io
import os
import zipfile
import pytest
import tempfile
from app import create_app
from app.models import (
    db, User, ShowcaseProject, HackathonEvent, ProjectMember,
    ProjectAsset, DevNote, JudgeScore
)
from app.showcase.services import (
    extract_demo_zip, validate_external_embed, render_markdown_safe, is_safe_zip_path
)
import site_config


@pytest.fixture
def app():
    """Temporary isolated Flask app with SQLite database and temporary upload folder."""
    db_fd, db_path = tempfile.mkstemp()
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "UPLOAD_FOLDER": tempfile.mkdtemp()
    }
    app = create_app(test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def users(app):
    """Creates a student, reviewer, judge, and admin user."""
    with app.app_context():
        student = User(
            name="Test Student", email="student@aitpune.edu.in", role="student"
        )
        student.set_password("Pass123")

        judge = User(
            name="Test Judge", email="judge@aitpune.edu.in", role="judge"
        )
        judge.set_password("Pass123")

        admin = User(
            name="Test Admin", email="admin@aitpune.edu.in", role="admin"
        )
        admin.set_password("Pass123")

        db.session.add_all([student, judge, admin])
        db.session.commit()
        return {"student": student.id, "judge": judge.id, "admin": admin.id}


@pytest.fixture
def sample_event(app):
    with app.app_context():
        event = HackathonEvent(
            name="Test Hackathon 2026",
            year=2026,
            theme="Innovation",
            organiser="Dept of IT",
            tracks="AI, Web3, Campus",
            description="Testing Hackathon",
            is_active=True,
            results_published=True
        )
        db.session.add(event)
        db.session.commit()
        return event.id


# ==============================================================================
# 1. SECURITY: ZIP SLIP & PATH TRAVERSAL DEFENSE
# ==============================================================================
def test_zip_slip_rejection(app, sample_event, users):
    """Ensure zip files containing directory traversal (e.g. ../../) are rejected."""
    with app.app_context():
        project = ShowcaseProject(
            title="Zip Slip Test", pitch="Testing zip slip",
            description="Comprehensive security test for zip-slip vulnerability",
            event_id=sample_event, track="AI", team_name="SecTeam",
            owner_id=users["student"], demo_mode="hosted_webgl"
        )
        db.session.add(project)
        db.session.commit()

        # Build malicious in-memory zip
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("../../malicious.txt", "pwned")
        zip_buf.seek(0)

        # Helper path test
        assert is_safe_zip_path("c:\\safe\\root", "c:\\safe\\root\\index.html") is True
        assert is_safe_zip_path("c:\\safe\\root", "c:\\safe\\root\\..\\escape.txt") is False

        # Service extraction test
        success, msg = extract_demo_zip(project.id, zip_buf)
        assert success is False
        assert "directory traversal" in msg.lower() or "suspicious" in msg.lower()


# ==============================================================================
# 2. SECURITY: DISALLOWED EXTENSIONS IN ZIP
# ==============================================================================
def test_disallowed_zip_extensions(app, sample_event, users):
    """Zip containing executable scripts (like .sh or .py or .exe) must be blocked."""
    with app.app_context():
        project = ShowcaseProject(
            title="Extension Test", pitch="Testing disallowed extensions",
            description="Security test for executable extension filtering",
            event_id=sample_event, track="AI", team_name="SecTeam",
            owner_id=users["student"], demo_mode="hosted_webgl"
        )
        db.session.add(project)
        db.session.commit()

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("index.html", "<h1>Hello</h1>")
            z.writestr("backdoor.py", "import os; os.system('echo bad')")
        zip_buf.seek(0)

        success, msg = extract_demo_zip(project.id, zip_buf)
        assert success is False
        assert "disallowed file type" in msg.lower()


# ==============================================================================
# 3. SUCCESSFUL DEMO ZIP EXTRACTION & ENTRY DETECTION
# ==============================================================================
def test_valid_demo_zip_extraction(app, sample_event, users):
    """Valid zip containing index.html extracts properly and sets relative path."""
    with app.app_context():
        project = ShowcaseProject(
            title="Valid WebGL Test", pitch="Testing valid zip",
            description="Testing standard WebGL zip bundle extraction",
            event_id=sample_event, track="AI", team_name="GameDevs",
            owner_id=users["student"], demo_mode="hosted_webgl"
        )
        db.session.add(project)
        db.session.commit()

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("build/index.html", "<!DOCTYPE html><html><body>Game</body></html>")
            z.writestr("build/game.js", "console.log('running');")
        zip_buf.seek(0)

        success, entry = extract_demo_zip(project.id, zip_buf)
        assert success is True
        assert entry.endswith("index.html")


# ==============================================================================
# 4. EXTERNAL EMBED DOMAIN ALLOW-LIST
# ==============================================================================
def test_external_embed_validation():
    """Validates allowed hosts and blocks unauthorized domains."""
    # Allowed hosts
    ok1, url1, err1 = validate_external_embed("https://huggingface.co/spaces/user/space")
    assert ok1 is True
    assert "huggingface.co" in url1
    assert err1 is None

    # YouTube normalization to youtube-nocookie
    ok2, url2, err2 = validate_external_embed("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert ok2 is True
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in url2
    assert err2 is None

    # Disallowed domain
    ok_bad, url_bad, err_bad = validate_external_embed("https://malicious-tracking-site.com/embed")
    assert ok_bad is False
    assert url_bad is None
    assert "not in the allowed hosts" in err_bad.lower()


# ==============================================================================
# 5. MARKDOWN SANITIZATION WITH BLEACH
# ==============================================================================
def test_markdown_sanitization():
    """Ensures XSS scripts and dangerous event handlers are cleaned."""
    dirty_md = (
        "### Architecture\n"
        "Here is a code block: `print(1)`\n\n"
        "<script>alert('xss')</script>\n"
        "<a href=\"https://google.com\" onclick=\"steal()\">Safe Link</a>"
    )
    cleaned_html = render_markdown_safe(dirty_md)
    assert "<script>" not in cleaned_html
    assert "</script>" not in cleaned_html
    assert "onclick" not in cleaned_html
    assert "<h3>Architecture</h3>" in cleaned_html
    assert "<code>print(1)</code>" in cleaned_html


# ==============================================================================
# 6. SANDBOXED DEMO SERVING & CSP HEADERS
# ==============================================================================
def test_demo_serving_csp_headers(client, app, sample_event, users):
    """Demo route must return strict CSP sandbox and nosniff headers."""
    with app.app_context():
        project = ShowcaseProject(
            title="CSP Header Test", pitch="CSP verification",
            description="Testing Content-Security-Policy headers",
            event_id=sample_event, track="AI", team_name="SecTeam",
            owner_id=users["student"], demo_mode="hosted_webgl", status="published"
        )
        db.session.add(project)
        db.session.flush()

        # Create demo file
        upload_base = app.config["UPLOAD_FOLDER"]
        demo_dir = os.path.join(upload_base, "showcase", str(project.id), "demo")
        os.makedirs(demo_dir, exist_ok=True)
        with open(os.path.join(demo_dir, "index.html"), "w") as f:
            f.write("<h1>Sandboxed Canvas</h1>")

        project.demo_entry_path = f"showcase/{project.id}/demo/index.html"
        db.session.commit()
        project_id = project.id

    res = client.get(f"/showcase/{project_id}/demo/index.html")
    assert res.status_code == 200
    assert "Content-Security-Policy" in res.headers
    assert "sandbox allow-scripts allow-pointer-lock allow-fullscreen" in res.headers["Content-Security-Policy"]
    assert "nosniff" in res.headers.get("X-Content-Type-Options", "")
    assert res.headers.get("Referrer-Policy") == "no-referrer"


# ==============================================================================
# 7. DEMO KILL SWITCH
# ==============================================================================
def test_demo_kill_switch(client, app, sample_event, users):
    """When demo_disabled is True, demo route returns 403."""
    with app.app_context():
        project = ShowcaseProject(
            title="Kill Switch Test", pitch="Kill switch verification",
            description="Testing kill switch route behavior",
            event_id=sample_event, track="AI", team_name="SecTeam",
            owner_id=users["student"], demo_mode="hosted_webgl",
            status="published", demo_disabled=True
        )
        db.session.add(project)
        db.session.flush()

        upload_base = app.config["UPLOAD_FOLDER"]
        demo_dir = os.path.join(upload_base, "showcase", str(project.id), "demo")
        os.makedirs(demo_dir, exist_ok=True)
        with open(os.path.join(demo_dir, "index.html"), "w") as f:
            f.write("<h1>Kill Switch Demo</h1>")

        project.demo_entry_path = f"showcase/{project.id}/demo/index.html"
        db.session.commit()
        project_id = project.id

    res = client.get(f"/showcase/{project_id}/demo/index.html")
    assert res.status_code == 403
    assert b"disabled by a reviewer" in res.data


# ==============================================================================
# 8. JUDGE PERMISSIONS & SCORING
# ==============================================================================
def test_judge_role_access(client, app, sample_event, users):
    """Normal student cannot access judge dashboard (403), while judge can score."""
    # Student login
    client.post("/login", data={"email": "student@aitpune.edu.in", "password": "Pass123"}, follow_redirects=True)
    res_student = client.get("/showcase/judge")
    assert res_student.status_code == 403

    # Judge login
    client.get("/logout", follow_redirects=True)
    client.post("/login", data={"email": "judge@aitpune.edu.in", "password": "Pass123"}, follow_redirects=True)

    res_judge = client.get("/showcase/judge")
    assert res_judge.status_code == 200

    # Score a project
    with app.app_context():
        p = ShowcaseProject(
            title="Scored Project", pitch="Project for scoring",
            description="Description for scoring project",
            event_id=sample_event, track="AI", team_name="ScoredTeam",
            owner_id=users["student"], demo_mode="screenshot", status="published"
        )
        db.session.add(p)
        db.session.commit()
        p_id = p.id

    score_res = client.post(f"/showcase/judge/{p_id}", data={
        "innovation": 9,
        "technical_depth": 8,
        "completeness": 9,
        "design_ux": 8,
        "presentation": 9,
        "impact": 9,
        "private_feedback": "Great build",
        "public_feedback": "Well done team!"
    }, follow_redirects=True)
    assert score_res.status_code == 200

    with app.app_context():
        score = JudgeScore.query.filter_by(project_id=p_id).first()
        assert score is not None
        assert score.total_score == 52
        assert score.innovation == 9


# ==============================================================================
# 9. UNIFIED SEARCH IN /browse
# ==============================================================================
def test_browse_unified_search(client, app, sample_event, users):
    """Searching on /browse returns matching showcase projects."""
    with app.app_context():
        p = ShowcaseProject(
            title="Quantum Cryptography Simulator",
            pitch="Simulation of BB84 protocol for defense communications",
            description="Comprehensive physics simulation of single-photon transmission",
            tech_tags="Quantum, Python, WebGL",
            event_id=sample_event, track="Web3", team_name="QuantumKnights",
            owner_id=users["student"], demo_mode="screenshot", status="published"
        )
        db.session.add(p)
        db.session.commit()

    res = client.get("/browse?q=Quantum")
    assert res.status_code == 200
    assert b"Quantum Cryptography Simulator" in res.data
    assert b"Matching Hackathon Demonstrations" in res.data
