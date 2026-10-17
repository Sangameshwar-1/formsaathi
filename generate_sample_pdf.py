"""
Simple pure-Python PDF generator for creating realistic official demo documents.
Generates compliant PDF 1.4 files without requiring external heavy dependencies.
"""

import os


def create_pdf(filename: str, title: str, lines: list):
    """Generates a multi-line valid PDF file."""
    # Build text stream
    stream_ops = ["BT", "/F1 12 Tf", "14.5 TL", "50 740 Td"]
    # Title in larger font
    stream_ops.append(f"({escape_pdf(title)}) Tj T*")
    stream_ops.append("T*")

    for line in lines:
        if line == "":
            stream_ops.append("T*")
        else:
            escaped = escape_pdf(line)
            stream_ops.append(f"({escaped}) Tj T*")

    stream_ops.append("ET")
    stream_content = "\n".join(stream_ops).encode("latin-1", errors="replace")

    objects = []
    # Obj 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # Obj 2: Pages
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # Obj 3: Page
    objects.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n")
    # Obj 4: Font
    objects.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    # Obj 5: Stream
    stream_obj = (
        f"5 0 obj\n<< /Length {len(stream_content)} >>\nstream\n".encode("latin-1")
        + stream_content
        + b"\nendstream\nendobj\n"
    )
    objects.append(stream_obj)

    # Calculate offsets
    pdf_header = b"%PDF-1.4\n"
    offsets = [len(pdf_header)]
    running_offset = len(pdf_header)

    for i in range(len(objects) - 1):
        running_offset += len(objects[i])
        offsets.append(running_offset)

    xref_offset = running_offset + len(objects[-1])

    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )

    full_pdf = pdf_header + b"".join(objects) + xref.encode("latin-1") + trailer.encode("latin-1")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(full_pdf)
    print(f"Created {filename} ({len(full_pdf)} bytes)")


def escape_pdf(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_samples():
    scholarship_lines = [
        "DEPARTMENT OF HIGHER EDUCATION & SOCIAL WELFARE",
        "NOTIFICATION NO: EDN/SCH/2026-8840",
        "SCHEME: NATIONAL MERIT-CUM-MEANS SCHOLARSHIP SCHEME (NMMSS) 2026-27",
        "",
        "1. OBJECTIVE AND PURPOSE:",
        "The objective of the scheme is to award scholarships to meritorious students of",
        "economically weaker sections to arrest their drop-out at class VIII and encourage",
        "them to continue their education at secondary stage.",
        "",
        "2. IMPORTANT DATES & TIMELINES:",
        "- Portal Opening Date: October 15, 2026",
        "- Last Date for Online Application Submission: November 30, 2026",
        "- Institution Level Verification Deadline: December 15, 2026",
        "- State Nodal Officer Verification Deadline: December 31, 2026",
        "- State-level Examination Date: January 18, 2027",
        "",
        "3. ELIGIBILITY CRITERIA:",
        "- The candidate must be a regular student enrolled in recognized government / aided schools.",
        "- Minimum Academic Qualification: 55% marks or equivalent grade in Class VII annual examination.",
        "- Parental Annual Income: Total annual income from all sources must not exceed Rs. 2,50,000.",
        "- Students studying in Kendriya Vidyalayas and Jawahar Navodaya Vidyalayas are NOT eligible.",
        "",
        "4. REQUIRED CERTIFICATES & DOCUMENTS:",
        "- Verified Income Certificate issued by Revenue Authority (Tahsildar/MRO) dated after April 2026.",
        "- Class VII Annual Exam Marksheet certified by School Principal.",
        "- Student Aadhaar Card copy (or Aadhaar Enrolment Slip).",
        "- Caste / Category Certificate (SC/ST/OBC), if applicable.",
        "- Bank Account Passbook (active account linked with Aadhaar in student name).",
        "- Recent passport-sized color photograph (3.5 cm x 4.5 cm).",
        "",
        "5. FINANCIAL BENEFIT & APPLICATION FEE:",
        "- Scholarship Amount: Rs. 12,000 per annum (Rs. 1,000 per month).",
        "- Application Processing Fee: NIL (Application is completely free of charge).",
        "",
        "6. HOW TO APPLY (STEP-BY-STEP):",
        "Step 1: Register on the National Scholarship Portal (scholarships.gov.in).",
        "Step 2: Fill in personal, educational, and bank details accurately.",
        "Step 3: Upload scanned copies of required certificates (PDF/JPEG max 200KB).",
        "Step 4: Submit application and submit printed copy to School Principal.",
        "",
        "7. WARNINGS & CONSEQUENCES OF FALSE INFORMATION:",
        "- Submission of forged income or caste certificates will lead to immediate cancellation",
        "  and recovery of disbursed amounts along with legal action under IPC Section 420.",
        "- Late applications submitted after November 30, 2026 will be rejected automatically.",
        "- NOTE: Hostel allowance and private tuition fees are NOT covered under this scheme."
    ]

    create_pdf(
        "sample_docs/National_Merit_Scholarship_2026.pdf",
        "GOVERNMENT OF INDIA - SCHOLARSHIP NOTIFICATION",
        scholarship_lines,
    )

    admission_lines = [
        "INSTITUTE OF ADVANCED STUDIES & RESEARCH",
        "CIRCULAR: POSTGRADUATE ADMISSIONS 2026-2027",
        "",
        "1. OVERVIEW:",
        "Applications are invited for admission to 2-year M.Tech and M.S. Programs.",
        "",
        "2. SCHEDULE OF EVENTS:",
        "- Application Start: November 1, 2026",
        "- Application Closing: December 10, 2026 (5:00 PM IST)",
        "- Written Test / Online Interview: December 28, 2026",
        "- Announcement of Shortlisted Candidates: January 5, 2027",
        "",
        "3. ELIGIBILITY REQUIREMENTS:",
        "- B.E. / B.Tech in CSE, ECE, or related disciplines with minimum 60% marks or 6.5 CGPA.",
        "- Valid GATE score is mandatory for institute fellowship categories.",
        "- Sponsored candidates require minimum 2 years of full-time industrial experience.",
        "",
        "4. APPLICATION FEE & PAYMENT:",
        "- General / OBC / EWS Male candidates: Rs. 1,000.",
        "- SC / ST / PwD / Female candidates: Rs. 500.",
        "- Mode: Online payment through Net Banking / Credit Card / UPI only.",
        "",
        "5. MANDATORY DOCUMENTS:",
        "- GATE Score Card, Degree Certificate, Official Transcripts, Category Certificate.",
        "",
        "6. IMPORTANT INSTRUCTIONS:",
        "- Incomplete applications without payment receipt will be summarily rejected."
    ]

    create_pdf(
        "sample_docs/University_Admission_Notice_2026.pdf",
        "CENTRAL ADMISSIONS COMMITTEE - OFFICIAL CIRCULAR",
        admission_lines,
    )


if __name__ == "__main__":
    make_samples()
