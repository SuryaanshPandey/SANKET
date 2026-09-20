"use client";

import React, { useEffect, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { ClassificationHeader } from "@/components/layout/ClassificationHeader";
import { NavigationDock } from "@/components/layout/NavigationDock";
import { DocumentCarousel } from "@/components/layout/DocumentCarousel";
import { TacticalProgressHUD } from "@/components/layout/TacticalProgressHUD";
import { ExecutiveDossierView } from "@/components/views/ExecutiveDossierView";
import { NetworkGraphView } from "@/components/views/NetworkGraphView";
import { InvestigationCanvasView } from "@/components/views/InvestigationCanvasView";
import { GeospatialMapView } from "@/components/views/GeospatialMapView";
import { EvidenceDataTableView } from "@/components/views/EvidenceDataTableView";
import { DocumentInspectorView } from "@/components/views/DocumentInspectorView";
import { ForensicAnalyticsView } from "@/components/views/ForensicAnalyticsView";
import { EvidenceReviewView } from "@/components/views/EvidenceReviewView";
import { useCaseStore, ViewMode } from "@/store/useCaseStore";

const VIEW_META: Record<ViewMode, { eyebrow: string; title: string; description: string }> = {
  dossier: { eyebrow: "CASE MEMORY", title: "Overview", description: "A compact memory of what the case contains, what changed, and what needs attention." },
  network: { eyebrow: "EXPLORE", title: "Entity network", description: "See people, evidence and relationships as one connected case model." },
  investigation: { eyebrow: "INVESTIGATE", title: "Investigation workflow", description: "Build a transparent sequence of analytical steps and run it against the case." },
  geospatial: { eyebrow: "EXPLORE", title: "Locations", description: "Review places referenced by the case and jump from a site back to its evidence." },
  table: { eyebrow: "EVIDENCE", title: "Evidence ledger", description: "Inspect every structured field and open its source evidence." },
  inspector: { eyebrow: "EVIDENCE", title: "Document inspector", description: "Compare the source document with the fields extracted from it." },
  analytics: { eyebrow: "REVIEW", title: "Quality & analytics", description: "Review network, timeline, confidence and evidence-quality signals without losing source context." },
  evidence: { eyebrow: "REVIEW", title: "Evidence review", description: "Trace observations to sources and surface contradictions before drawing conclusions." },
};

export default function SanketWorkbenchPage() {
  const { viewMode, documents, status, processUploadedFiles, loadCatalog, restoreActiveCase, loadSampleCaseBundle } = useCaseStore();
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void loadCatalog();
    void restoreActiveCase();
  }, [loadCatalog, restoreActiveCase]);

  const meta = VIEW_META[viewMode];

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(false);
    if (event.dataTransfer.files?.length) {
      void processUploadedFiles(Array.from(event.dataTransfer.files));
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    if (event.currentTarget === event.target) setIsDragOver(false);
  };

  const renderView = () => {
    switch (viewMode) {
      case "network": return <NetworkGraphView />;
      case "investigation": return <InvestigationCanvasView />;
      case "geospatial": return <GeospatialMapView />;
      case "table": return <EvidenceDataTableView />;
      case "inspector": return <DocumentInspectorView />;
      case "analytics": return <ForensicAnalyticsView />;
      case "evidence": return <EvidenceReviewView />;
      default: return <ExecutiveDossierView />;
    }
  };

  return (
    <div className="sanket-app" onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
      <ClassificationHeader fileInputRef={fileInputRef} />

      <div className="sanket-layout">
        <NavigationDock />

        <div className="sanket-workspace">
          <DocumentCarousel />

          <div className="sanket-page-header">
            <div>
              <span className="sanket-eyebrow">{meta.eyebrow}</span>
              <h2>{meta.title}</h2>
              <p>{meta.description}</p>
            </div>
            <div className="sanket-page-header__state">
              <span className={`sanket-state-dot sanket-state-dot--${status}`} />
              <span>{documents.length ? `${documents.length} documents in case` : "No evidence loaded"}</span>
            </div>
          </div>

          <main className="sanket-view-shell">
            {documents.length === 0 ? (
              <section className="sanket-empty-case" aria-label="Start an investigation">
                <div className="sanket-empty-case__copy">
                  <span className="sanket-eyebrow">CASE SETUP</span>
                  <h3>Build the case memory</h3>
                  <p>Load the prepared case or bring in your own scanned evidence. SANKET will keep the source document, extracted facts, relationships and review state together.</p>
                </div>
                <div className="sanket-empty-case__actions">
                  <button type="button" className="sanket-button sanket-button--primary" onClick={() => void loadSampleCaseBundle()}>
                    Load sample case
                  </button>
                  <button type="button" className="sanket-button" onClick={() => fileInputRef.current?.click()}>
                    <Upload size={15} /> Ingest documents
                  </button>
                </div>
              </section>
            ) : renderView()}
          </main>

          <footer className="sanket-footer">
            <span>Case evidence is source-linked. Review flags remain visible until resolved.</span>
            <span>{status === "loading" ? "Processing evidence…" : "SANKET · Evidence intelligence workspace"}</span>
          </footer>
        </div>
      </div>

      <TacticalProgressHUD />

      {isDragOver && (
        <div className="sanket-dropzone" aria-live="polite">
          <div className="sanket-dropzone__icon"><Upload size={22} /></div>
          <strong>Release to ingest evidence</strong>
          <span>Images and scanned documents · multi-document supported</span>
        </div>
      )}
    </div>
  );
}
