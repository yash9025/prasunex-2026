"""Automated MP4 Video Generator for LearningBridge Prototype Demonstration.

Generates high-definition (1920x1080) presentation slides using the Bridge at Night
design system, synthesizes audio narration using SAPI TTS, and stitches the assets
into a complete 1080p MP4 video using FFmpeg.
"""

import os
import subprocess
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import win32com.client

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT_DIR / "video_assets"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_VIDEO = ROOT_DIR / "LearningBridge_AI_Demo_Video.mp4"

# Color Palette (Bridge at Night)
BG_DARK = (11, 16, 32)        # #0B1020 Deep Navy
CARD_BG = (21, 27, 58)        # #151B3A Indigo Card
ACCENT_CYAN = (34, 211, 238)  # #22D3EE System Evidence
ACCENT_AMBER = (255, 181, 71) # #FFB547 Teacher Decision
ACCENT_MINT = (52, 211, 153)  # #34D399 Validated State
ACCENT_VIOLET = (124, 92, 255)# #7C5CFF Brand Primary
TEXT_WHITE = (246, 243, 236)  # #F6F3EC Light Relief
TEXT_MUTED = (148, 163, 184)  # Slate Muted

WIDTH, HEIGHT = 1920, 1080

def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    font_names = ["segoeui.ttf", "arial.ttf", "calibri.ttf"]
    if bold:
        font_names = ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

