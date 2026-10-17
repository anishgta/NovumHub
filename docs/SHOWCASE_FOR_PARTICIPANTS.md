# 🏆 Hackrec Showcase: Student Participant's Guide

Welcome to the **Army Institute of Technology (AIT) Hackathon Showcase**!

The Showcase is where student hackathon teams publish interactive demonstrations, presentation decks, source code repositories, and engineering notes. Judges use this arena to evaluate your build during hackathons, and future AIT engineering batches study your developer notes as a reference library.

---

## 📋 What to Prepare Before Submitting

To get the highest evaluation scores from the judging panel, prepare the following materials before entering the submission wizard:

### 1. Basic Metadata
- **Project Title:** Clear, concise name (e.g. *AIT Campus Navigator 3D* or *Tactical Perimeter AI*).
- **One-Line Pitch:** A single high-impact sentence explaining what your project solves and who it helps.
- **Track / Theme:** Select the hackathon track you registered under (e.g. *AI & Automation*, *Campus Defense Tech*, *Smart Campus IoT*, *Web3*).
- **Team Name & Members:** Names, technical roles, and portfolio/GitHub links for everyone on your team.
- **GitHub / GitLab URL:** Clean public repository link with a well-maintained `README.md`.

### 2. Choose Your Demo Mode
You can showcase your project in one of five flexible modes:
- **Mode A: Hosted Interactive Build (.zip):**
  - Ideal for Unity WebGL, Godot HTML5, Three.js, or frontend canvas applications.
  - Package your build into a standard `.zip` archive (up to 50MB).
  - **Rule:** Your zip file **must** contain an `index.html` file at the root or within your build folder.
  - Supports WebAssembly (`.wasm`), Unity WebGL (`.unityweb`), `.data`, gzip (`.gz`), and Brotli (`.br`) compression.
- **Mode B: External Interactive Embed:**
  - Ideal for hosted demos on **Hugging Face Spaces**, **Streamlit Apps**, **itch.io**, or **YouTube**.
  - Provide your public URL. The portal automatically embeds it in a sandboxed viewport.
- **Mode C: Recorded Video Walkthrough:**
  - Upload an `.mp4` video (up to 30MB) or provide a public YouTube video link demonstrating the live software.
- **Mode D: Downloadable Precompiled Application:**
  - Ideal for native C++, Python, or mobile applications (Windows `.exe`, Android `.apk`, or packaged `.zip`).
  - Provide run instructions in your developer notes.
- **Mode E: Screenshot Gallery:**
  - Upload 2 to 5 high-resolution interface screenshots or architecture diagrams with descriptive captions.

### 3. Presentation Pitch Deck
- **PDF File (Required for in-browser slide viewing):** Judges can flip through your slides directly inside the evaluation console.
- **Source Deck (.pptx / .key - Optional):** Uploaded as a downloadable backup for presentations.

### 4. Structured Developer Notes (The 8 Sections)
High-performing teams write thorough developer notes using Markdown (`# Header`, `- bullet`, `code block`):
1. **Problem We Tackled:** What pain point does this solve on campus or in society?
2. **How It Works (Architecture):** System diagrams, data pipelines, client-server relationships.
3. **Tech Stack & Why We Chose It:** Which frameworks/languages did you pick and why over alternatives?
4. **How to Run Locally:** Bulletproof, step-by-step instructions:
   ```bash
   git clone https://github.com/your-team/repo.git
   cd repo
   npm install   # or pip install -r requirements.txt
   npm run dev
   ```
5. **Challenges & How We Solved Them:** What bugs, latency bottlenecks, or hardware snags did you conquer?
6. **What We Would Do Differently:** Retrospective lessons learned under time pressure.
7. **Time Breakdown:** How your team distributed 24/36/48 hours between ideation, design, coding, and debugging.
8. **Useful Resources & Links:** Tutorials, papers, libraries, or datasets that helped your team.

---

## 🛠️ Step-by-Step Submission Walkthrough

1. **Log in** with your student credentials at `/login`.
2. Click **`+ Submit Demo Project`** in the navigation bar or visit `/showcase/create`.
3. **Step 1 (Basics):** Fill out your title, pitch, event dropdown, track, team name, and tags.
   - *Tip:* If this project originated as a suggestion in the Hackrec idea channel, select it in the *“Started as a Hackrec Idea?”* dropdown to link your innovation's lifecycle!
4. **Step 2 (Demo):** Select your demo mode and upload your build zip or external link.
5. **Step 3 (Team):** Add all teammates so they receive credit on the public card.
6. **Step 4 (Assets):** Upload your presentation PDF, source slides, and screenshots.
7. **Step 5 (Dev Notes):** Fill out the 8 developer note fields.
8. **Step 6 (Review & Publish):** Check the completeness checklist. Click **`Publish to Showcase`**!

---

## 🎖️ Tips for Winning Hackathon Judging

Judges score your project across 6 criteria (10 points each, 60 points maximum):
- **Innovation & Originality (10 pts):** Focus on what makes your approach novel.
- **Technical Depth (10 pts):** Highlight challenging algorithms, edge compute, or systems code in your notes.
- **Completeness & Functionality (10 pts):** Ensure your demo build boots cleanly without crashing.
- **Design & UX (10 pts):** Clean fonts, consistent spacing, and intuitive controls.
- **Presentation & Documentation (10 pts):** Clear PDF slides and complete local setup instructions.
- **Impact & Viability (10 pts):** Real-world usefulness for AIT students, faculty, or defense applications.

Good luck, engineers! 🚀
