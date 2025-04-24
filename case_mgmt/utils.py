# utils.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.utils import timezone 
def build_pdf_content(case, user, signature_path=None):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add disclosure form content
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "OFFICIAL DISCLOSURE FORM")
    p.setFont("Helvetica", 12)
    
    p.drawString(100, 720, f"Case: {case.name}")
    p.drawString(100, 700, f"Number: {case.case_number}")
    p.drawString(100, 680, f"Officer: {user.get_full_name()}")
    p.drawString(100, 660, f"Badge/ID: {user.username}")  # Or add badge_number to user model
    p.drawString(100, 640, f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    p.drawString(100, 600, "I certify that all evidence has been properly documented")
    p.drawString(100, 580, "and chain of custody maintained in accordance with")
    p.drawString(100, 560, "departmental policies and legal requirements.")
    
    # Add signature if available
    if signature_path:
        p.drawString(100, 520, "Officer Signature:")
        p.drawImage(signature_path, 100, 450, width=200, height=80, preserveAspectRatio=True)
    
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    return pdf