"""Defensive parsing, sanitization, and Pydantic validation of model outputs."""

import json
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    x: float = Field(default=0.0, description="Normalized x coordinate (0-1000)")
    y: float = Field(default=0.0, description="Normalized y coordinate (0-1000)")
    w: float = Field(default=0.0, description="Normalized width (0-1000)")
    h: float = Field(default=0.0, description="Normalized height (0-1000)")


class PartyItem(BaseModel):
    name: str
    role: Optional[str] = "party"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None


class DateItem(BaseModel):
    label: str
    value: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None


class AmountItem(BaseModel):
    label: str
    value: float
    currency: Optional[str] = "USD"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None

    @field_validator("value", mode="before")
    @classmethod
    def parse_numeric(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Clean commas, dollar signs, currency symbols
            cleaned = re.sub(r"[^\d.-]", "", v)
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0


class IdentifierItem(BaseModel):
    type: str
    value: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None


class StructuredExtraction(BaseModel):
    document_type: str = "other"
    parties: List[Union[PartyItem, str]] = Field(default_factory=list)
    dates: List[DateItem] = Field(default_factory=list)
    amounts: List[AmountItem] = Field(default_factory=list)
    identifiers: List[IdentifierItem] = Field(default_factory=list)
    raw_text: str = ""
    notes_on_legibility: str = ""
    overall_confidence: float = Field(default=0.9, ge=0.0, le=1.0)

    @field_validator("document_type", mode="before")
    @classmethod
    def normalize_doc_type(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "other"
        lower = v.lower().strip()
        if lower in {"receipt", "invoice", "fir_report", "seizure_memo", "arrest_memo", "charge_sheet", "medical_legal", "forensic_report", "case_diary", "contract", "bank_statement", "id_document", "other"}:
            return lower
        if any(k in lower for k in ["fir", "first information", "police report", "thana", "form 27"]):
            return "fir_report"
        if any(k in lower for k in ["seizure", "panch", "fard", "mahazar"]):
            return "seizure_memo"
        if any(k in lower for k in ["arrest", "basu", "custody"]):
            return "arrest_memo"
        if any(k in lower for k in ["charge", "challan", "173", "193"]):
            return "charge_sheet"
        if any(k in lower for k in ["medic", "post-mortem", "pmr", "autopsy", "mlc"]):
            return "medical_legal"
        if any(k in lower for k in ["forensic", "fsl", "cyber", "65b", "63 bsa"]):
            return "forensic_report"
        if any(k in lower for k in ["invoice", "receipt", "bill"]):
            return "invoice"
        if any(k in lower for k in ["contract", "agreement", "deed"]):
            return "contract"
        if any(k in lower for k in ["bank", "statement"]):
            return "bank_statement"
        return lower or "other"


def extract_json_substring(text: str) -> str:
    """Strip markdown code blocks, preambles, and conversational artifacts, prioritizing outer document JSON."""
    text = text.strip()

    # 1. Strip markdown code fence if present
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)(?:```|$)"
    match = re.search(fence_pattern, text, re.IGNORECASE)
    cleaned = match.group(1).strip() if match else text

    # Scope to the first opening brace
    first_brace = cleaned.find("{")
    if first_brace != -1:
        cleaned = cleaned[first_brace:]

    # 2. Try direct decode from the outermost {
    decoder = json.JSONDecoder()
    try:
        obj, end = decoder.raw_decode(cleaned)
        if isinstance(obj, dict) and any(k in obj for k in ["document_type", "parties", "identifiers", "dates", "amounts", "raw_text"]):
            return cleaned[:end]
    except Exception:
        pass

    # 3. Try repair_truncated_json on the outermost structure
    try:
        repaired = repair_truncated_json(cleaned)
        obj, end = decoder.raw_decode(repaired)
        if isinstance(obj, dict) and any(k in obj for k in ["document_type", "parties", "identifiers", "dates", "amounts", "raw_text"]):
            return repaired
    except Exception:
        pass

    # 4. Try prefix extraction on the outermost structure
    prefix_obj = extract_valid_json_prefix(cleaned)
    if isinstance(prefix_obj, dict):
        return json.dumps(prefix_obj)

    # 5. Search for any valid dictionary, but ONLY if it contains root document keys
    start_pos = 0
    valid_candidates = []
    while True:
        idx = cleaned.find("{", start_pos)
        if idx == -1:
            break
        try:
            obj, end = decoder.raw_decode(cleaned[idx:])
            if isinstance(obj, dict) and any(k in obj for k in ["document_type", "parties", "identifiers", "dates", "amounts", "raw_text"]):
                valid_candidates.append(cleaned[idx : idx + end])
        except Exception:
            pass
        start_pos = idx + 1

    if valid_candidates:
        return max(valid_candidates, key=len)

    # 6. Fallback to outer braces if present
    last_brace = cleaned.rfind("}")
    if last_brace != -1 and last_brace > 0:
        return cleaned[: last_brace + 1].strip()

    return cleaned


def repair_common_json_issues(json_str: str) -> str:
    """Heuristic cleanup for trailing commas and control characters."""
    # Remove trailing commas before } or ]
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
    return json_str


def heuristic_extract_from_text(raw_text: str) -> StructuredExtraction:
    """Robust fallback and enrichment extractor that mines parties, dates, amounts, and identifiers from text."""
    lower = raw_text.lower()

    # 1. Determine document type
    if any(k in lower for k in ["first information report", "fir", "b.p. form", "police station", "thana"]):
        doc_type = "fir_report"
    elif any(k in lower for k in ["seizure memo", "panchnama", "fard-e-zabti", "mahazar", "seizure list", "sec 27"]):
        doc_type = "seizure_memo"
    elif any(k in lower for k in ["arrest memo", "inspection memo", "d.k. basu", "arrested person"]):
        doc_type = "arrest_memo"
    elif any(k in lower for k in ["charge sheet", "chargesheet", "challan", "final report under sec 173", "iif-5"]):
        doc_type = "charge_sheet"
    elif any(k in lower for k in ["medico-legal", "injury report", "post-mortem", "pmr", "autopsy", "mlc"]):
        doc_type = "medical_legal"
    elif any(k in lower for k in ["forensic", "fsl", "ballistic", "toxicology", "65b certificate", "cyber report"]):
        doc_type = "forensic_report"
    elif any(k in lower for k in ["invoice", "bill", "tax invoice", "receipt"]):
        doc_type = "invoice"
    elif any(k in lower for k in ["contract", "agreement", "mou", "deed"]):
        doc_type = "contract"
    elif any(k in lower for k in ["bank", "statement", "passbook"]):
        doc_type = "bank_statement"
    else:
        doc_type = "other"

    parties: List[PartyItem] = []
    identifiers: List[IdentifierItem] = []
    dates: List[DateItem] = []
    amounts: List[AmountItem] = []

    # 2. Extract Parties
    party_patterns = [
        (r"(?:complainant|informant)\s*(?:name)?[:\s\-]+([A-Za-z\s.]{3,35})", "complainant"),
        (r"(?:inform\s+you\s+that\s+I|beg\s+to\s+state\s+that\s+I|that\s+I|I\b)[,\s]+([A-Z][a-zA-Z\s.]{2,30}?)(?=[,\s]+(?:residing|aged|s/o|d/o|w/o|a\s+resident|\n))", "complainant"),
        (r"(?:accused|suspect)\s*(?:name)?[:\s\-]+([A-Za-z0-9\s.,]{3,40})", "accused"),
        (r"(?:panch\s*witness|panch\s*no\.?\s*\d?|witness)\s*[:\s\-]+([A-Za-z\s.]{3,35})", "panch_witness"),
        (r"(?:arrestee|person\s*arrested)\s*[:\s\-]+([A-Za-z\s.]{3,35})", "arrestee"),
        (r"(?:arresting\s*officer)\s*[:\s\-]+([A-Za-z\s.]{3,35})", "arresting_officer"),
        (r"(?:relative|intimated\s*person)\s*[:\s\-]+([A-Za-z\s.]{3,35})", "intimated_person"),
        (r"(?:examining\s*doctor|medical\s*officer)\s*[:\s\-]+([A-Za-z\s.]{3,35})", "examining_doctor"),
        (r"(?:hospital|institution)\s*[:\s\-]+([A-Za-z\s.]{3,35})", "hospital"),
        (r"(?:victim|deceased|injured)\s*(?:name)?[:\s\-]+([A-Za-z\s.]{3,35})", "victim"),
        (r"(?:investigating\s*officer|io|sho)\s*(?:name)?[:\s\-]+([A-Za-z\s.]{3,35})", "investigating_officer"),
        (r"(?:seller|vendor)\s*(?:name)?[:\s\-]+([A-Za-z0-9\s.,&]{3,40})", "vendor"),
        (r"(?:buyer|customer|bill to)\s*(?:name)?[:\s\-]+([A-Za-z0-9\s.,&]{3,40})", "buyer"),
    ]
    seen_names = set()
    for pat, role in party_patterns:
        for match in re.finditer(pat, raw_text, re.IGNORECASE):
            name = match.group(1).strip().strip(".,;:\"'")
            if name and name.lower() not in seen_names and len(name) >= 3 and not any(k in name.lower() for k in ["police", "station", "report", "subject"]):
                seen_names.add(name.lower())
                parties.append(PartyItem(name=name, role=role, confidence=0.85))

    # 3. Extract Identifiers
    id_patterns = [
        (r"fir\s*(?:no|number|#)?[:\s.]+([0-9]+(?:\/[0-9]+)?)", "FIR Number"),
        (r"(?:police\s*station|p\.?s\.?|thana)[:\s.]+([A-Za-z\s]{3,30})", "Police Station"),
        (r"(?:saving\s*account\s*no\.?|account\s*no\.?|a/c\s*no\.?)[:\s.]+([0-9\s]{6,20})", "Bank Account Number"),
        (r"(?:district|dist)[:\s.]+([A-Za-z\s]{3,25})", "District"),
        (r"(?:u/s|sec(?:tion)?|ipc)[:\s.]+([A-Za-z0-9,\s\/]+(?:ipc|act|crpc|bns)?)", "Act & Section"),
        (r"(?:fsl\s*(?:ref|case|report)?\s*no)[:\s.]+([A-Za-z0-9\/\-_]+)", "FSL Reference No"),
        (r"(?:mlc\s*(?:no|number)|pmr\s*no)[:\s.]+([A-Za-z0-9\/\-_]+)", "Medico-Legal Record No"),
        (r"(?:sha-?256|hash)[:\s.]+([A-Fa-f0-9]{64})", "SHA-256 Hash"),
        (r"(?:serial|imei)[:\s.]+([A-Za-z0-9\/\-_]+)", "Serial / IMEI Number"),
        (r"(?:grounds\s*of\s*arrest)[:\s.]+([A-Za-z0-9\s,.\-_]{5,60})", "Grounds of Arrest"),
        (r"(?:seal\s*(?:status|mark|impression))[:\s.]+([A-Za-z0-9\s]{3,30})", "Seal Status"),
        (r"(?:g\.?d\.?\s*entry|gd\s*no)[:\s.]+([A-Za-z0-9\/\-_]+)", "GD Entry No"),
        (r"(?:invoice\s*(?:no|number|#))[:\s.]+([A-Za-z0-9\/\-_]+)", "Invoice Number"),
    ]
    seen_ids = set()
    for pat, label in id_patterns:
        for match in re.finditer(pat, raw_text, re.IGNORECASE):
            val = match.group(1).strip().strip(".,;:\"'")
            if val and val.lower() not in seen_ids and len(val) >= 2:
                seen_ids.add(val.lower())
                identifiers.append(IdentifierItem(type=label, value=val, confidence=0.85))

    # Also recover from JSON-like fragments
    for match in re.finditer(r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"role"\s*:\s*"([^"]+)"', raw_text, re.IGNORECASE):
        n, r = match.group(1).strip(), match.group(2).strip()
        if n and n.lower() not in seen_names and len(n) >= 2:
            seen_names.add(n.lower())
            parties.append(PartyItem(name=n, role=r, confidence=0.9))

    for match in re.finditer(r'\{\s*"type"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"([^"]+)"', raw_text, re.IGNORECASE):
        t, v = match.group(1).strip(), match.group(2).strip()
        if v and v.lower() not in seen_ids and len(v) >= 2:
            seen_ids.add(v.lower())
            identifiers.append(IdentifierItem(type=t, value=v, confidence=0.9))

    for match in re.finditer(r'\{\s*"label"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"([^"]+)"', raw_text, re.IGNORECASE):
        lbl, val = match.group(1).strip(), match.group(2).strip()
        dates.append(DateItem(label=lbl, value=val, confidence=0.9))

    # 4. Extract Dates
    date_matches = re.findall(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b", raw_text)
    for i, d in enumerate(date_matches[:5]):
        dates.append(DateItem(label=f"Date_{i+1}", value=d, confidence=0.85))

    # 5. Extract Amounts
    amt_matches = re.finditer(r"(?:rs\.?|inr|₹|\$)\s*([\d,]+(?:\.\d{2})?)", raw_text, re.IGNORECASE)
    for match in amt_matches:
        raw_val = match.group(1).replace(",", "")
        try:
            val = float(raw_val)
            curr = "INR" if any(c in lower for c in ["rs", "₹", "inr"]) else "USD"
            amounts.append(AmountItem(label="Property Value / Stated Amount", value=val, currency=curr, confidence=0.85))
        except ValueError:
            pass

    # Clean narrative summary: strip any raw JSON markup if present
    clean_summary = raw_text.strip()
    if clean_summary.startswith("{") or '"document_type"' in clean_summary:
        rt_match = re.search(r'"raw_text"\s*:\s*"([^"]+)"', clean_summary)
        clean_summary = rt_match.group(1) if rt_match else ""

    return StructuredExtraction(
        document_type=doc_type,
        parties=parties,
        dates=dates,
        amounts=amounts,
        identifiers=identifiers,
        raw_text=clean_summary[:2000],
        notes_on_legibility="Extracted via forensic heuristic recovery engine",
        overall_confidence=0.80,
    )


def repair_truncated_json(text: str) -> str:
    """Repair incomplete JSON caused by token budget cut-offs by closing open brackets/braces."""
    cleaned = text.strip()
    # Strip any trailing incomplete key or unclosed value e.g. "bounding_box": {"x": 100, "y":
    cleaned = re.sub(r",?\s*\"[^\"]*\"?\s*:\s*[^,}\]]*$", "", cleaned)
    cleaned = re.sub(r",\s*$", "", cleaned)

    stack = []
    in_str = False
    escape = False
    for ch in cleaned:
        if ch == "\\" and in_str:
            escape = not escape
            continue
        if ch == "\"" and not escape:
            in_str = not in_str
        elif not in_str:
            if ch in "{[":
                stack.append(ch)
            elif ch == "}" and stack and stack[-1] == "{":
                stack.pop()
            elif ch == "]" and stack and stack[-1] == "[":
                stack.pop()
        escape = False

    tail = ""
    if in_str:
        tail += "\""

    while stack:
        top = stack.pop()
        if top == "{":
            tail += "}"
        elif top == "[":
            tail += "]"
    return cleaned + tail


def extract_valid_json_prefix(text: str) -> Optional[Dict[str, Any]]:
    """Progressively recover the largest valid JSON object from interrupted or corrupted VLM streams."""
    text = text.strip()
    first_brace = text.find("{")
    if first_brace == -1:
        return None
    scoped = text[first_brace:]

    for idx in range(len(scoped), 0, -1):
        char = scoped[idx - 1]
        if char in ("\"", "}", "]", ","):
            sub = scoped[:idx].rstrip(",")
            for closing in ["}", "]}", "]}}", "\"}", "\"} }"]:
                try:
                    candidate = sub + closing
                    res = json.loads(candidate)
                    if isinstance(res, dict) and any(k in res for k in ["parties", "identifiers", "dates", "amounts", "document_type"]):
                        return res
                except Exception:
                    pass
    return None


def parse_and_validate_extraction(raw_text: str) -> StructuredExtraction:
    """Defensively parse and validate VLM output into StructuredExtraction with schema normalization and heuristic fallback."""
    candidate = extract_json_substring(raw_text)
    candidate = repair_common_json_issues(candidate)

    data = None
    try:
        data = json.loads(candidate)
    except Exception:
        try:
            repaired = repair_truncated_json(candidate)
            data = json.loads(repaired)
        except Exception:
            pass

    if not isinstance(data, dict):
        prefix_data = extract_valid_json_prefix(raw_text)
        if isinstance(prefix_data, dict):
            data = prefix_data
        else:
            return heuristic_extract_from_text(raw_text)

    # 1. Normalize dates (handles both list of dicts and key-value dict)
    if "dates" in data:
        norm_dates: List[DateItem] = []
        if isinstance(data["dates"], dict):
            for k, v in data["dates"].items():
                if isinstance(v, dict):
                    norm_dates.append(DateItem(
                        label=k,
                        value=str(v.get("value", "")),
                        confidence=float(v.get("confidence", 0.9)),
                        bounding_box=v.get("bounding_box")
                    ))
                elif v is not None:
                    norm_dates.append(DateItem(label=str(k), value=str(v), confidence=0.9))
            data["dates"] = norm_dates
        elif isinstance(data["dates"], list):
            for d in data["dates"]:
                if isinstance(d, dict):
                    norm_dates.append(DateItem(
                        label=d.get("label") or d.get("type") or "date",
                        value=str(d.get("value", "")),
                        confidence=float(d.get("confidence", 0.9)),
                        bounding_box=d.get("bounding_box")
                    ))
                elif isinstance(d, str):
                    norm_dates.append(DateItem(label="date", value=d, confidence=0.9))
            data["dates"] = norm_dates

    # 2. Normalize identifiers (handles both list of dicts and key-value dict)
    if "identifiers" in data:
        norm_ids: List[IdentifierItem] = []
        if isinstance(data["identifiers"], dict):
            for k, v in data["identifiers"].items():
                if isinstance(v, dict):
                    norm_ids.append(IdentifierItem(
                        type=k,
                        value=str(v.get("value", "")),
                        confidence=float(v.get("confidence", 0.9)),
                        bounding_box=v.get("bounding_box")
                    ))
                elif v is not None:
                    norm_ids.append(IdentifierItem(type=str(k), value=str(v), confidence=0.9))
            data["identifiers"] = norm_ids
        elif isinstance(data["identifiers"], list):
            for item in data["identifiers"]:
                if isinstance(item, dict):
                    norm_ids.append(IdentifierItem(
                        type=item.get("type") or item.get("label") or item.get("key") or "identifier",
                        value=str(item.get("value", "")),
                        confidence=float(item.get("confidence", 0.9)),
                        bounding_box=item.get("bounding_box")
                    ))
                elif isinstance(item, str):
                    norm_ids.append(IdentifierItem(type="identifier", value=item, confidence=0.9))
            data["identifiers"] = norm_ids

    # 3. Normalize amounts (handles both list of dicts and key-value dict)
    if "amounts" in data:
        norm_amounts: List[AmountItem] = []
        if isinstance(data["amounts"], dict):
            for k, v in data["amounts"].items():
                norm_amounts.append(AmountItem(label=str(k), value=v, currency="INR", confidence=0.9))
            data["amounts"] = norm_amounts
        elif isinstance(data["amounts"], list):
            for item in data["amounts"]:
                if isinstance(item, dict):
                    norm_amounts.append(AmountItem(
                        label=item.get("label") or item.get("type") or "amount",
                        value=item.get("value", 0.0),
                        currency=item.get("currency", "INR"),
                        confidence=float(item.get("confidence", 0.9)),
                        bounding_box=item.get("bounding_box")
                    ))
                elif isinstance(item, (int, float, str)):
                    norm_amounts.append(AmountItem(label="amount", value=item, currency="INR", confidence=0.9))
            data["amounts"] = norm_amounts

    # 4. Normalize parties (handles list of dicts, strings, and key-value dict)
    if "parties" in data:
        norm_parties: List[PartyItem] = []
        if isinstance(data["parties"], dict):
            for k, v in data["parties"].items():
                norm_parties.append(PartyItem(name=str(v), role=str(k), confidence=0.9))
            data["parties"] = norm_parties
        elif isinstance(data["parties"], list):
            for p in data["parties"]:
                if isinstance(p, str):
                    norm_parties.append(PartyItem(name=p, role="party", confidence=0.9))
                elif isinstance(p, dict):
                    norm_parties.append(PartyItem(
                        name=p.get("name") or p.get("value") or p.get("party") or "Unknown Party",
                        role=p.get("role") or "party",
                        confidence=float(p.get("confidence", 0.9)),
                        bounding_box=p.get("bounding_box")
                    ))
            data["parties"] = norm_parties

    # Clean narrative summary
    if "raw_text" in data and isinstance(data["raw_text"], str):
        narrative = data["raw_text"].strip()
        if narrative.startswith("{") or '"document_type"' in narrative:
            data["raw_text"] = ""
        else:
            data["raw_text"] = narrative[:1500]

    try:
        extraction = StructuredExtraction.model_validate(data)
    except Exception:
        extraction = heuristic_extract_from_text(raw_text)

    # 5. Enrich with forensic heuristic extraction if entities are missing
    heuristic = heuristic_extract_from_text(raw_text)
    if not extraction.parties and heuristic.parties:
        extraction.parties = heuristic.parties
    if not extraction.dates and heuristic.dates:
        extraction.dates = heuristic.dates
    if not extraction.amounts and heuristic.amounts:
        extraction.amounts = heuristic.amounts
    if not extraction.identifiers and heuristic.identifiers:
        extraction.identifiers = heuristic.identifiers
    if (not extraction.raw_text or len(extraction.raw_text.strip()) < 10) and heuristic.raw_text:
        extraction.raw_text = heuristic.raw_text
    if extraction.document_type in ("other", "official letter") and heuristic.document_type != "other":
        extraction.document_type = heuristic.document_type

    return extraction


def flatten_extracted_fields(extraction: StructuredExtraction) -> List[Dict[str, Any]]:
    """Transform StructuredExtraction into a flat list of fields for the extracted_fields table."""
    items: List[Dict[str, Any]] = []

    # Parties
    for i, party in enumerate(extraction.parties):
        if isinstance(party, PartyItem):
            items.append({
                "field_name": f"party:{party.role or 'party'}_{i+1}",
                "field_value": party.name,
                "confidence": party.confidence,
                "bounding_box": party.bounding_box.model_dump() if party.bounding_box else None,
            })
        elif isinstance(party, str):
            items.append({
                "field_name": f"party_{i+1}",
                "field_value": party,
                "confidence": 0.9,
                "bounding_box": None,
            })

    # Dates
    for item in extraction.dates:
        items.append({
            "field_name": f"date:{item.label}",
            "field_value": item.value,
            "confidence": item.confidence,
            "bounding_box": item.bounding_box.model_dump() if item.bounding_box else None,
        })

    # Amounts
    for item in extraction.amounts:
        label = f"amount:{item.label} ({item.currency})" if item.currency else f"amount:{item.label}"
        items.append({
            "field_name": label,
            "field_value": f"{item.value:.2f}",
            "confidence": item.confidence,
            "bounding_box": item.bounding_box.model_dump() if item.bounding_box else None,
        })

    # Identifiers
    for item in extraction.identifiers:
        items.append({
            "field_name": f"id:{item.type}",
            "field_value": item.value,
            "confidence": item.confidence,
            "bounding_box": item.bounding_box.model_dump() if item.bounding_box else None,
        })

    # Summary narrative and text notes
    if extraction.raw_text and len(extraction.raw_text.strip()) > 5:
        items.append({
            "field_name": "summary:incident_description",
            "field_value": extraction.raw_text.strip(),
            "confidence": extraction.overall_confidence,
            "bounding_box": None,
        })
    if extraction.notes_on_legibility and len(extraction.notes_on_legibility.strip()) > 3:
        items.append({
            "field_name": "notes:legibility_assessment",
            "field_value": extraction.notes_on_legibility.strip(),
            "confidence": 1.0,
            "bounding_box": None,
        })

    return items
