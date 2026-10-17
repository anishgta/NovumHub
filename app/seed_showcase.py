"""
app/seed_showcase.py
================================================================================
SHOWCASE SEED DATA GENERATOR
Populates realistic Hackathon events, multi-mode project demonstrations,
interactive HTML5 canvas builds, presentation decks, 8-part developer notes,
team rosters, and judge evaluations.
================================================================================
"""

import os
import zipfile
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash
from app.models import (
    db, User, Submission, HackathonEvent, ShowcaseProject,
    ProjectMember, ProjectAsset, DevNote, JudgeScore, Upvote, Comment
)
import site_config


def create_showcase_seed_data(app=None):
    """Generates complete sample data for Hackrec Showcase."""
    
    # 1. Ensure Judge & Reviewer accounts exist
    judge_user = User.query.filter_by(email="judge@aitpune.edu.in").first()
    if not judge_user:
        judge_user = User(
            name="Dr. Rajesh Kulkarni",
            email="judge@aitpune.edu.in",
            password_hash=generate_password_hash("Judge@123"),
            role="judge",
            department="Computer Engineering",
            year="Faculty",
            roll_no="FAC-CE-042"
        )
        db.session.add(judge_user)

    student_user = User.query.filter_by(role="student").first()
    if not student_user:
        student_user = User(
            name="Arjun Sharma",
            email="arjun.sharma@aitpune.edu.in",
            password_hash=generate_password_hash("Student@123"),
            role="student",
            department="Information Technology",
            year="TE",
            roll_no="23IT045"
        )
        db.session.add(student_user)

    admin_user = User.query.filter_by(role="admin").first()
    db.session.commit()

    # 2. Hackathon Events
    event_past = HackathonEvent.query.filter_by(name="HackAIT 2025").first()
    if not event_past:
        event_past = HackathonEvent(
            name="HackAIT 2025",
            year=2025,
            theme="Resilient Engineering for Modern India",
            organiser="Open Source Club & Dept of Comp Engg",
            tracks="AI & Automation, Campus Defense Tech, Web3 & Cryptography, Clean Energy",
            description="The flagship 36-hour hackathon of Army Institute of Technology, Pune with 45 competing teams.",
            is_active=False,
            results_published=True
        )
        db.session.add(event_past)

    event_current = HackathonEvent.query.filter_by(name="HackAIT 2026").first()
    if not event_current:
        event_current = HackathonEvent(
            name="HackAIT 2026",
            year=2026,
            theme="Next-Gen Intelligent Campus Solutions",
            organiser="Robotics & AI Club, AIT Pune",
            tracks="AI & Automation, Smart Campus IoT, Cyber Defense, Green Tech",
            description="Annual 48-hour hackathon focusing on practical, deployable campus and tactical technologies.",
            is_active=True,
            results_published=False
        )
        db.session.add(event_current)

    db.session.commit()

    # Prepare upload directories
    base_upload = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(base_upload, exist_ok=True)

    # 3. Project 1: Hosted WebGL / HTML5 Interactive Canvas Build
    p1 = ShowcaseProject.query.filter_by(title="AIT Campus Navigator 3D").first()
    if not p1:
        p1 = ShowcaseProject(
            title="AIT Campus Navigator 3D",
            pitch="An interactive 3D WebGL campus map with real-time room navigation, wheelchair routing, and event beacon tracking.",
            description=(
                "Built using three.js and HTML5 Canvas, AIT Campus Navigator provides a realistic 3D spatial walkthrough "
                "of academic blocks, hostels, sports grounds, and the central library. Designed for freshers and visiting dignitaries."
            ),
            event_id=event_current.id,
            track="Smart Campus IoT",
            team_name="VectorHawks",
            tech_tags="Three.js, WebGL, JavaScript, Blender, Vite",
            repo_url="https://github.com/ait-vectorhawks/campus-nav-3d",
            owner_id=student_user.id,
            demo_mode="hosted_webgl",
            is_featured=True,
            is_reference=True,
            status="published"
        )
        db.session.add(p1)
        db.session.flush()

        # Create interactive HTML5 canvas build on disk
        demo_dest = os.path.join(base_upload, "showcase", str(p1.id), "demo")
        os.makedirs(demo_dest, exist_ok=True)
        html_file = os.path.join(demo_dest, "index.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AIT Campus Navigator 3D - Live Build</title>
<style>
  body { margin: 0; background: #080A1A; color: #FFF; font-family: sans-serif; overflow: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
  canvas { border: 2px solid #8B5CF6; border-radius: 8px; box-shadow: 0 0 25px rgba(139,92,246,0.5); }
  #hud { position: absolute; top: 15px; left: 20px; font-size: 14px; color: #C7D2FE; background: rgba(0,0,0,0.6); padding: 8px 14px; border-radius: 6px; }
</style>
</head>
<body>
<div id="hud">AIT Campus 3D Node Mesh &bull; Move mouse to rotate camera</div>
<canvas id="c" width="760" height="460"></canvas>
<script>
  const c = document.getElementById('c');
  const ctx = c.getContext('2d');
  let angle = 0, mouseX = 0, mouseY = 0;
  c.addEventListener('mousemove', e => {
    const r = c.getBoundingClientRect();
    mouseX = (e.clientX - r.left - c.width/2) * 0.005;
    mouseY = (e.clientY - r.top - c.height/2) * 0.005;
  });
  const nodes = [];
  for(let i=0; i<45; i++) {
    nodes.push({
      x: (Math.random()-0.5)*350,
      y: (Math.random()-0.5)*200,
      z: (Math.random()-0.5)*350,
      label: i % 8 === 0 ? ['Admin Block', 'Library', 'Mech Workshop', 'Hostel 4', 'Ramanujan Lab', 'Parade Ground'][i/8|0] : ''
    });
  }
  function loop() {
    angle += 0.015;
    ctx.fillStyle = '#090B22';
    ctx.fillRect(0, 0, c.width, c.height);
    const ca = Math.cos(angle + mouseX), sa = Math.sin(angle + mouseX);
    ctx.strokeStyle = 'rgba(139, 92, 246, 0.25)';
    ctx.beginPath();
    nodes.forEach((n, idx) => {
      const rx = n.x * ca - n.z * sa;
      const rz = n.x * sa + n.z * ca + 400;
      const f = 380 / rz;
      const sx = c.width/2 + rx * f;
      const sy = c.height/2 + (n.y + mouseY*80) * f;
      if(idx === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
    });
    ctx.stroke();
    nodes.forEach(n => {
      const rx = n.x * ca - n.z * sa;
      const rz = n.x * sa + n.z * ca + 400;
      const f = 380 / rz;
      const sx = c.width/2 + rx * f;
      const sy = c.height/2 + (n.y + mouseY*80) * f;
      ctx.fillStyle = n.label ? '#10B981' : '#8B5CF6';
      ctx.beginPath();
      ctx.arc(sx, sy, n.label ? 6 : 3, 0, Math.PI*2);
      ctx.fill();
      if(n.label) {
        ctx.fillStyle = '#FFF';
        ctx.font = 'bold 11px sans-serif';
        ctx.fillText(n.label, sx + 8, sy + 4);
      }
    });
    requestAnimationFrame(loop);
  }
  loop();
</script>
</body>
</html>
""")
        p1.demo_entry_path = os.path.relpath(html_file, base_upload).replace("\\", "/")

        # Team Members
        db.session.add(ProjectMember(project_id=p1.id, user_id=student_user.id, display_name="Arjun Sharma", role="Lead Graphics Dev & 3D Artist"))
        db.session.add(ProjectMember(project_id=p1.id, display_name="Rhea Sen", role="UI/UX & Spatial Layout", links="https://github.com/rhea-sen"))
        db.session.add(ProjectMember(project_id=p1.id, display_name="Vikram Aditya", role="Pathfinding Algorithms", links="https://linkedin.com"))

        # Developer Notes
        notes = {
            "problem": "First-year students and parents frequently get lost locating specific academic chambers, labs, and administrative offices across AIT's 30-acre campus.",
            "how_it_works": "We modeled key campus landmarks in Blender, exported lightweight glTF meshes, and built a custom three.js renderer with Dijkstra routing on an indexed graph.",
            "tech_stack": "HTML5, WebGL, three.js for 3D viewports, Vite for asset bundling, and SQLite for node coordinates.",
            "run_locally": "1. `git clone https://github.com/ait-vectorhawks/campus-nav-3d`\n2. `npm install`\n3. `npm run dev`\n4. Open `http://localhost:5173`.",
            "challenges": "Reducing mobile memory usage from 280MB to 42MB by baking lighting into vertex colors instead of heavy real-time shadows.",
            "differently": "We would use Level-of-Detail (LOD) earlier in the pipeline to speed up initial load times on slow hostel cellular connections.",
            "time_breakdown": "- 10h 3D Modeling & Texture Baking\n- 14h Pathfinding Graph Construction\n- 8h WebGL Shaders & Minimap UI\n- 4h Testing & Presentation Prep",
            "resources": "- [three.js docs](https://threejs.org)\n- [AIT Campus Master Plan 2024](https://aitpune.com)"
        }
        for k, v in notes.items():
            db.session.add(DevNote(project_id=p1.id, section_key=k, body_markdown=v))

        # Sample PDF Asset
        sample_pdf_dir = os.path.join(base_upload, "showcase", str(p1.id), "assets")
        os.makedirs(sample_pdf_dir, exist_ok=True)
        sample_pdf_path = os.path.join(sample_pdf_dir, "campus_nav_deck.pdf")
        with open(sample_pdf_path, "wb") as f:
            # Minimal valid PDF binary header
            f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000108 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n188\n%%EOF")
        
        pdf_rel = os.path.relpath(sample_pdf_path, base_upload).replace("\\", "/")
        db.session.add(ProjectAsset(
            project_id=p1.id,
            kind="presentation_pdf",
            title="AIT Campus Navigator 3D - Presentation Deck",
            file_path=pdf_rel,
            size_bytes=os.path.getsize(sample_pdf_path)
        ))

        # Judge Score
        db.session.add(JudgeScore(
            project_id=p1.id,
            judge_id=judge_user.id,
            innovation=9,
            technical_depth=9,
            completeness=8,
            design_ux=9,
            presentation=9,
            impact=8,
            private_feedback="Exceptional WebGL execution. The memory optimizations made the model responsive even on budget test phones.",
            public_feedback="Outstanding 3D visualization and real-world campus utility. Highly recommend testing with the incoming first-year batch!"
        ))

    # 4. Project 2: External Embed Video / Streamlit (Defense AI)
    p2 = ShowcaseProject.query.filter_by(title="Tactical Perimeter AI").first()
    if not p2:
        p2 = ShowcaseProject(
            title="Tactical Perimeter AI",
            pitch="Real-time thermal intrusion detection and drone trajectory tracking for perimeter security.",
            description=(
                "Developed during HackAIT 2025, Tactical Perimeter AI uses YOLOv8 nano models optimized for edge NPU hardware "
                "to spot unauthorized intrusions across wide-angle night cameras."
            ),
            event_id=event_past.id,
            track="Campus Defense Tech",
            team_name="Sentinels of AIT",
            tech_tags="Python, PyTorch, YOLOv8, OpenCV, FastAPI",
            repo_url="https://github.com/ait-sentinels/tactical-perimeter",
            owner_id=student_user.id,
            demo_mode="external_embed",
            demo_external_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
            is_featured=True,
            is_reference=True,
            status="published"
        )
        db.session.add(p2)
        db.session.flush()

        db.session.add(ProjectMember(project_id=p2.id, display_name="Karan Malhotra", role="Computer Vision Engineer"))
        db.session.add(ProjectMember(project_id=p2.id, display_name="Pooja Verma", role="Embedded Hardware & Jetson Nano"))

        # Developer notes
        notes2 = {
            "problem": "Thermal cameras generate high false-positive rates due to stray wildlife near boundary walls.",
            "how_it_works": "Dual-pass detection: Fast edge YOLO filter followed by lightweight optical flow trajectory verification.",
            "tech_stack": "PyTorch, TensorRT, FastAPI, React dashboard.",
            "run_locally": "`python -m venv venv && pip install -r requirements.txt && python detect.py --source demo.mp4`",
            "challenges": "Running 30 FPS inference on a low-power 10W edge device.",
            "differently": "Collect more thermal training samples during rain and fog conditions.",
            "time_breakdown": "16h model tuning, 10h pipeline integration, 8h edge benchmark.",
            "resources": "- [Ultralytics YOLO](https://docs.ultralytics.com)"
        }
        for k, v in notes2.items():
            db.session.add(DevNote(project_id=p2.id, section_key=k, body_markdown=v))

        # Judge Score (Won 1st place in 2025)
        db.session.add(JudgeScore(
            project_id=p2.id,
            judge_id=judge_user.id,
            innovation=10,
            technical_depth=10,
            completeness=9,
            design_ux=8,
            presentation=10,
            impact=10,
            private_feedback="Ready for campus defense perimeter deployment trials.",
            public_feedback="A gold-standard demonstration of practical engineering and clear technical presentation."
        ))

    # 5. Project 3: Downloadable Desktop Binary (C++ Packet Analyzer)
    p3 = ShowcaseProject.query.filter_by(title="AIT WireSentry").first()
    if not p3:
        p3 = ShowcaseProject(
            title="AIT WireSentry",
            pitch="High-throughput C++20 packet sniffer and campus network anomaly detection agent.",
            description="A lightweight native application for monitoring rogue DHCP servers, DNS spoofing, and abnormal campus traffic spikes.",
            event_id=event_past.id,
            track="Web3 & Cryptography",
            team_name="KernelPanic",
            tech_tags="C++, WinPcap, Libpcap, Multithreading, Qt6",
            owner_id=student_user.id,
            demo_mode="download",
            is_featured=False,
            is_reference=True,
            status="published"
        )
        db.session.add(p3)
        db.session.flush()

        db.session.add(ProjectMember(project_id=p3.id, display_name="Devansh Roy", role="C++ Systems Developer"))

        # Create dummy download asset
        dl_dir = os.path.join(base_upload, "showcase", str(p3.id), "assets")
        os.makedirs(dl_dir, exist_ok=True)
        dl_path = os.path.join(dl_dir, "WireSentry-v1.0-Win64.zip")
        with open(dl_path, "wb") as f:
            f.write(b"PK\x05\x06" + b"\x00"*18)  # Empty valid zip
        
        db.session.add(ProjectAsset(
            project_id=p3.id,
            kind="build_download",
            title="WireSentry Windows x64 Binary",
            file_path=os.path.relpath(dl_path, base_upload).replace("\\", "/"),
            size_bytes=os.path.getsize(dl_path)
        ))

        db.session.add(JudgeScore(
            project_id=p3.id,
            judge_id=judge_user.id,
            innovation=8,
            technical_depth=10,
            completeness=8,
            design_ux=7,
            presentation=8,
            impact=8,
            private_feedback="Clean modern C++ codebase with zero memory leaks.",
            public_feedback="Robust systems programming. Excellent benchmark charts in the developer notes."
        ))

    # 6. Project 4: Linked Idea Project (Evolved from Hackrec Idea #1)
    first_idea = Submission.query.first()
    p4 = ShowcaseProject.query.filter_by(title="Hostel Laundry Availability Beacon").first()
    if not p4:
        p4 = ShowcaseProject(
            title="Hostel Laundry Availability Beacon",
            pitch="IoT sensor array tracking washing machine vibration and notifying students via Telegram when wash cycles finish.",
            description="Started as a community idea on Hackrec and evolved into a physical prototype deployed in Hostel 3.",
            event_id=event_current.id,
            track="Smart Campus IoT",
            team_name="CleanCode Crew",
            tech_tags="ESP32, MicroPython, MQTT, TelegramBot",
            linked_submission_id=first_idea.id if first_idea else None,
            owner_id=student_user.id,
            demo_mode="video",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            is_featured=True,
            is_reference=False,
            status="published"
        )
        db.session.add(p4)
        db.session.flush()

        db.session.add(ProjectMember(project_id=p4.id, display_name="Sneha Joshi", role="Firmware & Circuit Design"))
        db.session.add(ProjectMember(project_id=p4.id, display_name="Nikhil Rao", role="Cloud API & Bot Service"))

        db.session.add(JudgeScore(
            project_id=p4.id,
            judge_id=judge_user.id,
            innovation=9,
            technical_depth=8,
            completeness=9,
            design_ux=9,
            presentation=8,
            impact=9,
            private_feedback="Solves an immediate daily student pain point with less than Rs. 500 in components.",
            public_feedback="Inspiring proof of how a simple campus suggestion can evolve into a working IoT deployment!"
        ))

    # 7. Add sample upvotes & comments
    db.session.commit()

    all_projs = ShowcaseProject.query.all()
    for proj in all_projs:
        if not Upvote.query.filter_by(showcase_project_id=proj.id, user_id=judge_user.id).first():
            db.session.add(Upvote(showcase_project_id=proj.id, user_id=judge_user.id))
        if not Comment.query.filter_by(showcase_project_id=proj.id).first():
            db.session.add(Comment(
                showcase_project_id=proj.id,
                author_id=judge_user.id,
                body="Remarkable execution during the hackathon time constraint. Kudos to the entire team!"
            ))

    db.session.commit()
