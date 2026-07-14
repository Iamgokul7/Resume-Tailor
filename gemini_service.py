# -*- coding: utf-8 -*-
"""
gemini_service.py - Wraps the Google Gemini API call for resume tailoring.

Uses the current google-genai SDK (google.genai).
Single responsibility: send the content bank + JD to Gemini and return
a validated Python dict matching the tailored-resume schema.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
import collections
from typing import Any

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini client setup
# ---------------------------------------------------------------------------

# Ordered list of known-working model names for automatic fallback
GEMINI_MODELS = ["gemini-3.1-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash"]

SYSTEM_INSTRUCTION = """You are a professional resume tailoring assistant and senior recruiter. Your job is to extract contact details, build a semantic profile of the candidate, perform an intelligent semantic analysis of the Job Description (JD), select a dynamic resume strategy, and generate a tailored resume along with a scoring dashboard.

Follow these instructions strictly to ensure the tailored output is of the highest quality:

1. INTELLIGENT JOB DESCRIPTION (JD) UNDERSTANDING & DYNAMIC REORDERING:
   - Semantically analyze the JD to prioritize requirements:
     * HIGH PRIORITY: Core programming languages, frameworks, tech skills, required years of experience, and primary responsibilities.
     * MEDIUM PRIORITY: Preferred tools, methodologies, testing practices, databases, DevOps, security, and cloud ecosystems.
     * LOW PRIORITY: Equal opportunity statements, legal disclaimers, fraud warnings, marketing pitches, benefits.
   - Ignore company marketing, benefits, and low priority statements completely.
   - Dynamically identify the core focus of the target job (e.g., Backend, Frontend, Cloud, QA, Cybersecurity, Data Analyst, Business Analyst, Support, SAP/ERP, AI/ML, etc.) and automatically reorder the Technical Skill categories to place the most important domain categories first. Do not use fixed templates. Within each category, prioritize the individual items by relevance.
   - Only reorder existing skills from the candidate's master resume. Do not invent new skills.

2. TECHNICAL SKILL NORMALIZATION:
   - Reduce redundancy in technical skills by grouping related items under normalized category headings. For example, instead of separate items for 'MySQL' and 'SQLite' under a flat list, prefer 'Relational Databases (MySQL, SQLite)' where it improves readability. Instead of 'OCI', prefer 'Cloud Platforms (Oracle Cloud Infrastructure)'. Ensure all original technologies are preserved and normalized rather than deleted. Normalization must only be done when it improves readability.

3. IMPACT-FOCUSED BULLET REWRITING:
   - Rewrite project and internship bullets to emphasize the outcome, purpose, or functional impact of the tasks rather than just describing the tasks.
   - Good examples:
     * Instead of: 'Developed REST APIs.' -> Prefer: 'Developed REST APIs supporting secure data exchange across multiple application modules.'
     * Instead of: 'Tested application.' -> Prefer: 'Performed functional and regression testing to identify defects and improve application reliability.'
   - CRITICAL SAFETY RULE: Never fabricate metrics, percentages, business impact, scale, or outcomes. If no metric or business outcome exists in the source resume, rewrite only for clarity, purpose, and stronger active wording, preserving absolute factual truthfulness.

4. SEMANTIC JD MAPPING:
   - Ensure high semantic mapping rather than verbatim keyword mirroring. If the JD uses a generic term (e.g., 'Software Applications' or 'Internet-related tools') and the candidate has a specific, truthful equivalent experience (e.g., 'REST APIs' or 'Web Applications'), use the candidate's specific terms instead of copying the broad/vague JD wording. Express experience naturally. Never copy generic JD phrases blindly without candidate-supported context.

5. REWRITING BULLETS LIKE A SENIOR RECRUITER & TARGET COUNT:
   - Rewrite project and internship bullets to be concise, natural, and achievement-oriented.
   - Lead every bullet with a strong action verb (e.g., Designed, Built, Developed, Implemented, Integrated, Created, Validated, Improved, Optimized, Configured, Analyzed, Tested, Maintained, Refined, Documented, Verified, Reviewed, Generated, Debugged).
   - NEVER overuse verbs like "Engineered", "Architected", "Leveraged", "Utilized", "Programmed" unless context genuinely requires it.
   - Avoid AI-sounding robotic phrases or keyword dumping. Every sentence must read naturally and vary in structure.
   - Target approximately 18–25 words per bullet point for readability.

6. PROFESSIONAL SUMMARY REWRITING:
   - Generate a brand-new professional summary under 4 lines for every JD.
   - Reflect the candidate's actual background and highlight the most relevant skills matching the target role naturally.
   - NEVER use generic buzzword openings (e.g., "Forward-thinking", "Passionate", "Results-driven", "Dynamic", "Detail-oriented"). Open immediately with the candidate's actual professional identity and key expertise.
   - Never mention the target company's name.

7. INTELLIGENT BULLET PRIORITIZATION:
   - Within each project and internship, sort bullets by relevance to the JD (e.g., database/API work first for a backend role, test automation/regression testing first for a QA role, etc.).

