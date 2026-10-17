"""
app/__init__.py
================================================================================
APPLICATION FACTORY
This file initializes our Flask application, connects the SQLite database,
sets up user login sessions and CSRF security, registers our blueprints,
and defines CLI commands like 'flask make-admin' and 'flask seed-demo'.
================================================================================
"""

import os
import click
from datetime import datetime, timezone
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from app.models import db, User, Submission, StatusChange, Comment, Upvote, Notification, Report
import site_config

# Security and session managers
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    """
    Creates and configures an instance of the Flask application.
    This pattern is called the 'Application Factory'.
    """
    # Base directory of the project
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static")
    )

    # Standard configuration
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    db_path = os.path.join(base_dir, "hackrec.db")
    upload_path = os.path.join(base_dir, "uploads")

    if is_serverless:
        # Vercel serverless environment has a read-only root directory; copy db to /tmp for read-write access
        import shutil
        tmp_db = "/tmp/hackrec.db"
        if os.path.exists(db_path) and not os.path.exists(tmp_db):
            try:
                shutil.copy2(db_path, tmp_db)
            except Exception as e:
                print(f"[Vercel Init] Could not copy seed DB to /tmp: {e}")
        db_path = tmp_db
        upload_path = "/tmp/uploads"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "hackrec-ait-super-secret-key-2026"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", f"sqlite:///{db_path}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=upload_path,
        MAX_CONTENT_LENGTH=site_config.MAX_UPLOAD_SIZE_MB * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    # Ensure uploads folder exists
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Security check for banned accounts on every request
    @app.before_request
    def check_banned_user_session():
        if current_user.is_authenticated and getattr(current_user, "is_banned", False):
            from flask_login import logout_user
            from flask import redirect, url_for, flash
            reason = current_user.ban_reason or "Account suspended by administration."
            logout_user()
            flash(f"Session terminated: Your account has been suspended by administration. Notice / Reason: {reason}", "danger")
            return redirect(url_for("auth.login"))

    # Context processor: makes site_config data, unread notifications & active warnings available to all templates!
    @app.context_processor
    def inject_global_data():
        unread_count = 0
        active_warnings = []
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            active_warnings = getattr(current_user, "active_warnings", [])
        return {
            "config_data": site_config,
            "unread_notif_count": unread_count,
            "active_user_warnings": active_warnings,
            "current_year": datetime.now(timezone.utc).year
        }

    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Register Blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.submissions import submissions_bp
    from app.review import review_bp
    from app.showcase import showcase_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(showcase_bp)

    # CLI Command: flask make-admin <email>
    @app.cli.command("make-admin")
    @click.argument("email")
    def make_admin(email):
        """Promote a registered user to Administrator role by email."""
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            click.echo(f"Error: No user found with email '{email}'.")
            return
        user.role = "admin"
        db.session.commit()
        click.echo(f"Success! {user.name} ({user.email}) is now an Administrator.")

    # CLI Command: flask make-judge <email>
    @app.cli.command("make-judge")
    @click.argument("email")
    def make_judge(email):
        """Promote a registered user to Judge role by email."""
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            click.echo(f"Error: No user found with email '{email}'.")
            return
        user.role = "judge"
        db.session.commit()
        click.echo(f"Success! {user.name} ({user.email}) is now a Judge.")

    # CLI Command: flask seed-demo
    @app.cli.command("seed-demo")
    def seed_demo():
        """Creates sample users and ~12 realistic submissions across all categories & statuses."""
        from app.seed_data import create_seed_data
        create_seed_data()
        click.echo("Success! Sample demo data successfully seeded.")

    # CLI Command: flask seed-showcase
    @app.cli.command("seed-showcase")
    def seed_showcase():
        """Creates sample hackathon events, projects, assets, notes, and judge scores."""
        from app.seed_showcase import create_showcase_seed_data
        create_showcase_seed_data()
        click.echo("Success! Sample showcase data successfully seeded.")

    # CLI Command: flask migrate-showcase
    @app.cli.command("migrate-showcase")
    def migrate_showcase():
        """Performs non-destructive schema migration for showcase tables and columns."""
        from app.migrate_db import upgrade_schema
        upgrade_schema(app)
        click.echo("Success! Showcase database tables and columns are up to date.")

    # Automatically create database tables and apply non-destructive column updates
    with app.app_context():
        from app.migrate_db import upgrade_schema
        upgrade_schema(app)

    return app
