"use client";

import React, { useMemo, useState } from "react";
import { AlertTriangle, CalendarDays, CheckCircle2, Coins, Copy, Download, ExternalLink, FileText, Fingerprint, Layers, Search, Scale, Users } from "lucide-react";
import { API_BASE, useCaseStore } from "@/store/useCaseStore";

export const DocumentInspectorView: React.FC = () => {
  const { documents, activeDocIndex } = useCaseStore();
  const [imageType, setImageType] = useState<"preprocessed" | "original">("preprocessed");
  const [highlightedBbox, setHighlightedBbox] = useState<any | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(null);
  const [reviewState, setReviewState] = useState<Record<string, { human_verified: boolean; corrected_value?: string | null }>>({});
  const [reviewBusy, setReviewBusy] = useState(false);
  const doc = documents[activeDocIndex];

  if (!doc) return <div className="sanket-empty-state">Select a source document to inspect.</div>;

  const imageUrl = `${API_BASE}/api/v1/documents/${doc.document_id}/image?type=${imageType}`;
  const prepEvent = doc.audit_trail?.find((event) => event.action === "preprocessing");
  const metrics = prepEvent?.detail?.metrics || {};
  const confPct = Math.round((doc.overall_confidence || 0) * 100);

  const copyHash = async () => {
    try { await navigator.clipboard.writeText(doc.file_hash_sha256); alert("SHA-256 copied to clipboard"); } catch { alert("Unable to copy SHA-256"); }
  };

  const exportContract = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/documents/${doc.document_id}/graph-contract`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const contract = await response.json();
      const blob = new Blob([JSON.stringify(contract, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `graph_contract_${doc.original_filename.replace(/[^a-zA-Z0-9_-]/g, "_")}.json`; link.click(); URL.revokeObjectURL(url);
    } catch (error: any) { alert(`Unable to export Graph Contract: ${error?.message || "unknown error"}`); }
  };

  const categoryOf = (name: string) => {
    const value = name.toLowerCase();
    if (value.startsWith("rule:")) return "RULE";
    if (value.startsWith("party:") || value.includes("accused") || value.includes("witness") || value.includes("officer")) return "PARTY";
    if (value.startsWith("date:") || value.includes("date") || value.includes("time")) return "DATE";
    if (value.startsWith("amount:") || value.includes("amount") || value.includes("total") || value.includes("price") || value.includes("tax")) return "AMOUNT";
    if (value.startsWith("id:") || value.includes("number") || value.includes("hash") || value.includes("fir") || value.includes("serial") || value.includes("imei") || value.includes("section")) return "ID";
    return "OTHER";
  };

  const ruleFields = useMemo(() => (doc.field_items || []).filter((field) => categoryOf(field.field_name) === "RULE"), [doc.field_items]);
  const filteredFields = useMemo(() => (doc.field_items || []).filter((field) => {
    if (selectedCategory !== "ALL" && categoryOf(field.field_name) !== selectedCategory) return false;
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase(); return field.field_name.toLowerCase().includes(query) || field.field_value.toLowerCase().includes(query);
  }), [doc.field_items, selectedCategory, searchQuery]);
  const selectedField = filteredFields.find((field) => field.id === selectedFieldId) || null;

  const reviewField = async (correctedValue?: string) => {
    if (!selectedField?.id || reviewBusy) return;
    setReviewBusy(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/extracted-fields/${encodeURIComponent(selectedField.id)}/review?actor_id=lead_investigator`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ human_verified: true, corrected_value: correctedValue ?? selectedField.field_value }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
      setReviewState((current) => ({ ...current, [selectedField.id as string]: { human_verified: true, corrected_value: body.corrected_value } }));
    } catch (error: any) {
      alert(`Unable to record field review: ${error?.message || "unknown error"}`);
    } finally {
      setReviewBusy(false);
    }
  };

  const correctSelectedField = async () => {
    if (!selectedField?.id) return;
    const corrected = window.prompt(`Correct value for ${selectedField.field_name}`, selectedField.field_value);
    if (corrected === null) return;
    await reviewField(corrected.trim());
  };

  const categories = [
    { key: "ALL", label: "All", count: doc.field_items?.length || 0, icon: Layers },
    { key: "RULE", label: "Rules", count: ruleFields.length, icon: Scale },
    { key: "PARTY", label: "People", count: (doc.field_items || []).filter((f) => categoryOf(f.field_name) === "PARTY").length, icon: Users },
    { key: "DATE", label: "Dates", count: (doc.field_items || []).filter((f) => categoryOf(f.field_name) === "DATE").length, icon: CalendarDays },
    { key: "AMOUNT", label: "Amounts", count: (doc.field_items || []).filter((f) => categoryOf(f.field_name) === "AMOUNT").length, icon: Coins },
    { key: "ID", label: "Identifiers", count: (doc.field_items || []).filter((f) => categoryOf(f.field_name) === "ID").length, icon: Fingerprint },
  ];

  return (
    <div className="sanket-inspector">
      <div className="sanket-inspector__source">
        <div className="sanket-inspector__toolbar">
          <div><span className="sanket-card__meta">Source document</span><strong>{doc.original_filename}</strong></div>
          <div className="sanket-inspector__toolbar-actions">
            <button type="button" className={`sanket-button ${imageType === "preprocessed" ? "is-active" : ""}`} onClick={() => setImageType("preprocessed")} title="View the processed image used for extraction">Processed</button>
            <button type="button" className={`sanket-button ${imageType === "original" ? "is-active" : ""}`} onClick={() => setImageType("original")} title="View the untouched source image">Original</button>
            <button type="button" className="sanket-button" onClick={copyHash} title="Copy the source SHA-256 digest"><Copy size={13} /> SHA-256</button>
          </div>
        </div>
        <div className="sanket-inspector__image-area">
          <div className="sanket-document-frame">
            <img src={imageUrl} alt={doc.original_filename} />
            <svg className="sanket-document-bboxes" viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true">
              {(doc.field_items || []).map((field, index) => field.bounding_box ? <rect key={index} x={field.bounding_box.x} y={field.bounding_box.y} width={field.bounding_box.w} height={field.bounding_box.h} className={highlightedBbox === field ? "is-highlighted" : ""} /> : null)}
            </svg>
          </div>
        </div>
        <div className="sanket-inspector__source-footer">
          <div><span>SHA-256</span><strong>{doc.file_hash_sha256.slice(0, 22)}…</strong></div>
          <div><span>Confidence</span><strong className={confPct < 85 ? "is-warn" : ""}>{confPct}%</strong></div>
          <div><span>Preprocessing</span><strong>{metrics.perspective_corrected ? "Perspective corrected" : "Planar"} · {Number(metrics.deskew_angle_degrees || 0).toFixed(1)}° deskew</strong></div>
        </div>
      </div>

      <aside className="sanket-inspector__details">
        <div className="sanket-inspector__details-head">
          <div><span className="sanket-card__meta">Extracted record</span><h3>{String(doc.doc_type || "document").replaceAll("_", " ")}</h3><span className="sanket-pill">{doc.field_items?.length || 0} fields</span></div>
          <button type="button" className="sanket-button" onClick={exportContract} title="Export this document as a Graph Contract"><Download size={13} /> Graph Contract</button>
        </div>

        {doc.validation_flags?.length ? <div className="sanket-inspector__flags"><div className="sanket-card__meta">Needs attention</div>{doc.validation_flags.map((flag, index) => <div className="sanket-inspector__flag" key={index}><AlertTriangle size={14} color="var(--amber)" /><span>{flag.message || JSON.stringify(flag)}</span></div>)}</div> : <div className="sanket-inspector__pass"><CheckCircle2 size={14} color="var(--green)" /> No document-level validation flags</div>}

        {ruleFields.length > 0 && <details className="sanket-inspector__rules" open><summary><span><Scale size={13} /> Rule-derived checks</span><span>{ruleFields.length}</span></summary><div className="sanket-rule-list">{ruleFields.map((field, index) => <div className="sanket-rule-row" key={index}><strong>{field.field_name.replace(/^rule:/, "").replaceAll("_", " ")}</strong><span>{field.field_value}</span></div>)}</div></details>}

        <div className="sanket-inspector__fields-head"><div><span className="sanket-card__meta">Fields</span><strong>Inspect extracted values</strong></div><div className="sanket-inspector__field-search"><Search size={13} /><input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search fields" /></div></div>
        <div className="sanket-category-row">{categories.map(({ key, label, count, icon: Icon }) => <button key={key} type="button" className={selectedCategory === key ? "is-active" : ""} onClick={() => setSelectedCategory(key)} title={`Show ${label} extracted fields`}><Icon size={12} />{label}<span>{count}</span></button>)}</div>
        <div className="sanket-field-list">
          {filteredFields.map((field, index) => { const reviewed = field.id ? reviewState[field.id] : undefined; return <button key={`${field.id || field.field_name}-${index}`} type="button" className={`sanket-field-item ${highlightedBbox === field ? "is-highlighted" : ""} ${selectedFieldId === field.id ? "is-selected" : ""}`} title={`Inspect ${field.field_name}: ${field.field_value || "no value"}`} onClick={() => setSelectedFieldId(field.id || null)} onMouseEnter={() => setHighlightedBbox(field)} onMouseLeave={() => setHighlightedBbox(null)}><div><span>{field.field_name}</span><span className="flex items-center gap-1">{field.bounding_box && <em>BBOX</em>}{reviewed?.human_verified ? <em className="is-verified">VERIFIED</em> : null}</span></div><strong>{reviewed?.corrected_value || field.field_value || "—"}</strong><small>{Math.round((field.confidence || 0) * 100)}% confidence{reviewed?.human_verified ? " · human reviewed" : ""}</small></button>; })}
          {!filteredFields.length && <div className="sanket-summary-copy">No fields match this filter.</div>}
        </div>
        {selectedField && <div className="sanket-field-review-bar"><div><span>Selected field</span><strong>{selectedField.field_name}</strong><small>{selectedField.field_value || "—"}</small></div><div className="sanket-field-review-actions"><button type="button" className="sanket-button" onClick={() => void reviewField()} disabled={!selectedField.id || reviewBusy || Boolean(reviewState[selectedField.id || ""]?.human_verified)}> <CheckCircle2 size={12} /> {reviewState[selectedField.id || ""]?.human_verified ? "Verified" : "Verify"}</button><button type="button" className="sanket-button" onClick={() => void correctSelectedField()} disabled={!selectedField.id || reviewBusy}><ExternalLink size={12} /> Correct</button></div></div>}

        <details className="sanket-inspector__audit"><summary><span>Audit trail</span><span>{doc.audit_trail?.length || 0} entries</span></summary><div>{(doc.audit_trail || []).map((entry, index) => <div key={index}><strong>{entry.action}</strong><span>{entry.timestamp?.slice(11, 19) || "—"} UTC · {entry.actor_id}</span></div>)}</div></details>
      </aside>
    </div>
  );
};
