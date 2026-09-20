"""Statutory forensic quality gates for Indian Police investigation documents.

Enforces compliance with:
- Code of Criminal Procedure (CrPC) / Bharatiya Nagarik Suraksha Sanhita (BNSS)
- Indian Penal Code (IPC) / Bharatiya Nyaya Sanhita (BNS)
- Indian Evidence Act (IEA) / Bharatiya Sakshya Adhiniyam (BSA)
- Supreme Court directives (D.K. Basu guidelines on arrest & custody)
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional
from clarity.vlm.parser import StructuredExtraction


def parse_flexible_date(date_str: str) -> Optional[datetime]:
    """Attempt parsing multiple Indian date formats (DD/MM/YYYY, DD-MM-YY, etc.)."""
    cleaned = re.sub(r"[^\d/-]", "", date_str.strip())
    formats = [
        "%d/%m/%Y", "%d-%m-%Y",
        "%d/%m/%y", "%d-%m-%y",
        "%Y-%m-%d", "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def verify_fir_compliance(extraction: StructuredExtraction) -> List[Dict[str, Any]]:
    """Verify statutory FIR requirements under Sec 154 CrPC / Sec 173 BNSS."""
    flags: List[Dict[str, Any]] = []

    # 1. Mandatory Identifiers
    id_types = [i.type.lower() for i in extraction.identifiers]
    id_values = {i.type.lower(): i.value for i in extraction.identifiers}

    has_fir_no = any("fir" in t for t in id_types) or any("fir" in i.value.lower() for i in extraction.identifiers)
    if not has_fir_no:
        flags.append({
            "type": "missing_fir_number",
            "field": "identifiers:FIR Number",
            "severity": "critical",
            "message": "FIR Number is missing from document extraction (mandatory under Sec 154 CrPC).",
        })

    has_ps = any("police station" in t or "ps" in t or "thana" in t for t in id_types)
    if not has_ps:
        flags.append({
            "type": "missing_police_station",
            "field": "identifiers:Police Station",
            "severity": "high",
            "message": "Police Station (Thana) jurisdiction is missing from FIR extraction.",
        })

    has_acts = any("act" in t or "sec" in t or "ipc" in t or "bns" in t for t in id_types)
    if not has_acts:
        flags.append({
            "type": "missing_acts_and_sections",
            "field": "identifiers:Acts & Sections",
            "severity": "high",
            "message": "Statutory penal provisions (IPC / BNS / Special Acts) not detected.",
        })

    # 2. Chronological Integrity
    occurrence_dt = None
    registration_dt = None
    for d in extraction.dates:
        lbl = d.label.lower()
        if "occurrence" in lbl:
            occurrence_dt = parse_flexible_date(d.value)
        elif "registration" in lbl or "reporting" in lbl or "dispatch" in lbl:
            registration_dt = parse_flexible_date(d.value)

    if occurrence_dt and registration_dt and occurrence_dt > registration_dt:
        flags.append({
            "type": "chronology_violation",
            "field": "dates:occurrence_vs_registration",
            "severity": "critical",
            "message": f"Temporal impossibility: Occurrence date ({occurrence_dt.strftime('%d-%m-%Y')}) is after FIR registration date ({registration_dt.strftime('%d-%m-%Y')}).",
        })

    return flags


def verify_seizure_memo_compliance(extraction: StructuredExtraction) -> List[Dict[str, Any]]:
    """Verify Panchnama / Seizure Memo under Sec 100 & 102 CrPC / Sec 105 BNSS."""
    flags: List[Dict[str, Any]] = []

    # 1. Two Independent Panch Witnesses requirement (Sec 100(4) CrPC)
    panch_count = 0
    for p in extraction.parties:
        role = p.role.lower() if hasattr(p, "role") and p.role else ""
        name = p.name.lower() if hasattr(p, "name") else str(p).lower()
        if "panch" in role or "witness" in role or "panch" in name:
            panch_count += 1

    if panch_count < 2:
        flags.append({
            "type": "insufficient_panch_witnesses",
            "field": "parties:panch_witness",
            "severity": "critical",
            "message": f"Sec 100(4) CrPC / Sec 105 BNSS requires at least 2 independent Panch witnesses. Found {panch_count}.",
        })

    # 2. Seal Status Check
    id_types = [i.type.lower() for i in extraction.identifiers]
    has_seal_info = any("seal" in t for t in id_types) or any("seal" in extraction.raw_text.lower() for _ in [1])
    if not has_seal_info:
        flags.append({
            "type": "missing_seal_impression",
            "field": "identifiers:Seal Status",
            "severity": "medium",
            "message": "No sample seal impression or sealed parcel condition verified on seizure memo.",
        })

    return flags


def verify_arrest_memo_compliance(extraction: StructuredExtraction) -> List[Dict[str, Any]]:
    """Verify D.K. Basu Human Rights Directives & Sec 41B CrPC / Sec 36 BNSS."""
    flags: List[Dict[str, Any]] = []

    # 1. Arrestee identification
    has_arrestee = any(
        ("arrest" in (getattr(p, "role", "") or "").lower() or "accused" in (getattr(p, "role", "") or "").lower())
        for p in extraction.parties
    )
    if not has_arrestee:
        flags.append({
            "type": "missing_arrestee_identity",
            "field": "parties:arrestee",
            "severity": "critical",
            "message": "Arrestee identity not confirmed in arrest memo.",
        })

    # 2. Grounds of Arrest
    id_types = [i.type.lower() for i in extraction.identifiers]
    has_grounds = any("ground" in t for t in id_types) or "ground" in extraction.raw_text.lower()
    if not has_grounds:
        flags.append({
            "type": "missing_grounds_of_arrest",
            "field": "identifiers:Grounds of Arrest",
            "severity": "high",
            "message": "Constitutional requirement (Article 22(1) & Sec 41B CrPC): Grounds of arrest not recorded.",
        })

    # 3. Family Intimation
    has_intimation = any(
        ("relat" in (getattr(p, "role", "") or "").lower() or "intimat" in (getattr(p, "role", "") or "").lower())
        for p in extraction.parties
    ) or any("intimat" in extraction.raw_text.lower() for _ in [1])

    if not has_intimation:
        flags.append({
            "type": "missing_family_intimation",
            "field": "parties:intimated_person",
            "severity": "high",
            "message": "D.K. Basu mandate: Intimation of arrest to next-of-kin / friend is missing.",
        })

    return flags


def verify_charge_sheet_compliance(extraction: StructuredExtraction) -> List[Dict[str, Any]]:
    """Verify Final Police Report under Sec 173 CrPC / Sec 193 BNSS."""
    flags: List[Dict[str, Any]] = []

    # 1. At least one chargesheeted accused
    chargesheeted_count = 0
    for p in extraction.parties:
        role = (getattr(p, "role", "") or "").lower()
        if "accused" in role or "chargesheet" in role:
            chargesheeted_count += 1

    if chargesheeted_count == 0:
        flags.append({
            "type": "missing_chargesheeted_accused",
            "field": "parties:accused",
            "severity": "critical",
            "message": "No chargesheeted accused identified in final police report.",
        })

    # 2. Penal Sections
    id_types = [i.type.lower() for i in extraction.identifiers]
    has_sections = any("act" in t or "sec" in t or "ipc" in t or "bns" in t for t in id_types)
    if not has_sections:
        flags.append({
            "type": "missing_penal_charges",
            "field": "identifiers:Acts & Sections",
            "severity": "critical",
            "message": "Charge sheet lacks specific penal sections of law (IPC/BNS).",
        })

    return flags


def verify_medical_legal_compliance(extraction: StructuredExtraction) -> List[Dict[str, Any]]:
    """Verify Medico-Legal Certificates (MLC) and Post-Mortem Reports (PMR)."""
    flags: List[Dict[str, Any]] = []

    has_doctor = any(
        ("doctor" in (getattr(p, "role", "") or "").lower() or "medical" in (getattr(p, "role", "") or "").lower())
        for p in extraction.parties
    )
    if not has_doctor:
        flags.append({
            "type": "missing_examining_doctor",
            "field": "parties:examining_doctor",
            "severity": "high",
            "message": "Examining Medical Officer / Autopsy Surgeon identity is missing.",
        })

    # Check for injury nature classification
    raw_lower = extraction.raw_text.lower()
    has_injury_classification = any(
        term in raw_lower for term in ["simple", "grievous", "fatal", "dangerous", "blunt", "sharp", "firearm"]
    )
    if not has_injury_classification and not any("injury" in i.type.lower() for i in extraction.identifiers):
        flags.append({
            "type": "missing_injury_classification",
            "field": "identifiers:Injury Classification",
            "severity": "medium",
            "message": "Medico-legal classification (Simple vs. Grievous) not formally categorized.",
        })

    return flags


def verify_forensic_report_compliance(extraction: StructuredExtraction) -> List[Dict[str, Any]]:
    """Verify FSL & Cyber Forensic Certificates under Sec 65B IEA / Sec 63 BSA."""
    flags: List[Dict[str, Any]] = []

    # Digital forensic certificates must have cryptographic hash
    id_types = [i.type.lower() for i in extraction.identifiers]
    has_hash = any("hash" in t or "sha" in t or "md5" in t for t in id_types)
    raw_has_hash = bool(re.search(r"\b[A-Fa-f0-9]{32,64}\b", extraction.raw_text))

    if not has_hash and not raw_has_hash:
        flags.append({
            "type": "missing_digital_hash",
            "field": "identifiers:Cryptographic Hash",
            "severity": "high",
            "message": "Section 65B IEA / Sec 63 BSA electronic evidence certificate missing cryptographic hash verification (SHA-256 / MD5).",
        })

    return flags
