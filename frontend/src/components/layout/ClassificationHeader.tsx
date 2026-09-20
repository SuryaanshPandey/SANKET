"use client";

import React from "react";
import { ChevronDown, FolderOpen, LoaderCircle, Upload } from "lucide-react";
import { SanketEmblem } from "@/components/brand/SanketEmblem";
import { useCaseStore } from "@/store/useCaseStore";

interface Props {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
}

export const ClassificationHeader: React.FC<Props> = ({ fileInputRef }) => {
  const {
    activeCaseId,
    caseTitle,
    status,
    documents,
    loadDiverseDataset,
    processUploadedFiles,
    availableDatasets,
    selectedDatasetKey,
  } = useCaseStore();

  const isLoading = status === "loading";

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.length) {
      void processUploadedFiles(Array.from(event.target.files));
      event.target.value = "";
    }
  };

  return (
    <header className="sanket-topbar">
      <div className="sanket-topbar__brand">
        <div className="sanket-brand-mark"><SanketEmblem size={34} /></div>
        <div className="sanket-brand-copy">
          <div className="sanket-brand-row">
            <h1>SANKET</h1>
            <span className="sanket-version">v2.0</span>
          </div>
          <p>Evidence Intelligence &amp; Reconciliation</p>
        </div>
      </div>

      <div className="sanket-casebar">
        <span className="sanket-eyebrow">ACTIVE CASE</span>
        <strong>{activeCaseId}</strong>
        <small title={caseTitle}>{caseTitle}</small>
      </div>

      <div className="sanket-topbar__status">
        <span className={`sanket-state-dot sanket-state-dot--${status}`} />
        <span>{status === "loading" ? "Processing evidence" : documents.length ? `${documents.length} documents loaded` : "Ready"}</span>
        {isLoading && <LoaderCircle className="sanket-status-spinner" size={14} />}
      </div>

      <div className="sanket-topbar__actions">
        <label className="sanket-case-select" title="Load a prepared case or benchmark dataset">
          <FolderOpen size={14} />
          <select
            value={selectedDatasetKey}
            onChange={(event) => void loadDiverseDataset(event.target.value)}
            disabled={isLoading}
            aria-label="Load prepared case"
          >
            {availableDatasets.map((dataset) => (
              <option key={dataset.key} value={dataset.key}>Load {dataset.name} · {dataset.count}</option>
            ))}
          </select>
          <ChevronDown size={13} />
        </label>

        <button
          className="sanket-button sanket-button--primary sanket-button--ingest"
          title="Add one or more case documents and start ingestion"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          <Upload size={15} />
          <span>Ingest evidence</span>
        </button>
        <input ref={fileInputRef} type="file" accept="image/*" multiple onChange={handleFileChange} className="hidden" />
      </div>

      <div className="sanket-topbar__proof">
        <span className="sanket-proof-mark" />
        <span>Local inference</span>
        <span>Source-linked case memory</span>
      </div>
    </header>
  );
};
