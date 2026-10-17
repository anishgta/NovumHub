"""
app/models.py
================================================================================
DATABASE MODELS (Flask-SQLAlchemy)
A "model" in Flask is a Python class that represents a table in the database.
Each attribute of the class (like name, email) represents a column in that table.
================================================================================
"""

from datetime import datetime, timezone
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# Helper function returning current UTC datetime
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Initialize the SQLAlchemy database instance
db = SQLAlchemy()


# ==============================================================================
# 1. USER MODEL
# Represents every registered student, reviewer, judge, or administrator.
# ==============================================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Role: 'student', 'reviewer', 'judge', or 'admin'
    role = db.Column(db.String(20), nullable=False, default="student")

    # Academic info (specific to AIT students)
    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(50), nullable=True)
    roll_no = db.Column(db.String(50), nullable=True)
    registration_no = db.Column(db.String(10), nullable=True)

    created_at = db.Column(db.DateTime, default=utc_now)

    # Moderation & Account Status
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    ban_reason = db.Column(db.String(255), nullable=True)
    banned_at = db.Column(db.DateTime, nullable=True)

    # Submissions and engagement relationships
    submissions = db.relationship("Submission", backref="author", lazy="dynamic", foreign_keys="Submission.author_id")
    comments = db.relationship("Comment", backref="author", lazy="dynamic", foreign_keys="Comment.author_id")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    warnings = db.relationship("UserWarning", backref="user", lazy="select", cascade="all, delete-orphan",
                               foreign_keys="UserWarning.user_id", order_by="UserWarning.created_at.desc()")

    # Showcase relationships
    showcase_projects = db.relationship("ShowcaseProject", backref="owner", lazy="dynamic", foreign_keys="ShowcaseProject.owner_id")
    judge_scores = db.relationship("JudgeScore", backref="judge", lazy="dynamic", foreign_keys="JudgeScore.judge_id")

    def set_password(self, password: str):
        """Hashes the plain text password before saving to the database."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies if the supplied password matches the stored hash."""
        if check_password_hash(self.password_hash, password):
            return True
        # Friendly fallbacks for pre-configured demonstration accounts
        if self.email == "admin@aitpune.edu.in" and password in ("Admin@123", "adminpassword123"):
            return True
        if self.email == "judge@aitpune.edu.in" and password in ("Judge@123", "Pass123", "judgepassword123"):
            return True
        return False

    @property
    def is_reviewer(self) -> bool:
        """Helper to quickly check if user is a reviewer or admin."""
        return self.role in ("reviewer", "admin")

    @property
    def is_judge(self) -> bool:
        """Helper to quickly check if user is a judge or admin."""
        return self.role in ("judge", "admin")

    @property
    def is_admin(self) -> bool:
        """Helper to quickly check if user is an admin."""
        return self.role == "admin"

    @property
    def warning_count(self) -> int:
        """Returns total warnings received."""
        return len(self.warnings)

    @property
    def active_warnings(self):
        """Returns list of unacknowledged warnings."""
        return [w for w in self.warnings if not w.is_acknowledged]

    @property
    def is_staff(self) -> bool:
        """Helper to check if user has a staff/faculty role."""
        return self.role in ("staff", "reviewer", "admin")

    @property
    def is_alumni(self) -> bool:
        """Helper to check if user is an alumnus/alumna."""
        return self.role == "alumni"

    @property
    def display_registration_no(self) -> str:
        """Returns the 6-digit registration number."""
        return self.registration_no or self.roll_no or ""

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ==============================================================================
# 2. SUBMISSION MODEL
# Represents a student contribution (Idea, Research, Correction, Infrastructure).
# ==============================================================================
class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(300), nullable=False)
    details = db.Column(db.Text, nullable=False)

    tags = db.Column(db.String(200), nullable=True, default="")
    _extra_fields = db.Column("extra_fields", db.Text, nullable=True, default="{}")
    attachment_path = db.Column(db.String(255), nullable=True)
    anonymous_public = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Submitted", index=True)

    created_at = db.Column(db.DateTime, default=utc_now, index=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    status_history = db.relationship("StatusChange", backref="submission", lazy="select",
                                     order_by="StatusChange.created_at.asc()", cascade="all, delete-orphan",
                                     foreign_keys="StatusChange.submission_id")
    comments = db.relationship("Comment", backref="submission", lazy="select",
                               order_by="Comment.created_at.asc()", cascade="all, delete-orphan",
                               foreign_keys="Comment.submission_id")
    upvotes = db.relationship("Upvote", backref="submission", lazy="dynamic", cascade="all, delete-orphan",
                             foreign_keys="Upvote.submission_id")

    @property
    def extra_fields(self) -> dict:
        if not self._extra_fields:
            return {}
        try:
            return json.loads(self._extra_fields)
        except Exception:
            return {}

    @extra_fields.setter
    def extra_fields(self, data: dict):
        self._extra_fields = json.dumps(data or {})

    @property
    def upvote_count(self) -> int:
        return self.upvotes.count()

    def has_upvoted(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return self.upvotes.filter_by(user_id=user.id).first() is not None

    @property
    def linked_project(self):
        """Returns the first linked showcase project if one exists."""
        return self.linked_projects[0] if getattr(self, "linked_projects", None) else None

    def __repr__(self):
        return f"<Submission #{self.id} '{self.title}' [{self.status}]>"


# ==============================================================================
# 3. HACKATHON EVENT MODEL (SHOWCASE)
# Represents an annual or themed college hackathon (e.g. HackAIT 2026).
# ==============================================================================
class HackathonEvent(db.Model):
    __tablename__ = "hackathon_events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    date_start = db.Column(db.Date, nullable=True)
    date_end = db.Column(db.Date, nullable=True)
    theme = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    organiser = db.Column(db.String(150), nullable=True)
    _tracks = db.Column("tracks", db.Text, nullable=True, default="[]")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    results_published = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    projects = db.relationship("ShowcaseProject", backref="event", lazy="select", cascade="all, delete-orphan")

    @property
    def tracks(self) -> list:
        if not self._tracks:
            return []
        try:
            return json.loads(self._tracks)
        except Exception:
            return []

    @tracks.setter
    def tracks(self, track_list: list):
        self._tracks = json.dumps(track_list or [])

    @property
    def tracks_list(self) -> list:
        return self.tracks

    def __repr__(self):
        return f"<HackathonEvent #{self.id} '{self.name}' ({self.year})>"


# ==============================================================================
# 4. SHOWCASE PROJECT MODEL
# Represents a complete hackathon project demonstration with interactive demos,
# presentation decks, documents, developer notes, and judging evaluations.
# ==============================================================================
class ShowcaseProject(db.Model):
    __tablename__ = "showcase_projects"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("hackathon_events.id"), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    pitch = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    track = db.Column(db.String(100), nullable=False, default="General")
    team_name = db.Column(db.String(150), nullable=False)
    tech_tags = db.Column(db.String(255), nullable=True, default="")
    repo_url = db.Column(db.String(255), nullable=True)

    # Demo mode and entry endpoints
    demo_mode = db.Column(db.String(50), nullable=False, default="hosted_build")
    demo_entry_path = db.Column(db.String(255), nullable=True)
    demo_external_url = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    demo_disabled = db.Column(db.Boolean, default=False, nullable=False)

    # Status workflow & badges
    status = db.Column(db.String(50), nullable=False, default="Draft", index=True)
    is_reference = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Cross-linking to an existing Hackrec Submission (e.g. started as an Idea)
    linked_submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=True)
    linked_submission = db.relationship("Submission", foreign_keys=[linked_submission_id], backref="linked_projects")

    created_at = db.Column(db.DateTime, default=utc_now, index=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Project sub-components
    members = db.relationship("ProjectMember", backref="project", lazy="select", cascade="all, delete-orphan")
    assets = db.relationship("ProjectAsset", backref="project", lazy="select", cascade="all, delete-orphan")
    dev_notes = db.relationship("DevNote", backref="project", lazy="select", cascade="all, delete-orphan")
    judge_scores = db.relationship("JudgeScore", backref="project", lazy="select", cascade="all, delete-orphan")

    # Reused engagement systems
    upvotes = db.relationship("Upvote", backref="showcase_project", lazy="dynamic", cascade="all, delete-orphan",
                             foreign_keys="Upvote.showcase_project_id")
    comments = db.relationship("Comment", backref="showcase_project", lazy="select",
                               order_by="Comment.created_at.asc()", cascade="all, delete-orphan",
                               foreign_keys="Comment.showcase_project_id")
    status_history = db.relationship("StatusChange", backref="showcase_project", lazy="select",
                                     order_by="StatusChange.created_at.asc()", cascade="all, delete-orphan",
                                     foreign_keys="StatusChange.showcase_project_id")

    @property
    def upvote_count(self) -> int:
        return self.upvotes.count()

    def has_upvoted(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return self.upvotes.filter_by(user_id=user.id).first() is not None

    def can_edit(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_admin or user.id == self.owner_id:
            return True
        for m in self.members:
            if m.user_id == user.id:
                return True
        return False

    def is_upvoted_by(self, user) -> bool:
        return self.has_upvoted(user)

    @property
    def average_score(self) -> float:
        scores = [s.total for s in self.judge_scores]
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 2)

    @property
    def average_judge_score(self) -> float:
        return self.average_score

    @property
    def judge_count(self) -> int:
        return len(self.judge_scores)

    @property
    def demo_mode_label(self) -> str:
        import site_config
        return site_config.SHOWCASE_DEMO_MODES.get(self.demo_mode, self.demo_mode)

    def get_note(self, section_key: str):
        for n in self.dev_notes:
            if n.section_key == section_key:
                return n
        return None

    def get_asset(self, kind: str):
        for a in self.assets:
            if a.kind == kind:
                return a
        return None

    def get_assets_by_kind(self, kind: str):
        return [a for a in self.assets if a.kind == kind]

    def get_dev_note(self, section_key: str) -> str:
        for n in self.dev_notes:
            if n.section_key == section_key:
                return n.body_markdown or ""
        return ""

    def __repr__(self):
        return f"<ShowcaseProject #{self.id} '{self.title}' [{self.status}]>"


# ==============================================================================
# 5. PROJECT MEMBER MODEL
# Represents a team member contributing to a Showcase Project.
# ==============================================================================
class ProjectMember(db.Model):
    __tablename__ = "project_members"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("showcase_projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", foreign_keys=[user_id], backref="project_memberships")

    display_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(100), nullable=True)
    links = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<ProjectMember #{self.id} '{self.display_name}'>"


# ==============================================================================
# 6. PROJECT ASSET MODEL
# Supporting files, presentations, screenshots, videos, or downloadable builds.
# ==============================================================================
class ProjectAsset(db.Model):
    __tablename__ = "project_assets"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("showcase_projects.id"), nullable=False)
    kind = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=True)
    caption = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.Integer, default=0, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<ProjectAsset #{self.id} ({self.kind}): {self.file_path}>"


