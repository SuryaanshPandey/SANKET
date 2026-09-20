"""Cross-Document Intelligence, Entity Reconciliation, and Master Timeline Aggregator."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class EntityOccurrence:
    document_id: str
    filename: str
    doc_type: str
    role: str
    confidence: float


@dataclass
class ReconciledEntity:
    canonical_name: str
    roles: List[str]
    document_count: int
    documents: List[str]  # List of filenames
    occurrences: List[EntityOccurrence]


@dataclass
class TimelineEvent:
    raw_date: str
    normalized_date: Optional[str]  # YYYY-MM-DD if parseable
    document_id: str
    filename: str
    doc_type: str
    label: str
    detail: str


@dataclass
class CrossReferenceItem:
    identifier_type: str
    value: str
    document_count: int
    documents: List[str]  # List of filenames


@dataclass
class DiscrepancyFlag:
    flag_type: str
    severity: str  # "high", "medium", "low"
    documents_involved: List[str]
    message: str


@dataclass
class CrossDocumentAnalysisResult:
    total_documents: int
    doc_types: Dict[str, int]
    overall_case_confidence: float
    reconciled_entities: List[Dict[str, Any]]
    master_timeline: List[Dict[str, Any]]
    cross_references: List[Dict[str, Any]]
    financial_ledger: Dict[str, Any]
    discrepancies: List[Dict[str, Any]]
    case_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_name(name: str) -> str:
    """Normalize names for cross-document reconciliation (strip titles, aliases, parentage)."""
    clean = name.strip()
    # Strip common prefixes
    clean = re.sub(
        r"^(?:shri\.?|smt\.?|mr\.?|ms\.?|mrs\.?|dr\.?|late\b|si\b|io\b|sho\b|adv\.?|inspr\.?|sub-inspector)\s+",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    # Strip parentage suffix e.g. "s/o Late Mohan Lal", "d/o ...", "w/o ..."
    clean = re.split(r"\s+(?:s\/o|d\/o|w\/o|son of|daughter of|wife of)\s+", clean, flags=re.IGNORECASE)[0]
    # Strip age or address suffix
    clean = re.split(r",\s*(?:age|r\/o|resident of)", clean, flags=re.IGNORECASE)[0]
    # Remove special punctuation
    clean = re.sub(r"[\"'\(\)]", "", clean).strip()
    return " ".join(part.upper() if "." in part else part.capitalize() for part in clean.split())


def parse_date_to_sortable(date_str: str) -> Optional[datetime]:
    """Defensively parse various date formats (DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY, etc.) into datetime."""
    clean_date = date_str.strip()
    # Match standard date substring
    m = re.search(r"(\d{1,4})[-/.](\d{1,2})[-/.](\d{1,4})", clean_date)
    if not m:
        return None

    p1, p2, p3 = m.group(1), m.group(2), m.group(3)
    formats = []
    if len(p1) == 4:  # YYYY-MM-DD
        formats.append("%Y-%m-%d")
        candidate = f"{p1}-{p2.zfill(2)}-{p3.zfill(2)}"
    elif len(p3) == 4:  # DD-MM-YYYY
        formats.append("%d-%m-%Y")
        formats.append("%m-%d-%Y")
        candidate = f"{p1.zfill(2)}-{p2.zfill(2)}-{p3}"
    elif len(p3) == 2:  # DD-MM-YY
        formats.append("%d-%m-%y")
        candidate = f"{p1.zfill(2)}-{p2.zfill(2)}-{p3}"
    else:
        return None

    for fmt in formats:
        try:
            return datetime.strptime(candidate, fmt)
        except ValueError:
            continue
    return None


class CrossDocumentAggregator:
    """Consolidates entities, timelines, cross-references, and financials across multiple documents."""

    def analyze(self, documents_data: List[Dict[str, Any]]) -> CrossDocumentAnalysisResult:
        """Run complete multi-document synthesis across a list of document extraction payloads."""
        if not documents_data:
            return CrossDocumentAnalysisResult(
                total_documents=0,
                doc_types={},
                overall_case_confidence=1.0,
                reconciled_entities=[],
                master_timeline=[],
                cross_references=[],
                financial_ledger={"total_amount": 0.0, "currency": "INR", "items": []},
                discrepancies=[],
                case_summary="No documents present in batch.",
            )

        # 1. Document Types & Confidence
        doc_types_count: Dict[str, int] = {}
        confidences: List[float] = []

        for doc in documents_data:
            dtype = doc.get("doc_type") or "other"
            doc_types_count[dtype] = doc_types_count.get(dtype, 0) + 1
            conf = doc.get("overall_confidence", 0.9)
            confidences.append(conf)

        avg_confidence = round(sum(confidences) / max(len(confidences), 1), 3)

        # 2. Reconcile Entities across all documents
        reconciled_entities = self._reconcile_entities(documents_data)

        # 3. Build Unified Chronological Master Timeline
        master_timeline, timeline_flags = self._build_timeline(documents_data)

        # 4. Correlate Identifiers & Cross-References
        cross_references, id_flags = self._correlate_identifiers(documents_data)

        # 5. Aggregate Financial & Property Ledger
        financial_ledger = self._aggregate_financials(documents_data)

        # 6. Collect all discrepancies & coherence warnings
        all_discrepancies = timeline_flags + id_flags
        all_discrepancies += self._check_case_coherence(documents_data, reconciled_entities, cross_references)

        # 7. Generate Executive Case Summary
        case_summary = self._generate_summary(
            total_docs=len(documents_data),
            doc_types=doc_types_count,
            entities=reconciled_entities,
            timeline=master_timeline,
            financials=financial_ledger,
            discrepancies=all_discrepancies,
        )

        return CrossDocumentAnalysisResult(
            total_documents=len(documents_data),
            doc_types=doc_types_count,
            overall_case_confidence=avg_confidence,
            reconciled_entities=[asdict(e) for e in reconciled_entities],
            master_timeline=[asdict(t) for t in master_timeline],
            cross_references=[asdict(r) for r in cross_references],
            financial_ledger=financial_ledger,
            discrepancies=[asdict(d) for d in all_discrepancies],
            case_summary=case_summary,
        )

    def _reconcile_entities(self, documents: List[Dict[str, Any]]) -> List[ReconciledEntity]:
        """Group parties and persons appearing across multiple documents."""
        entity_map: Dict[str, Dict[str, Any]] = {}

        for doc in documents:
            doc_id = doc.get("document_id", "")
            filename = doc.get("original_filename", "unknown")
            doc_type = doc.get("doc_type", "other")
            extracted_data = doc.get("extracted_data") or {}
            parties = extracted_data.get("parties") or []

            # Also check granular field items if parties empty
            if not parties:
                field_items = doc.get("field_items") or []
                for item in field_items:
                    fname = item.get("field_name", "")
                    if "party" in fname.lower() or "complainant" in fname.lower() or "accused" in fname.lower():
                        parties.append({
                            "name": str(item.get("field_value")),
                            "role": fname.split(":")[-1] if ":" in fname else "party",
                            "confidence": item.get("confidence", 0.9),
                        })

            for p in parties:
                if isinstance(p, dict):
                    raw_name = p.get("name") or ""
                    role = p.get("role") or "party"
                    confidence = float(p.get("confidence", 0.9))
                elif isinstance(p, str):
                    raw_name = p
                    role = "party"
                    confidence = 0.9
                else:
                    continue

                if not raw_name or len(raw_name.strip()) < 3:
                    continue

                norm = normalize_name(raw_name)
                # Find matching existing entity (fuzzy or exact key match)
                matched_key = None
                for existing_key in entity_map.keys():
                    if norm.lower() == existing_key.lower() or norm.lower() in existing_key.lower() or existing_key.lower() in norm.lower():
                        matched_key = existing_key
                        break

                if not matched_key:
                    matched_key = norm
                    entity_map[matched_key] = {
                        "canonical_name": norm,
                        "roles": set(),
                        "documents": set(),
                        "occurrences": [],
                    }

                entity_map[matched_key]["roles"].add(role)
                entity_map[matched_key]["documents"].add(filename)
                entity_map[matched_key]["occurrences"].append(
                    EntityOccurrence(
                        document_id=doc_id,
                        filename=filename,
                        doc_type=doc_type,
                        role=role,
                        confidence=confidence,
                    )
                )

        # Convert to ReconciledEntity list, sorted by frequency (descending)
        results = []
        for key, data in entity_map.items():
            results.append(
                ReconciledEntity(
                    canonical_name=data["canonical_name"],
                    roles=sorted(list(data["roles"])),
                    document_count=len(data["documents"]),
                    documents=sorted(list(data["documents"])),
                    occurrences=data["occurrences"],
                )
            )

        results.sort(key=lambda x: (x.document_count, len(x.canonical_name)), reverse=True)
        return results

    def _build_timeline(self, documents: List[Dict[str, Any]]) -> Tuple[List[TimelineEvent], List[DiscrepancyFlag]]:
        """Collect all extracted dates across documents, parse into chronological order, and detect conflicts."""
        events: List[Tuple[Optional[datetime], TimelineEvent]] = []
        flags: List[DiscrepancyFlag] = []

        for doc in documents:
            doc_id = doc.get("document_id", "")
            filename = doc.get("original_filename", "unknown")
            doc_type = doc.get("doc_type", "other")
            extracted_data = doc.get("extracted_data") or {}
            dates = extracted_data.get("dates") or []

            # Also check field items for dates
            if not dates:
                field_items = doc.get("field_items") or []
                for item in field_items:
                    fname = item.get("field_name", "").lower()
                    if "date" in fname:
                        dates.append({"label": fname, "value": str(item.get("field_value"))})

            for d in dates:
                val = d.get("value") if isinstance(d, dict) else str(d)
                lbl = d.get("label", "Date") if isinstance(d, dict) else "Date"
                if not val:
                    continue

                parsed_dt = parse_date_to_sortable(val)
                iso_str = parsed_dt.strftime("%Y-%m-%d") if parsed_dt else None

                event = TimelineEvent(
                    raw_date=val,
                    normalized_date=iso_str,
                    document_id=doc_id,
                    filename=filename,
                    doc_type=doc_type,
                    label=lbl,
                    detail=f"Recorded in {filename} ({doc_type.upper()})",
                )
                events.append((parsed_dt, event))

        # Sort: parseable dates sorted chronologically, unparseable placed at the end
        events_with_date = [e for e in events if e[0] is not None]
        events_without_date = [e for e in events if e[0] is None]
        events_with_date.sort(key=lambda x: x[0])

        sorted_timeline = [e[1] for e in events_with_date] + [e[1] for e in events_without_date]

        # Check for temporal discrepancies across documents
        # For instance: If doc_type 'fir_report' date is later than 'seizure_memo' or 'arrest_memo' date
        fir_dates = [e[0] for e in events_with_date if e[1].doc_type == "fir_report"]
        seizure_dates = [e[0] for e in events_with_date if e[1].doc_type == "seizure_memo"]
        arrest_dates = [e[0] for e in events_with_date if e[1].doc_type == "arrest_memo"]

        if fir_dates and seizure_dates:
            earliest_fir = min(fir_dates)
            earliest_seizure = min(seizure_dates)
            if earliest_seizure < earliest_fir:
                flags.append(
                    DiscrepancyFlag(
                        flag_type="TEMPORAL_CONTRADICTION",
                        severity="high",
                        documents_involved=["FIR Report", "Seizure Memo"],
                        message=(
                            f"Seizure date ({earliest_seizure.strftime('%Y-%m-%d')}) predates "
                            f"FIR registration date ({earliest_fir.strftime('%Y-%m-%d')}). "
                            f"Requires evidentiary justification under Sec 100/102 CrPC."
                        ),
                    )
                )

        if fir_dates and arrest_dates:
            earliest_fir = min(fir_dates)
            earliest_arrest = min(arrest_dates)
            if earliest_arrest < earliest_fir:
                flags.append(
                    DiscrepancyFlag(
                        flag_type="TEMPORAL_CONTRADICTION",
                        severity="high",
                        documents_involved=["FIR Report", "Arrest Memo"],
                        message=(
                            f"Arrest date ({earliest_arrest.strftime('%Y-%m-%d')}) predates "
                            f"FIR registration date ({earliest_fir.strftime('%Y-%m-%d')})."
                        ),
                    )
                )

        return sorted_timeline, flags

    def _correlate_identifiers(self, documents: List[Dict[str, Any]]) -> Tuple[List[CrossReferenceItem], List[DiscrepancyFlag]]:
        """Identify matching and divergent identifiers (FIR Nos, Case IDs, Serial Nos, Sections)."""
        id_map: Dict[str, Dict[str, Set[str]]] = {}  # type -> value -> set of filenames
        flags: List[DiscrepancyFlag] = []

        for doc in documents:
            filename = doc.get("original_filename", "unknown")
            extracted_data = doc.get("extracted_data") or {}
            identifiers = extracted_data.get("identifiers") or []

            if not identifiers:
                field_items = doc.get("field_items") or []
                for item in field_items:
                    fname = item.get("field_name", "").lower()
                    if any(k in fname for k in ["fir", "case", "station", "fsl", "mlc", "imei", "serial", "section"]):
                        identifiers.append({
                            "type": item.get("field_name"),
                            "value": str(item.get("field_value")),
                        })

            for item in identifiers:
                itype = item.get("type") or "Identifier"
                val = str(item.get("value") or "").strip()
                if not val or len(val) < 2:
                    continue

                # Standardize category
                norm_type = "FIR / Crime No" if any(k in itype.lower() for k in ["fir", "crime"]) else (
                    "Police Station" if any(k in itype.lower() for k in ["station", "thana", "ps"]) else (
                        "Act & Section" if any(k in itype.lower() for k in ["section", "u/s", "ipc", "bns"]) else (
                            "FSL / Forensic Ref" if "fsl" in itype.lower() else (
                                "Serial / IMEI" if any(k in itype.lower() for k in ["imei", "serial"]) else itype
                            )
                        )
                    )
                )

                if norm_type not in id_map:
                    id_map[norm_type] = {}
                if val not in id_map[norm_type]:
                    id_map[norm_type][val] = set()
                id_map[norm_type][val].add(filename)

        # Check for multiple conflicting FIR numbers across documents of the same case
        if "FIR / Crime No" in id_map and len(id_map["FIR / Crime No"]) > 1:
            values = list(id_map["FIR / Crime No"].keys())
            docs = [doc for val in values for doc in id_map["FIR / Crime No"][val]]
            flags.append(
                DiscrepancyFlag(
                    flag_type="IDENTIFIER_MISMATCH",
                    severity="high",
                    documents_involved=sorted(list(set(docs))),
                    message=f"Multiple conflicting FIR / Crime Numbers detected across documents: {', '.join(values)}",
                )
            )

        # Build list of CrossReferenceItem
        result: List[CrossReferenceItem] = []
        for itype, val_dict in id_map.items():
            for val, doc_set in val_dict.items():
                result.append(
                    CrossReferenceItem(
                        identifier_type=itype,
                        value=val,
                        document_count=len(doc_set),
                        documents=sorted(list(doc_set)),
                    )
                )

        # Sort: identifiers appearing in multiple documents first
        result.sort(key=lambda x: (x.document_count, x.identifier_type), reverse=True)
        return result, flags

    def _aggregate_financials(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate monetary amounts and itemized property values across all documents."""
        total = 0.0
        currency = "INR"
        items = []

        for doc in documents:
            filename = doc.get("original_filename", "unknown")
            doc_type = doc.get("doc_type", "other")
            extracted_data = doc.get("extracted_data") or {}
            amounts = extracted_data.get("amounts") or []

            for a in amounts:
                val = float(a.get("value", 0.0))
                lbl = a.get("label", "Amount")
                curr = a.get("currency", "INR")
                if curr:
                    currency = curr
                if val > 0:
                    total += val
                    items.append({
                        "label": lbl,
                        "value": val,
                        "currency": curr,
                        "source_doc": filename,
                        "doc_type": doc_type,
                    })

        return {
            "total_amount": round(total, 2),
            "currency": currency,
            "item_count": len(items),
            "items": items,
        }

    def _check_case_coherence(
        self,
        documents: List[Dict[str, Any]],
        entities: List[ReconciledEntity],
        identifiers: List[CrossReferenceItem],
    ) -> List[DiscrepancyFlag]:
        """Verify cross-document evidentiary rules (e.g. accused in FIR vs arrest memo)."""
        flags: List[DiscrepancyFlag] = []
        doc_types = {doc.get("doc_type") for doc in documents}

        # Check if case has both Seizure Memo and Arrest Memo, but different persons named
        if "seizure_memo" in doc_types and "arrest_memo" in doc_types:
            # Find persons with role 'accused' or 'arrestee'
            suspects = [
                e for e in entities
                if any(r in ["accused", "arrestee", "person from whom recovered"] for r in e.roles)
            ]
            if not suspects:
                flags.append(
                    DiscrepancyFlag(
                        flag_type="MISSING_CORROBORATION",
                        severity="medium",
                        documents_involved=["Seizure Memo", "Arrest Memo"],
                        message="No corroborated suspect or arrestee name linked across Seizure Memo and Arrest Memo.",
                    )
                )

        return flags

    def _generate_summary(
        self,
        total_docs: int,
        doc_types: Dict[str, int],
        entities: List[ReconciledEntity],
        timeline: List[TimelineEvent],
        financials: Dict[str, Any],
        discrepancies: List[DiscrepancyFlag],
    ) -> str:
        """Synthesize a human-readable case dossier summary."""
        type_str = ", ".join(f"{count} {dtype.replace('_', ' ').title()}" for dtype, count in doc_types.items())
        key_entities = [e.canonical_name for e in entities[:3]]
        entity_str = ", ".join(key_entities) if key_entities else "No major entities extracted"
        
        amt_str = f"{financials.get('currency', 'INR')} {financials.get('total_amount', 0.0):,.2f}"
        
        discrepancy_str = (
            f"⚠ {len(discrepancies)} cross-document discrepancy warning(s) detected requiring review."
            if discrepancies
            else "✓ Full cross-document evidentiary consistency verified (0 conflicting identifiers or dates)."
        )

        return (
            f"Case Dossier containing {total_docs} document(s) ({type_str}). "
            f"Primary cross-document entities identified: {entity_str}. "
            f"Total financial/property ledger: {amt_str} across {financials.get('item_count', 0)} itemized entries. "
            f"Timeline spans {len(timeline)} chronological event(s). {discrepancy_str}"
        )
