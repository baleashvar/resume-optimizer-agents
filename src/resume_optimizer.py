import os
import sys
import time
from docx import Document
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_FAST = os.environ.get("MODEL_FAST", "llama-3.3-70b-versatile")
MODEL_SMALL = os.environ.get("MODEL_SMALL", "llama-3.1-8b-instant")
MAX_ROUNDS = 2

TARGET_SECTIONS = {"summary", "experience", "skills"}

SECTION_HEADERS = {
    "summary": ["summary", "professional summary", "profile", "objective"],
    "experience": ["experience", "work experience", "employment", "work history"],
    "skills": ["skills", "technical skills", "core competencies", "key skills"],
}


def call_agent(model: str, system_prompt: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=400,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def writer_prompt_for(section: str, text: str, job_context: str) -> tuple[str, str]:
    if section == "summary":
        system = "Complete the template. Output only the filled template, nothing else."
        user = f"""{job_context}

Fill this template using the original text below:
TEMPLATE: [Job Title] with [X] years of experience in [skills]. Proven track record of [achievement] at [company].

Original: {text}

Filled template:"""
    elif section == "experience":
        system = "Convert job duties to bullet points. Output only bullets starting with -, nothing else."
        user = f"""{job_context}

Rewrite each duty as a bullet point starting with - using action verbs. Max 3 bullets per role.

Original:
{text}

Bullet points:"""
    else:
        system = "List skills as comma-separated values. Output only the list, nothing else."
        user = f"""{job_context}

Extract and list all skills as: Languages: x, y | Cloud: a, b

Original:
{text}

Skills list:"""
    return system, user


CRITIC_SYSTEM = "Output only: 1. [issue] 2. [issue]"
CEO_SYSTEM = "Output only APPROVED or REVISE: [reason]"


def detect_section(text: str) -> str | None:
    lower = text.strip().lower().rstrip(":")
    for section, aliases in SECTION_HEADERS.items():
        if lower in aliases:
            return section
    return None


def parse_docx_sections(path: str):
    doc = Document(path)
    paragraphs = []
    current_section = None
    for para in doc.paragraphs:
        text = para.text.strip()
        section_match = detect_section(text)
        if section_match:
            current_section = section_match
        paragraphs.append({
            "para": para,
            "text": text,
            "section": current_section,
            "is_header": section_match is not None,
            "style": para.style.name,
            "alignment": para.alignment,
        })
    return doc, paragraphs


def get_section_text(paragraphs: list, section: str) -> str:
    lines = []
    in_section = False
    for item in paragraphs:
        if item["is_header"] and item["section"] == section:
            in_section = True
            continue
        if in_section:
            if item["is_header"]:
                break
            if item["text"]:
                lines.append(item["text"])
    return "\n".join(lines)


def clean_output(text: str) -> str:
    bad_starts = ["here is", "here's", "to rewrite", "note:", "heading:"]
    lines = []
    for line in text.split("\n"):
        low = line.strip().lower()
        if any(low.startswith(b) for b in bad_starts):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def improve_section(section_name: str, section_text: str, job_context: str) -> str:
    current = section_text
    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"  ✍️  Writer improving {section_name} (round {round_num})...")
        w_system, w_user = writer_prompt_for(section_name, current, job_context)
        improved = clean_output(call_agent(MODEL_FAST, w_system, w_user))
        if not improved:
            improved = current

        print(f"  🔍 Critic reviewing {section_name}...")
        critique = call_agent(MODEL_SMALL, CRITIC_SYSTEM, f"Section ({section_name}):\n{improved}")
        print(f"     Critique: {critique}\n")

        print(f"  👔 CEO evaluating {section_name}...")
        decision = call_agent(MODEL_SMALL, CEO_SYSTEM, f"Section:\n{improved}\nCritic:\n{critique}")
        print(f"     CEO: {decision}\n")

        current = improved
        if decision.strip().upper().startswith("APPROVED"):
            print(f"  ✅ {section_name} approved!\n")
            break

    return current


def write_improved_docx(original_doc: Document, paragraphs: list, improved_sections: dict, output_path: str):
    new_doc = Document()
    for section in original_doc.sections:
        new_section = new_doc.sections[0]
        new_section.top_margin = section.top_margin
        new_section.bottom_margin = section.bottom_margin
        new_section.left_margin = section.left_margin
        new_section.right_margin = section.right_margin
        break

    current_section = None
    skip_until_next_header = False

    for item in paragraphs:
        if item["is_header"]:
            current_section = item["section"]
            skip_until_next_header = False
            new_para = new_doc.add_paragraph(item["text"])
            try:
                new_para.style = new_doc.styles[item["style"]]
            except KeyError:
                new_para.style = new_doc.styles["Normal"]
            new_para.alignment = item["alignment"]
            if current_section in improved_sections:
                for line in improved_sections[current_section].split("\n"):
                    line = line.strip()
                    if line:
                        p = new_doc.add_paragraph(line)
                        p.alignment = item["alignment"]
                skip_until_next_header = True
            continue

        if skip_until_next_header and current_section in improved_sections:
            continue

        new_para = new_doc.add_paragraph(item["text"])
        try:
            new_para.style = new_doc.styles[item["style"]]
        except KeyError:
            new_para.style = new_doc.styles["Normal"]
        new_para.alignment = item["alignment"]

    new_doc.save(output_path)
    print(f"\n✅ Resume saved to: {output_path}")


def run_pipeline(resume_path: str, job_role: str, jd_path: str = None):
    print(f"\n📄 Loading resume: {resume_path}")
    doc, paragraphs = parse_docx_sections(resume_path)

    job_context = f"Target Job Role: {job_role}"
    if jd_path:
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read().strip()
        job_context += f"\n\nJob Description:\n{jd_text}"
        print(f"📋 Job description loaded from: {jd_path}")

    print(f"🎯 Job role: {job_role}\n")

    improved_sections = {}
    for section in TARGET_SECTIONS:
        section_text = get_section_text(paragraphs, section)
        if not section_text:
            print(f"⚠️  Section '{section}' not found, skipping.\n")
            continue
        print(f"{'='*50}")
        print(f"📝 Improving section: {section.upper()}")
        print(f"{'='*50}")
        improved_sections[section] = improve_section(section, section_text, job_context)

    base = os.path.splitext(resume_path)[0]
    output_path = f"{base}_improved.docx"
    write_improved_docx(doc, paragraphs, improved_sections, output_path)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python resume_optimizer.py <resume.docx> <job_role> [--jd job_description.txt]")
        print('Example: python resume_optimizer.py resume.docx "MLOps Engineer"')
        sys.exit(1)

    jd_file = None
    args = sys.argv[1:]
    if "--jd" in args:
        jd_index = args.index("--jd")
        jd_file = args[jd_index + 1]
        args = args[:jd_index] + args[jd_index + 2:]

    run_pipeline(args[0], " ".join(args[1:]), jd_file)
