"""
tests/test_hackrec.py
================================================================================
AUTOMATED TEST SUITE FOR HACKREC
Tests core features:
1. Student registration & secure authentication
2. Submission creation & category validations
3. Status timeline audit trail creation
4. Upvote toggling & database uniqueness constraint
5. Role-based access control (Student blocked from Reviewer queue)
6. Reviewer triage workflow & student notification generation
7. Public feed visibility filtering (only Accepted/Implemented visible)
8. Author edit and withdraw permissions
================================================================================
"""

import pytest
import os
import tempfile
from app import create_app
from app.models import db, User, Submission, StatusChange, Upvote, Notification
import site_config


@pytest.fixture
def app():
    """Creates a temporary isolated test app with SQLite in-memory database."""
    db_fd, db_path = tempfile.mkstemp()
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF in automated testing for direct POSTs
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
    """Test client for simulating HTTP browser requests."""
    return app.test_client()


@pytest.fixture
def student_user(app):
    """Creates a standard student user for tests."""
    with app.app_context():
        user = User(
            name="Test Student",
            email="student@aitpune.edu.in",
            role="student",
            department="Computer Engineering",
            year="Second Year (SE)"
        )
        user.set_password("secretpass123")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def reviewer_user(app):
    """Creates a faculty reviewer user for tests."""
    with app.app_context():
        user = User(
            name="Test Reviewer",
            email="reviewer@aitpune.edu.in",
            role="reviewer",
            department="Information Technology",
            year="Faculty / Staff"
        )
        user.set_password("secretpass123")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def admin_user(app):
    """Creates an administrator user for tests."""
    with app.app_context():
        user = User(
            name="Test Admin",
            email="admin@aitpune.edu.in",
            role="admin",
            department="Computer Engineering",
            year="Faculty / Staff"
        )
        user.set_password("adminpassword123")
        db.session.add(user)
        db.session.commit()
        return user.id