8. STRONG ACTION VERB ROTATION & ACTIVE VOICE:
   - Do NOT repeat the same starting verb multiple times within a project or experience section. Rotate naturally to show diverse capability.
   - Use active voice exclusively. Do not write passive sentences (e.g. "A system was built by...").

9. KEYWORD INTEGRATION ENGINE (STRICT HONESTY):
   - Truthfulness is your highest priority. Never fabricate, exaggerate, or stretch claims. Everything must be directly traceable to the master resume.
   - Integrate keywords naturally within meaningful sentences. If a keyword cannot be truthfully integrated based on the candidate's real experience, do not add it.

10. EDUCATION & GRADE FORMATTING:
    - For B.E., B.Tech, M.Tech, MCA, MBA, or other university/college degrees, represent scores as CGPA / 10.00 (e.g. "9.1/10.00" or "8.5/10.00" depending on the master resume score).
    - For school-level degrees/certificates (HSC, SSC, XII, X, Matriculation), mention scores as percentages (e.g. "92%").
    - Do NOT add coursework unless it exists verbatim in the master resume's education entry.

11. RESUME SCORING DASHBOARD:
    - Assess the final tailored resume against the JD to generate realistic scores and professional feedback:
      * "ats_score": Integer (0-100) based on clean formatting (no tables, single column, standard headings, machine-readability).
      * "ats_explanation": Clear rationale for the ATS score.
      * "readability_score": Integer (0-100) based on senior recruiter bullet quality, active verbs, flow, and word count.
      * "readability_explanation": Clear rationale for readability.
      * "match_score": Integer (0-100) representing true capability fit against the prioritized JD requirements.
      * "match_explanation": Clear rationale for match score.
      * "keyword_coverage": Integer (0-100) percentage of selected keywords integrated.
      * "missing_skills": List of important skills from the JD missing in the candidate's profile.
      * "weaknesses": List of potential weaknesses in the candidate's match profile (e.g. gaps in specific technologies).
      * "strengths": List of candidate's strongest matching points.
      * "improvements": List of actionable improvement suggestions.

