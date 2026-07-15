# ResumeTailor AI

An AI-powered resume tailoring platform that transforms a master resume into an ATS-optimized, recruiter-quality resume tailored to any job description while preserving all factual information.

ResumeTailor AI intelligently analyzes a job description, rewrites resume content using recruiter-style language, dynamically prioritizes relevant skills and projects, and generates a professional PDF resume without fabricating experience or adding unsupported information.

---

# Features

- AI-powered resume tailoring using Google Gemini
- Semantic job description analysis
- ATS-friendly keyword optimization
- Recruiter-quality content rewriting
- Intelligent skill prioritization based on the target role
- Dynamic project and internship optimization
- Reverse chronological ordering of experience and education
- Professional PDF resume generation
- Resume scoring dashboard with ATS and recruiter analysis
- Complete factual information preservation
- Automatic completeness validation before PDF generation
- Hyperlinked GitHub, LinkedIn, and Portfolio URLs
- Generic support for freshers and experienced professionals
- Works across Software Engineering, QA, Cloud, DevOps, SAP, Data Engineering, Support Engineering, AI, and other technical roles

---

# How It Works

1. Upload your master resume.

2. Paste the target job description.

3. ResumeTailor AI performs semantic analysis of the job description.

4. The AI intelligently:

- rewrites experience
- optimizes project descriptions
- prioritizes relevant technical skills
- improves recruiter readability
- integrates ATS keywords naturally

while preserving every factual detail from the uploaded resume.

5. A Resume Completeness Validator verifies that:

- internships are preserved
- projects are preserved
- education history is preserved
- certifications are preserved
- technical skills are preserved
- contact information is preserved

6. A professionally formatted ATS-friendly PDF resume is generated.

---

# Tech Stack

## Backend

- Python
- FastAPI

## Artificial Intelligence

- Google Gemini API
- Semantic Job Description Matching
- Intelligent Resume Tailoring

## Frontend

- HTML
- CSS
- JavaScript

## PDF Generation

- Jinja2
- WeasyPrint

## Infrastructure

- Docker
- Render

---

# Installation

## Prerequisites

- Python 3.10+
- Google Gemini API Key

For Windows users:

WeasyPrint requires GTK.

Install GTK before installing project dependencies.

---

## Clone the Repository

```bash
git clone https://github.com/Iamgokul7/ResumeTailor-AI.git

cd ResumeTailor-AI
```

---

## Create a Virtual Environment

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Copy:

```text
.env.example
```

to

```text
.env
```

Add your Gemini API key.

Example:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## Run the Application

```bash
uvicorn main:app --reload
```

The application will start at

```
http://127.0.0.1:8000
```

---

# Usage

1. Open the web application.

2. Upload your master resume.

3. Paste the target job description.

4. Click **Generate Tailored Resume**.

5. Review:

- ATS Score
- Recruiter Analysis
- Keyword Matching
- Resume Preview

6. Download the generated PDF.

---

# Resume Optimization Engine

ResumeTailor AI performs:

- Semantic JD understanding
- Recruiter-style rewriting
- ATS keyword optimization
- Technical skill prioritization
- Project relevance optimization
- Internship enhancement
- Professional summary generation
- Bullet refinement
- Space optimization
- Formatting consistency

The AI never fabricates:

- work experience
- projects
- certifications
- education
- technical skills

---

# Resume Completeness Validator

Before generating the final PDF, ResumeTailor AI validates that every factual section from the uploaded master resume is preserved.

The validator verifies:

- Contact Information
- Professional Summary
- Technical Skills
- Projects
- Internship Experience
- Professional Experience
- Education
- Certifications
- Awards
- Publications
- Research
- Volunteer Experience
- Achievements

If required information is missing, the tailored resume is rejected and regenerated automatically.

---

# ATS Optimization

ResumeTailor AI improves ATS compatibility by:

- identifying high-priority keywords
- semantically matching recruiter expectations
- naturally integrating keywords
- reorganizing skills dynamically
- improving recruiter readability
- avoiding keyword stuffing

---

# Project Structure

```
ResumeTailor-AI
│
├── static/
│   ├── app.js
│   ├── index.html
│
├── templates/
│   ├── resume_template.html
│   ├── resume_template_simple.html
│
├── output/
│
├── main.py
├── gemini_service.py
├── pdf_service.py
├── storage.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

---

# Key Highlights

- AI-powered recruiter-style resume rewriting
- ATS-safe resume generation
- Semantic job description matching
- Dynamic technical skill prioritization
- Professional PDF formatting
- Resume completeness validation
- Reverse chronological ordering
- Generic support for any profession
- No fabricated information
- Production-ready architecture

---

# Future Improvements

- Multiple resume templates
- Cover letter generation
- LinkedIn profile optimization
- Multi-language resume support
- Interview preparation assistant
- Resume version history
- Analytics dashboard

---

# License

This project is licensed under the MIT License.

---

# Author

**Gokul P**

GitHub: https://github.com/Iamgokul7

LinkedIn: https://linkedin.com/in/gokulp0807

Portfolio: https://gokulp-portfolio.vercel.app