# ==============================================================================
# 1. AUTHENTICATION & REGISTRATION TESTS
# ==============================================================================
def test_registration_and_login(client, app):
    """Verify that a student can register and subsequently log in."""
    # 1. Register
    response = client.post("/register", data={
        "name": "Priya Sharma",
        "email": "priya.sharma@aitpune.edu.in",
        "department": "Computer Engineering",
        "year": "First Year (FE)",
        "registration_no": "241001",
        "password": "mypassword123",
        "confirm_password": "mypassword123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to NovumHub" in response.data or b"Welcome to Hackrec" in response.data or b"Priya" in response.data

    with app.app_context():
        user = User.query.filter_by(email="priya.sharma@aitpune.edu.in").first()
        assert user is not None
        assert user.check_password("mypassword123") is True
        assert user.check_password("wrongpass") is False
        assert user.role == "student"

    # 2. Log out
    client.get("/logout", follow_redirects=True)

    # 3. Log back in
    login_resp = client.post("/login", data={
        "email": "priya.sharma@aitpune.edu.in",
        "password": "mypassword123"
    }, follow_redirects=True)

    assert login_resp.status_code == 200
    assert b"Welcome back" in login_resp.data


def test_login_invalid_credentials(client):
    """Verify friendly error message on incorrect password."""
    response = client.post("/login", data={
        "email": "nonexistent@aitpune.edu.in",
        "password": "wrongpassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid email address or password" in response.data


# ==============================================================================
# 2. SUBMISSION CREATION & TIMELINE TESTS
# ==============================================================================
def test_submission_creation_and_timeline(client, app, student_user):
    """Verify submission creation and automatic timeline recording."""
    with app.app_context():
        user = db.session.get(User, student_user)

    # Log in as student
    client.post("/login", data={"email": user.email, "password": "secretpass123"})

    response = client.post("/submit", data={
        "category": "idea",
        "title": "Smart Campus Waste Sorter",
        "summary": "AI powered bin sorting plastic vs paper on campus.",
        "details": "We built an optical classification model for waste sorting at AIT canteen.",
        "tags": "ai, waste, green-campus",
        "idea_impact": "Reduces plastic pollution and improves campus cleanliness.",
        "idea_resources": "2 webcams and a Raspberry Pi."
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        sub = Submission.query.filter_by(title="Smart Campus Waste Sorter").first()
        assert sub is not None
        assert sub.status == "Submitted"
        assert sub.author_id == student_user
        assert sub.extra_fields.get("expected_impact") == "Reduces plastic pollution and improves campus cleanliness."

        # Verify initial status history timeline record was created automatically
        assert len(sub.status_history) == 1
        assert sub.status_history[0].to_status == "Submitted"
        assert sub.status_history[0].actor_id == student_user


def test_category_validation_correction_requires_evidence(client, app, student_user):
    """Verify research corrections require citation/evidence."""
    with app.app_context():
        user = db.session.get(User, student_user)

    client.post("/login", data={"email": user.email, "password": "secretpass123"})

    # Missing evidence field should trigger validation error
    response = client.post("/submit", data={
        "category": "correction",
        "title": "Data Structures Formula Error",
        "summary": "Correction to heap delete formula.",
        "details": "Details about heap delete formula in textbook.",
        "correction_item": "Lab manual page 10",
        "correction_wrong": "Said O(1)",
        "correction_correct": "Should be O(log n)",
        "correction_evidence": ""  # EMPTY EVIDENCE
    })

    assert response.status_code == 200
    assert b"Evidence or citation is required" in response.data


# ==============================================================================
# 3. UPVOTE UNIQUENESS & TOGGLE TESTS
# ==============================================================================
def test_upvote_toggle_and_uniqueness(client, app, student_user):
    """Verify upvote toggle (1 -> 0 -> 1) and database uniqueness."""
    with app.app_context():
        user = db.session.get(User, student_user)
        user_email = user.email
        sub = Submission(
            author_id=user.id,
            category="idea",
            title="AIT Robotics Lab Upgrade",
            summary="New motors and ESC controllers.",
            details="Detailed proposal for modernizing club robotics kits.",
            status="Accepted"
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

    # Log in as user
    client.post("/login", data={"email": user_email, "password": "secretpass123"})

    # 1. First upvote -> Should add upvote
    resp1 = client.post(f"/submissions/{sub_id}/upvote")
    data1 = resp1.get_json()
    assert data1["success"] is True
    assert data1["upvoted"] is True
    assert data1["upvote_count"] == 1

    # 2. Second upvote -> Should remove upvote (toggle off)
    resp2 = client.post(f"/submissions/{sub_id}/upvote")
    data2 = resp2.get_json()
    assert data2["success"] is True
    assert data2["upvoted"] is False
    assert data2["upvote_count"] == 0

    # 3. Third upvote -> Should add upvote again
    resp3 = client.post(f"/submissions/{sub_id}/upvote")
    data3 = resp3.get_json()
    assert data3["success"] is True
    assert data3["upvoted"] is True
    assert data3["upvote_count"] == 1

    with app.app_context():
        assert Upvote.query.filter_by(submission_id=sub_id, user_id=student_user).count() == 1


# ==============================================================================
# 4. PERMISSION CHECKS (ROLE-BASED ACCESS CONTROL)
# ==============================================================================
def test_student_cannot_access_review_pages(client, app, student_user):
    """Verify that a regular student cannot access faculty triage queue (HTTP 403)."""
    with app.app_context():
        user = db.session.get(User, student_user)
        user_email = user.email

    client.post("/login", data={"email": user_email, "password": "secretpass123"})

    # Try accessing review queue
    response = client.get("/review")
    assert response.status_code == 403
    assert b"Access Denied" in response.data or b"403" in response.data


def test_reviewer_can_access_review_queue(client, app, reviewer_user):
    """Verify that a reviewer can access triage queue."""
    with app.app_context():
        reviewer = db.session.get(User, reviewer_user)
        reviewer_email = reviewer.email

    client.post("/login", data={"email": reviewer_email, "password": "secretpass123"})

    response = client.get("/review")
    assert response.status_code == 200
    assert b"Faculty &amp; Admin Triage Queue" in response.data or b"Triage Queue" in response.data


# ==============================================================================
# 5. REVIEWER TRIAGE & NOTIFICATIONS WORKFLOW
# ==============================================================================
def test_reviewer_status_transition_and_notification(client, app, student_user, reviewer_user):
    """Verify reviewer can accept a submission and student gets notified."""
    with app.app_context():
        student = db.session.get(User, student_user)
        reviewer = db.session.get(User, reviewer_user)
        reviewer_email = reviewer.email

        sub = Submission(
            author_id=student.id,
            category="infrastructure",
            title="Water Cooler Filter Replacement in Library",
            summary="Filter cartridge is overdue for replacement.",
            details="Drinking water TDS level is elevated; needs new carbon block filter.",
            status="Submitted"
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

    # Log in as reviewer
    client.post("/login", data={"email": reviewer_email, "password": "secretpass123"})

    # Change status to Accepted
    response = client.post(f"/review/{sub_id}", data={
        "to_status": "Accepted",
        "public_comment": "Approved. Campus estate office has ordered replacement filters.",
        "internal_note": "Budget code #412 charged."
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        updated_sub = db.session.get(Submission, sub_id)
        assert updated_sub.status == "Accepted"

        # Check status timeline history
        latest_change = updated_sub.status_history[-1]
        assert latest_change.from_status == "Submitted"
        assert latest_change.to_status == "Accepted"
        assert "Approved" in latest_change.public_comment
        assert latest_change.internal_note == "Budget code #412 charged."

        # Verify student submitter received an in-site notification!
        notif = Notification.query.filter_by(user_id=student_user).first()
        assert notif is not None
        assert "Accepted" in notif.message


# ==============================================================================
# 6. PUBLIC FEED VISIBILITY TEST
# ==============================================================================
def test_public_feed_shows_only_accepted_and_implemented(client, app, student_user):
    """Verify that only Accepted and Implemented submissions appear on public feed."""
    with app.app_context():
        user = db.session.get(User, student_user)

        sub_submitted = Submission(
            author_id=user.id, category="idea", title="Pending Idea Test",
            summary="A test summary", details="A test detail", status="Submitted"
        )
        sub_accepted = Submission(
            author_id=user.id, category="idea", title="Accepted Idea Test",
            summary="A test summary", details="A test detail", status="Accepted"
        )
        sub_implemented = Submission(
            author_id=user.id, category="idea", title="Implemented Idea Test",
            summary="A test summary", details="A test detail", status="Implemented"
        )
        db.session.add_all([sub_submitted, sub_accepted, sub_implemented])
        db.session.commit()

    # Anonymous visitor checks public feed
    resp = client.get("/browse")
    assert resp.status_code == 200
    assert b"Accepted Idea Test" in resp.data
    assert b"Implemented Idea Test" in resp.data
    assert b"Pending Idea Test" not in resp.data


# ==============================================================================
# 7. NOVUMHUB REGISTRATION ROLES, DOMAIN RESTRICTION, REG NO & OTP TESTS
# ==============================================================================
def test_registration_roles_staff_and_alumni(client, app):
    """Verify that selecting Faculty / Staff assigns role 'staff' and Alumni assigns role 'alumni'."""
    # Register Faculty/Staff
    resp1 = client.post("/register", data={
        "name": "Prof. Arvind Rao",
        "email": "arvind.rao@aitpune.edu.in",
        "department": "Computer Engineering",
        "year": "Faculty / Staff",
        "registration_no": "990001",
        "password": "facultyPassword1",
        "confirm_password": "facultyPassword1"
    }, follow_redirects=True)
    assert resp1.status_code == 200

    with app.app_context():
        staff_user = User.query.filter_by(email="arvind.rao@aitpune.edu.in").first()
        assert staff_user is not None
        assert staff_user.role == "staff"
        assert staff_user.is_staff is True

    # Register Alumni
    client.get("/logout", follow_redirects=True)
    resp2 = client.post("/register", data={
        "name": "Vikram Seth (Alumni)",
        "email": "vikram.seth@aitpune.edu.in",
        "department": "Mechanical Engineering",
        "year": "Alumni",
        "registration_no": "180042",
        "password": "alumniPassword1",
        "confirm_password": "alumniPassword1"
    }, follow_redirects=True)
    assert resp2.status_code == 200

    with app.app_context():
        alumni_user = User.query.filter_by(email="vikram.seth@aitpune.edu.in").first()
        assert alumni_user is not None
        assert alumni_user.role == "alumni"
        assert alumni_user.is_alumni is True


def test_registration_email_domain_restriction(client, app):
    """Verify that non-@aitpune.edu.in email addresses are strictly rejected during registration."""
    # Attempt registration with @gmail.com
    resp = client.post("/register", data={
        "name": "External User",
        "email": "external.user@gmail.com",
        "department": "Computer Engineering",
        "year": "First Year (FE)",
        "registration_no": "241099",
        "password": "somepassword123",
        "confirm_password": "somepassword123"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"aitpune.edu.in" in resp.data
    with app.app_context():
        assert User.query.filter_by(email="external.user@gmail.com").first() is None


def test_registration_number_validation_and_privacy(client, app, admin_user, student_user):
    """Verify 6-digit validation and that registration numbers are only visible to admin and author."""
    # 1. Invalid registration number (not 6 digits)
    resp_invalid = client.post("/register", data={
        "name": "Bad Reg User",
        "email": "badreg@aitpune.edu.in",
        "department": "Computer Engineering",
        "year": "First Year (FE)",
        "registration_no": "12345",  # only 5 digits
        "password": "somepassword123",
        "confirm_password": "somepassword123"
    }, follow_redirects=True)
    assert resp_invalid.status_code == 200
    assert b"6 digits" in resp_invalid.data

    # 2. Check privacy on submission detail page
    with app.app_context():
        author = db.session.get(User, student_user)
        author.registration_no = "231088"
        db.session.commit()

        sub = Submission(
            author_id=author.id, category="idea", title="Smart Energy Audit",
            summary="Solar grid monitor", details="Full details", status="Accepted"
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

    # A) Public anonymous visitor cannot see registration number
    resp_anon = client.get(f"/submissions/{sub_id}")
    assert resp_anon.status_code == 200
    assert b"231088" not in resp_anon.data

    # B) Submitter themself logs in -> CAN see registration number
    client.post("/login", data={"email": "student@aitpune.edu.in", "password": "secretpass123"}, follow_redirects=True)
    resp_author = client.get(f"/submissions/{sub_id}")
    assert resp_author.status_code == 200
    assert b"231088" in resp_author.data
    client.get("/logout", follow_redirects=True)

    # C) Administrator logs in -> CAN see registration number
    client.post("/login", data={"email": "admin@aitpune.edu.in", "password": "adminpassword123"}, follow_redirects=True)
    resp_admin = client.get(f"/submissions/{sub_id}")
    assert resp_admin.status_code == 200
    assert b"231088" in resp_admin.data


def test_direct_registration_flow(client, app):
    """Verify that registration creates account and logs in immediately without an OTP step."""
    resp_reg = client.post("/register", data={
        "name": "Ananya Kulkarni",
        "email": "ananya.kulkarni@aitpune.edu.in",
        "department": "Electronics & Telecommunication Engineering",
        "year": "Second Year (SE)",
        "registration_no": "232014",
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    }, follow_redirects=True)

    assert resp_reg.status_code == 200
    assert b"Welcome to NovumHub" in resp_reg.data or b"Ananya" in resp_reg.data

    # Verify user was created in DB with 6-digit registration_no and logged in
    with app.app_context():
        user = User.query.filter_by(email="ananya.kulkarni@aitpune.edu.in").first()
        assert user is not None
        assert user.registration_no == "232014"
        assert user.role == "student"

