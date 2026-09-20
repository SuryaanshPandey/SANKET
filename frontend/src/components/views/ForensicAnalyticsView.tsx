"use client";

import React, { useMemo } from "react";
import { AlertTriangle, BarChart3, CheckCircle2, FileSearch, Network, ShieldAlert, Timer } from "lucide-react";
import { useCaseStore } from "@/store/useCaseStore";

function percent(value: number) { return `${Math.max(0, Math.min(100, Math.round(value * 100)))}%`; }
function normalizeRole(value: string) { return value.replaceAll("_", " ").trim() || "unclassified"; }

export const ForensicAnalyticsView: React.FC = () => {
  const { documents, crossDocIntelligence, setViewMode } = useCaseStore();
  const c = crossDocIntelligence;

  const fields = useMemo(() => documents.flatMap((doc) => doc.field_items || []), [documents]);
  const averageConfidence = documents.length ? documents.reduce((sum, doc) => sum + (doc.overall_confidence || 0), 0) / documents.length : 0;
  const lowConfidenceFields = fields.filter((field) => (field.confidence || 0) < 0.85).length;
  const roleCounts = useMemo(() => {
    const counts = new Map<string, number>();
    c?.reconciled_entities.forEach((entity) => entity.roles.forEach((role) => counts.set(normalizeRole(role), (counts.get(normalizeRole(role)) || 0) + 1)));
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  }, [c]);
  const docActivity = useMemo(() => documents.map((doc) => ({ name: doc.original_filename, fields: doc.field_items?.length || 0, confidence: Math.round((doc.overall_confidence || 0) * 100), flags: doc.validation_flags?.length || 0 })), [documents]);
  const maxFields = Math.max(1, ...docActivity.map((item) => item.fields));

  if (!c) return <div className="sanket-empty-state">Analytics become available after the case is ingested.</div>;

  return (
    <div className="sanket-analytics">
      <div className="sanket-analytics__intro">
        <div>
          <span className="sanket-eyebrow">REVIEW</span>
          <h3>Quality & analytical signals</h3>
          <p>Use this page to understand the shape and quality of the current case memory. Analytical signals are leads and validation evidence, not legal conclusions.</p>
        </div>
        <div className="sanket-analytics__actions">
          <button className="sanket-button" type="button" onClick={() => setViewMode("evidence")} title="Open provenance and contradiction review"><FileSearch size={14} /> Evidence review</button>
          <button className="sanket-button" type="button" onClick={() => setViewMode("investigation")} title="Open the investigation workflow"><Network size={14} /> Investigation</button>
        </div>
      </div>

      <div className="sanket-summary-grid">
        <div className="sanket-card sanket-summary-card"><span>Average confidence</span><strong>{percent(averageConfidence)}</strong><small>Across ingested documents</small></div>
        <div className="sanket-card sanket-summary-card"><span>Structured fields</span><strong>{fields.length}</strong><small>Extracted and persisted</small></div>
        <div className="sanket-card sanket-summary-card"><span>Low-confidence fields</span><strong>{lowConfidenceFields}</strong><small>Below 85% review threshold</small></div>
        <div className={`sanket-card sanket-summary-card ${c.discrepancies.length ? "sanket-summary-card--alert" : ""}`}><span>Conflicts</span><strong>{c.discrepancies.length}</strong><small>Cross-document observations</small></div>
      </div>

      <div className="sanket-analytics__grid">
        <section className="sanket-card">
          <div className="sanket-card__header"><div><div className="sanket-card__meta">Document quality</div><div className="sanket-card__title">Extraction coverage</div></div><BarChart3 size={16} color="var(--teal)" /></div>
          <div className="sanket-quality-list">
            {docActivity.map((doc) => (
              <div className="sanket-quality-row" key={doc.name}>
                <div className="sanket-quality-row__label"><strong>{doc.name}</strong><span>{doc.fields} fields · {doc.flags} flag{doc.flags === 1 ? "" : "s"}</span></div>
                <div className="sanket-quality-row__bar"><span style={{ width: `${Math.max(4, (doc.fields / maxFields) * 100)}%` }} /></div>
                <strong className={doc.confidence < 85 ? "is-warn" : ""}>{doc.confidence}%</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="sanket-card">
          <div className="sanket-card__header"><div><div className="sanket-card__meta">Entity memory</div><div className="sanket-card__title">Observed role mix</div></div><Network size={16} color="var(--teal)" /></div>
          <div className="sanket-role-list">
            {roleCounts.length ? roleCounts.map(([role, count]) => <div className="sanket-role-row" key={role}><span>{role}</span><strong>{count}</strong></div>) : <div className="sanket-summary-copy">No role distribution is available.</div>}
          </div>
        </section>

        <section className="sanket-card">
          <div className="sanket-card__header"><div><div className="sanket-card__meta">Temporal shape</div><div className="sanket-card__title">Events by source document</div></div><Timer size={16} color="var(--amber)" /></div>
          <div className="sanket-role-list">
            {Object.entries(c.master_timeline.reduce<Record<string, number>>((acc, event) => { acc[event.filename] = (acc[event.filename] || 0) + 1; return acc; }, {})).map(([filename, count]) => <div className="sanket-role-row" key={filename}><span>{filename}</span><strong>{count}</strong></div>)}
            {!c.master_timeline.length && <div className="sanket-summary-copy">No timeline events are available.</div>}
          </div>
        </section>

        <section className="sanket-card">
          <div className="sanket-card__header"><div><div className="sanket-card__meta">Review queue</div><div className="sanket-card__title">Quality gates and conflicts</div></div><ShieldAlert size={16} color={c.discrepancies.length ? "var(--red)" : "var(--green)"} /></div>
          <div className="sanket-review-list">
            {c.discrepancies.map((item, index) => <button key={`${item.flag_type}-${index}`} type="button" className="sanket-review-row" onClick={() => setViewMode("evidence")} title="Open the selected quality issue in Evidence Review"><AlertTriangle size={14} color="var(--red)" /><span><strong>{item.flag_type.replaceAll("_", " ")}</strong><small>{item.message}</small></span><span className="sanket-pill sanket-pill--danger">{item.severity}</span></button>)}
            {!c.discrepancies.length && <div className="sanket-review-row is-static"><CheckCircle2 size={14} color="var(--green)" /><span><strong>No cross-document conflicts</strong><small>Document-level flags can still be reviewed in the inspector.</small></span></div>}
          </div>
        </section>
      </div>
    </div>
  );
};