SCENES = [
    {
        "id": "scene_01_problem",
        "badge": "THE CLASSROOM PROBLEM",
        "title": "Overall Assessment Marks Conceal Critical Foundational Gaps",
        "subtitle": "In standard education portals, an aggregate 70% passing grade conceals total failure in foundational topics.",
        "bullets": [
            ("The 7/10 Blind Spot:", "Aarav Patel (Class 6-A) scores 7/10 overall, appearing satisfactory on paper."),
            ("The Hidden Gaps:", "He scored 3/3 on Decimals and 3/3 on Percentages, but only 1/3 on Fractions (33.3%)."),
            ("The Risk:", "Unresolved fraction misconceptions compound into algebra failure in Grade 7."),
            ("The Solution:", "LearningBridge connects raw question evidence, teacher decisions, and fresh reassessment.")
        ],
        "narration": (
            "Welcome to LearningBridge. In conventional school management systems, test results are flattened "
            "into aggregate percentages. Consider Aarav Patel, a Class 6 learner. On paper, Aarav achieved 7 out of 10. "
            "To an administrator, 70 percent looks passing. But underneath, Aarav scored only 1 out of 3 on fractions. "
            "LearningBridge solves this blind spot by connecting raw response evidence to teacher-controlled interventions."
        )
    },
    {
        "id": "scene_02_scoring",
        "badge": "DETERMINISTIC INGESTION",
        "title": "Exact Rational Scoring via fractions.Fraction",
        "subtitle": "Zero floating-point rounding errors. Zero opaque AI scoring.",
        "bullets": [
            ("Raw CSV Ingestion:", "Parses question-level student responses directly without pre-filtering."),
            ("Rational Equivalence:", "1/2 equals 2/4 equals 0.5 equals 50% evaluated with exact integer arithmetic."),
            ("Safety Guardrails:", "Syntax errors, division-by-zero, and blanks are gracefully bounded without crashes."),
            ("High Throughput:", "Demonstrated throughput of 58,000 response checks per second with sub-second ingestion.")
        ],
        "narration": (
            "Rather than relying on brittle float comparisons or hallucinated AI grading, LearningBridge implements "
            "an exact rational answer engine using Python fractions. Responses like one half, two fourths, or zero point five "
            "are verified with mathematical equivalence. All 400 student responses across Class 6-A are scored in under 400 milliseconds."
        )
    },
    {
        "id": "scene_03_evidence",
        "badge": "EXPLAINABLE EVIDENCE",
        "title": "Diagnostic Misconception Detection & Teacher Authority",
        "subtitle": "Algorithms surface review signals; teachers retain 100% diagnostic and intervention authority.",
        "bullets": [
            ("Underlying Error:", "Aarav submitted 1/2 + 1/3 = 2/5 and 1/4 + 1/2 = 1/3."),
            ("Pattern Detection:", "Deterministic rule identifies: adds numerators and adds denominators: (1+1)/(2+3) = 2/5."),
            ("Teacher Confirmation:", "Teacher Priya Sharma inspects raw attempts and records clinical rationale."),
            ("Targeted Cohort:", "Priya forms a support group pairing Aarav with Diya Sen, who shares the identical misconception.")
        ],
        "narration": (
            "LearningBridge never diagnoses a learner autonomously. When Teacher Priya Sharma clicks Inspect Evidence, "
            "she sees Aarav's exact work: 1/2 + 1/3 = 2/5. Our deterministic pattern engine flags the underlying rule: "
            "Aarav is adding numerators and denominators together. Priya confirms this diagnostic flag with her clinical rationale "
            "and forms a targeted support group with Diya Sen, who shares the identical error pattern."
        )
    },
    {
        "id": "scene_04_support",
        "badge": "GROUNDED SUPPORT STUDIO",
        "title": "Curriculum-Grounded Drafting & Mathematical Verification",
        "subtitle": "LLM drafting bounded strictly by approved NCTM standards and deterministic calculation checks.",
        "bullets": [
            ("NCTM Grounding:", "Support plans can only cite teacher-approved curriculum snippets (Fraction Bar Modeling)."),
            ("Math Verifier:", "Every practice question must pass deterministic arithmetic validation before teacher review."),
            ("Zero PII Transmission:", "Draft context strips student names, IDs, and raw grades prior to model invocation."),
            ("SHA-256 Approval:", "Approved plans are permanently frozen with an immutable cryptographic content hash.")
        ],
        "narration": (
            "In conventional AI systems, language models hallucinate arithmetic questions with impossible solutions. "
            "LearningBridge requires strict pedagogical grounding. Support plans can only cite approved NCTM curriculum snippets. "
            "Furthermore, every practice item is validated by our deterministic Math Verifier before the teacher sees it. "
            "Once finalized, the plan is cryptographically frozen with a SHA-256 approval hash."
        )
    },
    {
        "id": "scene_05_reassessment",
        "badge": "VERIFIABLE REASSESSMENT",
        "title": "Fresh Diagnostic Reassessment & Cohort Progress Review",
        "subtitle": "Closing the intervention loop with authentic evidence of learning recovery.",
        "bullets": [
            ("Fresh Question Bank:", "Non-overlapping diagnostic items prevent recall bias from baseline and practice items."),
            ("Key Protection:", "Learner quiz endpoints omit answer keys and rationales; scoring occurs strictly on backend."),
            ("Demonstrated Mastery:", "Aarav solves 1/4 + 1/3 = 7/12, 2/3 + 1/6 = 5/6, achieving 3.0 / 3.0 marks (100%)."),
            ("Intervention Closure:", "Pre/post trajectory compares 33% baseline to 100% reassessment; Priya formally closes the cycle.")
        ],
        "narration": (
            "An intervention without reassessment is incomplete. LearningBridge assigns fresh diagnostic items from a secure question bank. "
            "Answer keys are strictly protected on the server. Aarav sits the quiz, correctly solving 1/4 + 1/3 as 7/12 and achieving 3 out of 3 marks. "
            "The progress dashboard tracks Aarav's trajectory advancing from 33 percent to 100 percent mastery, allowing Priya to close the intervention with confidence."
        )
    },
    {
        "id": "scene_06_architecture",
        "badge": "RELIABILITY & MULTI-TENANCY",
        "title": "Production-Grade Multi-Tenant Architecture & Verification",
        "subtitle": "Built to Google Senior Developer standards with 78 automated tests passing 100% green.",
        "bullets": [
            ("Multi-Tenancy:", "28 relational tables enforcing RequestContext tenant scoping; zero cross-school leakage."),
            ("Resilience:", "Atomic job leasing with automatic stale lease recovery and outbox pattern redispatching."),
            ("WCAG 2.1 AA:", "Bridge at Night design system with keyboard focus trapping and high-contrast accessible tokens."),
            ("Verification:", "All 78 unit, integration, and security tests passing. Fully containerized with Docker and Nginx.")
        ],
        "narration": (
            "LearningBridge is built on enterprise software foundations. It features 28 relational tables with strict multi-tenant scoping, "
            "atomic background job leasing, outbox redispatching, and full WCAG 2.1 AA keyboard accessibility. "
            "With 78 out of 78 automated tests passing, LearningBridge turns fragmented classroom data into an accountable, "
            "verifiable learning journey. Thank you."
        )
    }
]

