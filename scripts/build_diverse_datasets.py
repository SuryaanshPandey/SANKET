"""Acquire and generate diverse document datasets for testing Clarity / Sanket."""

import os
import shutil
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT_DIR / "samples"
DIVERSE_DIR = SAMPLES_DIR / "diverse"


def get_default_font(size: int = 14) -> ImageFont.ImageFont:
    try:
        # Common macOS fonts
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except Exception:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def get_bold_font(size: int = 16) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
    except Exception:
        return get_default_font(size)


def setup_directories():
    for sub in ["police_case", "receipts", "invoices", "financial", "contracts", "degraded"]:
        (DIVERSE_DIR / sub).mkdir(parents=True, exist_ok=True)


def setup_police_case():
    """Copy forensic police documents into police_case bundle."""
    target = DIVERSE_DIR / "police_case"
    mappings = [
        ("01_fir_report.png", "sample_fir_report.png"),
        ("02_seizure_memo.png", "sample_seizure_memo.png"),
        ("03_arrest_memo.png", "sample_arrest_memo.png"),
        ("04_medico_legal.png", "sample_medical_legal.png"),
        ("05_forensic_report.png", "sample_forensic_report.png"),
    ]
    for dst_name, src_name in mappings:
        src = SAMPLES_DIR / src_name
        if src.exists():
            shutil.copy2(src, target / dst_name)
    print("✓ Setup Police Case Dossier (5 docs)")


def download_sroie_receipts():
    """Download authentic scanned receipts from ICDAR 2019 SROIE competition."""
    target = DIVERSE_DIR / "receipts"
    urls = [
        ("01_sroie_grocery_receipt.jpg", "https://raw.githubusercontent.com/zzzDavid/ICDAR-2019-SROIE/master/data/img/000.jpg"),
        ("02_sroie_retail_pos.jpg", "https://raw.githubusercontent.com/zzzDavid/ICDAR-2019-SROIE/master/data/img/001.jpg"),
        ("03_sroie_supermarket_tax.jpg", "https://raw.githubusercontent.com/zzzDavid/ICDAR-2019-SROIE/master/data/img/002.jpg"),
    ]
    for fname, url in urls:
        dst = target / fname
        if not dst.exists():
            try:
                urllib.request.urlretrieve(url, dst)
                print(f"✓ Downloaded ICDAR SROIE receipt: {fname}")
            except Exception as e:
                print(f"Warning: could not download {url}: {e}")
                # Create fallback receipt
                create_sample_receipt(dst, fname)
        else:
            print(f"✓ Found existing receipt: {fname}")


def create_sample_receipt(dst: Path, title: str):
    """Generate high-contrast thermal receipt if download fails."""
    img = Image.new("RGB", (480, 800), color=(250, 248, 240))
    draw = ImageDraw.Draw(img)
    font = get_default_font(13)
    bold = get_bold_font(18)

    draw.text((120, 30), "MEGA RETAIL MART", fill=(20, 20, 20), font=bold)
    draw.text((140, 60), "TAX INVOICE / RECEIPT", fill=(60, 60, 60), font=font)
    draw.text((40, 90), "Date: 12-OCT-2026 14:32   Reg: 04-B   Cashier: Alex", fill=(40, 40, 40), font=font)
    draw.line([(40, 115), (440, 115)], fill=(120, 120, 120), width=1)

    items = [
        ("Organic Whole Milk 1L", "2 x $3.50", "$7.00"),
        ("Sourdough Artisanal Bread", "1 x $4.25", "$4.25"),
        ("Fairtrade Dark Roast Coffee", "1 x $12.99", "$12.99"),
        ("California Almonds 500g", "1 x $8.50", "$8.50"),
        ("Eco Paper Bags", "2 x $0.25", "$0.50"),
    ]
    y = 130
    for name, qty, price in items:
        draw.text((40, y), name, fill=(20, 20, 20), font=font)
        draw.text((260, y), qty, fill=(60, 60, 60), font=font)
        draw.text((390, y), price, fill=(20, 20, 20), font=font)
        y += 26

    draw.line([(40, y + 10), (440, y + 10)], fill=(120, 120, 120), width=1)
    y += 25
    draw.text((240, y), "SUBTOTAL:", fill=(30, 30, 30), font=bold)
    draw.text((385, y), "$33.24", fill=(30, 30, 30), font=bold)
    y += 24
    draw.text((240, y), "TAX (8.25%):", fill=(60, 60, 60), font=font)
    draw.text((395, y), "$2.74", fill=(60, 60, 60), font=font)
    y += 26
    draw.text((240, y), "GRAND TOTAL:", fill=(10, 10, 10), font=bold)
    draw.text((375, y), "$35.98", fill=(10, 10, 10), font=bold)
    y += 35
    draw.text((40, y), "CARD PAYMENT: VISA ENDING IN *4921", fill=(50, 50, 50), font=font)
    draw.text((40, y + 20), "AUTH CODE: 839210   REF: TR-892147", fill=(50, 50, 50), font=font)
    draw.text((120, y + 70), "THANK YOU FOR SHOPPING WITH US!", fill=(40, 40, 40), font=font)

    img.save(dst)


