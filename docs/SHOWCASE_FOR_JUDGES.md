# ⚖️ Hackrec Showcase: Faculty & Industry Judge's Handbook

Welcome to the **AIT Hackrec Judging System**.

This handbook explains how to evaluate student hackathon projects, interact with live interactive builds and presentation decks, and enter scoring rubrics and feedback.

---

## 🔑 1. Accessing the Judge Workspace

1. Log in with your registered college email at `/login`.
2. Ensure your account has the **`judge`** or **`admin`** role.
   - *Admins can grant this role using:* `flask make-judge professor@aitpune.edu.in` or via `/admin/users`.
3. Click the purple **`★ Judging`** button in the top navigation bar or navigate directly to:
   - **`/showcase/judge`**

---

## 🖥️ 2. The Judge Dashboard

The dashboard provides an overview of all competing submissions for the selected hackathon:
- **Event Dropdown:** Switch between active hackathons (e.g. *HackAIT 2026*) and past archived events.
- **Submissions Table:** Lists each team's project, category track, demo mode, and your personal evaluation status:
  - `Pending Review` (grey badge)
  - `48 / 60` (green badge once evaluated)
- Click **`Score Project →`** or **`Update Score`** to enter the side-by-side evaluation console.

---

## 📐 3. Side-by-Side Evaluation Console

The evaluation workspace is split into two panels for streamlined grading without having to juggle multiple browser tabs:

### Left Panel: Demonstration & Evidence
- **Interactive Live Build:** If the team uploaded a WebGL or HTML5 application, it boots directly in the sandboxed viewport. You can test controls, rotate cameras, and full-screen the build.
- **Slide Deck (PDF):** Embedded PDF reader allowing you to browse their presentation slides in-line.
- **Source Code Repository:** Direct link to their GitHub/GitLab repository to inspect code hygiene and commit activity.
- **Developer Notes:** Expandable technical write-ups covering the problem, system architecture, challenges, and local setup steps.

### Right Panel: Official Evaluation Rubric (60 Points Total)
Scores are entered on a 0 to 10 scale across six weighted criteria. The total score updates dynamically in real time:

| Criterion | Max Points | What to Evaluate |
| :--- | :---: | :--- |
| **1. Innovation & Originality** | 10 | How novel and creative is the core idea? Does it take an inventive angle compared to existing campus or commercial tools? |
| **2. Technical Depth & Rigor** | 10 | Engineering complexity, architectural design, code cleanliness, algorithm difficulty, and technical challenge tackled during the sprint. |
| **3. Completeness & Functionality** | 10 | Does the live demo or downloadable binary function reliably as claimed? Error handling, stability, and polish under test conditions. |
| **4. Design & User Experience** | 10 | Visual ergonomics, typography, user interface clarity, responsive layout, and ease of navigation. |
| **5. Presentation & Documentation** | 10 | Quality of the PDF presentation deck, clarity of developer notes, and completeness of local setup instructions. |
| **6. Potential Impact & Viability** | 10 | Real-world utility for the campus, societal value, or relevance to defense technology applications. |

---

## 💬 4. Providing Meaningful Feedback

Below the scoring sliders, two feedback textareas are provided:

1. **Private Feedback (Admins & Judges Only):**
   - Strictly confidential.
   - Use this space to record technical notes, verification questions, or award category nominations for judging panel deliberations.
2. **Public Constructive Feedback (Visible to Team):**
   - Published on the project page discussion tab.
   - Keep comments constructive, educational, and encouraging. Highlight strong architectural choices and offer suggestions for future iterations.

Click **`✓ Submit Project Evaluation`** to record your assessment. You may return and update your scores at any time before the event is locked.

---

## 🏆 5. Event Leaderboards & CSV Export

- **Leaderboard Calculation:** Projects are ranked automatically by average judge score across all panel evaluations.
- **Publication Control:** By default, live scores remain confidential among judges until the event organizer toggles **`Publish Results`** in the Admin Console.
- **Data Export:** Administrators can download a complete CSV spreadsheet of all project scores, demo links, and team rosters by clicking **`Showcase CSV`** in the Review Queue (`/review`).

Thank you for mentoring and evaluating the next generation of AIT engineering innovators! 🎖️
