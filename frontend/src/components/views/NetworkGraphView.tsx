"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import cytoscape from "cytoscape";
import {
  ArrowRight,
  Eye,
  EyeOff,
  FileSearch,
  Maximize2,
  RefreshCw,
  Search,
  Share2,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useCaseStore, GraphContractEntity, GraphContractEvent } from "@/store/useCaseStore";

const COLORS = {
  person: "#5B5BC7",
  officer: "#2E7A95",
  witness: "#25845B",
  accused: "#B44A52",
  property: "#9A6808",
  location: "#277A70",
  account: "#7455A2",
  phone: "#526A7E",
  organization: "#3F748A",
  event: "#66737D",
  other: "#6E7982",
};

function getRoleColor(roles: string[] = []) {
  const normalized = roles.map((role) => role.toLowerCase());
  if (normalized.some((role) => ["accused", "arrestee", "suspect"].includes(role))) return COLORS.accused;
  if (normalized.some((role) => ["investigating_officer", "arresting_officer", "io", "sho", "officer"].includes(role))) return COLORS.officer;
  if (normalized.some((role) => ["panch_witness", "witness", "informant"].includes(role))) return COLORS.witness;
  return COLORS.person;
}

function getTypeColor(type: string) {
  const normalized = type.toLowerCase();
  if (normalized === "person") return COLORS.person;
  if (normalized === "location") return COLORS.location;
  if (normalized === "account") return COLORS.account;
  if (normalized === "phone") return COLORS.phone;
  if (normalized === "organization") return COLORS.organization;
  return COLORS.other;
}

