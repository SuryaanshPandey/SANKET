"use client";

import React from "react";
import { AlertTriangle, ArrowRight, CalendarDays, CircleCheck, FileText, Link2, MapPin, Package, UserRound } from "lucide-react";
import { useCaseStore, ReconciledEntity } from "@/store/useCaseStore";

function shortDate(value: string) {
  if (!value) return "—";
  const match = value.match(/(\d{4}-\d{2}-\d{2})/);
  return match?.[1] || value.split(" ")[0];
}

function roleLabel(roles: string[]) {
  if (!roles.length) return "Observed person";
  return roles.slice(0, 2).map((role) => role.replaceAll("_", " ")).join(" · ");
}

const EntityButton: React.FC<{ entity: ReconciledEntity; onOpen: () => void }> = ({ entity, onOpen }) => {
  const initials = entity.canonical_name.split(/\s+/).slice(0, 2).map((v) => v[0]).join("").toUpperCase() || "?";
  return (
    <button className="sanket-entity-row" onClick={onOpen} type="button">
      <span className="sanket-entity-row__avatar">{initials}</span>
      <span>
        <strong>{entity.canonical_name}</strong>
        <small>{roleLabel(entity.roles)}</small>
      </span>
      <span className="sanket-entity-row__count">{entity.document_count} doc{entity.document_count === 1 ? "" : "s"}</span>
    </button>
  );
};

