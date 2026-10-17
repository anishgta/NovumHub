"""
app/seed_data.py
================================================================================
SAMPLE DEMO SEED DATA
Populates the Hackrec database with 1 Admin, 1 Reviewer, 3 Students,
and 12 realistic submissions across all 4 categories and various statuses.
================================================================================
"""

from datetime import datetime, timezone, timedelta
from app.models import db, User, Submission, StatusChange, Comment, Upvote, Notification
import site_config


def create_seed_data():
    """Generates demonstration data for Army Institute of Technology."""
    
    # 1. CREATE USERS
    users_data = [
        {
            "name": "Prof. Vikram Rathore",
            "email": "admin@aitpune.edu.in",
            "password": "adminpassword123",
            "role": "admin",
            "department": "Information Technology (IT)",
            "year": "Faculty / Staff",
            "roll_no": "FAC-IT-01"
        },
        {
            "name": "Dr. Neha Kulkarni",
            "email": "reviewer@aitpune.edu.in",
            "password": "reviewerpassword123",
            "role": "reviewer",
            "department": "Computer Engineering (Comp)",
            "year": "Faculty / Staff",
            "roll_no": "FAC-COMP-04"
        },
        {
            "name": "Aarav Mehta",
            "email": "aarav.mehta@aitpune.edu.in",
            "password": "studentpassword123",
            "role": "student",
            "department": "Computer Engineering (Comp)",
            "year": "Second Year (SE)",
            "roll_no": "22104"
        },
        {
            "name": "Pooja Deshmukh",
            "email": "pooja.deshmukh@aitpune.edu.in",
            "password": "studentpassword123",
            "role": "student",
            "department": "Electronics & Telecommunication (E&TC)",
            "year": "Third Year (TE)",
            "roll_no": "21215"
        },
        {
            "name": "Karan Rawat",
            "email": "karan.rawat@aitpune.edu.in",
            "password": "studentpassword123",
            "role": "student",
            "department": "Mechanical Engineering (Mech)",
            "year": "First Year (FE)",
            "roll_no": "23308"
        }
    ]

    created_users = {}
    for ud in users_data:
        user = User.query.filter_by(email=ud["email"]).first()
        if not user:
            user = User(
                name=ud["name"],
                email=ud["email"],
                role=ud["role"],
                department=ud["department"],
                year=ud["year"],
                roll_no=ud["roll_no"]
            )
            user.set_password(ud["password"])
            db.session.add(user)
            db.session.flush()
        created_users[ud["role"] if ud["role"] != "student" else ud["name"]] = user

    admin_user = created_users["admin"]
    reviewer_user = created_users["reviewer"]
    aarav = created_users["Aarav Mehta"]
    pooja = created_users["Pooja Deshmukh"]
    karan = created_users["Karan Rawat"]

    # 2. CREATE SAMPLE SUBMISSIONS (12 items across all 4 categories)
    submissions_data = [
        # --- CATEGORY 1: INNOVATIVE IDEA ---
        {
            "author": aarav,
            "category": "idea",
            "title": "Automated Lab Attendance & Asset Tracking via ESP32 RFID Scanners",
            "summary": "Low-cost RFID attendance readers installed at lab entrances to automate logging and equipment borrowing.",
            "details": (
                "Currently, students manually sign attendance paper sheets during practical sessions in Comp and IT labs, "
                "which causes delays and misplaced logbooks. We propose installing low-cost ESP32 microcontrollers with "
                "RC522 RFID readers at each lab door. Students simply tap their AIT student identity cards when entering. "
                "The attendance is instantly synchronized with a central dashboard."
            ),
            "tags": "iot, esp32, attendance, rfid, automation",
            "extra": {
                "expected_impact": "Saves 10-15 minutes per laboratory slot across 4 departments and maintains verifiable digital logs.",
                "resources_needed": "4 ESP32 boards, RFID readers, approval for wall mounting in Lab 3 & 4."
            },
            "status": "Accepted",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Initial proposal submitted.", aarav),
                ("Submitted", "Under Review", "Evaluating hardware security and campus network integration.", reviewer_user),
                ("Under Review", "Accepted", "Excellent initiative. Budget approved for pilot testing in Computer Lab 3.", reviewer_user)
            ],
            "upvoters": [pooja, karan, reviewer_user]
        },
        {
            "author": pooja,
            "category": "idea",
            "title": "Campus Drone Delivery Simulation for Inter-Hostel Technical Equipment",
            "summary": "Autonomous quadcopter navigation model for rapid delivery of urgent lab parts between AIT academic blocks.",
            "details": (
                "Developing an autonomous drone delivery routing algorithm tailored for AIT's campus layout. "
                "The system uses ultrasonic obstacle avoidance and GPS waypoint navigation to transport small circuit components "
                "and microcontrollers between the central workshop and student hostels during hackathons."
            ),
            "tags": "drone, robotics, navigation, autonomous, ai",
            "extra": {
                "expected_impact": "Accelerates prototyping turnaround time for student technical clubs.",
                "resources_needed": "Test flight approval on campus football ground and battery charging dock."
            },
            "status": "Submitted",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Contribution submitted.", pooja)
            ],
            "upvoters": [aarav]
        },
        {
            "author": aarav,
            "category": "idea",
            "title": "Open Source Coding Club Problem-Solving Repository & Mentorship Portal",
            "summary": "Centralized GitHub repository with curated competitive programming solutions and weekly peer code reviews.",
            "details": (
                "A student-run open source repository providing well-commented C++, Python, and Java solutions for standard "
                "algorithms (graphs, dynamic programming, trees). Includes a peer code review system where senior students "
                "mentor juniors preparing for national hackathons and placement tests."
            ),
            "tags": "coding, algorithms, open-source, mentorship, cpp",
            "extra": {
                "expected_impact": "Directly helps over 300 first and second-year students build strong algorithmic foundations.",
                "resources_needed": "Official endorsement by the AIT Coding Club and announcement in class groups."
            },
            "status": "Implemented",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Proposal submitted.", aarav),
                ("Submitted", "Under Review", "Discussed with Coding Club faculty coordinator.", reviewer_user),
                ("Under Review", "Accepted", "Approved. Repository created on GitHub.", reviewer_user),
                ("Accepted", "Implemented", "Live repository deployed and 120 students onboarded!", admin_user)
            ],
            "upvoters": [pooja, karan, reviewer_user, admin_user]
        },

        # --- CATEGORY 2: RESEARCH FINDING ---
        {
            "author": pooja,
            "category": "research",
            "title": "Low-Power LoRa Mesh Sensor Network for Microclimate Monitoring on Campus",
            "summary": "Experimental study showing 99.2% packet delivery ratio over 1.8km using low-power LoRa mesh topology.",
            "details": (
                "We deployed 5 LoRa-based sensor nodes across the AIT campus to measure ambient temperature, humidity, "
                "and solar irradiance. Using a customized lightweight routing protocol, nodes operated on 2000mAh batteries "
                "for over 60 days while achieving a 99.2% packet delivery ratio across foliage and building obstacles."
            ),
            "tags": "lora, iot, wireless, sensor-networks, research",
            "extra": {
                "methodology": "5 SX1278 transceiver nodes tested at 868MHz; metrics logged every 15 minutes to Raspberry Pi gateway.",
                "key_results": "Average latency: 340ms, Packet Loss < 0.8%, Battery lifetime projected at 14 months.",
                "link_or_doi": "https://github.com/ait-pune/lora-mesh-study"
            },
            "status": "Accepted",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Research findings submitted.", pooja),
                ("Submitted", "Under Review", "Reviewing experimental dataset and methodology.", reviewer_user),
                ("Under Review", "Accepted", "Verified data. Recommended for presentation at the AIT Annual Student Research Symposium.", reviewer_user)
            ],
            "upvoters": [aarav, karan, admin_user]
        },
        {
            "author": karan,
            "category": "research",
            "title": "Comparative Analysis of Lightweight CNNs for Micro-Defect Detection in 3D Prints",
            "summary": "Benchmarking MobileNetV3 vs ShuffleNetV2 for real-time layer-shift defect detection in fused deposition modeling.",
            "details": (
                "In our mechanical engineering prototyping lab, 3D printing failures often waste filament due to undetected layer shifts. "
                "We trained MobileNetV3 and ShuffleNetV2 on an edge camera connected to the Ender-3 printer. MobileNetV3 achieved "
                "94.6% mAP with 28ms inference latency on a Raspberry Pi 4."
            ),
            "tags": "cad, 3d-printing, cnn, edge-ai, mechanical",
            "extra": {
                "methodology": "Custom dataset of 1,200 defective and non-defective layer photos taken under varied lab lighting.",
                "key_results": "MobileNetV3: 94.6% mAP, 35 FPS on Raspberry Pi 4 with Coral TPU.",
                "link_or_doi": "https://doi.org/10.1145/example-preprint"
            },
            "status": "Under Review",
            "anonymous_public": True,
            "history": [
                ("None", "Submitted", "Submitted for review.", karan),
                ("Submitted", "Under Review", "Reviewer validating dataset distribution.", reviewer_user)
            ],
            "upvoters": [aarav]
        },
        {
            "author": aarav,
            "category": "research",
            "title": "Energy Efficiency Benchmarking of ARM vs RISC-V in Edge Computing Nodes",
            "summary": "Preliminary power-consumption benchmarks of Cortex-A53 against StarFive JH7110 RISC-V SBC.",
            "details": (
                "We evaluated power consumption under matrix multiplication workloads between Raspberry Pi 3 (ARM) "
                "and VisionFive 2 (RISC-V). Initial results show competitive efficiency for integer arithmetic on RISC-V."
            ),
            "tags": "risc-v, arm, computer-architecture, energy",
            "extra": {
                "methodology": "Current shunt resistor with digital oscilloscope measuring dynamic power.",
                "key_results": "RISC-V drew 18% less idle power but took 1.3x time for FP benchmarks.",
                "link_or_doi": ""
            },
            "status": "Needs Changes",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Submitted.", aarav),
                ("Submitted", "Needs Changes", "Please include exact thermal dissipation numbers and rerun benchmarks with compiler optimization -O3.", reviewer_user)
            ],
            "upvoters": []
        },

        # --- CATEGORY 3: RESEARCH CORRECTION ---
        {
            "author": aarav,
            "category": "correction",
            "title": "TE Comp Data Structures Lab Manual: Incorrect Time Complexity for Fibonacci Heap Deletion",
            "summary": "Correction to Experiment 4 manual which erroneously states deletion amortized time as O(1) instead of O(log n).",
            "details": (
                "In the TE Computer Engineering Advanced Data Structures laboratory manual (2025-2026 edition), "
                "Experiment 4 states that deleting an arbitrary node in a Fibonacci Heap takes O(1) amortized time. "
                "This contradicts standard algorithmic literature; deletion requires Decrease-Key (O(1)) followed by "
                "Extract-Min which is amortized O(log n)."
            ),
            "tags": "syllabus, data-structures, lab-manual, correction",
            "extra": {
                "item_corrected": "TE Comp ADS Lab Manual (Exp 4, Section 2.3, Page 14)",
                "what_is_wrong": "The manual states: 'Deleting any arbitrary node in a Fibonacci heap has an amortized cost of O(1)'.",
                "what_is_correct": "The correct amortized time complexity is O(log n), because Delete(x) is implemented as DecreaseKey(x, -inf) followed by ExtractMin().",
                "evidence_source": "Cormen, Leiserson, Rivest, Stein (CLRS) 'Introduction to Algorithms', 4th Edition, Chapter 19, Theorem 19.3."
            },
            "status": "Accepted",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Correction submitted with textbook citations.", aarav),
                ("Submitted", "Under Review", "Faculty verifying CLRS textbook theorem.", reviewer_user),
                ("Under Review", "Accepted", "Verified. Errata sheet issued and digital lab manual updated.", reviewer_user)
            ],
            "upvoters": [pooja, karan, reviewer_user]
        },
        {
            "author": pooja,
            "category": "correction",
            "title": "Syllabus Unit 3 Reference Error: Outdated RFC 2616 cited instead of RFC 9110 for HTTP Semantics",
            "summary": "Correction for Computer Networks syllabus referencing obsolete RFC 2616 from 1999 instead of current RFC 9110.",
            "details": (
                "The current Computer Networks curriculum document for third-year students lists RFC 2616 as the primary "
                "reference for HTTP/1.1 protocol semantics. RFC 2616 was formally obsoleted by the IETF (first by RFC 7230-7235 and now RFC 9110). "
                "Students citing RFC 2616 in exams get penalized or learn obsolete header behaviors."
            ),
            "tags": "networks, syllabus, rfc, http, internet-standards",
            "extra": {
                "item_corrected": "SE Computer Networks Syllabus 2025, Unit 3: Application Layer, Page 7",
                "what_is_wrong": "Lists 'RFC 2616: Hypertext Transfer Protocol -- HTTP/1.1' as required reading.",
                "what_is_correct": "Should reference 'RFC 9110: HTTP Semantics (IETF Standard)' published in June 2022.",
                "evidence_source": "IETF Official Datatracker: https://datatracker.ietf.org/doc/rfc9110/ (Status: INTERNET STANDARD)"
            },
            "status": "Implemented",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Correction submitted.", pooja),
                ("Submitted", "Accepted", "Academic committee confirmed. Digital syllabus PDF revised on college portal.", reviewer_user),
                ("Accepted", "Implemented", "Correction pushed to college website notices.", admin_user)
            ],
            "upvoters": [aarav, karan, admin_user]
        },
        {
            "author": karan,
            "category": "correction",
            "title": "Applied Chemistry Lab Manual: Inaccurate Neutralization Titration Normality Formula in Exp 2",
            "summary": "Typo in denominator of normality calculation leading to a 10x error in calculated acid concentration.",
            "details": (
                "Experiment 2 on Hardness of Water in the FE Chemistry manual has a printed formula: N1*V1 = N2*(V2/100) "
                "instead of N1*V1 = N2*V2, causing first-year students to calculate 10x deviation in lab records."
            ),
            "tags": "chemistry, fe, lab-manual, errata",
            "extra": {
                "item_corrected": "FE Applied Chemistry Lab Manual, Experiment 2, Page 9, Step 5",
                "what_is_wrong": "Formula printed with unintended /100 division.",
                "what_is_correct": "Standard law of equivalence N1 * V1 = N2 * V2.",
                "evidence_source": "Vogel's Textbook of Quantitative Chemical Analysis, 6th Edition."
            },
            "status": "Needs Changes",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Submitted.", karan),
                ("Submitted", "Needs Changes", "Please clarify which print batch of the FE manual contains this typo (2024 or 2025).", reviewer_user)
            ],
            "upvoters": []
        },

        # --- CATEGORY 4: INFRASTRUCTURE SUGGESTION ---
        {
            "author": karan,
            "category": "infrastructure",
            "title": "Dual-Band Wi-Fi 6 Access Points Installation in D-Hostel 2nd & 3rd Floor Wings",
            "summary": "Resolve high packet loss and poor signal reception in D-Hostel student rooms by installing modern APs.",
            "details": (
                "Currently, the Wi-Fi signal in D-Hostel drops below -82 dBm in the end rooms of the 2nd and 3rd floors, "
                "making it impossible to participate in online hackathons or stream academic lectures. "
                "Installing two ceiling-mounted dual-band Wi-Fi 6 access points in the corridor will eliminate dead spots."
            ),
            "tags": "wifi, hostel, network, infrastructure, connectivity",
            "extra": {
                "location": "D-Hostel, 2nd & 3rd Floor Corridors",
                "problem": "Severe signal attenuation through concrete walls; average speed drops to < 1.5 Mbps in rooms 210-224.",
                "solution": "Mount 2 enterprise PoE Access Points with CAT6 cabling connected to the floor switch.",
                "priority": "High"
            },
            "status": "Implemented",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Suggestion submitted.", karan),
                ("Submitted", "Under Review", "Campus Network Administrator surveyed signal strength.", reviewer_user),
                ("Under Review", "Accepted", "Procurement sanctioned for 2 Cisco/Aruba APs.", reviewer_user),
                ("Accepted", "Implemented", "Access points installed and tested. Speed now exceeds 85 Mbps throughout the wing!", admin_user)
            ],
            "upvoters": [aarav, pooja, karan, reviewer_user, admin_user]
        },
        {
            "author": pooja,
            "category": "infrastructure",
            "title": "Solar Powered Emergency Phone Charging & Ambient Lighting Station near Sports Complex",
            "summary": "Install a weather-proof solar-charging bench near the basketball and football grounds for student safety.",
            "details": (
                "Students practicing for inter-college tournaments often stay late near the sports complex. There are currently "
                "no power outlets to charge dead phones in emergency situations. Installing a simple solar canopy with USB-C "
                "fast charging ports and LED night lighting will significantly boost convenience and campus safety."
            ),
            "tags": "solar, green-energy, safety, sports, campus",
            "extra": {
                "location": "Sports Ground & Basketball Court Perimeter",
                "problem": "No lighting or charging access after sunset; safety concern for late-night student athletes.",
                "solution": "100W solar panel with lithium battery bank powering 4 USB charging ports and dusk-to-dawn LED.",
                "priority": "Medium"
            },
            "status": "Accepted",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Submitted.", pooja),
                ("Submitted", "Accepted", "Forwarded to Campus Infrastructure Maintenance Committee. Work scheduled next month.", reviewer_user)
            ],
            "upvoters": [aarav, karan, reviewer_user]
        },
        {
            "author": aarav,
            "category": "infrastructure",
            "title": "Ergonomic Seating & Additional Power Sockets for Central Library Reading Hall",
            "summary": "Equip reading tables with grounded 3-pin power sockets and replace rigid metal chairs with cushioned ergonomic seating.",
            "details": (
                "The Central Library is heavily used during exam months. However, out of 30 study tables, only 6 have working "
                "power outlets. Students trip over extension cords or have their laptops die during research. Adding neat "
                "under-desk multi-plug strips will make the library far more productive."
            ),
            "tags": "library, study, electricity, ergonomics, facilities",
            "extra": {
                "location": "Central Library, Ground Floor Main Study Hall",
                "problem": "Lack of laptop charging sockets causing overcrowded tables and cable hazards.",
                "solution": "Install modular cable channels and surge-protected sockets under each study table row.",
                "priority": "Medium"
            },
            "status": "Under Review",
            "anonymous_public": False,
            "history": [
                ("None", "Submitted", "Suggestion submitted.", aarav),
                ("Submitted", "Under Review", "Librarian and electrician conducting feasibility inspection.", reviewer_user)
            ],
            "upvoters": [pooja, karan]
        }
    ]

    for sdata in submissions_data:
        sub = Submission.query.filter_by(title=sdata["title"]).first()
        if not sub:
            sub = Submission(
                author_id=sdata["author"].id,
                category=sdata["category"],
                title=sdata["title"],
                summary=sdata["summary"],
                details=sdata["details"],
                tags=sdata["tags"],
                status=sdata["status"],
                anonymous_public=sdata["anonymous_public"],
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=5)
            )
            sub.extra_fields = sdata["extra"]
            db.session.add(sub)
            db.session.flush()

            # Status history entries
            for i, (f_st, t_st, comment_text, actor) in enumerate(sdata["history"]):
                ch = StatusChange(
                    submission_id=sub.id,
                    actor_id=actor.id,
                    from_status=f_st,
                    to_status=t_st,
                    public_comment=comment_text,
                    internal_note=f"Evaluation step {i+1} performed by {actor.name}.",
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=5 - i)
                )
                db.session.add(ch)

            # Upvotes
            for voter in sdata.get("upvoters", []):
                up = Upvote(submission_id=sub.id, user_id=voter.id)
                db.session.add(up)

            # Add a realistic comment
            if sdata["status"] in ("Accepted", "Implemented"):
                c = Comment(
                    submission_id=sub.id,
                    author_id=reviewer_user.id,
                    body="Glad to see this progressing well. The department fully supports this student contribution!"
                )
                db.session.add(c)

    db.session.commit()
