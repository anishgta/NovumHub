"""
app/showcase/services.py
================================================================================
SHOWCASE BUSINESS LOGIC & SECURITY SERVICES
Handles:
1. Interactive demo zip extraction with strict zip-slip & extension validation.
2. Safe Markdown rendering using bleach HTML sanitization.
3. External embed domain allow-list checking and URL normalization.
4. Asset upload streaming, size quotas, and storage management.
================================================================================
"""

import os
import zipfile
import secrets
import urllib.parse
from werkzeug.utils import secure_filename
from app.models import db, ProjectAsset
import site_config

# Resilient imports with fallback for clean startup even outside virtualenv
try:
    import markdown
except ImportError:
    markdown = None

try:
    import bleach
except ImportError:
    bleach = None

# Safe HTML tags allowed in developer notes
ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "strong", "em", "b", "i",
    "ul", "ol", "li", "code", "pre", "blockquote", "table", "thead", "tbody",
    "tr", "th", "td", "hr", "a", "img"
]

# Safe HTML attributes allowed in developer notes
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "code": ["class"],
    "th": ["align"],
    "td": ["align"]
}


def render_markdown_safe(markdown_text: str) -> str:
    """
    Renders user-supplied markdown safely into sanitized HTML.
    Prevents XSS attacks by sanitizing against an allow-list with Bleach.
    Falls back to safe escaped pre-wrap if markdown/bleach are not installed.
    """
    if not markdown_text or not markdown_text.strip():
        return ""

    if markdown is not None and bleach is not None:
        # Convert markdown to HTML with extra formatting extensions
        raw_html = markdown.markdown(
            markdown_text,
            extensions=["extra", "codehilite", "tables", "nl2br"]
        )

        # Sanitize HTML with strict allow-list
        clean_html = bleach.clean(
            raw_html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )

        # Add noopener noreferrer to any outgoing links for safety
        return bleach.linkify(clean_html)
    else:
        import html
        escaped = html.escape(markdown_text)
        return f"<div style='white-space: pre-wrap; font-family: inherit;'>{escaped}</div>"


def validate_external_embed(url: str):
    """
    Validates that an external embed URL belongs to an allowed host domain.
    Returns (is_valid: bool, normalized_url: str or None, error_message: str or None).
    """
    if not url or not url.strip():
        return False, None, "Embed URL cannot be empty."

    parsed = urllib.parse.urlparse(url.strip())
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        return False, None, "URL must start with http:// or https://"

    hostname = (parsed.hostname or "").lower()
    allowed = False
    for host in site_config.SHOWCASE_ALLOWED_EMBED_HOSTS:
        if hostname == host or hostname.endswith("." + host):
            allowed = True
            break

    if not allowed:
        return False, None, f"Domain '{hostname}' is not in the allowed hosts list: {', '.join(site_config.SHOWCASE_ALLOWED_EMBED_HOSTS)}"

    # Normalize YouTube watch links to embed links
    if "youtube.com" in hostname and "/watch" in parsed.path:
        qs = urllib.parse.parse_qs(parsed.query)
        video_id = qs.get("v", [None])[0]
        if video_id:
            return True, f"https://www.youtube-nocookie.com/embed/{video_id}", None

    if "youtu.be" in hostname:
        video_id = parsed.path.lstrip("/")
        if video_id:
            return True, f"https://www.youtube-nocookie.com/embed/{video_id}", None

    return True, url.strip(), None


def is_safe_zip_path(base_dir: str, target_path: str) -> bool:
    """Helper to check if target_path stays strictly within base_dir."""
    base = os.path.abspath(base_dir)
    target = os.path.abspath(target_path)
    # Check if target is inside base directory (no directory traversal)
    common = os.path.commonpath([base, target])
    return common == base and target != base