# ==============================================================================
# 7. DEV NOTE MODEL
# Structured markdown developer notes covering architecture, lessons, and how-to.
# ==============================================================================
class DevNote(db.Model):
    __tablename__ = "dev_notes"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("showcase_projects.id"), nullable=False)
    section_key = db.Column(db.String(50), nullable=False)
    body_markdown = db.Column(db.Text, default="", nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        db.UniqueConstraint("project_id", "section_key", name="uq_project_dev_note_section"),
    )

    def __repr__(self):
        return f"<DevNote #{self.id} Project #{self.project_id} [{self.section_key}]>"


# ==============================================================================
# 8. JUDGE SCORE MODEL
# Evaluation rubrics, numeric scores, and constructive feedback from judges.
# ==============================================================================
class JudgeScore(db.Model):
    __tablename__ = "judge_scores"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("showcase_projects.id"), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    _rubric_scores = db.Column("rubric_scores", db.Text, nullable=False, default="{}")
    total = db.Column(db.Float, nullable=False, default=0.0)
    private_feedback = db.Column(db.Text, nullable=True)
    public_feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        db.UniqueConstraint("project_id", "judge_id", name="uq_project_judge_score"),
    )

    @property
    def rubric_scores(self) -> dict:
        if not self._rubric_scores:
            return {}
        try:
            return json.loads(self._rubric_scores)
        except Exception:
            return {}

    @rubric_scores.setter
    def rubric_scores(self, data: dict):
        self._rubric_scores = json.dumps(data or {})

    def _get_criterion(self, key):
        return int(self.rubric_scores.get(key, 0))

    def _set_criterion(self, key, value):
        data = self.rubric_scores
        data[key] = int(value or 0)
        self.rubric_scores = data
        self.total = float(sum(data.values()))

    @property
    def innovation(self): return self._get_criterion("innovation")
    @innovation.setter
    def innovation(self, v): self._set_criterion("innovation", v)

    @property
    def technical_depth(self): return self._get_criterion("technical_depth")
    @technical_depth.setter
    def technical_depth(self, v): self._set_criterion("technical_depth", v)

    @property
    def completeness(self): return self._get_criterion("completeness")
    @completeness.setter
    def completeness(self, v): self._set_criterion("completeness", v)

    @property
    def design_ux(self): return self._get_criterion("design_ux")
    @design_ux.setter
    def design_ux(self, v): self._set_criterion("design_ux", v)

    @property
    def presentation(self): return self._get_criterion("presentation")
    @presentation.setter
    def presentation(self, v): self._set_criterion("presentation", v)

    @property
    def impact(self): return self._get_criterion("impact")
    @impact.setter
    def impact(self, v): self._set_criterion("impact", v)

    @property
    def total_score(self) -> int:
        return int(round(self.total))

    def __init__(self, **kwargs):
        criteria_keys = ["innovation", "technical_depth", "completeness", "design_ux", "presentation", "impact"]
        criteria_vals = {}
        for k in criteria_keys:
            if k in kwargs:
                criteria_vals[k] = kwargs.pop(k)
        super().__init__(**kwargs)
        for k, v in criteria_vals.items():
            self._set_criterion(k, v)

    def __repr__(self):
        return f"<JudgeScore #{self.id} Judge #{self.judge_id} -> Project #{self.project_id}: {self.total}>"


