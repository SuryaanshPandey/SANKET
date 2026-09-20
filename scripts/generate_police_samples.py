"""Generate forensically authentic Indian Police investigation document test samples.

Creates realistic visual test documents matching official Indian Police / CCTNS / Hospital formats:
1. Seizure Memo / Panchnama (Fard-e-Zabti under Sec 100/102 CrPC)
2. Arrest & Inspection Memo (Sec 41B CrPC & D.K. Basu Guidelines)
3. Charge Sheet / Final Report (Sec 173 CrPC / IIF-5)
4. Medico-Legal Certificate (MLC / Injury Report)
5. Forensic Science Lab (FSL) Cyber Certificate under Sec 65B IEA
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def get_font(size: int, bold: bool = False):
    # Try system fonts or default
    try:
        if bold:
            return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def create_seizure_memo(out_path: Path):
    """Panchnama / Seizure Memo under Sec 100/102 CrPC & Sec 105 BNSS."""
    w, h = 900, 1300
    img = Image.new("RGB", (w, h), color=(252, 250, 245))
    draw = ImageDraw.Draw(img)

    f_title = get_font(22, bold=True)
    f_sub = get_font(15, bold=True)
    f_body = get_font(13)
    f_body_bold = get_font(13, bold=True)

    # Header
    draw.text((w//2 - 190, 40), "INDIAN POLICE / CCTNS IIF-2", fill=(20, 20, 20), font=f_title)
    draw.text((w//2 - 250, 75), "SEIZURE MEMO / PANCHNAMA (FARD-E-ZABTI)", fill=(40, 40, 40), font=f_sub)
    draw.text((w//2 - 220, 100), "[Under Section 100 & 102 Cr.P.C. / Section 105 BNSS]", fill=(70, 70, 70), font=f_body)
    draw.line([(40, 130), (w - 40, 130)], fill=(80, 80, 80), width=2)

    # Case Metadata Box
    y = 150
    draw.rectangle([(40, y), (w - 40, y + 90)], outline=(120, 120, 120), width=1)
    draw.text((50, y + 10), "District: South West Delhi", fill=(20, 20, 20), font=f_body_bold)
    draw.text((450, y + 10), "Police Station: Vasant Vihar", fill=(20, 20, 20), font=f_body_bold)
    draw.text((50, y + 35), "FIR / Crime No: 184/2026", fill=(20, 20, 20), font=f_body_bold)
    draw.text((450, y + 35), "Date of FIR: 12-05-2026", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 60), "Acts & Sections: U/S 379, 411 IPC / Sec 303, 317 BNS", fill=(20, 20, 20), font=f_body)
    draw.text((450, y + 60), "Date & Time of Seizure: 14-05-2026 at 16:30 hrs", fill=(20, 20, 20), font=f_body_bold)

    # Recovery Spot & Accused
    y += 110
    draw.text((40, y), "1. Place of Recovery / Seizure:", fill=(20, 20, 20), font=f_body_bold)
    draw.text((280, y), "House No. 42, Munirka Village, New Delhi (Rented premise)", fill=(20, 20, 20), font=f_body)
    y += 30
    draw.text((40, y), "2. Person from whom Recovered:", fill=(20, 20, 20), font=f_body_bold)
    draw.text((280, y), "Ramesh Kumar s/o Late Mohan Lal, age 32 yrs (Accused)", fill=(20, 20, 20), font=f_body)

    # Panch Witnesses (Mandatory 2 independent witnesses under Sec 100(4) CrPC)
    y += 45
    draw.rectangle([(40, y), (w - 40, y + 110)], outline=(0, 100, 150), width=2)
    draw.text((50, y + 8), "INDEPENDENT PANCH WITNESSES (Sec 100(4) Cr.P.C. Compliance):", fill=(0, 80, 130), font=f_body_bold)
    draw.text((50, y + 35), "Panch Witness 1: Vikramaditya Singh s/o Ram Singh, r/o 14-B Munirka, New Delhi", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 55), "Occupation / ID: Shopkeeper (Aadhaar No. XXXX-XXXX-4912)", fill=(60, 60, 60), font=f_body)
    draw.text((50, y + 80), "Panch Witness 2: Harish Chand s/o Gyaneshwar, r/o 18 Munirka Village, New Delhi", fill=(20, 20, 20), font=f_body)

    # Seized Articles Table
    y += 135
    draw.text((40, y), "3. Description of Seized Material Evidence & Property:", fill=(20, 20, 20), font=f_body_bold)
    y += 25
    headers = ["Item No.", "Article Description", "Serial / IMEI No.", "Est. Value", "Seal Mark Status"]
    col_x = [40, 120, 480, 660, 780]
    draw.rectangle([(40, y), (w - 40, y + 30)], fill=(230, 235, 240), outline=(150, 150, 150))
    for i, h_text in enumerate(headers):
        draw.text((col_x[i] + 5, y + 7), h_text, fill=(20, 20, 20), font=f_body_bold)

    rows = [
        ("01", "Apple iPhone 15 Pro Max (Natural Titanium)", "IMEI: 356891094821034", "Rs. 1,35,000", "Sealed in Cloth Parcel 'A'"),
        ("02", "Dell Latitude 7420 Laptop (Black)", "Serial: DL-9921-X4", "Rs. 85,000", "Sealed in Parcel 'B'"),
        ("03", "Cash Indian Currency Notes (500x120)", "Denomination Rs. 500", "Rs. 60,000", "Enclosed in Bank Envelope 'C'"),
    ]
    for r_idx, row in enumerate(rows):
        ry = y + 30 + r_idx * 35
        draw.rectangle([(40, ry), (w - 40, ry + 35)], outline=(180, 180, 180))
        for c_idx, val in enumerate(row):
            draw.text((col_x[c_idx] + 5, ry + 8), val, fill=(30, 30, 30), font=f_body)

    # Narrative of Recovery
    y = ry + 60
    draw.text((40, y), "4. Recovery Circumstances & Seal Condition:", fill=(20, 20, 20), font=f_body_bold)
    narrative = (
        "The aforesaid articles were recovered from the personal bedroom of the accused inside an iron almirah in the "
        "presence of independent Panch witnesses. All electronic articles and cash were inspected, cataloged, wrapped in pristine "
        "white cloth, and sealed with official brass seal impression 'SHO-VV-26'. The sample seal impression has been affixed below."
    )
    draw.text((40, y + 25), narrative, fill=(40, 40, 40), font=f_body)

    # Signatures
    y += 180
    draw.text((50, y), "Sd/- Vikramaditya Singh\n(Panch Witness 1)", fill=(10, 10, 10), font=f_body_bold)
    draw.text((320, y), "Sd/- Harish Chand\n(Panch Witness 2)", fill=(10, 10, 10), font=f_body_bold)
    draw.text((620, y), "Sd/- Inspector R.K. Sharma\nInvestigating Officer, PS Vasant Vihar", fill=(10, 10, 10), font=f_body_bold)

    # Official Seal
    draw.ellipse([(700, y + 60), (820, y + 180)], outline=(160, 40, 40), width=3)
    draw.text((715, y + 110), "POLICE SEAL\nVASANT VIHAR", fill=(160, 40, 40), font=get_font(11, bold=True))

    img.save(out_path, "PNG")


def create_arrest_memo(out_path: Path):
    """Arrest & Inspection Memo under Sec 41B CrPC / Sec 36 BNSS (D.K. Basu Compliance)."""
    w, h = 900, 1300
    img = Image.new("RGB", (w, h), color=(253, 252, 248))
    draw = ImageDraw.Draw(img)

    f_title = get_font(21, bold=True)
    f_sub = get_font(15, bold=True)
    f_body = get_font(13)
    f_body_bold = get_font(13, bold=True)

    draw.text((w//2 - 200, 40), "DELHI POLICE HEADQUARTERS", fill=(20, 20, 20), font=f_title)
    draw.text((w//2 - 270, 75), "ARREST & INSPECTION MEMO (FARD-E-GIRAFTARI)", fill=(40, 40, 40), font=f_sub)
    draw.text((w//2 - 260, 100), "[Compliance with Sec 41B Cr.P.C. & Supreme Court D.K. Basu Guidelines]", fill=(70, 70, 70), font=f_body)
    draw.line([(40, 130), (w - 40, 130)], fill=(80, 80, 80), width=2)

    # Metadata
    y = 150
    draw.text((50, y), "Police Station: Connaught Place", fill=(20, 20, 20), font=f_body_bold)
    draw.text((480, y), "FIR No: 92/2026, U/S 420, 468, 471 IPC", fill=(20, 20, 20), font=f_body_bold)
    y += 30
    draw.text((50, y), "Arresting Officer: Sub-Inspector Amit Verma", fill=(20, 20, 20), font=f_body)
    draw.text((480, y), "Date & Time of Arrest: 18-06-2026 at 11:15 AM", fill=(20, 20, 20), font=f_body_bold)

    # Arrestee Profile
    y += 45
    draw.rectangle([(40, y), (w - 40, y + 120)], outline=(100, 100, 100), width=1)
    draw.text((50, y + 10), "PARTICULARS OF PERSON ARRESTED (ARRESTEE):", fill=(0, 60, 120), font=f_body_bold)
    draw.text((50, y + 35), "Name: Rajesh Singhania", fill=(20, 20, 20), font=f_body_bold)
    draw.text((450, y + 35), "Father's Name: O.P. Singhania", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 60), "Age: 44 Years | Gender: Male", fill=(20, 20, 20), font=f_body)
    draw.text((450, y + 60), "Mobile: +91-9811029384", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 85), "Permanent Address: Flat 402, Royal Residency, Sector 54, Gurugram, Haryana", fill=(20, 20, 20), font=f_body)

    # D.K. Basu Compliance Box
    y += 140
    draw.rectangle([(40, y), (w - 40, y + 250)], outline=(160, 40, 40), width=2)
    draw.text((50, y + 10), "STATUTORY SAFEGUARDS & D.K. BASU COMPLIANCE CHECKLIST:", fill=(160, 30, 30), font=f_body_bold)

    items = [
        ("1. Grounds of Arrest:", "Accused was informed that he is arrested on substantive evidence of forging bank guarantees worth Rs. 2.4 Crores."),
        ("2. Intimation to Family / Friend:", "Intimated to Mrs. Sunita Singhania (Wife) at Phone: 9811029385 on 18-06-2026 at 11:40 AM."),
        ("3. Right to Legal Counsel:", "Accused informed of right to consult Advocate of choice under Section 41D Cr.P.C."),
        ("4. Physical Health Inspection:", "Body examined by IO at time of arrest. No external visible injuries observed. Accused has mild diabetes."),
        ("5. Magistrate Remand Target:", "To be produced before Metropolitan Magistrate, Patiala House Courts, New Delhi within 24 hours."),
    ]
    iy = y + 35
    for title, desc in items:
        draw.text((50, iy), title, fill=(20, 20, 20), font=f_body_bold)
        draw.text((260, iy), desc, fill=(40, 40, 40), font=f_body)
        iy += 40

    # Attestation
    y += 280
    draw.text((40, y), "Attesting Witness to Arrest: Deepak Khurana (Independent Local Merchant), r/o Regal Building, CP", fill=(20, 20, 20), font=f_body)

    # Signatures
    y += 90
    draw.text((50, y), "Signature of Arrestee:\nSd/- Rajesh Singhania", fill=(10, 10, 10), font=f_body_bold)
    draw.text((320, y), "Signature of Witness:\nSd/- Deepak Khurana", fill=(10, 10, 10), font=f_body_bold)
    draw.text((600, y), "Arresting Officer:\nSd/- SI Amit Verma\nPS Connaught Place", fill=(10, 10, 10), font=f_body_bold)

    img.save(out_path, "PNG")


def create_chargesheet(out_path: Path):
    """Charge Sheet under Sec 173 CrPC / Sec 193 BNSS (CCTNS Form IIF-5)."""
    w, h = 900, 1300
    img = Image.new("RGB", (w, h), color=(250, 252, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(22, bold=True)
    f_sub = get_font(15, bold=True)
    f_body = get_font(13)
    f_body_bold = get_font(13, bold=True)

    draw.text((w//2 - 220, 40), "COURT OF CHIEF METROPOLITAN MAGISTRATE", fill=(20, 20, 20), font=f_title)
    draw.text((w//2 - 240, 75), "FINAL REPORT / CHARGE SHEET (SECTION 173 Cr.P.C.)", fill=(40, 40, 40), font=f_sub)
    draw.text((w//2 - 180, 100), "[CCTNS Integrated Investigation Form IIF-5]", fill=(70, 70, 70), font=f_body)
    draw.line([(40, 130), (w - 40, 130)], fill=(80, 80, 80), width=2)

    y = 150
    draw.text((50, y), "Police Station: Cyber Crime Cell, Bengaluru", fill=(20, 20, 20), font=f_body_bold)
    draw.text((500, y), "Final Report / Charge Sheet No: 48/2026", fill=(20, 20, 20), font=f_body_bold)
    y += 28
    draw.text((50, y), "FIR No: 112/2025 | Date of FIR: 10-11-2025", fill=(20, 20, 20), font=f_body)
    draw.text((500, y), "Date of Filing in Court: 05-02-2026", fill=(20, 20, 20), font=f_body_bold)
    y += 28
    draw.text((50, y), "Statutory Acts & Sections: Section 66C, 66D IT Act, 2000 and Section 419, 420, 120B IPC", fill=(20, 20, 20), font=f_body_bold)

    # Accused Sent for Trial
    y += 50
    draw.rectangle([(40, y), (w - 40, y + 120)], outline=(0, 120, 60), width=2)
    draw.text((50, y + 10), "PARTICULARS OF ACCUSED PERSONS CHARGESHEETED (SENT FOR TRIAL):", fill=(0, 100, 50), font=f_body_bold)
    draw.text((50, y + 35), "1. Accused: Karthik Sundaram, age 29 yrs | Custody Status: In Judicial Custody (Central Prison, Parappana Agrahara)", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 60), "2. Accused: Anand Rajan, age 31 yrs | Custody Status: On Regular Bail granted by Sessions Court", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 85), "3. Accused: Nitin Sharma, age 27 yrs | Custody Status: Absconding (Proceedings U/S 82/83 Cr.P.C. initiated)", fill=(180, 20, 20), font=f_body)

    # Prosecution Witnesses Table
    y += 140
    draw.text((40, y), "LIST OF PROSECUTION WITNESSES (PWs) CITED:", fill=(20, 20, 20), font=f_body_bold)
    y += 25
    pw_rows = [
        ("PW-1", "Sanjay Nambiar (Complainant / Defrauded Account Holder)", "Proves unauthorized debit of Rs. 42 Lakhs"),
        ("PW-2", "Deepa Krishnan (Branch Manager, HDFC Bank, Indiranagar)", "Proves bogus beneficiary account KYC documents"),
        ("PW-3", "Dr. V. Rao (Scientific Officer, Cyber FSL, Madiwala)", "Proves forensic data extraction report & SHA-256 hash"),
        ("PW-4", "Inspector Prakash Gowda (Investigating Officer)", "Proves entire investigation, arrests, and charge sheet"),
    ]
    for idx, (p_no, p_name, p_purpose) in enumerate(pw_rows):
        ry = y + idx * 32
        draw.text((50, ry), f"{p_no}:", fill=(20, 20, 20), font=f_body_bold)
        draw.text((110, ry), p_name, fill=(30, 30, 30), font=f_body)
        draw.text((580, ry), f"- {p_purpose}", fill=(70, 70, 70), font=f_body)

    # Material Evidence
    y += 150
    draw.text((40, y), "MATERIAL EVIDENCE & EXHIBITS FORWARDED:", fill=(20, 20, 20), font=f_body_bold)
    draw.text((50, y + 25), "• MO-1: HP Pavilion Laptop (Serial: 5CD23910L) used for creating phishing gateways.", fill=(30, 30, 30), font=f_body)
    draw.text((50, y + 50), "• MO-2: Samsung Galaxy S22 containing OTP intercepts and forged identity documents.", fill=(30, 30, 30), font=f_body)
    draw.text((50, y + 75), "• Ex. P-1 to P-8: Forensic Lab Extraction Report with 65B Electronic Certificate.", fill=(30, 30, 30), font=f_body)

    # Forwarding Endorsement
    y += 140
    draw.text((50, y), "Forwarded by:\nSd/- ACP Crime Branch, Bengaluru", fill=(20, 20, 20), font=f_body_bold)
    draw.text((500, y), "Submitted by:\nSd/- Inspector Prakash Gowda\nInvestigating Officer, Cyber Crime Cell", fill=(20, 20, 20), font=f_body_bold)

    img.save(out_path, "PNG")


def create_medical_legal(out_path: Path):
    """Medico-Legal Certificate (MLC) / Injury Report."""
    w, h = 900, 1300
    img = Image.new("RGB", (w, h), color=(255, 252, 250))
    draw = ImageDraw.Draw(img)

    f_title = get_font(22, bold=True)
    f_sub = get_font(15, bold=True)
    f_body = get_font(13)
    f_body_bold = get_font(13, bold=True)

    draw.text((w//2 - 250, 40), "ALL INDIA INSTITUTE OF MEDICAL SCIENCES", fill=(20, 20, 20), font=f_title)
    draw.text((w//2 - 230, 75), "CASUALTY & EMERGENCY MEDICINE DEPARTMENT", fill=(40, 40, 40), font=f_sub)
    draw.text((w//2 - 180, 100), "MEDICO-LEGAL CERTIFICATE (MLC REPORT)", fill=(180, 20, 20), font=f_title)
    draw.line([(40, 130), (w - 40, 130)], fill=(80, 80, 80), width=2)

    y = 150
    draw.text((50, y), "MLC Number: MLC-2026-9812", fill=(20, 20, 20), font=f_body_bold)
    draw.text((500, y), "Date & Time of Exam: 22-07-2026 at 21:45 hrs", fill=(20, 20, 20), font=f_body_bold)
    y += 28
    draw.text((50, y), "Police Station: Hauz Khas, New Delhi", fill=(20, 20, 20), font=f_body)
    draw.text((500, y), "Brought by: Constable Manjeet Singh (No. 491-S)", fill=(20, 20, 20), font=f_body)

    # Patient particulars
    y += 45
    draw.rectangle([(40, y), (w - 40, y + 80)], outline=(120, 120, 120), width=1)
    draw.text((50, y + 10), "Patient / Injured Person: Arvind Sharma s/o Kailash Sharma, Age: 36 yrs, Male", fill=(20, 20, 20), font=f_body_bold)
    draw.text((50, y + 35), "Address: H-12, Green Park Extension, New Delhi", fill=(30, 30, 30), font=f_body)
    draw.text((50, y + 55), "Alleged History: Physical assault with sharp and blunt weapons near metro parking at 20:30 hrs.", fill=(50, 50, 50), font=f_body)

    # Injury details
    y += 105
    draw.text((40, y), "TABULAR DETAILS OF EXTERNAL INJURIES:", fill=(20, 20, 20), font=f_body_bold)
    y += 25
    draw.rectangle([(40, y), (w - 40, y + 30)], fill=(240, 240, 240), outline=(150, 150, 150))
    col_x = [40, 90, 380, 560, 720]
    headers = ["No.", "Injury Location & Description", "Dimensions (L x W x D)", "Weapon Inferred", "Nature of Injury"]
    for i, h_text in enumerate(headers):
        draw.text((col_x[i] + 5, y + 7), h_text, fill=(20, 20, 20), font=f_body_bold)

    injuries = [
        ("1", "Incised wound over left forearm", "6.5 cm x 1.2 cm x bone-deep", "Sharp weapon", "Grievous"),
        ("2", "Contusion / hematoma on right parietal scalp", "4.0 cm x 3.0 cm", "Blunt force", "Simple"),
        ("3", "Abrasion over right cheek and nasal bridge", "2.0 cm x 0.8 cm", "Blunt / friction", "Simple"),
    ]
    for r_idx, row in enumerate(injuries):
        ry = y + 30 + r_idx * 35
        draw.rectangle([(40, ry), (w - 40, ry + 35)], outline=(180, 180, 180))
        for c_idx, val in enumerate(row):
            draw.text((col_x[c_idx] + 5, ry + 8), val, fill=(30, 30, 30), font=f_body)

    # Medical Opinion
    y = ry + 60
    draw.rectangle([(40, y), (w - 40, y + 100)], outline=(180, 40, 40), width=1)
    draw.text((50, y + 10), "MEDICAL OPINION & PROGNOSIS:", fill=(180, 20, 20), font=f_body_bold)
    draw.text((50, y + 35), "• Nature of Injury No. 1 is GRIEVOUS (fracture of left ulna confirmed on X-Ray No. XR-4819).", fill=(20, 20, 20), font=f_body_bold)
    draw.text((50, y + 55), "• Nature of Injuries No. 2 and 3 are SIMPLE.", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 75), "• Duration of injuries: Fresh within 2 to 4 hours.", fill=(20, 20, 20), font=f_body)

    # Signatures
    y += 140
    draw.text((50, y), "Signature / LTI of Patient:\nArvind Sharma", fill=(20, 20, 20), font=f_body)
    draw.text((520, y), "Examining Doctor:\nSd/- Dr. Sneha Kulkarni, MBBS, MD (Forensic Medicine)\nReg. No: DMC-68192\nCasualty Medical Officer, AIIMS, New Delhi", fill=(20, 20, 20), font=f_body_bold)

    img.save(out_path, "PNG")


def create_forensic_report(out_path: Path):
    """Forensic Science Lab (FSL) Cyber Certificate under Sec 65B IEA / Sec 63 BSA."""
    w, h = 900, 1300
    img = Image.new("RGB", (w, h), color=(252, 252, 250))
    draw = ImageDraw.Draw(img)

    f_title = get_font(21, bold=True)
    f_sub = get_font(15, bold=True)
    f_body = get_font(13)
    f_body_bold = get_font(13, bold=True)

    draw.text((w//2 - 240, 40), "CENTRAL FORENSIC SCIENCE LABORATORY", fill=(20, 20, 20), font=f_title)
    draw.text((w//2 - 190, 75), "CYBER FORENSICS & DIGITAL EVIDENCE DIVISION", fill=(40, 40, 40), font=f_sub)
    draw.text((w//2 - 270, 100), "CERTIFICATE UNDER SECTION 65B INDIAN EVIDENCE ACT / SEC 63 BSA", fill=(150, 30, 30), font=f_title)
    draw.line([(40, 130), (w - 40, 130)], fill=(80, 80, 80), width=2)

    y = 150
    draw.text((50, y), "FSL Case Reference No: CFSL/CYBER/2026/0419", fill=(20, 20, 20), font=f_body_bold)
    draw.text((500, y), "Date of Certificate: 14-08-2026", fill=(20, 20, 20), font=f_body_bold)
    y += 28
    draw.text((50, y), "Forwarding Authority: Superintendent of Police, CBI, EOW", fill=(20, 20, 20), font=f_body)
    draw.text((500, y), "Crime / FIR No: RC-218/2026/EOW", fill=(20, 20, 20), font=f_body)
    y += 28
    draw.text((50, y), "Parcel Condition: Received 1 Sealed Cloth Parcel with Lead Seal intact ('CBI-SP-ND')", fill=(0, 100, 50), font=f_body_bold)

    # Forensic Examination Findings
    y += 45
    draw.rectangle([(40, y), (w - 40, y + 160)], outline=(100, 100, 100), width=1)
    draw.text((50, y + 10), "EXAMINATION & BIT-STREAM FORENSIC IMAGE DETAILS:", fill=(0, 50, 100), font=f_body_bold)
    draw.text((50, y + 35), "Target Evidence Exhibit: SanDisk 2TB Portable SSD (Serial: SD-992014881)", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 60), "Forensic Acquisition Tool: Tableau Forensic Imager TX1 (Firmware Version 22.4)", fill=(20, 20, 20), font=f_body)
    draw.text((50, y + 90), "Cryptographic Verification Hash (SHA-256):", fill=(20, 20, 20), font=f_body_bold)
    draw.text((50, y + 115), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", fill=(180, 20, 20), font=f_body_bold)
    draw.text((50, y + 135), "MD5 Checksum: d41d8cd98f00b204e9800998ecf8427e (Bit-stream verification: MATCH)", fill=(0, 100, 50), font=f_body)

    # Opinion
    y += 180
    draw.text((40, y), "EXPERT FORENSIC OPINION & STATUTORY DECLARATION:", fill=(20, 20, 20), font=f_body_bold)
    statement = (
        "I hereby certify that the electronic record contained in Exhibit-1 was extracted using forensically validated "
        "write-blocking hardware. The computer system / storage device was operating properly without any alteration or "
        "tampering. The cryptographic SHA-256 hash calculated prior to acquisition matches the post-acquisition image exactly, "
        "establishing unbroken digital chain-of-custody under Section 65B of the Indian Evidence Act, 1872."
    )
    draw.text((40, y + 25), statement, fill=(40, 40, 40), font=f_body)

    # Signatures
    y += 160
    draw.text((500, y), "Forensic Examiner:\nSd/- Dr. Alok Mathur, M.Sc., Ph.D.\nSenior Scientific Officer (Cyber Forensics)\nCentral Forensic Science Laboratory, CBI", fill=(20, 20, 20), font=f_body_bold)

    img.save(out_path, "PNG")


def main():
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)

    print("Generating Indian Police investigation document test samples...")
    create_seizure_memo(samples_dir / "sample_seizure_memo.png")
    print("✓ Created samples/sample_seizure_memo.png")

    create_arrest_memo(samples_dir / "sample_arrest_memo.png")
    print("✓ Created samples/sample_arrest_memo.png")

    create_chargesheet(samples_dir / "sample_chargesheet.png")
    print("✓ Created samples/sample_chargesheet.png")

    create_medical_legal(samples_dir / "sample_medical_legal.png")
    print("✓ Created samples/sample_medical_legal.png")

    create_forensic_report(samples_dir / "sample_forensic_report.png")
    print("✓ Created samples/sample_forensic_report.png")
    print("All samples successfully generated.")


if __name__ == "__main__":
    main()
