import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_text_pdf():
    # Create a valid text-based PDF resume
    c = canvas.Canvas("test_resume.pdf", pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 750, "ALEX JORDAN")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 735, "alex.jordan@email.com | +1 (555) 123-4567 | San Francisco, CA")
    
    # Skills
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 700, "TECHNICAL SKILLS")
    c.setFont("Helvetica", 10)
    c.drawString(100, 685, "Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, CI/CD, Git")
    
    # Experience
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 650, "WORK EXPERIENCE")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, 635, "TechCorp Inc. - Software Engineering Intern")
    c.setFont("Helvetica", 10)
    c.drawString(100, 620, "- Developed and shipped 3 REST API endpoints using Python and FastAPI.")
    c.drawString(100, 605, "- Optimized PostgreSQL query execution time from 8 minutes to 40 seconds.")
    
    # Projects
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 560, "PROJECTS")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, 545, "SecureVault - Secrets Manager")
    c.setFont("Helvetica", 10)
    c.drawString(100, 530, "- Built a self-hosted secrets manager using AES-256 encryption.")
    c.drawString(100, 515, "- Deployed full stack with Docker Compose and set up GitHub Actions CI/CD.")
    
    # Education
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 470, "EDUCATION")
    c.setFont("Helvetica", 10)
    c.drawString(100, 455, "University of California, Berkeley - B.S. in Computer Science")
    
    c.save()
    print("Created test_resume.pdf")

def create_scanned_pdf():
    # Create a PDF with no text layer (empty canvas)
    c = canvas.Canvas("test_scanned.pdf", pagesize=letter)
    c.drawString(100, 750, "") # empty text
    c.save()
    print("Created test_scanned.pdf")

if __name__ == "__main__":
    create_text_pdf()
    create_scanned_pdf()