Return ONLY a valid JSON object matching this exact schema — no markdown, no prose, no code fences:
{
  "tailored_resume": {
    "contact": {
      "name": "<string>",
      "location": "<string>",
      "email": "<string>",
      "phone": "<string>",
      "linkedin": "<string>",
      "github": "<string>",
      "portfolio": "<string>"
    },
    "summary": "<string>",
    "skills_selected": [{"category": "<string>", "items": ["<string>"]}],
    "flagship_projects_selected": [
      {
        "name": "<string>",
        "dates": "<string>",
        "tech_stack": "<string>",
        "github_link": "<string>",
        "bullets": ["<string>"]
      }
    ],
    "other_projects_selected": [
      {
        "name": "<string>",
        "dates": "<string>",
        "tech_stack": "<string>",
        "github_link": "<string>",
        "bullets": ["<string>"]
      }
    ],
    "internships_selected": [
      {
        "company": "<string>",
        "role": "<string>",
        "dates": "<string>",
        "bullets": ["<string>"]
      }
    ],
    "education": [
      {
        "institution": "<string>",
        "degree": "<string>",
        "dates": "<string>",
        "gpa": "<string>",
        "relevant_coursework": "<string>"
      }
    ],
    "certifications": [
      {
        "name": "<string>",
        "issuer": "<string>",
        "date": "<string>"
      }
    ]
  },
  "dashboard": {
    "ats_score": <int>,
    "ats_explanation": "<string>",
    "readability_score": <int>,
    "readability_explanation": "<string>",
    "match_score": <int>,
    "match_explanation": "<string>",
    "keyword_coverage": <int>,
    "missing_skills": ["<string>"],
    "weaknesses": ["<string>"],
    "strengths": ["<string>"],
    "improvements": ["<string>"]
  }
}"""



# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _generate_fallback_dashboard(tailored: dict[str, Any], jd_text: str) -> dict[str, Any]:
    """Generates a fallback dashboard analysis in case the model does not return one."""
    return {
        "ats_score": 85,
        "ats_explanation": "Single-column format, standard section headings, and machine-readable text structures ensure high ATS compatibility.",
        "readability_score": 80,
        "readability_explanation": "Action-oriented bullet points starting with strong verbs provide clear readability for recruiters.",
        "match_score": 75,
        "match_explanation": "Factual experiences align moderately well with the core responsibilities of the role.",
        "keyword_coverage": 70,
        "missing_skills": [],
        "weaknesses": ["Preferred tools or secondary frameworks not explicitly found in the master resume."],
        "strengths": ["Strong foundational background relevant to the key role description."],
        "improvements": ["Consider highlighting quantifiable metrics for completed project bullets."]
    }


def tailor_resume(master_resume: str, jd_text: str, selected_keywords: list[str] | None = None) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    """
    Send the master resume text and JD to Gemini; return the parsed tailored-resume dict,
    a list of warnings, and the scoring dashboard dict.

    Raises:
        ValueError: If the API key is missing, Gemini returns non-parseable JSON,
                    or a structurally invalid response.
    """
    from google import genai  # type: ignore   # import at call-time to avoid crash on startup
    from google.genai import types as genai_types  # type: ignore

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Add it to your .env file and restart the server."
        )

    client = genai.Client(api_key=api_key)

    keywords_instruction = ""
    if selected_keywords:
        kw_list = ", ".join(selected_keywords)
        keywords_instruction = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER-SELECTED KEYWORDS TO INTEGRATE: {kw_list}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT — How to integrate these keywords:

These are the EXACT keywords the user wants reflected in the final resume. Follow these rules STRICTLY:

1. PROFESSIONAL SUMMARY (highest priority):
   - The summary MUST open by establishing the candidate's identity using 1–2 of the most important keywords from the list above.
   - Weave at least 4–6 of the selected keywords naturally into the summary paragraph.
   - The summary should read like a confident, senior-authored career statement — not a keyword list. Do NOT use buzzword openers (e.g. "Forward-thinking", "Dynamic").
   - Example tone: "Full-stack software engineer with a strong foundation in Python and Flask, experienced in building REST APIs and managing the complete SDLC from design to production deployment."

2. TECHNICAL SKILLS SECTION:
   - ALL selected keywords that are technologies, tools, languages, or frameworks MUST appear in the skills section.
   - Keywords already present in the master resume keep their original category.
   - Keywords from the JD that are NOT in the master resume but ARE in the selected list should be added to the most appropriate existing skill category ONLY IF the candidate's bullets or project descriptions genuinely demonstrate that skill (even if named differently). Do NOT add a skill that has zero evidence in the resume.
   - NEVER copy category headers or activity phrases (e.g., "Software Development," "Testing") into the skills items list.
   - Reorder skill categories so the most JD-relevant ones appear first.

3. PROJECT BULLETS:
   - Rewrite project bullets to use the JD's vocabulary and the selected keywords wherever the underlying fact honestly supports it.
   - Each major project should contain at least 1–2 of the selected keywords in its bullets, woven into the context of what was actually built (e.g., "Designed REST APIs in Flask to expose...", "Managed full SDLC from requirements gathering to Docker-based deployment...").
   - Do NOT repeat the same keyword in every bullet — spread them across bullets for natural flow.
   - Ensure bullets lead with strong action verbs in the past tense, and never end with a vague or generic filler phrase.

4. INTERNSHIP BULLETS:
   - Apply the same keyword-weaving approach but with a lighter touch since internships are supporting evidence.
   - If a keyword clearly maps to something done in an internship (e.g. "HTML/CSS" for a frontend intern), include it in that bullet naturally.

5. NATURALNESS CHECK (mandatory):
   - After composing every section, mentally re-read it. If any keyword placement sounds forced, robotic, or out of context, REWRITE that sentence until the keyword reads as if the candidate would have written it themselves.
   - A reader should never be able to tell that keywords were selectively inserted — the resume must read as one coherent, professionally authored document.
"""

    prompt = f"""Below is the candidate's complete master resume content (raw text extracted from their PDF/DOCX):

{master_resume}

---

Job Description:
{jd_text}
{keywords_instruction}

---

Using ONLY the facts and experiences present in the master resume above, produce a tailored resume and dashboard JSON \
matching the schema in your system instructions. Follow the schema exactly. \
Extract all available contact details (name, email, phone, location, linkedin, github, portfolio) from the master resume. \
Write every section — especially the summary and project bullets — with the quality and precision of \
a professional resume writer: clear, concise, achievement-oriented sentences that flow naturally. \
Sort bullets within each project or experience by relevance to the JD, rotate starting action verbs naturally, \
and use active voice. Do not add any text outside the JSON object."""

    try:
        response = generate_content_with_fallback(
            client=client,
            prompt=prompt,
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4
        )
    except Exception as exc:
        logger.error("All models failed during tailoring: %s", exc)
        raise

    raw_text: str = response.text
    logger.info("Received Gemini response (%d chars).", len(raw_text))

    tailored_data, dashboard_data = _parse_json_response(raw_text)
    cleaned = clean_tailored_resume(tailored_data, master_resume)
    finalized, quality_warnings = validate_and_correct_resume(cleaned, master_resume, jd_text)
    
    if not dashboard_data:
        dashboard_data = _generate_fallback_dashboard(finalized, jd_text)

    return finalized, quality_warnings, dashboard_data


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def generate_content_with_fallback(
    client: Any,
    prompt: str,
    system_instruction: str,
    temperature: float,
) -> Any:
    """
    Tries to generate content using GEMINI_MODELS list sequentially.
    On 429/503, performs exponential backoff retries.
    On 404 (model not found), falls back immediately.
    On any other error, falls back to the next model.
    """
    from google.genai import types as genai_types
    from google.genai.errors import APIError

    last_exception = None

    for model in GEMINI_MODELS:
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                logger.info("Attempting generation using model: %s (attempt %d/%d)...", model, attempt + 1, max_retries + 1)
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                    ),
                )
                logger.info("Generation successful using model: %s", model)
                return response
            except APIError as exc:
                last_exception = exc
                err_msg = str(exc).lower()
                status_code = getattr(exc, "code", None)

                # Check if it's 404 (Model not found)
                if status_code == 404 or "404" in err_msg or "not_found" in err_msg:
                    logger.warning("Model %s not found (404). Falling back immediately...", model)
                    break  # Break out of attempts loop to try the next model

                # Check if it's a transient error (429 or 503)
                is_transient = (status_code in (429, 503) or
                                any(term in err_msg for term in ["429", "503", "resource_exhausted", "quota", "unavailable"]))

                if is_transient and attempt < max_retries:
                    # Exponential backoff: 2s, 4s
                    delay = (2 ** attempt) * 2 + random.uniform(0.1, 0.5)
                    logger.warning("Transient error (%s) on model %s. Retrying in %.2fs...", status_code or "APIError", model, delay)
                    time.sleep(delay)
                    continue
                else:
                    logger.warning("Model %s failed with error: %s. Falling back to next model...", model, exc)
                    break
            except Exception as exc:
                last_exception = exc
                logger.warning("Unexpected error on model %s: %s. Falling back to next model...", model, exc)
                break

    if last_exception:
        raise last_exception
    raise RuntimeError("All models failed to generate content.")