function normalize(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function formatType(value: string) {
  return value.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

interface HoverInfo {
  left: number;
  top: number;
  title: string;
  meta: string;
  detail: string;
}

function buildNodeTooltip(data: any) {
  const kind = data.kind === "event" ? "Event" : formatType(data.type || "entity");
  const confidence = typeof data.confidence === "number" ? `${Math.round(data.confidence * 100)}% confidence` : "Confidence unavailable";
  const degree = typeof data.degree === "number" ? `${data.degree} connection${data.degree === 1 ? "" : "s"}` : "";
  if (data.kind === "document") {
    return {
      title: data.fullLabel || data.label || "Source document",
      meta: ["Source document", confidence, degree].filter(Boolean).join(" · "),
      detail: "Click to open this source in the document inspector.",
    };
  }
  const source = data.graphEntity?.source?.filename || data.graphEvent?.source?.filename || "Source linked in evidence";
  return {
    title: data.fullLabel || data.label || "Untitled",
    meta: [kind, confidence, degree].filter(Boolean).join(" · "),
    detail: `${source} · Click to inspect the case memory behind this node.`,
  };
}

export const NetworkGraphView: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const layoutRef = useRef<cytoscape.Layouts | null>(null);

  const {
    crossDocIntelligence,
    graphContract,
    documents,
    setSelectedEntity,
    setViewMode,
  } = useCaseStore();

  const [activeNodeData, setActiveNodeData] = useState<any>(null);
  const [layoutMode, setLayoutMode] = useState<"cose" | "concentric" | "breadthfirst">("cose");
  const [query, setQuery] = useState("");
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);

  const [showIsolates, setShowIsolates] = useState(false);

  const graphData = useMemo(() => {
    const contract = graphContract;
    const semanticTypes = new Set(["person", "phone", "account", "location", "organization", "vehicle", "weapon"]);

    if (contract && contract.entities.length) {
      const nodesById = new Map<string, cytoscape.ElementDefinition>();
      const displayIdByContractId = new Map<string, string>();
      const nodes: cytoscape.ElementDefinition[] = [];
      const edges: cytoscape.ElementDefinition[] = [];
      const documentNodeByFilename = new Map<string, string>();

      // Documents are first-class case-memory objects. Connecting observed entities
      // to their source documents gives the network a truthful evidence spine even
      // when the upstream contract contains only a small number of semantic RELs.
      documents.forEach((document, index) => {
        const filename = document.original_filename;
        const id = `document:${filename}`;
        documentNodeByFilename.set(filename, id);
        const node = {
          data: {
            id,
            label: filename,
            fullLabel: filename,
            kind: "document",
            type: "document",
            color: "#6E7982",
            confidence: document.overall_confidence,
            degree: 0,
            document,
          },
        };
        nodes.push(node);
        nodesById.set(id, node);
      });

      const addResolvedPerson = (entity: any, fallbackId: string, sourceEntity?: GraphContractEntity) => {
        const key = normalize(entity.canonical_name || sourceEntity?.normalized_name || sourceEntity?.name || fallbackId);
        const id = `person:${key || fallbackId}`;
        if (nodesById.has(id)) return id;
        const roles = entity.roles || (sourceEntity?.role ? [sourceEntity.role] : []);
        const source = sourceEntity?.source || null;
        const node = {
          data: {
            id,
            label: entity.canonical_name || sourceEntity?.name || fallbackId,
            fullLabel: entity.canonical_name || sourceEntity?.name || fallbackId,
            kind: "entity",
            type: "person",
            role: sourceEntity?.role || roles[0] || "observed",
            color: getRoleColor(roles),
            confidence: sourceEntity?.confidence ?? 1,
            graphEntity: sourceEntity || null,
            reconciledEntity: entity,
            degree: 0,
          },
        };
        nodes.push(node);
        nodesById.set(id, node);
        return id;
      };

      const reconciled = crossDocIntelligence?.reconciled_entities || [];
      const reconciledMatches = new Map<string, any>();
      reconciled.forEach((entity) => reconciledMatches.set(normalize(entity.canonical_name), entity));

      // Prefer investigator-facing reconciled people rather than rendering every
      // extracted date/hash/note as if it were a network entity.
      reconciled.forEach((entity) => addResolvedPerson(entity, entity.canonical_name));

      contract.entities.forEach((entity) => {
        const type = String(entity.type || "").toLowerCase();
        if (!semanticTypes.has(type)) return;
        const match = type === "person" ? reconciledMatches.get(normalize(entity.normalized_name || entity.name)) : null;
        if (match) {
          displayIdByContractId.set(entity.id, addResolvedPerson(match, entity.id, entity));
          return;
        }
        const id = entity.id;
        const node = {
          data: {
            id,
            label: entity.name,
            fullLabel: entity.name,
            kind: "entity",
            type,
            role: entity.role || "observed",
            color: type === "person" ? getRoleColor(entity.role ? [entity.role] : []) : getTypeColor(entity.type),
            confidence: entity.confidence,
            graphEntity: entity,
            reconciledEntity: null,
            degree: 0,
          },
        };
        nodes.push(node);
        nodesById.set(id, node);
        displayIdByContractId.set(entity.id, id);
      });

      // Add event nodes only when they participate in the actual graph contract.
      const eventIdsUsed = new Set<string>();
      contract.relationships.forEach((relationship) => {
        if (contract.events.some((event) => event.id === relationship.source_entity)) eventIdsUsed.add(relationship.source_entity);
        if (contract.events.some((event) => event.id === relationship.target_entity)) eventIdsUsed.add(relationship.target_entity);
      });
      contract.events.forEach((event) => {
        if (event.source_entity || event.target_entity || eventIdsUsed.has(event.id)) {
          const id = event.id;
          const node = {
            data: {
              id,
              label: event.title,
              fullLabel: event.title,
              kind: "event",
              type: "event",
              color: COLORS.event,
              confidence: 1,
              graphEvent: event,
              degree: 0,
            },
          };
          nodes.push(node);
          nodesById.set(id, node);
        }
      });

      const edgeKeys = new Set<string>();
      const addEdge = (sourceRaw: string | null | undefined, targetRaw: string | null | undefined, id: string, relationshipType: string, confidence: number, evidence?: string | null, contextual = false) => {
        if (!sourceRaw || !targetRaw) return;
        const source = nodesById.has(sourceRaw) ? sourceRaw : displayIdByContractId.get(sourceRaw);
        const target = nodesById.has(targetRaw) ? targetRaw : displayIdByContractId.get(targetRaw);
        if (!source || !target || source === target) return;
        const key = `${source}->${target}:${relationshipType}`;
        if (edgeKeys.has(key)) return;
        edgeKeys.add(key);
        edges.push({
          data: {
            id,
            source,
            target,
            fullLabel: formatType(relationshipType),
            label: "",
            confidence,
            color: contextual ? "#94A0A8" : (confidence < 0.7 ? "#9A6808" : "#70808A"),
            evidence: evidence || (contextual ? "Event endpoint recorded in the Graph Contract." : "Observed relationship in the Graph Contract."),
            contextual,
          },
        });
      };

      const addDocumentEvidenceEdge = (objectId: string | null | undefined, filename: string | null | undefined, confidence: number) => {
        if (!objectId || !filename) return;
        const documentId = documentNodeByFilename.get(filename);
        if (!documentId) return;
        addEdge(objectId, documentId, `${objectId}:evidence:${filename}`, "OBSERVED_IN", confidence, `Observed in ${filename}.`, true);
      };

      contract.relationships.forEach((relationship) => {
        addEdge(relationship.source_entity, relationship.target_entity, relationship.id, relationship.relationship_type, relationship.confidence, relationship.evidence);
      });

      // Event endpoint links are valid structural relationships and make the graph
      // readable even when the upstream contract contains few explicit REL records.
      contract.events.forEach((event) => {
        if (event.source_entity) addEdge(event.source_entity, event.id, `${event.id}:source`, `${event.type}_SOURCE`, 1, undefined, true);
        if (event.target_entity) addEdge(event.id, event.target_entity, `${event.id}:target`, `${event.type}_TARGET`, 1, undefined, true);
        if (nodesById.has(event.id)) addDocumentEvidenceEdge(event.id, event.source?.filename, 1);
      });

      // Preserve source lineage as a real, visible case-memory connection.
      nodes.forEach((node) => {
        const data = node.data as any;
        const sourceFilename = data.graphEntity?.source?.filename || data.graphEvent?.source?.filename;
        if (sourceFilename) addDocumentEvidenceEdge(String(data.id), sourceFilename, Number(data.confidence) || 1);
        if (data.reconciledEntity?.documents) {
          data.reconciledEntity.documents.forEach((filename: string) => addDocumentEvidenceEdge(String(data.id), filename, 1));
        }
      });

      // Keep unlinked, field-like extracted objects out of the relationship view.
      const connectedIds = new Set<string>();
      edges.forEach((edge) => {
        connectedIds.add(String(edge.data.source));
        connectedIds.add(String(edge.data.target));
      });
      nodes.forEach((node) => {
        node.data.degree = connectedIds.has(String(node.data.id))
          ? edges.reduce((count, edge) => count + (edge.data.source === node.data.id || edge.data.target === node.data.id ? 1 : 0), 0)
          : 0;
      });

      const filteredNodes = edges.length && !showIsolates ? nodes.filter((node) => (node.data.degree || 0) > 0) : nodes;
      const visibleIds = new Set(filteredNodes.map((node) => String(node.data.id)));
      const filteredEdges = edges.filter((edge) => visibleIds.has(String(edge.data.source)) && visibleIds.has(String(edge.data.target)));

      return {
        nodes: filteredNodes,
        edges: filteredEdges,
        totalNodes: nodes.length,
        connectedNodes: nodes.filter((node) => (node.data.degree || 0) > 0).length,
        isolatedNodes: nodes.filter((node) => (node.data.degree || 0) === 0).length,
        entityCount: nodes.filter((node) => node.data.kind === "entity").length,
        eventCount: nodes.filter((node) => node.data.kind === "event").length,
        source: "graph-contract" as const,
      };
    }

    if (!crossDocIntelligence) {
      return { nodes: [], edges: [], totalNodes: 0, connectedNodes: 0, isolatedNodes: 0, entityCount: 0, eventCount: 0, source: "fallback" as const };
    }

    const nodes: cytoscape.ElementDefinition[] = [];
    const edges: cytoscape.ElementDefinition[] = [];
    const caseId = "case-memory";
    nodes.push({
      data: {
        id: caseId,
        label: "CASE MEMORY",
        fullLabel: "CASE MEMORY",
        displayLabel: "CASE MEMORY",
        kind: "case",
        type: "case",
        color: "#0F766E",
        degree: (crossDocIntelligence.reconciled_entities || []).length,
      },
    });

    (crossDocIntelligence.reconciled_entities || []).forEach((entity, index) => {
      const isAccused = entity.roles.some((role) => ["accused", "arrestee", "suspect"].includes(role.toLowerCase()));
      const isOfficer = entity.roles.some((role) => ["investigating_officer", "arresting_officer", "io", "sho", "officer"].includes(role.toLowerCase()));
      const isWitness = entity.roles.some((role) => ["panch_witness", "witness", "informant"].includes(role.toLowerCase()));
      const nodeType = isAccused ? "accused" : isOfficer ? "officer" : isWitness ? "witness" : "person";
      const color = isAccused ? COLORS.accused : isOfficer ? COLORS.officer : isWitness ? COLORS.witness : COLORS.person;
      const id = `entity-${index}`;
      nodes.push({
        data: {
          id,
          label: entity.canonical_name,
          fullLabel: entity.canonical_name,
          displayLabel: entity.canonical_name,
          kind: "entity",
          type: nodeType,
          color,
          roles: entity.roles,
          degree: 1,
          reconciledEntity: entity,
        },
      });
      edges.push({ data: { id: `case-${id}`, source: id, target: caseId, label: "", fullLabel: "Case evidence", color: "#87929A", confidence: 1 } });
    });

    const visibleNodes = edges.length && !showIsolates ? nodes.filter((node) => node.data.kind === "case" || node.data.degree > 0) : nodes;
    const visibleIds = new Set(visibleNodes.map((node) => String(node.data.id)));
    const visibleEdges = edges.filter((edge) => visibleIds.has(String(edge.data.source)) && visibleIds.has(String(edge.data.target)));
    return {
      nodes: visibleNodes,
      edges: visibleEdges,
      totalNodes: nodes.length,
      connectedNodes: nodes.filter((node) => node.data.degree > 0).length,
      isolatedNodes: 0,
      entityCount: nodes.filter((node) => node.data.kind === "entity").length,
      eventCount: 0,
      source: "fallback" as const,
    };
  }, [crossDocIntelligence, graphContract, documents, showIsolates]);
  const renderLayout = () => {
    const cy = cyRef.current;
    if (!cy || cy.destroyed()) return;
    try {
      layoutRef.current?.stop();

      const connected = cy.nodes().filter((node) => node.degree() > 0);
      const isolates = cy.nodes().filter((node) => node.degree() === 0);

      if (layoutMode === "cose") {
        const target = connected.length > 1 ? connected : cy.nodes();
        const layout = target.layout({
          name: "cose",
          animate: false,
          fit: false,
          padding: 60,
          randomize: true,
          nodeRepulsion: 26000,
          nodeOverlap: 30,
          idealEdgeLength: 170,
          edgeElasticity: 0.22,
          gravity: 0.16,
          numIter: 900,
          componentSpacing: 180,
          tile: true,
          tilingPaddingVertical: 100,
          tilingPaddingHorizontal: 100,
          initialEnergyOnIncremental: 0.25,
        } as any);
        layoutRef.current = layout;
        layout.run();

        if (connected.length > 1 && isolates.length) {
          const bb = connected.boundingBox();
          const cols = Math.max(3, Math.ceil(Math.sqrt(isolates.length)));
          const startX = bb.x1;
          const startY = bb.y2 + 130;
          isolates.forEach((node, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);
            node.position({ x: startX + col * 145, y: startY + row * 105 });
          });
        }
      } else {
        const layout = cy.layout({
          name: layoutMode,
          animate: false,
          fit: false,
          padding: 70,
          spacingFactor: 1.35,
          avoidOverlap: true,
          minNodeSpacing: 75,
          directed: layoutMode === "breadthfirst",
          concentric: (node: cytoscape.NodeSingular) => node.degree(),
          levelWidth: (nodes: cytoscape.NodeCollection) => Math.max(1, Math.sqrt(nodes.length)),
        } as any);
        layoutRef.current = layout;
        layout.run();
      }

      cy.fit(cy.nodes(), 65);
    } catch (error) {
      console.warn("Network layout warning:", error);
    }
  };
  useEffect(() => {
    if (!containerRef.current || !graphData.nodes.length) return;

    let cy: cytoscape.Core | null = null;
    try {
      cy = cytoscape({
        container: containerRef.current,
        elements: [...graphData.nodes, ...graphData.edges],
        style: [
          {
            selector: "node",
            style: {
              "background-color": "#FFFFFF",
              "border-width": 2,
              "border-color": "data(color)",
              label: "data(displayLabel)",
              color: "#172026",
              "font-size": 10,
              "font-family": "Inter, sans-serif",
              "text-wrap": "ellipsis",
              "text-max-width": 160,
              "text-valign": "bottom",
              "text-margin-y": 8,
              width: "mapData(degree, 0, 6, 40, 62)",
              height: "mapData(degree, 0, 6, 40, 62)",
            } as any,
          },
          {
            selector: 'node[kind = "case"]',
            style: {
              shape: "round-rectangle",
              width: 92,
              height: 42,
              "background-color": "#E6F4F2",
              "border-color": "#0F766E",
              "font-size": 10,
              "font-weight": 700,
              "text-valign": "center",
              "text-margin-y": 0,
            } as any,
          },
          {
            selector: 'node[kind = "event"]',
            style: {
              shape: "rectangle",
              width: 34,
              height: 34,
              "background-color": "#F0F3F5",
              "border-color": "#7B8790",
              "font-size": 8,
              "text-margin-y": 6,
            } as any,
          },
          {
            selector: 'node[kind = "document"]',
            style: {
              shape: "round-rectangle",
              width: 110,
              height: 42,
              "background-color": "#F4F6F8",
              "border-color": "#79858E",
              "font-size": 8,
              "font-weight": 650,
              "text-wrap": "ellipsis",
              "text-max-width": 92,
              "text-valign": "center",
              "text-margin-y": 0,
            } as any,
          },
          {
            selector: 'node[type = "accused"]',
            style: {
              "background-color": "#FFF1F2",
              "border-color": COLORS.accused,
            } as any,
          },
          {
            selector: 'node[type = "officer"]',
            style: {
              "background-color": "#EDF7F8",
              "border-color": COLORS.officer,
            } as any,
          },
          {
            selector: 'node[type = "witness"]',
            style: {
              shape: "round-rectangle",
              "background-color": "#EDF8F2",
              "border-color": COLORS.witness,
            } as any,
          },
          {
            selector: 'node[type = "property"]',
            style: {
              shape: "diamond",
              width: 40,
              height: 40,
              "background-color": "#FFF7E6",
              "border-color": COLORS.property,
            } as any,
          },
          {
            selector: "edge",
            style: {
              width: "mapData(confidence, 0, 1, 1, 3)",
              "line-color": "data(color)",
              "target-arrow-color": "data(color)",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              opacity: 0.6,
              label: "data(label)",
              color: "#66727B",
              "font-size": 8,
              "font-family": "Inter, sans-serif",
              "text-rotation": "autorotate",
              "text-background-color": "#FFFFFF",
              "text-background-opacity": 0.88 as any,
              "text-background-padding": 3 as any,
            } as any,
          },
          {
            selector: 'edge[contextual = true]',
            style: {
              "line-style": "dashed",
              "target-arrow-shape": "none",
              opacity: 0.42,
              width: 1.5,
            } as any,
          },
          {
            selector: ".hovered",
            style: {
              label: "data(fullLabel)",
              "border-width": 3,
              "border-color": "#A66A00",
              "overlay-color": "#0F766E",
              "overlay-opacity": 0.08,
              opacity: 1,
            } as any,
          },
          {
            selector: ".hovered-edge",
            style: {
              label: "data(fullLabel)",
              width: 3,
              opacity: 1,
            } as any,
          },
          {
            selector: ":selected",
            style: {
              "border-width": 3,
              "border-color": "#A66A00",
              "overlay-color": "#A66A00",
              "overlay-opacity": 0.06,
              label: "data(fullLabel)",
              opacity: 1,
            } as any,
          },
          {
            selector: ".search-match",
            style: {
              "border-width": 3,
              "border-color": "#0F766E",
              "overlay-color": "#0F766E",
              "overlay-opacity": 0.08,
              label: "data(fullLabel)",
            } as any,
          },
        ],
      });

      cy.ready(() => renderLayout());

      cy.on("tap", "node", (event) => {
        const node = event.target;
        const data = node.data();
        setActiveNodeData(data);
        if (data.reconciledEntity) setSelectedEntity(data.reconciledEntity);
        if (data.kind === "document" && data.document?.original_filename) openSource(data.document.original_filename);
      });

      cy.on("tap", (event) => {
        if (event.target === cy) setActiveNodeData(null);
      });

      cy.on("mouseover", "node", (event) => {
        const node = event.target;
        const data = node.data();
        const pos = event.renderedPosition || event.position || { x: 0, y: 0 };
        node.addClass("hovered");
        const tooltip = buildNodeTooltip(data);
        const width = containerRef.current?.clientWidth || 1000;
        const height = containerRef.current?.clientHeight || 700;
        setHoverInfo({
          left: Math.min(Math.max(12, pos.x + 18), Math.max(12, width - 325)),
          top: Math.min(Math.max(12, pos.y + 18), Math.max(12, height - 100)),
          ...tooltip,
        });
      });

      cy.on("mouseout", "node", (event) => {
        event.target.removeClass("hovered");
        setHoverInfo(null);
      });

      cy.on("mouseover", "edge", (event) => {
        const edge = event.target;
        const pos = event.renderedPosition || event.position || { x: 0, y: 0 };
        edge.addClass("hovered-edge");
        const data = edge.data();
        const width = containerRef.current?.clientWidth || 1000;
        const height = containerRef.current?.clientHeight || 700;
        setHoverInfo({
          left: Math.min(Math.max(12, pos.x + 18), Math.max(12, width - 325)),
          top: Math.min(Math.max(12, pos.y + 18), Math.max(12, height - 100)),
          title: data.fullLabel || "Relationship",
          meta: `${Math.round((Number(data.confidence) || 0) * 100)}% confidence`,
          detail: data.evidence || "Relationship recorded in the case graph.",
        });
      });

      cy.on("mouseout", "edge", (event) => {
        event.target.removeClass("hovered-edge");
        setHoverInfo(null);
      });

      cyRef.current = cy;
    } catch (error) {
      console.warn("Cytoscape initialization warning:", error);
    }

    return () => {
      try { layoutRef.current?.stop(); } catch (_) {}
      layoutRef.current = null;
      if (cy) {
        try {
          cy.stop();
          cy.removeAllListeners();
          if (!cy.destroyed()) cy.destroy();
        } catch (_) {}
      }
      cyRef.current = null;
      setHoverInfo(null);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphData, setSelectedEntity]);

  useEffect(() => {
    renderLayout();
  }, [layoutMode]);

  const focusSearch = (value: string) => {
    setQuery(value);
    const cy = cyRef.current;
    if (!cy || cy.destroyed()) return;
    cy.elements().removeClass("search-match");
    const q = value.trim().toLowerCase();
    if (!q) {
      cy.fit(undefined, 70);
      return;
    }
    const matches = cy.nodes().filter((node) => String(node.data("fullLabel") || node.data("label") || "").toLowerCase().includes(q));
    if (matches.length) {
      matches.addClass("search-match");
      cy.fit(matches, 130);
    }
  };

  const openSource = (filename: string) => {
    const index = documents.findIndex((document) => document.original_filename === filename);
    if (index >= 0) {
      useCaseStore.getState().setActiveDocIndex(index);
      useCaseStore.getState().setViewMode("inspector");
    }
  };

  const edgeCount = graphData.edges.length;

  if (!crossDocIntelligence && !graphContract) {
    return <div className="sanket-empty-state">No case memory is available. Ingest evidence to build the network.</div>;
  }

  return (
    <div className="sanket-network">
      <div className="sanket-network__toolbar">
        <div className="sanket-network__tool-title">
          <Share2 size={16} />
          <div>
            <strong>Case network</strong>
            <span>{graphData.entityCount} entities · {graphData.eventCount} events · {edgeCount} evidence connections</span>
          </div>
        </div>
        <div className="sanket-network__tools">
          <div className="sanket-network__search-wrap" data-tooltip="Search names, identifiers, events, and other case-memory objects">
            <Search size={13} />
            <input
              value={query}
              aria-label="Search case network"
              placeholder="Search case memory"
              onChange={(event) => focusSearch(event.target.value)}
            />
          </div>
          <select
            value={layoutMode}
            onChange={(event) => setLayoutMode(event.target.value as any)}
            className="sanket-network__select"
            aria-label="Network layout"
            data-tooltip="Choose how connected evidence is arranged"
            title="Choose how connected evidence is arranged"
          >
            <option value="cose">Connection layout</option>
            <option value="concentric">Radial layout</option>
            <option value="breadthfirst">Hierarchy layout</option>
          </select>
          <button type="button" className="sanket-icon-button" onClick={renderLayout} data-tooltip="Automatically arrange the network using its current connections" title="Auto arrange connected evidence"><RefreshCw size={15} /></button>
          {graphData.isolatedNodes > 0 && (
            <button
              type="button"
              className={`sanket-icon-button ${showIsolates ? "is-active" : ""}`}
              onClick={() => setShowIsolates((value) => !value)}
              data-tooltip={showIsolates ? "Hide unconnected observations so only relationships remain prominent" : `Show ${graphData.isolatedNodes} unconnected case objects that are still stored in case memory`}
              title={showIsolates ? "Hide unconnected observations" : "Show unconnected observations"}
            >
              {showIsolates ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          )}
          <button type="button" className="sanket-icon-button" onClick={() => cyRef.current?.zoom((cyRef.current?.zoom() || 1) * 1.2)} data-tooltip="Zoom in on the case network" title="Zoom in"><ZoomIn size={15} /></button>
          <button type="button" className="sanket-icon-button" onClick={() => cyRef.current?.zoom((cyRef.current?.zoom() || 1) * 0.8)} data-tooltip="Zoom out to see more of the case network" title="Zoom out"><ZoomOut size={15} /></button>
          <button type="button" className="sanket-icon-button" onClick={() => cyRef.current?.fit(undefined, 70)} data-tooltip="Fit all case-memory objects into view" title="Fit network"><Maximize2 size={15} /></button>
        </div>
      </div>

      <div className="sanket-network__content">
        <div ref={containerRef} className="sanket-network__canvas" />
        {hoverInfo && (
          <div className="sanket-network__hover" style={{ left: hoverInfo.left, top: hoverInfo.top }} role="status">
            <strong>{hoverInfo.title}</strong>
            <span>{hoverInfo.meta}</span>
            <small>{hoverInfo.detail}</small>
          </div>
        )}
        {edgeCount > 0 && graphData.isolatedNodes > 0 && (
          <div className="sanket-network__notice">
            <strong>{graphData.connectedNodes} connected objects · {graphData.isolatedNodes} additional observations</strong>
            <span>The network is arranged from actual relationships. Unconnected case-memory objects are hidden by default so the investigative structure stays readable.</span>
          </div>
        )}
        {!edgeCount && (
          <div className="sanket-network__notice">
            <strong>No direct relationships are recorded in the current graph contract.</strong>
            <span>Nothing has been invented to make the graph look connected. Use Evidence Review or show unconnected observations to inspect the underlying case memory.</span>
          </div>
        )}

        <div className="sanket-network__legend">
          <div className="sanket-network__legend-title">Network objects</div>
          <div><i className="legend-dot" style={{ background: COLORS.person }} /> Person</div>
          <div><i className="legend-dot" style={{ background: COLORS.officer }} /> Officer</div>
          <div><i className="legend-dot" style={{ background: COLORS.witness }} /> Witness</div>
          <div><i className="legend-dot" style={{ background: COLORS.property, borderRadius: 2, transform: "rotate(45deg)" }} /> Asset</div>
          <div><i className="legend-dot" style={{ background: COLORS.event, borderRadius: 2 }} /> Event</div>
          <div><i className="legend-dot" style={{ background: "#6E7982", borderRadius: 3 }} /> Source document</div>
          <div><i className="legend-line" style={{ background: "#70808A" }} /> Direct relationship</div>
          <div><i className="legend-line legend-line--dashed" style={{ background: "#94A0A8" }} /> Observed in source</div>
        </div>

        {activeNodeData && (
          <aside className="sanket-network__drawer">
            <div className="sanket-network__drawer-header">
              <div>
                <span className="sanket-card__meta">Case memory</span>
                <h3>{activeNodeData.fullLabel || activeNodeData.label}</h3>
                <span className="sanket-pill">{formatType(activeNodeData.type || activeNodeData.kind)}</span>
              </div>
              <button type="button" className="sanket-icon-button" onClick={() => setActiveNodeData(null)} data-tooltip="Close the case-memory inspector" title="Close"><X size={15} /></button>
            </div>
            <div className="sanket-network__drawer-body">
              {activeNodeData.reconciledEntity && (
                <>
                  <div className="sanket-drawer-section"><span>Recorded roles</span><div className="sanket-role-chips">{activeNodeData.reconciledEntity.roles.map((role: string) => <span key={role} className="sanket-pill">{formatType(role)}</span>)}</div></div>
                  <div className="sanket-drawer-section"><span>Source documents</span>{activeNodeData.reconciledEntity.documents.map((doc: string) => <button key={doc} type="button" className="sanket-source-row" onClick={() => openSource(doc)} title={`Open ${doc} in the document inspector`}>{doc}<ArrowRight size={12} /></button>)}</div>
                  <div className="sanket-drawer-section"><span>Occurrences</span>{activeNodeData.reconciledEntity.occurrences.slice(0, 8).map((occ: any, index: number) => <div key={`${occ.filename}-${index}`} className="sanket-occurrence"><strong>{formatType(occ.role)}</strong><small>{occ.filename} · {Math.round((occ.confidence || 0) * 100)}%</small></div>)}</div>
                </>
              )}

              {activeNodeData.graphEntity && (
                <>
                  <div className="sanket-drawer-section"><span>Observed value</span><div className="sanket-summary-copy">{activeNodeData.graphEntity.name}</div></div>
                  <div className="sanket-drawer-section"><span>Evidence source</span>
                    <button type="button" className="sanket-source-card" onClick={() => openSource(activeNodeData.graphEntity.source?.filename || "")} title="Open the source document for this observation">
                      <span><strong>{activeNodeData.graphEntity.source?.filename || "Source unavailable"}</strong><small>Page {activeNodeData.graphEntity.source?.page || 1} · {Math.round((activeNodeData.graphEntity.confidence || 0) * 100)}% confidence</small></span>
                      <ArrowRight size={13} />
                    </button>
                  </div>
                  {activeNodeData.graphEntity.source?.text_span && <div className="sanket-drawer-section"><span>Observed text</span><div className="sanket-occurrence"><small>{activeNodeData.graphEntity.source.text_span}</small></div></div>}
                </>
              )}

              {activeNodeData.graphEvent && (
                <>
                  <div className="sanket-drawer-section"><span>Event time</span><div className="sanket-occurrence"><strong>{activeNodeData.graphEvent.timestamp || activeNodeData.graphEvent.timestamp_start || "Unspecified"}</strong><small>{activeNodeData.graphEvent.type}</small></div></div>
                  {activeNodeData.graphEvent.source?.filename && <div className="sanket-drawer-section"><span>Source evidence</span><button type="button" className="sanket-source-row" onClick={() => openSource(activeNodeData.graphEvent.source.filename)} title="Open the source document for this event">{activeNodeData.graphEvent.source.filename}<ArrowRight size={12} /></button></div>}
                </>
              )}

              {activeNodeData.rawItem && <div className="sanket-drawer-section"><span>Recorded asset</span><div className="sanket-asset-focus"><strong>{activeNodeData.rawItem.currency || "INR"} {Number(activeNodeData.rawItem.value || 0).toLocaleString()}</strong><small>{activeNodeData.rawItem.source_doc}</small></div></div>}
            </div>
            <div className="sanket-network__drawer-footer">
              <button type="button" className="sanket-button" onClick={() => setViewMode("table")} data-tooltip="Open all structured evidence fields in the ledger" title="Open evidence ledger"><FileSearch size={14} /> Open evidence ledger</button>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};
