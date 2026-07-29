import os
import base64
from jinja2 import Environment, FileSystemLoader

def generate_prescription_pdf(
    patient: dict,
    doctor: dict, 
    medicines: list[dict],  # [{name, dosage, frequency, duration_days, dose_times, interval_hours}, ...]
    notes: str | None = None,
) -> bytes:
    """Render a prescription as a styled PDF. Returns raw PDF bytes.
    No DB access, no side effects — pure rendering function.
    """
    # Read and base64-encode the hospital logo
    logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'branding', 'hospital_logo.svg')
    with open(logo_path, 'r') as f:
        logo_svg = f.read()
    logo_b64 = base64.b64encode(logo_svg.encode()).decode()
    
    # Render Jinja2 template
    template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('prescription_pdf.html')
    
    import datetime
    html = template.render(
        patient=patient,
        doctor=doctor,
        medicines=medicines,
        notes=notes,
        logo_b64=logo_b64,
        generated_at=datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p'),
    )
    
    from weasyprint import HTML
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes
