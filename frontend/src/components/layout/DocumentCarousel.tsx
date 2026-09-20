"use client";

import React from "react";
import { AlertCircle, ArrowUpRight, Check, FileText } from "lucide-react";
import { useCaseStore } from "@/store/useCaseStore";

export const DocumentCarousel: React.FC = () => {
  const { documents, activeDocIndex, setActiveDocIndex, setViewMode } = useCaseStore();
  if (!documents.length) return null;

  return (
    <section className="sanket-evidence-strip" aria-label="Case evidence">
      <div className="sanket-evidence-strip__label">
        <FileText size={14} />
        <div>
          <strong>CASE EVIDENCE</strong>
          <span>{documents.length} source documents</span>
        </div>
      </div>

      <div className="sanket-evidence-strip__items">
        {documents.map((doc, index) => {
          const active = index === activeDocIndex;
          const confidence = Math.round((doc.overall_confidence || 0) * 100);
          const flags = doc.validation_flags?.length || 0;
          const type = (doc.doc_type || "document").replaceAll("_", " ");
          return (
            <button
              key={doc.document_id || index}
              type="button"
              className={`sanket-doc-chip ${active ? "is-active" : ""}`}
              onClick={() => setActiveDocIndex(index)}
              title={`Select ${doc.original_filename} as active case evidence`}
            >
              <span className="sanket-doc-chip__number">{String(index + 1).padStart(2, "0")}</span>
              <span className="sanket-doc-chip__body">
                <strong>{doc.original_filename}</strong>
                <small>{type}</small>
              </span>
              <span className={`sanket-doc-chip__confidence ${confidence < 85 ? "is-low" : ""}`}>{confidence}%</span>
              {flags > 0 ? <span className="sanket-doc-chip__flag"><AlertCircle size={11} />{flags}</span> : <Check size={12} className="sanket-doc-chip__ok" />}
              <span
                className="sanket-doc-chip__inspect"
                role="button"
                tabIndex={0}
                aria-label={`Inspect ${doc.original_filename}`}
                title={`Open ${doc.original_filename} in Document Inspector`}
                onClick={(event) => {
                  event.stopPropagation();
                  setActiveDocIndex(index);
                  setViewMode("inspector");
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    event.stopPropagation();
                    setActiveDocIndex(index);
                    setViewMode("inspector");
                  }
                }}
              >
                <ArrowUpRight size={11} />
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
};