export const ExecutiveDossierView: React.FC = () => {
  const { crossDocIntelligence, documents, setSelectedEntity, setViewMode } = useCaseStore();

  if (!crossDocIntelligence || !documents.length) {
    return <div className="sanket-empty-state">No case memory is available yet.</div>;
  }

  const {
    total_documents = documents.length,
    overall_case_confidence = 0,
    reconciled_entities = [],
    master_timeline = [],
    cross_references = [],
    financial_ledger = { total_amount: 0, currency: "INR", item_count: 0, items: [] },
    discrepancies = [],
    case_summary = "",
  } = crossDocIntelligence;

  const unresolved = documents.reduce((sum, doc) => sum + (doc.validation_flags?.length || 0), 0);
  const topEntities = [...reconciled_entities].sort((a, b) => (b.document_count - a.document_count) || a.canonical_name.localeCompare(b.canonical_name)).slice(0, 8);
  const timeline = [...master_timeline].slice(0, 8);

  const openNetwork = () => setViewMode("network");
  const openReview = () => setViewMode("evidence");
  const openLedger = () => setViewMode("table");

  return (
    <div className="sanket-overview">
      <section className="sanket-overview__intro">
        <div>
          <span className="sanket-eyebrow">CASE MEMORY</span>
          <h3>Everything important, kept together.</h3>
          <p>SANKET turns the source documents into a connected case record. Start from the summary, move through the network, then return to the evidence whenever something needs to be verified.</p>
        </div>
        <div className="sanket-overview__quick-actions">
          <button className="sanket-button" type="button" onClick={openNetwork} title="Open the connected entity network"><Link2 size={14} /> Explore network</button>
          <button className="sanket-button sanket-button--primary" type="button" onClick={() => setViewMode("investigation")} title="Open the investigation workflow and run analysis"><ArrowRight size={14} /> Start investigation</button>
        </div>
      </section>

      <div className="sanket-summary-grid">
        <div className="sanket-card sanket-summary-card"><span>Source documents</span><strong>{total_documents}</strong><small>In the current case</small></div>
        <div className="sanket-card sanket-summary-card"><span>Entities remembered</span><strong>{reconciled_entities.length}</strong><small>Resolved or observed</small></div>
        <div className="sanket-card sanket-summary-card"><span>Timeline events</span><strong>{master_timeline.length}</strong><small>Chronologically ordered</small></div>
        <div className={`sanket-card sanket-summary-card ${discrepancies.length ? "sanket-summary-card--alert" : ""}`}><span>Needs review</span><strong>{discrepancies.length + unresolved}</strong><small>{discrepancies.length ? `${discrepancies.length} cross-document conflict(s)` : "No cross-document conflicts"}</small></div>
      </div>

      <div className="sanket-overview__grid">
        <div className="sanket-overview__stack">
          <section className="sanket-card">
            <div className="sanket-card__header">
              <div><div className="sanket-card__meta">Synthesis</div><div className="sanket-card__title">Case summary</div></div>
              <span className="sanket-pill">Avg confidence {Math.round((overall_case_confidence || 0) * 100)}%</span>
            </div>
            <div className="sanket-summary-copy">{case_summary || "No consolidated case summary is available yet."}</div>
          </section>

          <section className="sanket-card">
            <div className="sanket-card__header">
              <div><div className="sanket-card__meta">Attention</div><div className="sanket-card__title">What needs a closer look</div></div>
              <button className="sanket-link" type="button" onClick={openReview} title="Open contradictions and provenance review">Open review <ArrowRight size={12} style={{ verticalAlign: "-2px" }} /></button>
            </div>
            <div className="sanket-attention-list">
              {discrepancies.length ? discrepancies.map((item, index) => (
                <button key={`${item.flag_type}-${index}`} type="button" className="sanket-attention-item sanket-attention-item--button" onClick={openReview} title="Review the evidence behind this flagged item">
                  <AlertTriangle size={15} color="var(--red)" />
                  <span><strong>{item.flag_type.replaceAll("_", " ")}</strong><small>{item.message}</small></span>
                </button>
              )) : (
                <div className="sanket-attention-item"><CircleCheck size={15} color="var(--green)" /><span><strong>No cross-document contradiction detected</strong><small>Quality flags may still exist inside individual documents.</small></span></div>
              )}
              {unresolved > 0 && <div className="sanket-attention-item"><FileText size={15} color="var(--amber)" /><span><strong>{unresolved} document quality flag{unresolved === 1 ? "" : "s"}</strong><small>Open Evidence Review or Document Inspector for the underlying source.</small></span></div>}
            </div>
          </section>

          <section className="sanket-card">
            <div className="sanket-card__header">
              <div><div className="sanket-card__meta">Evidence map</div><div className="sanket-card__title">Cross-referenced identifiers</div></div>
              <button className="sanket-link" type="button" onClick={openLedger} title="Open the full evidence ledger">Open ledger <ArrowRight size={12} style={{ verticalAlign: "-2px" }} /></button>
            </div>
            <div className="sanket-mini-grid">
              {cross_references.slice(0, 8).map((item, index) => (
                <div key={`${item.identifier_type}-${index}`} className="sanket-mini-item">
                  <span>{item.identifier_type}</span>
                  <strong>{item.value || "—"}</strong>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="sanket-overview__stack">
          <section className="sanket-card">
            <div className="sanket-card__header">
              <div><div className="sanket-card__meta">People & roles</div><div className="sanket-card__title">Remembered entities</div></div>
              <span className="sanket-pill">{reconciled_entities.length}</span>
            </div>
            <div className="sanket-entity-list">
              {topEntities.map((entity, index) => (
                <EntityButton key={`${entity.canonical_name}-${index}`} entity={entity} onOpen={() => { setSelectedEntity(entity); setViewMode("network"); }} />
              ))}
            </div>
          </section>

          <section className="sanket-card">
            <div className="sanket-card__header">
              <div><div className="sanket-card__meta">Chronology</div><div className="sanket-card__title">Master timeline</div></div>
              <span className="sanket-pill">{master_timeline.length} events</span>
            </div>
            <div className="sanket-timeline">
              {timeline.length ? timeline.map((event, index) => (
                <div className="sanket-timeline__item" key={`${event.document_id}-${event.label}-${index}`}>
                  <span className="sanket-timeline__date">{shortDate(event.normalized_date || event.raw_date)}</span>
                  <span className="sanket-timeline__dot" />
                  <span className="sanket-timeline__body"><strong>{event.label}</strong><small>{event.detail || event.filename}</small></span>
                </div>
              )) : <div className="sanket-summary-copy">No timeline events are available.</div>}
            </div>
          </section>

          <section className="sanket-card">
            <div className="sanket-card__header"><div><div className="sanket-card__meta">Assets</div><div className="sanket-card__title">Seized property</div></div><span className="sanket-pill">{financial_ledger.item_count || financial_ledger.items.length} items</span></div>
            <div className="sanket-asset-list">
              {financial_ledger.items.map((item, index) => <div className="sanket-asset-row" key={`${item.label}-${index}`}><div><span>{item.label}</span><small>{item.source_doc}</small></div><strong>{item.currency || financial_ledger.currency} {item.value.toLocaleString()}</strong></div>)}
              {!financial_ledger.items.length && <div className="sanket-summary-copy">No itemized property is recorded.</div>}
              {financial_ledger.items.length > 0 && <div className="sanket-asset-row"><div><span>Total stated value</span><small>From the current evidence ledger</small></div><strong>{financial_ledger.currency} {financial_ledger.total_amount.toLocaleString()}</strong></div>}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
