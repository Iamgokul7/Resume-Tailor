# ResumeTailor

> **AI-powered, ATS-safe resume generator.** Paste a job description, get a perfectly tailored PDF resume built only from your own content bank — zero hallucination, zero fabrication.

---

## How it Works

1. You maintain a **`resume_bank.json`** file with all your real skills, project bullet variants, internship descriptions, and summary options.
2. You paste a job description into the web UI.
3. ResumeTailor sends your bank + the JD to **Google Gemini** with a strict "select and lightly reword — never invent" instruction.
4. Gemini returns a JSON selection; the app runs a **fabrication safety check** to flag any skill not traceable to your bank.
5. **WeasyPrint** renders a clean, single-column, ATS-safe **PDF** that you can download immediately.

---

## Quick Start

### Prerequisites
- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (free tier works)
- **Windows only**: WeasyPrint requires GTK. Install [GTK for Windows](https://github.com/nicowillis/windows-gtk-binaries/releases) and add it to PATH before installing WeasyPrint.

### 1 — Clone / open the project folder

```bash
cd s:\RESUME_BUILDER_PROJECT
```

### 2 — Create and activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> **Note for Windows users:** If WeasyPrint installation fails, install the GTK runtime first:
> ```powershell
> winget install --id=GNOME.GTK --exact
> ```
> Then retry `pip install weasyprint`.

### 4 — Configure your API key

```bash
# Copy the example file
cp .env.example .env   # Windows: copy .env.example .env

# Open .env and replace the placeholder with your real key:
# GEMINI_API_KEY=AIza...your_key_here
```

### 5 — Personalise your content bank

Open **`resume_bank.json`** and replace the placeholder content with your real information:
- `contact` — your name, email, phone, links
- `education` — your degrees
- `certifications` — your certs
- `skills` — your actual skill categories and items
- `projects` — each project with multiple `bullet_variants` tagged by role type
- `internships` — work experience with `bullet_variants`
- `summary_variants` — 2–5 different professional summary options tagged by role

### 6 — Start the server

```bash
uvicorn main:app --reload
```

The app will be live at **http://localhost:8000**

---

## Usage

1. Open **http://localhost:8000** in your browser.
2. Paste a full job description into the textarea.
3. Click **"Generate Tailored Resume"** (or press **Ctrl+Enter**).
4. Wait ~5–15 seconds for the AI to tailor and the PDF to render.
5. Review the on-page preview — any fabrication warnings appear in amber.
6. Click **Download PDF** or **Copy as Plain Text**.

Generated PDFs are saved to the **`output/`** folder with a timestamp filename.

---

## Project Structure

```
.
├── main.py                  # FastAPI app + routes
├── gemini_service.py        # Google Gemini API wrapper
├── pdf_service.py           # WeasyPrint PDF renderer
├── storage.py               # JSON data access layer (swap-friendly)
├── resume_bank.json         # Your personal content database
├── requirements.txt
├── .env                     # Your API key (never commit this)
├── .env.example             # Safe template for .env
├── .gitignore
├── templates/
│   └── resume_template.html # Jinja2 + WeasyPrint template
├── static/
│   ├── index.html           # Single-page frontend
│   ├── app.js               # Frontend logic
│   └── style.css            # Frontend styles
└── output/                  # Generated PDFs (gitignored)
```

---

## Fabrication Safety Check

After Gemini responds, the server extracts every skill/technology token from the output and checks it against every word in your `resume_bank.json` (case-insensitive substring match).

- ✅ If all tokens match → no warnings
- ⚠️ If a token is unrecognised → a warning badge appears in the UI **and** a `WARNING` is logged to the terminal

This prevents Gemini from quietly inventing skills you don't have.

---

## Swapping the Storage Backend

All file I/O lives in **`storage.py`**. To switch to SQLite or PostgreSQL:
1. Keep the same function signatures: `load_bank()`, `save_bank()`, `get_all_keywords()`
2. Implement them against your new backend
3. No other file needs to change

---

## Licence

MIT