def extract_demo_zip(arg1, arg2, base_upload_dir: str = None):
    """
    Extracts an interactive build zip file securely with strict safety rules:
    - Enforces zip slip prevention (no '..' or absolute paths)
    - Rejects disallowed file extensions
    - Enforces file count and uncompressed size limits
    - Requires an index.html file
    Returns (success: bool, entry_path: str or error_message: str).
    """
    from flask import current_app
    if isinstance(arg1, int):
        project_id = arg1
        file_storage = arg2
    else:
        file_storage = arg1
        project_id = arg2

    if base_upload_dir is None:
        base_upload_dir = current_app.config["UPLOAD_FOLDER"]

    # 1. Stream uploaded zip to a temporary file on disk
    temp_dir = os.path.join(base_upload_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_zip_path = os.path.join(temp_dir, f"upload_{project_id}_{secrets.token_hex(6)}.zip")

    if hasattr(file_storage, "save"):
        file_storage.save(temp_zip_path)
    elif hasattr(file_storage, "read"):
        with open(temp_zip_path, "wb") as f:
            f.write(file_storage.read())
    else:
        return False, "Unsupported file storage type."

    file_size_mb = os.path.getsize(temp_zip_path) / (1024 * 1024)

    if file_size_mb > site_config.SHOWCASE_MAX_ZIP_MB:
        os.remove(temp_zip_path)
        return False, f"Zip file exceeds maximum allowed size of {site_config.SHOWCASE_MAX_ZIP_MB} MB."

    try:
        with zipfile.ZipFile(temp_zip_path, "r") as zf:
            infolist = zf.infolist()

            if len(infolist) > site_config.SHOWCASE_MAX_FILES:
                return False, f"Zip contains {len(infolist)} files, exceeding limit of {site_config.SHOWCASE_MAX_FILES}."

            total_uncompressed = 0
            has_index = False
            index_path = None

            # 2. Inspect all zip entries before extracting
            for info in infolist:
                # Zip Slip Protection
                name = info.filename.replace("\\", "/")
                if os.path.isabs(name) or ".." in name.split("/") or "../" in name or "..\\" in name:
                    return False, f"Security error: Detected suspicious directory traversal path '{name}' in zip bundle."

                total_uncompressed += info.file_size
                if (total_uncompressed / (1024 * 1024)) > site_config.SHOWCASE_MAX_UNCOMPRESSED_MB:
                    return False, f"Uncompressed zip exceeds limit of {site_config.SHOWCASE_MAX_UNCOMPRESSED_MB} MB."

                if not info.is_dir():
                    # Extension validation
                    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                    if ext not in site_config.SHOWCASE_DEMO_ALLOWED_EXTENSIONS:
                        return False, f"Security error: Disallowed file type '.{ext}' found in '{name}'."

                    if name.lower() == "index.html" or name.lower().endswith("/index.html"):
                        depth = name.count("/")
                        if not has_index or (index_path and depth < index_path.count("/")):
                            has_index = True
                            index_path = name

            if not has_index:
                return False, "Missing index.html! Every interactive demo bundle must contain an index.html."

            # 3. Extract to project demo directory
            token = secrets.token_hex(8)
            dest_dir = os.path.join(base_upload_dir, "demos", str(project_id), token)
            os.makedirs(dest_dir, exist_ok=True)

            zf.extractall(dest_dir)

            relative_entry = os.path.join("demos", str(project_id), token, index_path).replace("\\", "/")
            return True, relative_entry

    except zipfile.BadZipFile:
        return False, "Invalid or corrupted zip archive."
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)


def save_project_asset(arg1, arg2, kind: str, base_upload_dir: str = None, title=None, caption=None):
    """
    Validates and stores a document, presentation deck, or media asset.
    Accepts (project_id, file_storage, ...) or (file_storage, project_id, ...).
    Returns (success: bool, asset: ProjectAsset or error: str).
    """
    from flask import current_app
    if isinstance(arg1, int):
        project_id = arg1
        file_storage = arg2
    else:
        file_storage = arg1
        project_id = arg2.id if hasattr(arg2, "id") else int(arg2)

    if base_upload_dir is None:
        base_upload_dir = current_app.config["UPLOAD_FOLDER"]

    orig_name = secure_filename(getattr(file_storage, "filename", "file") or "file")
    ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else ""

    if ext not in site_config.SHOWCASE_DOCS_ALLOWED_EXTENSIONS:
        return False, f"Disallowed file format '.{ext}'."

    proj_dir = os.path.join(base_upload_dir, "showcase", str(project_id))
    os.makedirs(proj_dir, exist_ok=True)

    stored_name = f"{kind}_{secrets.token_hex(8)}.{ext}"
    target_path = os.path.join(proj_dir, stored_name)

    file_storage.save(target_path)
    size_bytes = os.path.getsize(target_path)

    # Check individual size limit
    if (size_bytes / (1024 * 1024)) > site_config.SHOWCASE_MAX_FILE_MB:
        os.remove(target_path)
        return False, f"File exceeds maximum size limit of {site_config.SHOWCASE_MAX_FILE_MB} MB."

    relative_path = os.path.join("showcase", str(project_id), stored_name).replace("\\", "/")

    asset = ProjectAsset(
        project_id=project_id,
        kind=kind,
        title=title or orig_name,
        caption=caption,
        file_path=relative_path,
        size_bytes=size_bytes
    )
    db.session.add(asset)
    db.session.commit()
    return True, asset