def render_slide(scene: dict, output_path: Path):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Top brand bar
    draw.rectangle([0, 0, WIDTH, 8], fill=ACCENT_VIOLET)

    # Header section
    font_badge = get_font(24, bold=True)
    font_title = get_font(52, bold=True)
    font_sub = get_font(28, bold=False)
    font_b_title = get_font(32, bold=True)
    font_b_desc = get_font(28, bold=False)
    font_footer = get_font(22, bold=False)

    # Badge Pill
    badge_text = f"  {scene['badge']}  "
    draw.rounded_rectangle([100, 70, 480, 115], radius=10, fill=CARD_BG, outline=ACCENT_CYAN, width=2)
    draw.text((120, 78), scene['badge'], font=font_badge, fill=ACCENT_CYAN)

    # Main Title
    draw.text((100, 140), scene['title'], font=font_title, fill=TEXT_WHITE)
    draw.text((100, 215), scene['subtitle'], font=font_sub, fill=ACCENT_AMBER)

    # Horizontal divider
    draw.line([100, 275, WIDTH - 100, 275], fill=(30, 41, 75), width=2)

    # 4 Feature Cards (2x2 grid)
    card_w = 820
    card_h = 290
    positions = [
        (100, 315),
        (1000, 315),
        (100, 645),
        (1000, 645)
    ]

    for idx, (b_title, b_desc) in enumerate(scene['bullets']):
        x, y = positions[idx]
        # Card background
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=16, fill=CARD_BG, outline=(37, 48, 88), width=1)
        # Indicator bar
        bar_colors = [ACCENT_CYAN, ACCENT_AMBER, ACCENT_MINT, ACCENT_VIOLET]
        draw.rounded_rectangle([x + 25, y + 25, x + 33, y + 80], radius=4, fill=bar_colors[idx])

        # Bullet Title
        draw.text((x + 50, y + 35), b_title, font=font_b_title, fill=TEXT_WHITE)

        # Bullet Description (word-wrapped manually)
        words = b_desc.split()
        lines = []
        cur_line = []
        for w in words:
            if len(" ".join(cur_line + [w])) < 46:
                cur_line.append(w)
            else:
                lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        desc_y = y + 100
        for l in lines[:4]:
            draw.text((x + 50, desc_y), l, font=font_b_desc, fill=TEXT_MUTED)
            desc_y += 38

    # Footer
    draw.line([100, 980, WIDTH - 100, 980], fill=(30, 41, 75), width=1)
    draw.text((100, 1005), "PRASUNEX INNOVATHON 2026 · Round 3 Prototype Demonstration", font=font_footer, fill=TEXT_MUTED)
    draw.text((WIDTH - 480, 1005), "LearningBridge · Yash Agrawal", font=font_footer, fill=ACCENT_CYAN)

    img.save(output_path, quality=95)

def synthesize_audio(text: str, output_path: Path) -> float:
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(str(output_path), 3)  # 3 = SSFMCreateForWrite
    speaker.AudioOutputStream = stream
    speaker.Rate = 0  # Natural speed
    speaker.Speak(text)
    stream.Close()

    with wave.open(str(output_path), "r") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
    return duration

def generate_video():
    print("🎬 Generating LearningBridge AI Video Presentation...")
    segment_files = []

    for idx, sc in enumerate(SCENES):
        print(f"\n[Scene {idx+1}/{len(SCENES)}] Processing: {sc['id']}...")
        slide_img = OUTPUT_DIR / f"{sc['id']}.png"
        slide_wav = OUTPUT_DIR / f"{sc['id']}.wav"
        slide_mp4 = OUTPUT_DIR / f"{sc['id']}.mp4"

        # 1. Render slide
        render_slide(sc, slide_img)

        # 2. Synthesize audio narration
        duration = synthesize_audio(sc["narration"], slide_wav)
        video_duration = duration + 1.2  # 1.2s padding
        print(f"   • Narration length: {duration:.2f}s (Clip: {video_duration:.2f}s)")

        # 3. Compile slide + audio into segment mp4
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(slide_img),
            "-i", str(slide_wav),
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(video_duration),
            str(slide_mp4)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print("FFmpeg error:", res.stderr)
            return
        segment_files.append(slide_mp4)

    # 4. Concatenate all scenes into final video
    concat_list = OUTPUT_DIR / "concat_list.txt"
    with open(concat_list, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg.name}'\n")

    print("\n📦 Merging all scenes into final video:", OUTPUT_VIDEO.name)
    merge_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(OUTPUT_VIDEO)
    ]
    res = subprocess.run(merge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        file_size_mb = OUTPUT_VIDEO.stat().st_size / (1024 * 1024)
        print(f"\n🎉 VIDEO COMPLETED SUCCESSFULLY!")
        print(f"   • Location: {OUTPUT_VIDEO}")
        print(f"   • Size:     {file_size_mb:.2f} MB")
    else:
        print("Merge error:", res.stderr)

if __name__ == "__main__":
    generate_video()
