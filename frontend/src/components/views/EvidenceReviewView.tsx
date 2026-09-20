"use client";

import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, FileSearch, Fingerprint, RefreshCw, ArrowRight } from "lucide-react";
import { API_BASE, useCaseStore } from "@/store/useCaseStore";

interface Observation { filename: string; field_name: string; value: string; confidence: number; bounding_box?: { x: number; y: number; w: number; h: number } | null; }
interface Contradiction { contradiction_id: string; type: string; severity: string; status: string; message: string; observations: Observation[]; }
interface ProvenanceItem { provenance_id: string; object_type: string; object_id: string; label: string; status: string; confidence: number; source_references: Array<{ filename: string; page: number; text_span?: string | null; bounding_box?: any; file_hash_sha256: string }>; derived_from: string[]; explanation: string; }

export const EvidenceReviewView: React.FC = () => {
  const { activeCaseId, documents, setActiveDocIndex, setViewMode } = useCaseStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<any>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(activeCaseId)}/evidence-review`, { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.detail || "Unable to load evidence review.");
      setReport(body);
      setSelectedId((current) => current || body?.provenance?.items?.[0]?.provenance_id || null);
    } catch (e: any) { setError(e?.message || "Unable to load evidence review."); }
    finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, [activeCaseId]);

  const contradictions: Contradiction[] = report?.contradictions?.items || [];
  const provenance: ProvenanceItem[] = useMemo(() => (report?.provenance?.items || []).filter((item: ProvenanceItem) => ["FIELD", "ENTITY", "EVENT", "RELATIONSHIP", "FINDING"].includes(item.object_type)), [report]);
  const selected = provenance.find((item) => item.provenance_id === selectedId) || provenance[0] || null;
  const totalItems = report?.provenance?.summary?.total_items || provenance.length;

  const openSource = (filename: string) => {
    const index = documents.findIndex((doc) => doc.original_filename === filename);
    if (index >= 0) setActiveDocIndex(index);
    setViewMode("inspector");
  };

  return (
    <div className="sanket-review">
      <div className="sanket-review__toolbar"><div><span className="sanket-card__meta">Evidence review</span><strong>What is known, where it came from, and what conflicts.</strong></div><button type="button" className="sanket-button" onClick={() => void load()} disabled={loading} title="Re-run provenance and contradiction checks without re-running VLM extraction"><RefreshCw size={13} className={loading ? "sanket-spin" : ""} /> Recheck</button></div>
      {loading ? <div className="sanket-empty-state">Building the deterministic evidence review…</div> : error ? <div className="sanket-review__error">{error}</div> : (
        <div className="sanket-review__body">
          <div className="sanket-review__summary">
            <div className="sanket-card sanket-review-stat"><span>Provenance items</span><strong>{totalItems}</strong></div>
            <div className="sanket-card sanket-review-stat"><span>Field records</span><strong>{report?.provenance?.summary?.field_items || 0}</strong></div>
            <div className={`sanket-card sanket-review-stat ${contradictions.length ? "is-alert" : ""}`}><span>Conflicts</span><strong>{contradictions.length}</strong></div>
          </div>

          <div className="sanket-review__grid">
            <section className="sanket-card sanket-review__conflicts">
              <div className="sanket-card__header"><div><div className="sanket-card__meta">Review queue</div><div className="sanket-card__title">Contradictions</div></div><span className="sanket-pill sanket-pill--danger">{contradictions.length} open</span></div>
              <div className="sanket-review-list">
                {contradictions.length ? contradictions.map((item) => (
                  <div key={item.contradiction_id} className="sanket-conflict-card">
                    <div className="sanket-conflict-card__head"><div><strong>{item.type.replaceAll("_", " ")}</strong><span>{item.severity} · {item.status}</span></div><AlertTriangle size={15} color="var(--amber)" /></div>
                    <p>{item.message}</p>
                    <div className="sanket-observation-list">
                      {item.observations.map((obs, index) => <button key={`${item.contradiction_id}-${index}`} type="button" className="sanket-observation" onClick={() => openSource(obs.filename)} title={`Open ${obs.filename} at the cited observation`}><span><strong>{obs.filename}</strong><small>{obs.field_name}: {obs.value}</small></span><span className="sanket-observation__meta">{Math.round((obs.confidence || 0) * 100)}% <ArrowRight size={11} /></span></button>)}
                    </div>
                  </div>
                )) : <div className="sanket-review-empty"><CheckCircle2 size={17} color="var(--green)" /><div><strong>No cross-document conflicts detected.</strong><small>Document-level warnings remain available in the inspector.</small></div></div>}
              </div>
            </section>

            <section className="sanket-card sanket-review__provenance">
              <div className="sanket-card__header"><div><div className="sanket-card__meta">Case memory</div><div className="sanket-card__title">Traceable objects</div></div><Fingerprint size={16} color="var(--teal)" /></div>
              <div className="sanket-review__provenance-body">
                <div className="sanket-review__object-list">{provenance.map((item) => <button key={item.provenance_id} type="button" className={`sanket-object-row ${selected?.provenance_id === item.provenance_id ? "is-active" : ""}`} onClick={() => setSelectedId(item.provenance_id)} title="Inspect this provenance record"><span><strong>{item.label}</strong><small>{item.object_type.replaceAll("_", " ")}</small></span><span>{Math.round((item.confidence || 0) * 100)}%</span></button>)}</div>
                <div className="sanket-review__detail">
                  {selected ? <>
                    <div className="sanket-review__detail-head"><div><span className="sanket-card__meta">Provenance record</span><h3>{selected.label}</h3><small>{selected.object_type} · {selected.object_id}</small></div><span className={`sanket-pill ${selected.status.includes("REVIEW") || selected.status === "CONFLICT" ? "sanket-pill--warn" : "sanket-pill--ok"}`}>{selected.status}</span></div>
                    <div className="sanket-review__info-grid"><div><span>Confidence</span><strong>{Math.round((selected.confidence || 0) * 100)}%</strong></div><div><span>Derived from</span><strong>{selected.derived_from.length ? selected.derived_from.join(", ") : "Direct observation"}</strong></div></div>
                    <div className="sanket-review__explanation"><span>Why this exists</span><p>{selected.explanation}</p></div>
                    <div className="sanket-review__sources"><span>Source references</span>{selected.source_references.length ? selected.source_references.map((ref, index) => <button key={index} type="button" onClick={() => openSource(ref.filename)} className="sanket-source-card" title={`Open ${ref.filename} at the cited source`}><div><strong>{ref.filename}</strong><small>Page {ref.page} · SHA-256 {ref.file_hash_sha256.slice(0, 18)}…</small>{ref.bounding_box && <small>BBOX {ref.bounding_box.x}, {ref.bounding_box.y}, {ref.bounding_box.w}, {ref.bounding_box.h}</small>}</div><ArrowRight size={13} /></button>) : <small className="sanket-review-muted">No direct source reference is attached.</small>}</div>
                  </> : <div className="sanket-review-empty">Select an object to inspect its lineage.</div>}
                </div>
              </div>
            </section>
          </div>
        </div>
      )}
    </div>
  );
};
