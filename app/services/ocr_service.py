"""
ocr_service.py — OCR Service for reading prescription images and PDFs.
Uses pytesseract for text extraction, then passes to LLM for structuring.
"""
import io
import os
import tempfile
from typing import Optional


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from an image using pytesseract OCR."""
    try:
        from PIL import Image
        import pytesseract
        
        image = Image.open(io.BytesIO(image_bytes))
        # Preprocessing for better OCR
        image = image.convert('L')  # Convert to grayscale
        text = pytesseract.image_to_string(image, lang='eng')
        return text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file. Tries text extraction first, falls back to OCR."""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Try text extraction first (for digital PDFs)
            text = page.get_text().strip()
            
            if text:
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
            else:
                # Fall back to OCR for scanned PDFs
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                ocr_text = extract_text_from_image(img_bytes)
                if ocr_text:
                    text_parts.append(f"--- Page {page_num + 1} (OCR) ---\n{ocr_text}")
        
        doc.close()
        return "\n\n".join(text_parts) if text_parts else "No text could be extracted."
    except Exception as e:
        return f"PDF Extraction Error: {str(e)}"


def process_uploaded_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Process an uploaded file and return extracted text."""
    if content_type == 'application/pdf' or filename.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif content_type.startswith('image/'):
        return extract_text_from_image(file_bytes)
    else:
        return "Unsupported file type. Please upload an image or PDF."


def structure_prescription_text(raw_text: str) -> dict:
    """Parse raw OCR text into a structured prescription dict.
    This is a simple rule-based parser. The AI endpoint handles LLM-based parsing."""
    result = {
        'raw_text': raw_text,
        'medicines': [],
        'patient_name': '',
        'doctor_name': '',
        'date': '',
    }
    
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Basic pattern matching
        lower = line.lower()
        if 'patient' in lower and ':' in line:
            result['patient_name'] = line.split(':', 1)[1].strip()
        elif 'doctor' in lower and ':' in line or 'dr.' in lower:
            result['doctor_name'] = line.split(':', 1)[-1].strip()
        elif 'date' in lower and ':' in line:
            result['date'] = line.split(':', 1)[1].strip()
    
    return result