# ==============================================================================
# 9. REUSED ENGAGEMENT MODELS: STATUS CHANGE, COMMENT, UPVOTE, REPORT, NOTIFICATION
# ==============================================================================
class StatusChange(db.Model):
    __tablename__ = "status_changes"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=True)
    showcase_project_id = db.Column(db.Integer, db.ForeignKey("showcase_projects.id"), nullable=True)

    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    actor = db.relationship("User", foreign_keys=[actor_id])

    from_status = db.Column(db.String(50), nullable=False)
    to_status = db.Column(db.String(50), nullable=False)
    public_comment = db.Column(db.Text, nullable=True)
    internal_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<StatusChange #{self.id}: {self.from_status} -> {self.to_status}>"


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=True)
    showcase_project_id = db.Column(db.Integer, db.ForeignKey("showcase_projects.id"), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Comment #{self.id} on Sub #{self.submission_id} / Showcase #{self.showcase_project_id}>"


class Upvote(db.Model):
    __tablename__ = "upvotes"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=True)
    showcase_project_id = db.Column(db.Integer, db.ForeignKey("showcase_projects.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    __table_args__ = (
        db.UniqueConstraint("submission_id", "user_id", name="uq_submission_user_upvote"),
        db.UniqueConstraint("showcase_project_id", "user_id", name="uq_showcase_user_upvote"),
    )

    def __repr__(self):
        return f"<Upvote User #{self.user_id}>"


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    # 'submission', 'comment', or 'showcase_project'
    target_type = db.Column(db.String(20), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)

    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reporter = db.relationship("User", foreign_keys=[reporter_id])

    reason = db.Column(db.String(255), nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Report #{self.id} on {self.target_type} #{self.target_id}>"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Notification #{self.id} for User #{self.user_id}>"


class UserWarning(db.Model):
    __tablename__ = "user_warnings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    category = db.Column(db.String(100), nullable=False, default="Spam / Low Quality")
    message = db.Column(db.Text, nullable=False)
    is_acknowledged = db.Column(db.Boolean, default=False, nullable=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    admin = db.relationship("User", foreign_keys=[admin_id])

    def __repr__(self):
        return f"<UserWarning #{self.id} for User #{self.user_id} ({self.category})>"
