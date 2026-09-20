"use client";

import React from "react";
import { Activity, FileCheck2, FileSearch, FileText, GitBranch, MapPin, Network, Workflow } from "lucide-react";
import { useCaseStore, ViewMode } from "@/store/useCaseStore";

interface NavItem {
  id: ViewMode;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  badge?: string;
}

export const NavigationDock: React.FC = () => {
  const { viewMode, setViewMode, crossDocIntelligence, documents } = useCaseStore();

  const groups: Array<{ title: string; items: NavItem[] }> = [
    { title: "Case", items: [{ id: "dossier", label: "Overview", icon: FileText, badge: documents.length ? String(documents.length) : undefined }] },
    {
      title: "Explore",
      items: [
        { id: "network", label: "Entity network", icon: Network, badge: crossDocIntelligence ? String(crossDocIntelligence.reconciled_entities.length) : undefined },
        { id: "geospatial", label: "Locations", icon: MapPin },
      ],
    },
    { title: "Investigate", items: [{ id: "investigation", label: "Workflow", icon: Workflow }] },
    {
      title: "Evidence",
      items: [
        { id: "table", label: "Ledger", icon: FileCheck2, badge: documents.length ? "FIELDS" : undefined },
        { id: "inspector", label: "Documents", icon: FileSearch, badge: documents.length ? String(documents.length) : undefined },
      ],
    },
    {
      title: "Review",
      items: [
        { id: "evidence", label: "Evidence review", icon: GitBranch, badge: crossDocIntelligence ? String(crossDocIntelligence.discrepancies.length) : undefined },
        { id: "analytics", label: "Quality & analytics", icon: Activity },
      ],
    },
  ];

  return (
    <aside className="sanket-sidebar" aria-label="Case navigation">
      <div className="sanket-sidebar__intro">
        <span>WORKSPACE</span>
        <strong>Case memory</strong>
        <small>Explore → investigate → verify</small>
      </div>

      <div className="sanket-sidebar__nav">
        {groups.map((group) => (
          <section key={group.title} className="sanket-nav-group">
            <div className="sanket-nav-group__title">{group.title}</div>
            <div className="sanket-nav-group__items">
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = viewMode === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`sanket-nav-item ${active ? "is-active" : ""}`}
                    onClick={() => setViewMode(item.id)}
                    title={`Open ${item.label} — ${({ dossier: "case memory overview", network: "connected entities and relationships", geospatial: "case locations on a map", investigation: "compose and run an investigation", table: "all extracted evidence fields", inspector: "inspect source documents and fields", evidence: "review provenance and contradictions", analytics: "review analytical and quality signals" } as Record<string, string>)[item.id]}`}
                  >
                    <span className="sanket-nav-item__icon"><Icon size={16} /></span>
                    <span className="sanket-nav-item__label">{item.label}</span>
                    {item.badge && <span className="sanket-nav-item__badge">{item.badge}</span>}
                  </button>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      <div className="sanket-sidebar__footer">
        <div className="sanket-sidebar__footer-line" />
        <span>Evidence first</span>
        <small>Every analytical result should be traceable to a source.</small>
      </div>
    </aside>
  );
};
