# Plan: Showcase Extension for Hackrec

## Overview
Add a top-level **Showcase** section to Hackrec for hackathon project demonstrations: interactive hosted builds (Unity WebGL, HTML5), external embeds (YouTube, HuggingFace, itch.io, Streamlit), video demos, screenshot galleries, presentation viewers (PDF preview + PPTX download), downloadable builds, structured developer notes (with safe Markdown), judging rubrics, reference library, and unified search.

---

## 1. Schema & Models (`app/models.py`)
- **User Role**: Add `"judge"` role and `user.is_judge` property.
- **`HackathonEvent`**: `id`, `name`, `year`, `date_start`, `date_end`, `theme`, `description`, `organiser`, `_tracks` (JSON), `is_active`, `results_published`, `created_at`.
- **`ShowcaseProject`**: `id`, `event_id`, `owner_id`, `title`, `pitch`, `description`, `track`, `team_name`, `tech_tags`, `repo_url`, `demo_mode`, `demo_entry_path`, `demo_external_url`, `video_url`, `status`, `is_reference`, `is_featured`, `demo_disabled`, `linked_submission_id`, `created_at`, `updated_at`.
- **`ProjectMember`**: `id`, `project_id`, `user_id` (nullable), `display_name`, `role`, `links`.
- **`ProjectAsset`**: `id`, `project_id`, `kind`, `title`, `caption`, `file_path`, `size_bytes`, `uploaded_at`.
- **`DevNote`**: `id`, `project_id`, `section_key`, `body_markdown`, `updated_at`.
- **`JudgeScore`**: `id`, `project_id`, `judge_id`, `_rubric_scores` (JSON), `total`, `private_feedback`, `public_feedback`, `created_at`, `updated_at`.
- **Engagement Reuse**:
  - Add nullable `showcase_project_id` to `Upvote`, `Comment`, and `StatusChange`.
  - Reuse `Report` with `target_type='showcase_project'`.
  - Reuse `Notification` for project publishing, comments, judge feedback, and team assignment.
- **Safe Migration**: Dynamic SQLite column inspection (`PRAGMA table_info`) and `ALTER TABLE ADD COLUMN` to preserve all existing data without data loss.

---

## 2. Configuration (`site_config.py`)
- Showcase navigation label, motto, allowed embed hosts (`youtube.com`, `drive.google.com`, `github.io`, `itch.io`, `huggingface.co`, `streamlit.app`).
- Demo zip restrictions (max zip MB, max uncompressed MB, max files, allowed extensions including `.unityweb`, `.br`, `.gz`, `.wasm`).
- Storage quotas and size limits per project.
- Fixed Dev Note sections and 6-criteria configurable judging rubric.

---

## 3. Modular Package (`app/showcase/`)
Keep each file under ~250 lines:
- `app/showcase/__init__.py`: Blueprint definition.
- `app/showcase/services.py`: Zip extraction (zip-slip prevention, extension validation, index.html detection), Markdown parsing & Bleach sanitization, file streaming.
- `app/showcase/routes.py`: Showcase home, library, project detail, tabbed view, sandboxed demo serving route with strict CSP (`Content-Security-Policy: sandbox allow-scripts allow-pointer-lock allow-fullscreen`, `X-Content-Type-Options: nosniff`).
- `app/showcase/forms.py`: Multi-step form models.
- `app/showcase/judge.py`: Judge workspace, rubric scoring, draft autosave.
- `app/showcase/admin.py`: Events, judge assignment, reference tagging, leaderboard management.

---

## 4. Templates (`templates/showcase/`)
- `home.html`: Showcase home with hero, event filter chips, featured row, project cards with demo type icons, search & filters.
- `detail.html`: In-page tabs (Demo, Presentation, Dev Notes, Files, Team, Discussion), sandboxed iframe, native PDF viewer, safe markdown dev notes.
- `form_wizard.html`: Multi-step project creator/editor with vanilla JS upload progress bar & draft saving.
- `event.html`: Event info, tracks, leaderboard (when published).
- `judge_workspace.html`: Side-by-side interactive demo + judging rubric.
- `library.html`: Reference library with tech stack filters and dev note snippets.

---

## 5. Integration Across Hackrec
- **Navbar & Footer**: Add Showcase link.
- **Homepage**: Add "Latest from the Showcase" strip.
- **Unified Search**: Search query searches both Submissions and Showcase Projects.
- **Cross-Linking**: "Started as an idea" & "Became a hackathon project".
- **Stats Page & CSV Export**: Include Showcase metrics and data.
- **Moderation Queue**: Include showcase project reports.

---

## 6. Seed Data, Tests, and Documentation
- `flask seed-showcase` CLI command: Sample events, 6 demo projects across all demo modes, judge account, and scores.
- `flask make-judge <email>` CLI command.
- Pytest suite testing security (zip-slip, extensions, CSP, sandbox), engagement reuse, judging permissions, and unified search.
- Updated `README.md`, `docs/HOW_TO_EDIT.md`, `docs/SHOWCASE_FOR_PARTICIPANTS.md`, `docs/SHOWCASE_FOR_JUDGES.md`.
