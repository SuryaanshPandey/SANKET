"use client";

import React from "react";
import { Check, Clock3, Cpu, LoaderCircle } from "lucide-react";
import { useCaseStore } from "@/store/useCaseStore";

const STAGE_ORDER = [
  { key: "ingestion", label: "Ingestion & hashing" },
  { key: "preprocessing", label: "Image preprocessing" },
  { key: "classification", label: "Document classification" },
  { key: "extraction", label: "Multimodal extraction" },
  { key: "validation", label: "Validation & persistence" },
  { key: "persisting", label: "Evidence persistence" },
  { key: "reconciliation", label: "Cross-document reconciliation" },
];

function normalizeStage(stage: string) {
  const value = stage.toLowerCase();
  const index = STAGE_ORDER.findIndex((item) => value.includes(item.key));
  return index >= 0 ? index : 0;
}

export const TacticalProgressHUD: React.FC = () => {
  const { status, progressPercentage, timeElapsedSeconds, currentStageName, currentStageDetail, totalDocumentsInBatch, batchId } = useCaseStore();
  if (status !== "loading") return null;

  const activeIndex = normalizeStage(currentStageName);
  const percent = Math.max(0, Math.min(99, progressPercentage || 0));
  const hasConfirmedProgress = percent > 0;

  return (
    <div className="sanket-progress-overlay" aria-live="polite">
      <section className="sanket-progress-card">
        <div className="sanket-progress-card__header">
          <div>
            <span className="sanket-eyebrow">INGESTION · {totalDocumentsInBatch} DOCUMENTS</span>
            <h2>{currentStageName}</h2>
            <p>{currentStageDetail}</p>
          </div>
          <LoaderCircle className="sanket-progress-spin" size={20} />
        </div>

        <div className="sanket-progress-track" aria-label={`Confirmed ingestion progress ${percent}%`}>
          <div className={`sanket-progress-fill ${hasConfirmedProgress ? "has-progress" : ""}`} style={{ width: `${percent}%` }} />
          {!hasConfirmedProgress && <div className="sanket-progress-indeterminate" />}
        </div>

        <div className="sanket-progress-summary">
          <strong>{percent}%</strong>
          <span>{percent >= 99 ? "Finalizing. Waiting for backend completion." : "Confirmed backend progress"}</span>
        </div>

        <div className="sanket-progress-meta">
          <div><Clock3 size={14} /><span>Elapsed</span><strong>{timeElapsedSeconds}s</strong></div>
          <div><Cpu size={14} /><span>Inference</span><strong>Qwen2.5-VL 3B</strong></div>
          <div><span>Job</span><strong>{batchId ? batchId.slice(0, 8) : "queued"}</strong></div>
        </div>

        <div className="sanket-progress-steps">
          {STAGE_ORDER.map((stage, index) => (
            <div key={stage.key} className={`sanket-progress-step ${index < activeIndex ? "done" : index === activeIndex ? "current" : ""}`}>
              <span className="sanket-progress-step__mark">{index < activeIndex ? <Check size={11} /> : index + 1}</span>
              <span>{stage.label}</span>
              <small>{index < activeIndex ? "Done" : index === activeIndex ? "Running" : "Queued"}</small>
            </div>
          ))}
        </div>

        <p className="sanket-progress-hint">The numeric bar never advances because of elapsed time. It moves only when the backend confirms progress and reaches completion only after the ingestion job finishes.</p>
      </section>
    </div>
  );
};