def generate_commercial_invoices():
    """Generate high-fidelity B2B tax invoices with itemized tables and tax calculation."""
    target = DIVERSE_DIR / "invoices"
    
    # 1. Cloud Infrastructure Tech Invoice
    img1 = Image.new("RGB", (1000, 1400), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    font = get_default_font(15)
    bold = get_bold_font(18)
    title_font = get_bold_font(26)

    # Header
    draw1.text((60, 60), "NEXUS CLOUD TECHNOLOGIES PVT LTD", fill=(15, 23, 42), font=title_font)
    draw1.text((60, 100), "Cyber City, DLF Phase II, Gurugram, HR 122002", fill=(71, 85, 105), font=font)
    draw1.text((60, 125), "GSTIN: 06AABCN8291M1Z5 | PAN: AABCN8291M", fill=(71, 85, 105), font=font)

    draw1.text((700, 60), "TAX INVOICE", fill=(30, 41, 59), font=title_font)
    draw1.text((700, 100), "Invoice No: INV-2026-0892", fill=(15, 23, 42), font=bold)
    draw1.text((700, 125), "Date: 15-JAN-2026", fill=(71, 85, 105), font=font)
    draw1.text((700, 150), "Due Date: 30-JAN-2026", fill=(71, 85, 105), font=font)

    # Bill To
    draw1.rectangle([(60, 190), (940, 290)], outline=(203, 213, 225), width=1, fill=(248, 250, 252))
    draw1.text((80, 205), "BILLED TO:", fill=(100, 116, 139), font=get_bold_font(13))
    draw1.text((80, 230), "Apex Global Logistics Solutions LLP", fill=(15, 23, 42), font=bold)
    draw1.text((80, 255), "Connaught Place, Barakhamba Road, New Delhi, DL 110001", fill=(51, 65, 85), font=font)

    # Table Header
    y = 320
    draw1.rectangle([(60, y), (940, y + 40)], fill=(226, 232, 240))
    draw1.text((80, y + 10), "DESCRIPTION", fill=(30, 41, 59), font=bold)
    draw1.text((480, y + 10), "HSN / SAC", fill=(30, 41, 59), font=bold)
    draw1.text((620, y + 10), "QTY", fill=(30, 41, 59), font=bold)
    draw1.text((720, y + 10), "UNIT RATE", fill=(30, 41, 59), font=bold)
    draw1.text((850, y + 10), "AMOUNT", fill=(30, 41, 59), font=bold)

    # Items
    items = [
        ("Enterprise GPU Compute Cluster (A100 x 8)", "998313", "1 Month", "145,000.00", "145,000.00"),
        ("Petabyte Object Storage Archive", "998315", "100 TB", "450.00", "45,000.00"),
        ("Dedicated Fiber Interconnect 10Gbps", "998422", "1 Port", "18,500.00", "18,500.00"),
        ("24/7 Forensic Audit & Compliance Tier", "998319", "1 Service", "25,000.00", "25,000.00"),
    ]
    y += 45
    for desc, hsn, qty, rate, amt in items:
        draw1.text((80, y), desc, fill=(15, 23, 42), font=font)
        draw1.text((480, y), hsn, fill=(71, 85, 105), font=font)
        draw1.text((620, y), qty, fill=(71, 85, 105), font=font)
        draw1.text((720, y), rate, fill=(71, 85, 105), font=font)
        draw1.text((850, y), amt, fill=(15, 23, 42), font=font)
        y += 35
        draw1.line([(60, y - 5), (940, y - 5)], fill=(241, 245, 249), width=1)

    # Totals Box
    y = 520
    draw1.rectangle([(550, y), (940, y + 190)], outline=(203, 213, 225), width=1, fill=(248, 250, 252))
    draw1.text((580, y + 15), "Taxable Subtotal:", fill=(71, 85, 105), font=font)
    draw1.text((820, y + 15), "INR 233,500.00", fill=(15, 23, 42), font=font)

    draw1.text((580, y + 45), "CGST @ 9.0%:", fill=(71, 85, 105), font=font)
    draw1.text((820, y + 45), "INR 21,015.00", fill=(15, 23, 42), font=font)

    draw1.text((580, y + 75), "SGST @ 9.0%:", fill=(71, 85, 105), font=font)
    draw1.text((820, y + 75), "INR 21,015.00", fill=(15, 23, 42), font=font)

    draw1.line([(570, y + 110), (920, y + 110)], fill=(203, 213, 225), width=1)

    draw1.text((580, y + 125), "TOTAL PAYABLE:", fill=(15, 23, 42), font=bold)
    draw1.text((800, y + 125), "INR 275,530.00", fill=(15, 23, 42), font=title_font)

    # Bank Details
    draw1.text((60, 540), "PAYMENT INSTRUCTIONS / NEFT / RTGS:", fill=(15, 23, 42), font=bold)
    draw1.text((60, 570), "Bank Name: HDFC Bank Ltd", fill=(71, 85, 105), font=font)
    draw1.text((60, 595), "A/C Name: Nexus Cloud Technologies Pvt Ltd", fill=(71, 85, 105), font=font)
    draw1.text((60, 620), "A/C Number: 50200084729104", fill=(71, 85, 105), font=font)
    draw1.text((60, 645), "IFSC Code: HDFC0000280", fill=(71, 85, 105), font=font)

    # Stamp & Sign
    draw1.rectangle([(680, 850), (900, 950)], outline=(59, 130, 246), width=2)
    draw1.text((700, 870), "NEXUS CLOUD TECH", fill=(59, 130, 246), font=bold)
    draw1.text((720, 900), "DIGITALLY SIGNED", fill=(59, 130, 246), font=get_bold_font(12))

    img1.save(target / "01_cloud_tech_b2b_invoice.png")

    # 2. Industrial Hardware Supply Invoice
    if (SAMPLES_DIR / "test_invoice.jpg").exists():
        shutil.copy2(SAMPLES_DIR / "test_invoice.jpg", target / "02_industrial_hardware_invoice.jpg")

    print("✓ Generated Commercial B2B Invoices (2 docs)")


def generate_bank_statements():
    """Generate financial transaction statement."""
    target = DIVERSE_DIR / "financial"
    img = Image.new("RGB", (1000, 1400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = get_default_font(14)
    bold = get_bold_font(16)
    title = get_bold_font(24)

    draw.text((60, 50), "STATE BANK OF COMMERCE", fill=(10, 30, 80), font=title)
    draw.text((60, 85), "Branch: Parliament Street, New Delhi 110001", fill=(80, 80, 80), font=font)
    draw.text((60, 110), "IFSC: SBOC0001924 | MICR: 110002014", fill=(80, 80, 80), font=font)

    draw.rectangle([(60, 145), (940, 235)], outline=(200, 200, 200), fill=(245, 248, 252))
    draw.text((80, 160), "Account Holder: RAJESH VERMA (TRADING CO)", fill=(20, 20, 20), font=bold)
    draw.text((80, 185), "Account Number: 309821448201", fill=(40, 40, 40), font=font)
    draw.text((80, 208), "Statement Period: 01-FEB-2026 to 28-FEB-2026", fill=(40, 40, 40), font=font)
    draw.text((600, 160), "Account Type: Current Account", fill=(40, 40, 40), font=font)
    draw.text((600, 185), "Opening Balance: INR 4,82,500.00", fill=(20, 20, 20), font=bold)
    draw.text((600, 208), "Closing Balance: INR 6,18,950.00", fill=(10, 120, 40), font=bold)

    # Table
    y = 260
    draw.rectangle([(60, y), (940, y + 35)], fill=(220, 230, 245))
    draw.text((70, y + 8), "DATE", fill=(20, 40, 80), font=bold)
    draw.text((180, y + 8), "TRANSACTION PARTICULARS", fill=(20, 40, 80), font=bold)
    draw.text((540, y + 8), "REF / CHQ", fill=(20, 40, 80), font=bold)
    draw.text((670, y + 8), "DEBIT (DR)", fill=(180, 20, 20), font=bold)
    draw.text((780, y + 8), "CREDIT (CR)", fill=(20, 140, 40), font=bold)
    draw.text((860, y + 8), "BALANCE", fill=(20, 40, 80), font=bold)

    txs = [
        ("02-FEB-2026", "RTGS INWARD: NEXUS CLOUD PAYMENT", "RTGS89210", "-", "2,75,530.00", "7,58,030.00"),
        ("05-FEB-2026", "NEFT OUTWARD: VENDOR HARDWARE SUPPLY", "NEFT41092", "1,85,000.00", "-", "5,73,030.00"),
        ("12-FEB-2026", "ATM CASH WITHDRAWAL VASANT VIHAR", "ATM9921", "25,000.00", "-", "5,48,030.00"),
        ("18-FEB-2026", "IMPS INWARD: LEGAL CONSULTANCY RETAINER", "IMPS33019", "-", "1,20,000.00", "6,68,030.00"),
        ("24-FEB-2026", "CHQ 004812: WAREHOUSE LEASE RENTAL", "CHQ004812", "50,000.00", "-", "6,18,030.00"),
        ("28-FEB-2026", "INTEREST CREDIT Q4", "INTCR91", "-", "920.00", "6,18,950.00"),
    ]
    y += 40
    for dt, desc, ref, dr, cr, bal in txs:
        draw.text((70, y), dt, fill=(40, 40, 40), font=font)
        draw.text((180, y), desc, fill=(20, 20, 20), font=font)
        draw.text((540, y), ref, fill=(70, 70, 70), font=font)
        draw.text((670, y), dr, fill=(180, 20, 20), font=font)
        draw.text((780, y), cr, fill=(20, 120, 30), font=font)
        draw.text((860, y), bal, fill=(20, 20, 20), font=bold)
        y += 35
        draw.line([(60, y - 5), (940, y - 5)], fill=(230, 230, 230), width=1)

    img.save(target / "01_bank_account_statement.png")

    # Wire transfer receipt
    img2 = Image.new("RGB", (900, 700), color=(255, 255, 255))
    d2 = ImageDraw.Draw(img2)
    d2.text((50, 40), "GLOBAL SWIFT WIRE TRANSFER CONFIRMATION", fill=(10, 20, 50), font=bold)
    d2.text((50, 80), "Transaction Reference Number: TRN-2026-SW-908124", fill=(70, 70, 70), font=font)
    d2.rectangle([(50, 110), (850, 400)], outline=(200, 200, 200), fill=(248, 248, 250))
    d2.text((70, 130), "Remitter Name: Apex Global Logistics Solutions LLP", fill=(20, 20, 20), font=font)
    d2.text((70, 160), "Beneficiary: Nexus Cloud Technologies Pvt Ltd", fill=(20, 20, 20), font=font)
    d2.text((70, 190), "Beneficiary Bank: HDFC Bank Ltd, New Delhi", fill=(20, 20, 20), font=font)
    d2.text((70, 220), "Amount: USD 3,310.00 (Equivalent INR 2,75,530.00)", fill=(10, 100, 30), font=bold)
    d2.text((70, 250), "Value Date: 02-FEB-2026", fill=(40, 40, 40), font=font)
    d2.text((70, 280), "Status: SETTLED & RECONCILED", fill=(10, 120, 30), font=bold)
    img2.save(target / "02_wire_transfer_receipt.png")

    print("✓ Generated Financial Statements (2 docs)")


def generate_contracts():
    """Generate legal contract / NDA."""
    target = DIVERSE_DIR / "contracts"
    img = Image.new("RGB", (1000, 1400), color=(253, 253, 250))
    draw = ImageDraw.Draw(img)
    font = get_default_font(14)
    bold = get_bold_font(16)
    title = get_bold_font(22)

    draw.text((250, 60), "MUTUAL NON-DISCLOSURE AGREEMENT", fill=(15, 23, 42), font=title)
    draw.text((380, 100), "CONFIDENTIAL & PROPRIETARY", fill=(180, 50, 50), font=bold)
    draw.line([(60, 130), (940, 130)], fill=(200, 200, 200), width=1)

    text = """
    This Mutual Non-Disclosure Agreement ("Agreement") is executed on this 10th day of January, 2026 ("Effective Date"),
    by and between:

    PARTIES:
    1. NEXUS CLOUD TECHNOLOGIES PVT. LTD., a private limited company incorporated under the Companies Act,
       having its registered office at Cyber City, Gurugram, HR (hereinafter referred to as the "Disclosing Party").

    2. APEX GLOBAL LOGISTICS SOLUTIONS LLP, a limited liability partnership incorporated under the LLP Act,
       having its principal place of business at Connaught Place, New Delhi (hereinafter referred to as "Recipient").

    RECITALS & PURPOSE:
    The parties desire to explore a mutual business transaction relating to sovereign artificial intelligence systems
    and enterprise data pipelines ("Purpose"), and in connection therewith, disclose Confidential Information.

    TERMS & CONDITIONS:
    1. DEFINITION OF CONFIDENTIAL INFORMATION:
       Includes technical source code, forensic algorithms, model weights, client lists, and operational documentation.

    2. NON-DISCLOSURE OBLIGATIONS:
       The Recipient agrees to hold all Confidential Information in strict confidence and not disclose it to any third party
       without prior written authorization from the Disclosing Party.

    3. TERM & TERMINATION:
       This Agreement shall remain in effect for a period of two (2) years from the Effective Date.

    4. GOVERNING LAW & JURISDICTION:
       This Agreement shall be governed by and construed in accordance with the Laws of India, and the Courts of New Delhi
       shall have exclusive territorial jurisdiction over any disputes arising hereunder.
    """
    y = 150
    for line in text.strip().split("\n"):
        draw.text((80, y), line.strip(), fill=(30, 41, 59), font=font)
        y += 24

    # Signatures
    y += 40
    draw.text((100, y), "FOR NEXUS CLOUD TECHNOLOGIES:", fill=(15, 23, 42), font=bold)
    draw.text((600, y), "FOR APEX GLOBAL LOGISTICS:", fill=(15, 23, 42), font=bold)
    y += 50
    draw.text((100, y), "Name: Vikramaditya Sen", fill=(71, 85, 105), font=font)
    draw.text((600, y), "Name: Rajesh Verma", fill=(71, 85, 105), font=font)
    y += 25
    draw.text((100, y), "Title: Managing Director", fill=(71, 85, 105), font=font)
    draw.text((600, y), "Title: Designated Partner", fill=(71, 85, 105), font=font)

    img.save(target / "01_mutual_nda_agreement.png")

    # Second contract: Master Service Level Agreement
    img2 = Image.new("RGB", (1000, 1400), color=(253, 253, 250))
    d2 = ImageDraw.Draw(img2)
    d2.text((280, 60), "MASTER SERVICE LEVEL AGREEMENT (SLA)", fill=(15, 23, 42), font=title)
    d2.text((60, 120), "Contract Identifier: SLA-2026-NX-8821", fill=(71, 85, 105), font=bold)
    d2.text((60, 150), "Service Tier: High-Availability Mission-Critical Enterprise (99.95% SLA)", fill=(15, 23, 42), font=font)
    d2.text((60, 180), "Monthly Retainer: INR 2,75,530.00 (Including applicable GST)", fill=(15, 23, 42), font=font)
    d2.text((60, 210), "Incident Resolution Time: Priority 1 issues within 30 minutes", fill=(15, 23, 42), font=font)
    img2.save(target / "02_service_level_agreement.png")

    print("✓ Generated Legal Contracts & NDAs (2 docs)")


def generate_degraded_scanner_samples():
    """Generate skewed and low-contrast degraded scanner tests for OpenCV preprocessing."""
    target = DIVERSE_DIR / "degraded"
    
    src = SAMPLES_DIR / "sample_fir_report.png"
    if src.exists():
        img = cv2.imread(str(src))
        # 1. Skewed / Rotated scan (3 degrees)
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, 3.5, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        cv2.imwrite(str(target / "01_skewed_rotated_fir.png"), rotated)

        # 2. Low Contrast & High Noise scan
        low_contrast = cv2.convertScaleAbs(img, alpha=0.55, beta=40)
        noise = np.random.normal(0, 15, low_contrast.shape).astype(np.uint8)
        noisy = cv2.add(low_contrast, noise)
        cv2.imwrite(str(target / "02_low_contrast_noisy_fir.png"), noisy)

    print("✓ Generated Degraded / Skewed Scanner Samples (2 docs)")


def main():
    setup_directories()
    setup_police_case()
    download_sroie_receipts()
    generate_commercial_invoices()
    generate_bank_statements()
    generate_contracts()
    generate_degraded_scanner_samples()
    print("\nAll diverse benchmark datasets successfully generated in samples/diverse/!")


if __name__ == "__main__":
    main()