def clean_tailored_resume(data: dict[str, Any], master_resume: str) -> dict[str, Any]:
    """
    Applies strict Python-based cleaning guardrails to ensure LLM output does not:
    1. Open with banned buzzwords (like 'Forward-thinking').
    2. Invent coursework if not in master resume.
    3. Include unearned stakeholder/deployment claims.
    4. Include inflated enterprise project descriptions.
    """
    if not isinstance(data, dict):
        return data

    # 1. Clean Summary: Strip any banned buzzwords (case-insensitive)
    banned_buzzwords = [
        "forward-thinking", "forward thinking", "dynamic", "passionate", 
        "results-driven", "results driven", "motivated", "dedicated", 
        "energetic", "creative", "experienced", "innovative", "proven ability", 
        "successful", "highly skilled", "detail-oriented", "detail oriented", 
        "enthusiastic", "proactive"
    ]
    
    summary = data.get("summary", "").strip()
    if summary:
        # Loop to strip multiple occurrences of leading buzzwords, e.g. "Forward-thinking and passionate software engineer..."
        while True:
            # Matches optional leading articles/adverbs + the buzzword + optional trailing conjunctions/punctuation/space
            pattern = r"^(?:a|an|the)?\s*(" + "|".join(banned_buzzwords) + r")(?:\b|,|\s*and\s*|\s*with\s*)*"
            match = re.match(pattern, summary, re.IGNORECASE)
            if not match:
                break
            # Remove the match
            summary = summary[match.end():].strip()
        
        # If we ended up stripping everything, default to a clean entry
        if not summary:
            summary = "Software engineer focused on full-stack application development."
        
        # Capitalize the first letter
        summary = summary[0].upper() + summary[1:]
        data["summary"] = summary

    # 2. Clean Coursework: Ensure no coursework is generated if not in master resume
    master_lower = master_resume.lower()
    has_coursework_in_master = "coursework" in master_lower or "subjects" in master_lower or "relevant course" in master_lower
    if not has_coursework_in_master:
        for edu in data.get("education", []):
            edu["relevant_coursework"] = ""

    # 3. Clean Project & Experience inflation and unearned claims
    # (Stakeholder collaboration, enterprise-level ERP, customer deployment, etc.)
    # We will sanitize specific phrases that violate the strict facts in Gokul's resume
    inflated_phrases = {
        "proven ability to deploy, customize, and troubleshoot scalable systems": "Experienced in building, testing, and debugging full-stack web applications",
        "proven ability to deploy, customize, and troubleshoot": "Experienced in building, testing, and debugging",
        "collaborating closely with stakeholders to drive product adoption": "implementing clean, functional UI/UX and efficient backend APIs",
        "collaborating closely with stakeholders": "collaborating with team members",
        "drive product adoption": "ensure correct implementation",
        "mirror enterprise-level sap/erp functionality": "implement ERP-inspired user flows and business process automation",
        "mirror enterprise-level sap/erp": "implement ERP-inspired",
        "enterprise-level sap/erp": "ERP-inspired",
        "enterprise-level": "project-level",
        "enterprise grade": "project grade",
        "enterprise-grade": "functional",
        "production-grade": "well-tested",
        "production grade": "well-tested",
        "industry-standard": "reliable",
        "industry standard": "reliable"
    }

    def sanitize_text(text: str) -> str:
        if not isinstance(text, str):
            return text
        lower_text = text.lower()
        for phrase, replacement in inflated_phrases.items():
            if phrase in lower_text:
                # Use case-insensitive replacement
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                text = pattern.sub(replacement, text)
        return text

    # Clean summary, project bullets, internship bullets
    if "summary" in data:
        data["summary"] = sanitize_text(data["summary"])

    for proj in data.get("flagship_projects_selected", []):
        if "bullets" in proj and isinstance(proj["bullets"], list):
            proj["bullets"] = [sanitize_text(bullet) for bullet in proj["bullets"]]

    for proj in data.get("other_projects_selected", []):
        if "bullets" in proj and isinstance(proj["bullets"], list):
            proj["bullets"] = [sanitize_text(bullet) for bullet in proj["bullets"]]

    for intern in data.get("internships_selected", []):
        if "bullets" in intern and isinstance(intern["bullets"], list):
            intern["bullets"] = [sanitize_text(bullet) for bullet in intern["bullets"]]

    return data


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json … ``` or ``` … ``` wrappers if Gemini added them."""
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?```\s*$"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _parse_json_response(raw: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Strip fences, parse JSON, and do a basic schema sanity-check."""
    cleaned = _strip_markdown_fences(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned non-JSON: %s", cleaned[:500])
        raise ValueError(
            f"Gemini response could not be parsed as JSON: {exc}"
        ) from exc

    required_keys = {
        "contact",
        "summary",
        "skills_selected",
        "flagship_projects_selected",
        "other_projects_selected",
        "internships_selected",
        "education",
        "certifications",
    }

    if "tailored_resume" in data:
        resume_data = data["tailored_resume"]
        dashboard_data = data.get("dashboard")
    else:
        resume_data = data
        dashboard_data = None

    missing = required_keys - set(resume_data.keys())
    if missing:
        raise ValueError(
            f"Gemini response is missing required keys: {missing}"
        )

    return resume_data, dashboard_data


def analyze_jd_match(master_resume: str, jd_text: str) -> dict[str, Any]:
    """
    Analyzes the master resume against the job description and returns match statistics.
    Returns:
        A dict matching the schema:
        {
            "overall_match_percentage": int,
            "matched_requirements": list[str],
            "missing_requirements": list[str],
            "experience_level_fit": str
        }
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    analysis_system_instruction = """You are a job applicant screening expert. Your job is to \
honestly and objectively evaluate a candidate's master resume against a job description (JD). \
Your evaluation must be 100% honest and accurate, pointing out both matches and gaps. \
Do not exaggerate, stretch, or assume skills that are not explicitly present. \
Return ONLY valid JSON matching this exact schema — no markdown, no prose, no code fences:
{
  "overall_match_percentage": <integer between 0 and 100>,
  "matched_requirements": ["<string>"],
  "missing_requirements": ["<string>"],
  "experience_level_fit": "<string>",
  "master_keywords": ["<string>"],
  "jd_keywords": ["<string>"],
  "keyword_alignments": [
    {
      "keyword": "<string>",
      "status": "<'integrated' or 'gap'>",
      "detail": "<string explaining how it is matched/reworded in the resume, or why it is a gap>"
    }
  ]
}"""

    prompt = f"""Evaluate the candidate's resume against the Job Description.

Master Resume Content:
{master_resume}

---

Job Description:
{jd_text}

---

Please perform the evaluation and return the JSON according to the schema.
For 'matched_requirements', list specific requirements from the JD that are satisfied, with a brief mention of which project, internship, or education entry in the resume supports it.
For 'missing_requirements', list specific requirements (tech stack, languages, tools, databases, or processes) from the JD that are not mentioned anywhere in the resume.
For 'experience_level_fit', write a short honest assessment of the fit between the JD's required years of experience and the candidate's actual timeline.
For 'master_keywords', extract a list of all key technologies, tools, skills, and languages mentioned in the candidate's master resume.
For 'jd_keywords', extract a list of all key technologies, tools, skills, and languages mentioned in the Job Description.
For 'keyword_alignments', extract a list of all key technologies, tools, skills, and languages mentioned in the JD. For each keyword:
  - If the candidate possesses a corresponding skill or experience (even if named slightly differently in the master resume), mark status as 'integrated' and provide a detail showing how it aligns (e.g. "REST APIs - reworded from REST-based backend modules").
  - If the candidate does not possess that skill, mark status as 'gap' and write "Not present in master resume".
"""

    try:
        response = generate_content_with_fallback(
            client=client,
            prompt=prompt,
            system_instruction=analysis_system_instruction,
            temperature=0.1
        )
    except Exception as exc:
        logger.error("All models failed during match analysis: %s", exc)
        raise

    raw_text: str = response.text
    logger.info("Received match analysis response (%d chars).", len(raw_text))

    cleaned = _strip_markdown_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned non-JSON for match analysis: %s", cleaned[:500])
        raise ValueError(
            f"Gemini response could not be parsed as JSON: {exc}"
        ) from exc

    required_keys = {
        "overall_match_percentage",
        "matched_requirements",
        "missing_requirements",
        "experience_level_fit",
        "master_keywords",
        "jd_keywords",
        "keyword_alignments",
    }
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(
            f"Gemini match analysis response is missing required keys: {missing}"
        )

    return data


# ---------------------------------------------------------------------------
# Quality Gate Validation & Self-Correction
# ---------------------------------------------------------------------------

BANNED_BUZZWORDS = [
    "forward-thinking", "forward thinking", "dynamic", "passionate", 
    "results-driven", "results driven", "motivated", "dedicated", 
    "energetic", "creative", "experienced", "innovative", "proven ability", 
    "successful", "highly skilled", "detail-oriented", "detail oriented", 
    "enthusiastic", "proactive"
]

WEAK_OPENERS = [
    "worked on", "helped with", "responsible for", "assisted in", 
    "involved in", "participated in", "handled", "did", "assisted with",
    "helped to", "responsible to", "worked with"
]

VAGUE_ENDINGS = [
    "to meet requirements", "to ensure compliance", "mirroring project-level reporting requirements",
    "to achieve goals", "to complete the task", "for testing purposes", "to ensure functionality",
    "in a timely manner", "to deliver results", "with industry-standard tools", "to satisfy stakeholders",
    "mirroring project-level reporting", "meeting project requirements", "ensuring functionality"
]

def check_summary_text(summary: str) -> list[str]:
    """Check summary for banned buzzwords and other quality issues."""
    errors = []
    summary_lower = summary.strip().lower()
    for buzz in BANNED_BUZZWORDS:
        if summary_lower.startswith(buzz) or summary_lower.startswith("a " + buzz) or summary_lower.startswith("an " + buzz):
            errors.append(f"Summary starts with banned buzzword: '{buzz}'")
    return errors


def check_bullet_text(bullet: str) -> list[str]:
    """Check a bullet point for weak verbs, vague endings, and length."""
    errors = []
    bullet_stripped = bullet.strip()
    bullet_lower = bullet_stripped.lower()
    
    # 1. Weak openers
    for opener in WEAK_OPENERS:
        if bullet_lower.startswith(opener) or bullet_lower.startswith("was " + opener):
            errors.append(f"Bullet starts with weak opener: '{opener}'")
            
    # 2. Vague endings
    for ending in VAGUE_ENDINGS:
        cleaned_bullet = bullet_lower.rstrip(".! ")
        if cleaned_bullet.endswith(ending):
            errors.append(f"Bullet ends with vague/generic filler: '{ending}'")
            
    # 3. Length check
    if len(bullet_stripped) > 250:
        errors.append("Bullet is too long (greater than 250 characters)")
        
    return errors


def check_repeated_starting_verbs(bullets: list[str]) -> list[str]:
    """Checks if multiple bullets in a section start with the same verb (verb duplication)."""
    errors = []
    verbs = []
    for b in bullets:
        words = b.strip().split()
        if words:
            # Clean punctuation from the verb
            verb = re.sub(r"[^\w]", "", words[0]).lower()
            if len(verb) > 2:
                verbs.append(verb)
    
    duplicates = [v for v, count in collections.Counter(verbs).items() if count > 1]
    if duplicates:
        errors.append(f"Start verb duplication detected: multiple bullets start with the same verb(s): {', '.join(duplicates)}. Ensure verb rotation.")
    return errors


PASSIVE_VOICE_TRIGGERS = [
    "was designed", "were designed", "was built", "were built", 
    "was developed", "were developed", "was implemented", "were implemented",
    "was created", "were created", "was optimized", "were optimized",
    "was tested", "were tested", "was run", "were run", "was responsible for",
    "were responsible for", "was involved in", "were involved in"
]

def check_passive_voice(bullet: str) -> list[str]:
    """Checks if a bullet is written in passive voice instead of active voice."""
    errors = []
    bullet_lower = bullet.lower()
    for trigger in PASSIVE_VOICE_TRIGGERS:
        if trigger in bullet_lower:
            errors.append(f"Passive voice trigger '{trigger}' detected. Rephrase to active voice starting with a strong action verb.")
    return errors


def check_repeated_bullets(bullets: list[str]) -> list[str]:
    """Checks if there are duplicate or near-duplicate bullets in a section."""
    errors = []
    seen = set()
    for b in bullets:
        b_norm = re.sub(r"\s+", "", b.lower())
        if b_norm in seen:
            errors.append(f"Duplicate bullet point detected: '{b[:40]}...'")
        seen.add(b_norm)
    return errors


def check_keyword_stuffing(bullet: str) -> list[str]:
    """Checks if a single technical term is repeated excessively in a single bullet point."""
    errors = []
    words = [w.strip(".,;:()[]\"'").lower() for w in bullet.split()]
    counts = collections.Counter(words)
    for word, count in counts.items():
        if len(word) >= 4 and count > 2:
            errors.append(f"Keyword stuffing detected: term '{word}' is repeated {count} times in a single bullet.")
    return errors


GENERIC_JD_PHRASES = [
    "software applications", "internet-related tools", "software systems design",
    "internet-related systems", "related tools", "software systems"
]

def check_generic_jd_phrases(bullet: str) -> list[str]:
    """Checks if generic job description phrases were copied verbatim without mapping to specific candidate experience."""
    errors = []
    bullet_lower = bullet.lower()
    for phrase in GENERIC_JD_PHRASES:
        if phrase in bullet_lower:
            errors.append(f"Generic JD phrase '{phrase}' copied without candidate context. Map to specific terms (e.g. REST APIs, web apps).")
    return errors


def check_skill_traceability(skills_selected: list[dict[str, Any]], master_resume: str) -> list[str]:
    """Checks if every technical skill listed in the skills_selected section is traceable to the master resume."""
    errors = []
    master_lower = master_resume.lower()
    for group in skills_selected:
        for item in group.get("items", []):
            item_clean = item.strip().lower()
            if not item_clean:
                continue
            
            # Simple substring check
            if item_clean in master_lower:
                continue
                
            # If not found, check if a direct acronym or primary token is traceable
            tokens = [t for t in re.split(r"[\s,;/()\-]+", item_clean) if len(t) > 2]
            if tokens and not any(t in master_lower for t in tokens):
                errors.append(f"Skill '{item}' under category '{group.get('category')}' has no supporting evidence in the master resume.")
    return errors


def regenerate_section_with_llm(
    section_name: str,
    current_content: Any,
    errors: list[str],
    master_resume: str,
    jd_text: str
) -> Any:
    """
    Use Gemini to rewrite a specific section (summary, skills, or bullets list) to fix quality issues.
    """
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return current_content
        
    client = genai.Client(api_key=api_key)
    
    errors_list = "\n".join(f"- {err}" for err in errors)
    
    if section_name == "summary":
        prompt = f"""You are a professional resume editor. We need to fix the Professional Summary section of a tailored resume.
The current tailored summary is:
"{current_content}"

The summary failed quality checks for the following reasons:
{errors_list}

Please rewrite the Professional Summary to fix these issues. 
Rules:
1. Absolutely NO banned buzzword openers (do not start with "Forward-thinking", "Dynamic", "Passionate", "Results-driven", "Motivated", "Dedicated", etc.). Open immediately with a concrete statement of the candidate's actual background/focus as it relates to the JD.
2. It must be written in a professional, natural, and active voice.
3. Every claim must remain 100% true based ONLY on the candidate's master resume below. Do not invent any new facts.
4. Do NOT mention the target company's name.

Candidate's Master Resume:
{master_resume}

Job Description:
{jd_text}

Return ONLY the plain text of the rewritten summary. Do not add markdown formatting, JSON, or code fences.
"""
    elif section_name == "skills_selected":
        prompt = f"""You are a professional resume editor. We need to fix the Technical Skills section of a tailored resume.
The current technical skills list is:
{json.dumps(current_content)}

The skills failed validation checks for the following reasons:
{errors_list}

Please rewrite the Technical Skills section to fix these issues.
Rules:
1. Every skill item must trace back to the candidate's master resume below. Do NOT add any tools, languages, or platforms that do not exist in the candidate's master resume.
2. Group related items under normalized category headings to improve readability (e.g. Relational Databases (MySQL, SQLite) or Cloud Platforms (AWS, GCP)) only where appropriate.
3. Only reorder existing skills; do not delete any real skill the candidate possesses.

Candidate's Master Resume:
{master_resume}

Job Description:
{jd_text}

Return the rewritten skills as a valid JSON array of category objects, e.g. [{{"category": "Languages", "items": ["Python", "SQL"]}}]. Do not add any text outside the JSON array.
"""
    else:  # projects or internships bullets
        bullets_str = "\n".join(f"- {b}" for b in current_content)
        prompt = f"""You are a professional resume editor. We need to fix the bullet points for the project or internship section "{section_name}".
The current bullets are:
{bullets_str}

The bullets failed quality checks for the following reasons:
{errors_list}

Please rewrite these bullets to fix these issues.
Rules:
1. Every bullet must lead with a strong, specific action verb in the past tense (e.g. "Built", "Designed", "Implemented", "Integrated", "Created", "Validated", "Improved", "Optimized", "Configured", "Analyzed", "Tested", "Maintained", "Refined", "Documented", "Verified", "Reviewed", "Generated", "Debugged"). Avoid weak/vague openers like "Worked on", "Helped with", "Responsible for", "Assisted in", "Involved in".
2. Do NOT repeat the same starting verb across bullets (ensure strong verb rotation).
3. Always use active voice. Avoid passive triggers (e.g., do not use "was developed", "were designed").
4. NO vague, generic filler closing phrases added purely to include a keyword (e.g. "to meet requirements", "mirroring project-level reporting requirements", "to ensure functionality"). Every sentence must convey real, specific, and professional information.
5. Keep bullets concise (ideally under 2 lines when rendered, around 100-200 characters each).
6. Avoid keyword stuffing and redundant repetition of the same phrase or fact across bullets.
7. Every claim must remain 100% true based ONLY on the candidate's master resume below. Do not invent any new facts.

Candidate's Master Resume:
{master_resume}

Job Description:
{jd_text}

Return the rewritten bullets as a valid JSON array of strings, e.g. ["bullet 1", "bullet 2"]. Do not add any text outside the JSON array.
"""

    system_instruction = "You are a professional resume editor and quality validator."
    
    try:
        response = generate_content_with_fallback(
            client=client,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.2
        )
        raw_text = response.text.strip()
        
        if section_name == "summary":
            raw_text = re.sub(r'^["\']|["\']$', '', raw_text)
            return raw_text.strip()
        else:
            cleaned = _strip_markdown_fences(raw_text)
            return json.loads(cleaned)
    except Exception as exc:
        logger.error("Failed to regenerate section %s: %s", section_name, exc)
        return current_content


def validate_and_correct_resume(
    tailored: dict[str, Any],
    master_resume: str,
    jd_text: str
) -> tuple[dict[str, Any], list[str]]:
    """
    Validates the tailored resume against quality rules and runs a self-correction loop
    using Gemini to rewrite failing sections up to 2 times.
    
    Returns:
        tuple of (finalized_tailored_dict, list_of_warning_strings)
    """
    warnings = []
    
    # 1. Validate Professional Summary
    summary = tailored.get("summary", "")
    if summary:
        for attempt in range(2):
            errors = check_summary_text(summary)
            if not errors:
                break
            logger.info("Summary failed quality checks (attempt %d/2): %s. Regenerating...", attempt + 1, errors)
            summary = regenerate_section_with_llm("summary", summary, errors, master_resume, jd_text)
            
        errors = check_summary_text(summary)
        if errors:
            warnings.append(f"Summary quality check failed: {', '.join(errors)}")
        tailored["summary"] = summary

    # 2. Validate Technical Skills Traceability & Readability
    skills = tailored.get("skills_selected", [])
    if skills:
        for attempt in range(2):
            errors = check_skill_traceability(skills, master_resume)
            if not errors:
                break
            logger.info("Skills failed quality checks (attempt %d/2): %s. Regenerating...", attempt + 1, errors)
            new_skills = regenerate_section_with_llm("skills_selected", skills, errors, master_resume, jd_text)
            if isinstance(new_skills, list) and all(isinstance(s, dict) for s in new_skills):
                skills = new_skills
                tailored["skills_selected"] = skills
            else:
                logger.warning("Regenerated skills were invalid format: %s", new_skills)
                
        errors = check_skill_traceability(skills, master_resume)
        if errors:
            warnings.append(f"Skills quality check failed: {', '.join(errors)}")

    # Helper to validate and regenerate project/experience bullets
    def process_bullets_section(key: str, entry_name_field: str):
        entries = tailored.get(key, [])
        if not entries:
            return
            
        for entry in entries:
            name = entry.get(entry_name_field, "")
            bullets = entry.get("bullets", [])
            if not bullets:
                continue
                
            for attempt in range(2):
                all_errors = []
                # 1. Bullet-level checks
                for idx, bullet in enumerate(bullets):
                    b_errors = check_bullet_text(bullet)
                    if b_errors:
                        all_errors.extend([f"Bullet {idx+1}: {e}" for e in b_errors])
                    passive_errs = check_passive_voice(bullet)
                    if passive_errs:
                        all_errors.extend([f"Bullet {idx+1}: {e}" for e in passive_errs])
                    stuffing_errs = check_keyword_stuffing(bullet)
                    if stuffing_errs:
                        all_errors.extend([f"Bullet {idx+1}: {e}" for e in stuffing_errs])
                    generic_errs = check_generic_jd_phrases(bullet)
                    if generic_errs:
                        all_errors.extend([f"Bullet {idx+1}: {e}" for e in generic_errs])

                # 2. Section-level checks
                verb_errs = check_repeated_starting_verbs(bullets)
                if verb_errs:
                    all_errors.extend(verb_errs)
                rep_errs = check_repeated_bullets(bullets)
                if rep_errs:
                    all_errors.extend(rep_errs)
                        
                if not all_errors:
                    break
                    
                logger.info("Bullets for %s failed quality checks (attempt %d/2): %s. Regenerating...", name, attempt + 1, all_errors)
                new_bullets = regenerate_section_with_llm(name, bullets, all_errors, master_resume, jd_text)
                if isinstance(new_bullets, list) and all(isinstance(b, str) for b in new_bullets):
                    bullets = new_bullets
                    entry["bullets"] = bullets
                else:
                    logger.warning("Regenerated bullets for %s were invalid format: %s", name, new_bullets)
                    
            # Run one final check to add warnings
            all_errors = []
            for idx, bullet in enumerate(bullets):
                b_errors = check_bullet_text(bullet)
                if b_errors:
                    all_errors.extend([f"Bullet {idx+1}: {e}" for e in b_errors])
                passive_errs = check_passive_voice(bullet)
                if passive_errs:
                    all_errors.extend([f"Bullet {idx+1}: {e}" for e in passive_errs])
                stuffing_errs = check_keyword_stuffing(bullet)
                if stuffing_errs:
                    all_errors.extend([f"Bullet {idx+1}: {e}" for e in stuffing_errs])
                generic_errs = check_generic_jd_phrases(bullet)
                if generic_errs:
                    all_errors.extend([f"Bullet {idx+1}: {e}" for e in generic_errs])

            verb_errs = check_repeated_starting_verbs(bullets)
            if verb_errs:
                all_errors.extend(verb_errs)
            rep_errs = check_repeated_bullets(bullets)
            if rep_errs:
                all_errors.extend(rep_errs)

            if all_errors:
                warnings.append(f"Bullets for '{name}' quality check failed: {', '.join(all_errors)}")

    # 3. Validate Flagship Projects
    process_bullets_section("flagship_projects_selected", "name")
    
    # 4. Validate Other Projects
    process_bullets_section("other_projects_selected", "name")
    
    # 5. Validate Projects (just in case they are under "projects_selected")
    process_bullets_section("projects_selected", "name")
    
    # 6. Validate Internships
    process_bullets_section("internships_selected", "company")
    
    return tailored, warnings

