"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Download,
  AlertTriangle,
  ArrowDownToLine,
  ArrowUpFromLine,
  Check,
  CircleDot,
  Clock3,
  Code2,
  ExternalLink,
  FileSearch,
  Edit3,
  GitBranch,
  Grip,
  Link2,
  ListChecks,
  Maximize2,
  Play,
  Plus,
  PlusSquare,
  RotateCcw,
  Save,
  PanelRight,
  Upload,
  ZoomIn,
  ZoomOut,
  Search,
  ShieldCheck,
  Target,
  Sparkles,
  Trash2,
  X,
  Zap,
} from "lucide-react";

import { API_BASE, useCaseStore } from "@/store/useCaseStore";

type WorkflowNodeType =
  | "TIME_FILTER"
  | "EXPAND_NETWORK"
  | "GRAPH_ANALYTICS"
  | "KEY_INDIVIDUALS"
  | "COMMUNITY_DETECTION"
  | "BRIDGE_ANALYSIS"
  | "ANOMALY_DETECTION"
  | "SHORTEST_PATH"
  | "EVIDENCE_REVIEW"
  | "REPORT";

type NodeStatus = "idle" | "ready" | "selected" | "error";

interface CanvasNode {
  id: string;
  type: WorkflowNodeType;
  label: string;
  description: string;
  x: number;
  y: number;
  config: Record<string, any>;
  status: NodeStatus;
}

interface CanvasEdge {
  id: string;
  source: string;
  target: string;
}

const NODE_META: Record<
  WorkflowNodeType,
  { title: string; short: string; color: string; icon: React.ComponentType<{ className?: string }>; description: string }
> = {
  TIME_FILTER: {
    title: "Time Filter",
    short: "TIME",
    color: "#3478A7",
    icon: Clock3,
    description: "Limit evidence and events to an explicit time window.",
  },
  EXPAND_NETWORK: {
    title: "Expand Network",
    short: "EXPAND",
    color: "#0F766E",
    icon: GitBranch,
    description: "Expand selected entities to a controlled graph depth.",
  },
  GRAPH_ANALYTICS: {
    title: "Graph Analytics",
    short: "GRAPH",
    color: "#7455A2",
    icon: Activity,
    description: "Compute structural metrics across the active graph.",
  },
  KEY_INDIVIDUALS: {
    title: "Key Individuals",
    short: "KEY",
    color: "#A66A00",
    icon: CircleDot,
    description: "Rank influential or structurally important entities.",
  },
  COMMUNITY_DETECTION: {
    title: "Community Detection",
    short: "CLUSTER",
    color: "#3B6EA5",
    icon: GitBranch,
    description: "Identify densely connected communities in the graph.",
  },
  BRIDGE_ANALYSIS: {
    title: "Bridge Analysis",
    short: "BRIDGE",
    color: "#C73E46",
    icon: Link2,
    description: "Surface possible cross-community intermediaries.",
  },
  ANOMALY_DETECTION: {
    title: "Anomaly Detection",
    short: "ANOMALY",
    color: "#B96B16",
    icon: AlertTriangle,
    description: "Detect unusual temporal or structural activity patterns.",
  },
  SHORTEST_PATH: {
    title: "Shortest Path",
    short: "TRACE",
    color: "#16805B",
    icon: ArrowUpFromLine,
    description: "Trace a shortest path between two entities.",
  },
  EVIDENCE_REVIEW: {
    title: "Evidence Review",
    short: "EVIDENCE",
    color: "#71808A",
    icon: ShieldCheck,
    description: "Inspect the source records behind a finding.",
  },
  REPORT: {
    title: "Report",
    short: "REPORT",
    color: "#46515A",
    icon: Code2,
    description: "Package the analysis into a reproducible investigation report.",
  },
};

const INITIAL_NODES: CanvasNode[] = [
  {
    id: "time-1",
    type: "TIME_FILTER",
    label: "LAST 30 DAYS",
    description: "Scope investigation to the active window.",
    x: 80,
    y: 150,
    config: { start: "2026-05-01T00:00:00+05:30", end: "2026-08-31T23:59:59+05:30" },
    status: "ready",
  },
  {
    id: "expand-1",
    type: "EXPAND_NETWORK",
    label: "EXPAND 2 HOPS",
    description: "Expand the selected entities and their evidence links.",
    x: 360,
    y: 150,
    config: { depth: 2 },
    status: "ready",
  },
  {
    id: "community-1",
    type: "COMMUNITY_DETECTION",
    label: "FIND COMMUNITIES",
    description: "Discover dense network clusters before bridge analysis.",
    x: 640,
    y: 90,
    config: {},
    status: "ready",
  },
  {
    id: "bridge-1",
    type: "BRIDGE_ANALYSIS",
    label: "FIND BRIDGE LEADS",
    description: "Search for cross-community intermediary candidates.",
    x: 930,
    y: 90,
    config: { minimum_cross_community_ratio: 0.2 },
    status: "ready",
  },
  {
    id: "anomaly-1",
    type: "ANOMALY_DETECTION",
    label: "CHECK ACTIVITY",
    description: "Compare recent activity against an explicit baseline.",
    x: 640,
    y: 300,
    config: { target_start: "2026-08-01T00:00:00+05:30", target_end: "2026-08-31T23:59:59+05:30", max_findings: 20 },
    status: "ready",
  },
  {
    id: "evidence-1",
    type: "EVIDENCE_REVIEW",
    label: "REVIEW EVIDENCE",
    description: "Inspect records supporting shortlisted leads.",
    x: 930,
    y: 300,
    config: {},
    status: "ready",
  },
  {
    id: "report-1",
    type: "REPORT",
    label: "INVESTIGATION REPORT",
    description: "Create a reproducible case summary with traceable findings.",
    x: 1210,
    y: 190,
    config: { include_node_outputs: true },
    status: "ready",
  },
];

const INITIAL_EDGES: CanvasEdge[] = [
  { id: "e1", source: "time-1", target: "expand-1" },
  { id: "e2", source: "expand-1", target: "community-1" },
  { id: "e3", source: "expand-1", target: "anomaly-1" },
  { id: "e4", source: "community-1", target: "bridge-1" },
  { id: "e5", source: "bridge-1", target: "evidence-1" },
  { id: "e6", source: "anomaly-1", target: "evidence-1" },
  { id: "e7", source: "evidence-1", target: "report-1" },
];

const CANVAS_WIDTH = 1600;
const CANVAS_HEIGHT = 760;
const NODE_WIDTH = 218;
const NODE_HEIGHT = 112;

const WORKFLOW_CONFIG_DEFAULTS: Record<WorkflowNodeType, Record<string, any>> = {
  TIME_FILTER: {
    start: "2026-08-01T00:00:00+05:30",
    end: "2026-08-31T23:59:59+05:30",
  },
  EXPAND_NETWORK: { depth: 2 },
  GRAPH_ANALYTICS: { target_entity_types: ["PERSON"], include_event_interactions: true },
  KEY_INDIVIDUALS: { top_k: 10, target_entity_types: ["PERSON"], include_event_interactions: true },
  COMMUNITY_DETECTION: { target_entity_types: ["PERSON"], include_event_interactions: true },
  BRIDGE_ANALYSIS: { minimum_cross_community_ratio: 0.2, target_entity_types: ["PERSON"], include_event_interactions: true },
  ANOMALY_DETECTION: {
    target_start: "2026-08-01T00:00:00+05:30",
    target_end: "2026-08-31T23:59:59+05:30",
    baseline_start: "2026-07-01T00:00:00+05:30",
    baseline_end: "2026-07-31T23:59:59+05:30",
    target_entity_types: ["PERSON"],
    max_findings: 20,
  },
  SHORTEST_PATH: { source_id: "", target_id: "" },
  EVIDENCE_REVIEW: {},
  REPORT: { title: "Investigation Report", include_node_outputs: [], notes: "" },
};

function cloneWorkflowConfig(type: WorkflowNodeType, config?: Record<string, any>) {
  return JSON.parse(JSON.stringify(config ?? WORKFLOW_CONFIG_DEFAULTS[type] ?? {}));
}

function nodePortPoint(node: CanvasNode, port: "in" | "out") {
  return {
    x: node.x + (port === "out" ? NODE_WIDTH : 0),
    y: node.y + NODE_HEIGHT / 2,
  };
}

function curvePath(source: CanvasNode, target: CanvasNode) {
  const a = nodePortPoint(source, "out");
  const b = nodePortPoint(target, "in");
  const dx = Math.max(48, Math.abs(b.x - a.x) * 0.45);
  return `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`;
}

function nextNodePosition(nodes: CanvasNode[]) {
  const rows = Math.floor(nodes.length / 3);
  const cols = nodes.length % 3;
  return { x: 80 + cols * 290, y: 520 + rows * 150 };
}

function workflowNameFromNodes(nodes: CanvasNode[]) {
  const labels = nodes.filter((node) => node.type !== "REPORT").slice(0, 2).map((node) => node.label.trim()).filter(Boolean);
  return labels.length ? labels.join(" → ") : "SANKET Investigation Workflow";
}

export const InvestigationCanvasView: React.FC = () => {
  const [nodes, setNodes] = useState<CanvasNode[]>(INITIAL_NODES);
  const [edges, setEdges] = useState<CanvasEdge[]>(INITIAL_EDGES);
  const [selectedId, setSelectedId] = useState<string | null>("bridge-1");
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);
  const [connectionCursor, setConnectionCursor] = useState<{ x: number; y: number } | null>(null);
  const [runStep, setRunStep] = useState(0);
  const [executionStatus, setExecutionStatus] = useState<"idle" | "running" | "completed" | "failed">("idle");
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [executionMessage, setExecutionMessage] = useState("Backend execution is ready.");
  const [nodeOutputs, setNodeOutputs] = useState<Record<string, any>>({});
  const [validationErrors, setValidationErrors] = useState<any[]>([]);
  const activeCaseId = useCaseStore((state) => state.activeCaseId);
  const setViewMode = useCaseStore((state) => state.setViewMode);
  const crossDocIntelligence = useCaseStore((state) => state.crossDocIntelligence);
  const setSelectedEntity = useCaseStore((state) => state.setSelectedEntity);
  const [showPalette, setShowPalette] = useState(true);
  const [search, setSearch] = useState("");
  const [showAiPlanner, setShowAiPlanner] = useState(false);
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiPlan, setAiPlan] = useState<any | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [executionBody, setExecutionBody] = useState<any | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [resultsTab, setResultsTab] = useState<"insights" | "evidence" | "run" | "report">("insights");
  const [selectedFindingIndex, setSelectedFindingIndex] = useState(0);
  const [showNodeInspector, setShowNodeInspector] = useState(true);
  const [executionHistory, setExecutionHistory] = useState<any[]>([]);
  const dragRef = useRef<{ id: string; dx: number; dy: number } | null>(null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const canvasViewportRef = useRef<HTMLDivElement | null>(null);
  const [zoom, setZoom] = useState(0.82);
  const [zoomMode, setZoomMode] = useState<"fit" | "manual">("fit");
  const [showNodeBuilder, setShowNodeBuilder] = useState(false);
  const [nodeBuilderMode, setNodeBuilderMode] = useState<"create" | "edit">("create");
  const [nodeBuilderType, setNodeBuilderType] = useState<WorkflowNodeType>("GRAPH_ANALYTICS");
  const [nodeBuilderLabel, setNodeBuilderLabel] = useState("MY ANALYSIS");
  const [nodeBuilderDescription, setNodeBuilderDescription] = useState(NODE_META.GRAPH_ANALYTICS.description);
  const [nodeBuilderConfigText, setNodeBuilderConfigText] = useState(JSON.stringify(WORKFLOW_CONFIG_DEFAULTS.GRAPH_ANALYTICS, null, 2));
  const [nodeBuilderError, setNodeBuilderError] = useState<string | null>(null);
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);

  const selectedNode = useMemo(() => nodes.find((node) => node.id === selectedId) ?? null, [nodes, selectedId]);

  const workflowFindings = useMemo(() => {
    const items: Array<{
      id: string;
      title: string;
      kind: "bridge" | "key" | "anomaly";
      workflowNodeId: string;
      entityId?: string;
      score?: number;
      severity?: string;
      status?: string;
      explanation?: string;
      reasons?: string[];
      relationshipIds: string[];
      eventIds: string[];
      raw: Record<string, any>;
    }> = [];

    nodes.forEach((node) => {
      const output = nodeOutputs[node.id];
      if (!output || typeof output !== "object") return;

      const bridgeCandidates = Array.isArray(output.bridge_candidates) ? output.bridge_candidates : [];
      bridgeCandidates.forEach((item: any, index: number) => items.push({
        id: String(item.node_id || `bridge-${node.id}-${index}`),
        title: String(item.label || item.node_id || `Bridge candidate ${index + 1}`),
        kind: "bridge",
        workflowNodeId: node.id,
        entityId: item.node_id ? String(item.node_id) : undefined,
        score: Number.isFinite(Number(item.bridge_score)) ? Number(item.bridge_score) : undefined,
        status: String(item.status || "INVESTIGATIVE_LEAD"),
        explanation: item.status ? `Cross-community ratio ${Math.round(Number(item.cross_community_ratio || 0) * 100)}% · ${item.supporting_relationship_ids?.length || 0} supporting relationships.` : undefined,
        relationshipIds: Array.isArray(item.supporting_relationship_ids) ? item.supporting_relationship_ids.map(String) : [],
        eventIds: Array.isArray(item.supporting_event_ids) ? item.supporting_event_ids.map(String) : [],
        raw: item,
      }));

      const keyIndividuals = Array.isArray(output.key_individuals) ? output.key_individuals : [];
      keyIndividuals.forEach((item: any, index: number) => items.push({
        id: String(item.node_id || `key-${node.id}-${index}`),
        title: String(item.label || item.node_id || `Key individual ${index + 1}`),
        kind: "key",
        workflowNodeId: node.id,
        entityId: item.node_id ? String(item.node_id) : undefined,
        score: Number.isFinite(Number(item.influence_score)) ? Number(item.influence_score) : undefined,
        status: "STRUCTURAL_LEAD",
        reasons: Array.isArray(item.reasons) ? item.reasons.map(String) : [],
        relationshipIds: [],
        eventIds: [],
        raw: item,
      }));

      const anomalyFindings = Array.isArray(output.findings) ? output.findings : [];
      anomalyFindings.forEach((item: any, index: number) => items.push({
        id: String(item.finding_id || `anomaly-${node.id}-${index}`),
        title: String(item.title || item.anomaly_type || `Anomaly ${index + 1}`),
        kind: "anomaly",
        workflowNodeId: node.id,
        entityId: item.entity_id ? String(item.entity_id) : undefined,
        score: Number.isFinite(Number(item.score)) ? Number(item.score) : undefined,
        severity: String(item.severity || "LOW"),
        status: String(item.status || "INVESTIGATIVE_LEAD"),
        explanation: String(item.explanation || "Unusual activity pattern surfaced by the deterministic anomaly engine."),
        relationshipIds: Array.isArray(item.supporting_relationship_ids) ? item.supporting_relationship_ids.map(String) : [],
        eventIds: Array.isArray(item.supporting_event_ids) ? item.supporting_event_ids.map(String) : [],
        raw: item,
      }));
    });

    return items.slice(0, 80);
  }, [nodeOutputs, nodes]);

  const evidenceReview = executionBody?.evidence_review || {};
  const contradictionItems = Array.isArray(evidenceReview?.contradictions?.items) ? evidenceReview.contradictions.items : [];
  const provenanceSummary = evidenceReview?.provenance?.summary || {};
  const evidenceReviewOutput = useMemo(() => {
    const evidenceNode = nodes.find((node) => node.type === "EVIDENCE_REVIEW" && nodeOutputs[node.id]);
    return evidenceNode ? nodeOutputs[evidenceNode.id] || {} : {};
  }, [nodeOutputs, nodes]);
  const evidenceReferences = Array.isArray(evidenceReviewOutput?.evidence_references) ? evidenceReviewOutput.evidence_references : [];
  const executionSummary = executionBody?.graph_summary || {};

  const saveWorkflow = useCallback(() => {
    try {
      const payload = { nodes, edges, savedAt: new Date().toISOString() };
      localStorage.setItem(`sanket-workflow:${activeCaseId}`, JSON.stringify(payload));
      setSavedAt(payload.savedAt);
    } catch (_) {
      setExecutionMessage("Unable to save the workflow in this browser.");
    }
  }, [activeCaseId, edges, nodes]);

  const loadWorkflow = useCallback(() => {
    try {
      const raw = localStorage.getItem(`sanket-workflow:${activeCaseId}`);
      if (!raw) {
        setExecutionMessage("No saved workflow exists for this case in this browser.");
        return;
      }
      const payload = JSON.parse(raw);
      if (!Array.isArray(payload?.nodes) || !Array.isArray(payload?.edges)) throw new Error("Invalid saved workflow");
      setNodes(payload.nodes);
      setEdges(payload.edges);
      setSelectedId(payload.nodes[0]?.id || null);
      setSelectedEdgeId(null);
      setSavedAt(payload.savedAt || null);
      setExecutionStatus("idle");
      setExecutionId(null);
      setNodeOutputs({});
      setExecutionBody(null);
      setExecutionMessage("Saved workflow restored. Validate it before running.");
    } catch (_) {
      setExecutionMessage("Saved workflow could not be restored.");
    }
  }, [activeCaseId]);

  const downloadFile = useCallback((filename: string, content: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }, []);

  const exportInvestigationReport = useCallback(() => {
    const markdown = executionBody?.report?.markdown;
    if (!markdown) {
      setExecutionMessage("Run the workflow first to generate a report.");
      return;
    }
    downloadFile(`sanket-investigation-report-${activeCaseId}.md`, String(markdown), "text/markdown;charset=utf-8");
  }, [activeCaseId, downloadFile, executionBody]);

  const executionHistoryKey = `sanket-workflow-history:${activeCaseId}`;

  useEffect(() => {
    try {
      const raw = localStorage.getItem(executionHistoryKey);
      const parsed = raw ? JSON.parse(raw) : [];
      setExecutionHistory(Array.isArray(parsed) ? parsed.slice(0, 8) : []);
    } catch (_) {
      setExecutionHistory([]);
    }
    setSelectedFindingIndex(0);
    setShowResults(false);
  }, [executionHistoryKey]);

  const persistExecutionHistory = useCallback((body: any) => {
    const execution = body?.execution;
    if (!execution?.execution_id) return;
    try {
      const entry = {
        execution_id: String(execution.execution_id),
        created_at: new Date().toISOString(),
        status: String(execution.status || "UNKNOWN"),
        workflow_name: String(workflowNameFromNodes(nodes)),
        node_count: Array.isArray(execution.node_results) ? execution.node_results.length : nodes.length,
        finding_count: Array.isArray(execution.node_results)
          ? execution.node_results.reduce((count: number, result: any) => count + ["bridge_candidates", "key_individuals", "findings"].reduce((inner: number, key: string) => inner + (Array.isArray(result?.output?.[key]) ? result.output[key].length : 0), 0), 0)
          : workflowFindings.length,
        contradiction_count: Number(body?.evidence_review?.contradictions?.contradiction_count || 0),
        body,
      };
      const existingRaw = localStorage.getItem(executionHistoryKey);
      const existing = existingRaw ? JSON.parse(existingRaw) : [];
      const next = [entry, ...(Array.isArray(existing) ? existing.filter((item: any) => item?.execution_id !== entry.execution_id) : [])].slice(0, 8);
      localStorage.setItem(executionHistoryKey, JSON.stringify(next));
      setExecutionHistory(next);
    } catch (_) {
      // History is convenience state only; a storage quota/error must never block the run.
    }
  }, [executionHistoryKey, nodes, workflowFindings]);

  const generateAiPlan = async () => {
    const question = aiQuestion.trim();
    if (question.length < 5 || aiLoading) return;
    setAiLoading(true);
    setAiError(null);
    setAiPlan(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(activeCaseId)}/investigate/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, max_nodes: 8, selected_entity_ids: [] }),
      });
      const raw = await response.text();
      let body: any = {};
      try {
        body = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error(`Investigation planner returned a non-JSON response (${response.status}).`);
      }
      if (!response.ok) throw new Error(body?.detail || `AI planner unavailable (${response.status}).`);
      setAiPlan(body);
    } catch (error: any) {
      setAiError(error?.message || "Unable to generate an investigation plan.");
    } finally {
      setAiLoading(false);
    }
  };

  const applyAiPlan = () => {
    const workflow = aiPlan?.workflow;
    if (!workflow || !Array.isArray(workflow.nodes)) return;
    const nextNodes: CanvasNode[] = workflow.nodes.map((node: any, index: number) => {
      const type = String(node.type) as WorkflowNodeType;
      const meta = NODE_META[type];
      return {
        id: String(node.id || `ai-${index + 1}`),
        type,
        label: String(node.label || meta?.title || type),
        description: String(meta?.description || "AI-generated investigation step."),
        x: Number(node.position?.x ?? 80 + (index % 4) * 290),
        y: Number(node.position?.y ?? 110 + Math.floor(index / 4) * 180),
        config: (node.config || {}) as Record<string, string | number | boolean>,
        status: "ready",
      };
    });
    const nextNodeIds = new Set(nextNodes.map((node) => node.id));
    const rawEdges: CanvasEdge[] = Array.isArray(workflow.edges)
      ? workflow.edges.map((edge: any, index: number) => ({
          id: String(edge.id || `ai-edge-${index + 1}`),
          source: String(edge.source_node_id),
          target: String(edge.target_node_id),
        }))
      : [];
    const rejectedEdgeCount = rawEdges.filter((edge) => !nextNodeIds.has(edge.source) || !nextNodeIds.has(edge.target)).length;
    const nextEdges = rawEdges.filter((edge) => nextNodeIds.has(edge.source) && nextNodeIds.has(edge.target));
    if (rejectedEdgeCount > 0) {
      setAiError(`${rejectedEdgeCount} AI connection(s) referenced missing nodes and were omitted. Review the plan warning before applying again.`);
      return;
    }
    setNodes(nextNodes);
    setEdges(nextEdges);
    setSelectedId(nextNodes[0]?.id || null);
    setSelectedEdgeId(null);
    setNodeOutputs({});
    setExecutionBody(null);
    setExecutionStatus("idle");
    setExecutionId(null);
    setExecutionMessage("AI plan applied to the canvas. Review, validate, then run it.");
    setShowAiPlanner(false);
  };

  const filteredLibrary = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (Object.entries(NODE_META) as Array<[WorkflowNodeType, (typeof NODE_META)[WorkflowNodeType]]>).filter(([type, meta]) => {
      if (!q) return true;
      return `${type} ${meta.title} ${meta.description}`.toLowerCase().includes(q);
    });
  }, [search]);

  const updateNodePosition = useCallback((id: string, x: number, y: number) => {
    setNodes((current) =>
      current.map((node) => ({
        ...node,
        ...(node.id === id
          ? {
              x: Math.max(12, Math.min(CANVAS_WIDTH - NODE_WIDTH - 12, x)),
              y: Math.max(12, Math.min(CANVAS_HEIGHT - NODE_HEIGHT - 12, y)),
            }
          : {}),
      }))
    );
  }, []);

  const canvasPointFromPointer = useCallback((event: React.PointerEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return null;
    return {
      x: ((event.clientX - rect.left) / rect.width) * CANVAS_WIDTH,
      y: ((event.clientY - rect.top) / rect.height) * CANVAS_HEIGHT,
    };
  }, []);

  const fitCanvas = useCallback(() => {
    const viewport = canvasViewportRef.current;
    if (!viewport) return;
    const availableWidth = Math.max(320, viewport.clientWidth - 28);
    const availableHeight = Math.max(260, viewport.clientHeight - 28);
    const scale = Math.min(1, Math.max(0.48, Math.min(availableWidth / CANVAS_WIDTH, availableHeight / CANVAS_HEIGHT)));
    setZoom(Math.round(scale * 100) / 100);
  }, []);

  useEffect(() => {
    const viewport = canvasViewportRef.current;
    if (!viewport || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      if (zoomMode === "fit") fitCanvas();
    });
    observer.observe(viewport);
    const frame = requestAnimationFrame(() => {
      if (zoomMode === "fit") fitCanvas();
    });
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [fitCanvas, zoomMode]);

  const setManualZoom = useCallback((nextZoom: number) => {
    setZoomMode("manual");
    setZoom(Math.max(0.48, Math.min(1.25, Math.round(nextZoom * 100) / 100)));
  }, []);

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      const point = canvasPointFromPointer(event);
      if (point && connectingFrom) setConnectionCursor(point);
      if (!dragRef.current || !point) return;
      updateNodePosition(dragRef.current.id, point.x - dragRef.current.dx, point.y - dragRef.current.dy);
    },
    [canvasPointFromPointer, connectingFrom, updateNodePosition]
  );

  const cancelConnection = useCallback((message?: string) => {
    setConnectingFrom(null);
    setConnectionCursor(null);
    if (message) setExecutionMessage(message);
  }, []);

  const wouldCreateCycle = useCallback((sourceId: string, targetId: string, currentEdges: CanvasEdge[]) => {
    const adjacency = new Map<string, string[]>();
    currentEdges.forEach((edge) => {
      const list = adjacency.get(edge.source) || [];
      list.push(edge.target);
      adjacency.set(edge.source, list);
    });
    const stack = [targetId];
    const visited = new Set<string>();
    while (stack.length) {
      const current = stack.pop()!;
      if (current === sourceId) return true;
      if (visited.has(current)) continue;
      visited.add(current);
      (adjacency.get(current) || []).forEach((next) => stack.push(next));
    }
    return false;
  }, []);

  const completeConnection = useCallback((event: React.PointerEvent | React.MouseEvent, targetId: string) => {
    event.preventDefault();
    event.stopPropagation();
    if (!connectingFrom) return;
    const sourceId = connectingFrom;
    if (sourceId === targetId) {
      cancelConnection("Connection cancelled: a workflow node cannot connect to itself.");
      return;
    }
    if (edges.some((edge) => edge.source === sourceId && edge.target === targetId)) {
      cancelConnection("That connection already exists.");
      return;
    }
    if (wouldCreateCycle(sourceId, targetId, edges)) {
      cancelConnection("Connection rejected: the workflow must remain acyclic.");
      return;
    }
    setEdges((current) => [
      ...current,
      { id: `edge-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, source: sourceId, target: targetId },
    ]);
    setSelectedId(targetId);
    setSelectedEdgeId(null);
    cancelConnection("Connection added. Validate the workflow before execution.");
  }, [cancelConnection, connectingFrom, edges, wouldCreateCycle]);

  const handlePointerUp = useCallback(() => {
    dragRef.current = null;
    if (connectingFrom) cancelConnection("Connection cancelled. Drag from an output pin to an input pin to connect nodes.");
  }, [cancelConnection, connectingFrom]);

  const startDrag = (event: React.PointerEvent<HTMLDivElement>, node: CanvasNode) => {
    const target = event.currentTarget.getBoundingClientRect();
    const interactive = (event.target as HTMLElement).closest("button, input, textarea, select");
    if (interactive || connectingFrom) return;
    const offsetX = ((event.clientX - target.left) / target.width) * NODE_WIDTH;
    const offsetY = ((event.clientY - target.top) / target.height) * NODE_HEIGHT;
    dragRef.current = { id: node.id, dx: offsetX, dy: offsetY };
    setSelectedId(node.id);
    setSelectedEdgeId(null);
  };

  const activateConnection = useCallback((nodeId: string, point?: { x: number; y: number } | null) => {
    setConnectingFrom(nodeId);
    setSelectedId(nodeId);
    setSelectedEdgeId(null);
    setConnectionCursor(point || null);
    setExecutionMessage("Connecting… release on an input pin to create the workflow edge.");
  }, []);

  const beginConnectionDrag = (event: React.PointerEvent, nodeId: string) => {
    event.preventDefault();
    event.stopPropagation();
    activateConnection(nodeId, canvasPointFromPointer(event));
  };

  const addNodeAtPoint = useCallback((type: WorkflowNodeType, point?: { x: number; y: number } | null, overrides?: Partial<CanvasNode>) => {
    const meta = NODE_META[type];
    const fallback = nextNodePosition(nodes);
    const x = point ? point.x - NODE_WIDTH / 2 : fallback.x;
    const y = point ? point.y - NODE_HEIGHT / 2 : Math.min(fallback.y, CANVAS_HEIGHT - NODE_HEIGHT - 16);
    const id = `${type.toLowerCase()}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const newNode: CanvasNode = {
      id,
      type,
      label: meta.title.toUpperCase(),
      description: meta.description,
      x: Math.max(12, Math.min(CANVAS_WIDTH - NODE_WIDTH - 12, x)),
      y: Math.max(12, Math.min(CANVAS_HEIGHT - NODE_HEIGHT - 12, y)),
      config: cloneWorkflowConfig(type),
      status: "idle",
      ...overrides,
    };
    setNodes((current) => [...current, newNode]);
    setSelectedId(id);
    setSelectedEdgeId(null);
    setExecutionMessage(`Added ${newNode.label}. Configure, connect, validate, then run.`);
    return id;
  }, [nodes]);

  const addNode = useCallback((type: WorkflowNodeType) => addNodeAtPoint(type), [addNodeAtPoint]);

  const addDraggedPaletteNode = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const type = event.dataTransfer.getData("application/x-sanket-node-type") as WorkflowNodeType;
    if (!type || !NODE_META[type]) return;
    const point = canvasPointFromPointer(event as unknown as React.PointerEvent);
    addNodeAtPoint(type, point);
    event.dataTransfer.clearData();
  }, [addNodeAtPoint, canvasPointFromPointer]);

  const openCreateNodeBuilder = useCallback((type: WorkflowNodeType = "GRAPH_ANALYTICS") => {
    setNodeBuilderMode("create");
    setEditingNodeId(null);
    setNodeBuilderType(type);
    setNodeBuilderLabel(NODE_META[type].title.toUpperCase());
    setNodeBuilderDescription(NODE_META[type].description);
    setNodeBuilderConfigText(JSON.stringify(WORKFLOW_CONFIG_DEFAULTS[type], null, 2));
    setNodeBuilderError(null);
    setShowNodeBuilder(true);
  }, []);

  const openEditNodeBuilder = useCallback((node: CanvasNode) => {
    setNodeBuilderMode("edit");
    setEditingNodeId(node.id);
    setNodeBuilderType(node.type);
    setNodeBuilderLabel(node.label);
    setNodeBuilderDescription(node.description);
    setNodeBuilderConfigText(JSON.stringify(node.config ?? {}, null, 2));
    setNodeBuilderError(null);
    setShowNodeBuilder(true);
  }, []);

  const applyNodeBuilder = useCallback(() => {
    const label = nodeBuilderLabel.trim();
    if (label.length < 2) {
      setNodeBuilderError("Give the node a clear label.");
      return;
    }
    let config: Record<string, any>;
    try {
      const parsed = JSON.parse(nodeBuilderConfigText || "{}");
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error("Configuration must be a JSON object.");
      config = parsed;
    } catch (error: any) {
      setNodeBuilderError(error?.message || "Configuration must be valid JSON.");
      return;
    }

    const allowedKeysByType: Record<WorkflowNodeType, string[]> = {
      TIME_FILTER: ["start", "end"],
      EXPAND_NETWORK: ["seed_entity_ids", "depth"],
      GRAPH_ANALYTICS: ["target_entity_types", "include_event_interactions"],
      KEY_INDIVIDUALS: ["top_k", "target_entity_types", "include_event_interactions"],
      COMMUNITY_DETECTION: ["target_entity_types", "include_event_interactions"],
      BRIDGE_ANALYSIS: ["minimum_cross_community_ratio", "target_entity_types", "include_event_interactions"],
      ANOMALY_DETECTION: ["target_start", "target_end", "baseline_start", "baseline_end", "target_entity_types", "max_findings"],
      SHORTEST_PATH: ["source_id", "target_id"],
      EVIDENCE_REVIEW: ["entity_ids", "event_ids", "relationship_ids", "finding_ids"],
      REPORT: ["title", "include_node_outputs", "notes"],
    };
    const unknownKeys = Object.keys(config).filter((key) => !allowedKeysByType[nodeBuilderType].includes(key));
    if (unknownKeys.length) {
      setNodeBuilderError(`Unsupported configuration key(s) for ${nodeBuilderType}: ${unknownKeys.join(", ")}`);
      return;
    }

    const description = nodeBuilderDescription.trim() || NODE_META[nodeBuilderType].description;
    if (nodeBuilderMode === "edit" && editingNodeId) {
      setNodes((current) => current.map((node) => node.id === editingNodeId ? { ...node, type: nodeBuilderType, label, description, config, status: node.status === "error" ? "idle" : node.status } : node));
      setSelectedId(editingNodeId);
      setExecutionMessage(`${label} updated. Validate the workflow before execution.`);
    } else {
      addNodeAtPoint(nodeBuilderType, null, { label, description, config });
    }
    setShowNodeBuilder(false);
    setNodeBuilderError(null);
  }, [addNodeAtPoint, editingNodeId, nodeBuilderConfigText, nodeBuilderDescription, nodeBuilderLabel, nodeBuilderMode, nodeBuilderType]);

  const handlePaletteDragStart = (event: React.DragEvent, type: WorkflowNodeType) => {
    event.dataTransfer.setData("application/x-sanket-node-type", type);
    event.dataTransfer.effectAllowed = "copy";
  };

  const handlePortClick = (event: React.MouseEvent, nodeId: string, port: "in" | "out") => {
    event.stopPropagation();
    if (port === "out") {
      activateConnection(nodeId, canvasPointFromPointer(event as unknown as React.PointerEvent));
      return;
    }
    completeConnection(event, nodeId);
  };

  const selectEdge = (event: React.MouseEvent, edgeId: string) => {
    event.stopPropagation();
    setSelectedEdgeId(edgeId);
    setSelectedId(null);
    cancelConnection();
  };

  const removeSelected = useCallback(() => {
    if (selectedEdgeId) {
      setEdges((current) => current.filter((edge) => edge.id !== selectedEdgeId));
      setExecutionMessage("Connection removed.");
      setSelectedEdgeId(null);
      return;
    }
    if (!selectedId) return;
    setNodes((current) => current.filter((node) => node.id !== selectedId));
    setEdges((current) => current.filter((edge) => edge.source !== selectedId && edge.target !== selectedId));
    setSelectedId(null);
    cancelConnection();
    setExecutionMessage("Node removed with its connections.");
  }, [cancelConnection, selectedEdgeId, selectedId]);

  const duplicateSelected = useCallback(() => {
    if (!selectedId) return;
    const source = nodes.find((node) => node.id === selectedId);
    if (!source) return;
    const id = `${source.type.toLowerCase()}-${Date.now()}`;
    const copy: CanvasNode = {
      ...source,
      id,
      x: Math.min(CANVAS_WIDTH - NODE_WIDTH - 16, source.x + 42),
      y: Math.min(CANVAS_HEIGHT - NODE_HEIGHT - 16, source.y + 42),
      label: `${source.label} COPY`,
      status: "idle",
      config: { ...source.config },
    };
    setNodes((current) => [...current, copy]);
    setSelectedId(id);
    setSelectedEdgeId(null);
    setExecutionMessage("Node duplicated. Connect it to the workflow using its output/input pins.");
  }, [nodes, selectedId]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const isField = !!target?.closest("input, textarea, select, [contenteditable=\"true\"]");
      if (event.key === "Escape" && connectingFrom) {
        event.preventDefault();
        cancelConnection("Connection cancelled.");
        return;
      }
      if ((event.key === "Delete" || event.key === "Backspace") && !isField && (selectedId || selectedEdgeId)) {
        event.preventDefault();
        removeSelected();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [cancelConnection, connectingFrom, removeSelected, selectedEdgeId, selectedId]);

  const resetCanvas = () => {
    setNodes(INITIAL_NODES);
    setEdges(INITIAL_EDGES);
    setSelectedId("bridge-1");
    setSelectedEdgeId(null);
    cancelConnection();
    setRunStep(0);
    setNodeOutputs({});
    setExecutionBody(null);
    setExecutionId(null);
    setExecutionStatus("idle");
    setShowResults(false);
    setResultsTab("insights");
    setExecutionMessage("Default workflow restored. Validate it before running.");
  };

  const buildWorkflowPayload = useCallback(() => ({
    workflow_id: "sanket-investigation-workflow",
    version: "1.0.0",
    name: "SANKET Investigation Workflow",
    description: "Investigator-composed analytical workflow",
    failure_policy: "STOP",
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.type,
      label: node.label,
      config: node.config,
      enabled: node.status !== "error",
      position: { x: node.x, y: node.y },
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      source_node_id: edge.source,
      target_node_id: edge.target,
      source_port: "output",
      target_port: "input",
      enabled: true,
    })),
    metadata: { case_id: activeCaseId, client: "sanket-canvas-v1.10.6-c4", investigation_question: aiQuestion.trim() || undefined },
  }), [activeCaseId, edges, nodes]);

  const validateWorkflow = async () => {
    if (executionStatus === "running") return;
    setValidationErrors([]);
    setExecutionMessage("Validating workflow against the active case evidence graph...");
    try {
      const response = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(activeCaseId)}/workflows/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildWorkflowPayload()),
      });
      const body = await response.json();
      const errors = Array.isArray(body?.errors) ? body.errors : [];
      const warnings = Array.isArray(body?.warnings) ? body.warnings : [];
      setValidationErrors(errors);
      setResultsTab("run");
      setShowResults(true);
      if (!response.ok || body?.valid === false) {
        setExecutionMessage(`Validation failed • ${errors.length} error(s).`);
        return;
      }
      setExecutionMessage(`Workflow valid • ${nodes.length} nodes • ${edges.length} connections${warnings.length ? ` • ${warnings.length} warning(s)` : ""}.`);
    } catch (error: any) {
      setExecutionMessage(error?.message || "Unable to reach the workflow validation endpoint.");
    }
  };

  const runWorkflow = async () => {
    if (executionStatus === "running") return;
    setExecutionStatus("running");
    setExecutionMessage("Validating workflow against the live case evidence graph...");
    setValidationErrors([]);
    setNodeOutputs({});
    setRunStep(0);
    const payload = buildWorkflowPayload();
    try {
      const validationResponse = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(activeCaseId)}/workflows/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const validation = await validationResponse.json();
      if (!validationResponse.ok || !validation.valid) {
        setValidationErrors(validation.errors || [{ message: validation.detail || "Workflow validation failed" }]);
        setExecutionStatus("failed");
        setExecutionMessage("Workflow validation failed. Fix the highlighted configuration before running.");
        return;
      }

      setExecutionMessage("Executing deterministic investigation nodes against the evidence graph...");
      const response = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(activeCaseId)}/workflows/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      setExecutionBody(response.ok ? body : null);
      if (!response.ok) {
        const errors = body?.detail?.issues || body?.detail || [{ message: "Execution failed" }];
        setValidationErrors(Array.isArray(errors) ? errors : [{ message: String(errors) }]);
        setExecutionStatus("failed");
        setExecutionMessage("Workflow execution failed. Inspect the execution trace.");
        return;
      }

      const execution = body.execution || {};
      const results = Array.isArray(execution.node_results) ? execution.node_results : [];
      const outputMap: Record<string, any> = {};
      results.forEach((result: any) => { outputMap[result.node_id] = result.output || {}; });
      setNodeOutputs(outputMap);
      setExecutionId(execution.execution_id || null);
      setExecutionStatus(execution.status === "COMPLETED" ? "completed" : "failed");
      setExecutionMessage(
        execution.status === "COMPLETED"
          ? `Execution complete • ${results.length} nodes • ${execution.execution_id || "deterministic run"}`
          : `Execution status: ${execution.status}`
      );
      setRunStep(results.length);
      setSelectedFindingIndex(0);
      setResultsTab("insights");
      setShowResults(true);
      persistExecutionHistory(body);
      setNodes((current) => current.map((node) => {
        const result = results.find((item: any) => item.node_id === node.id);
        return result?.status === "FAILED" ? { ...node, status: "error" } : { ...node, status: node.id === selectedId ? "selected" : "ready" };
      }));
    } catch (error: any) {
      setExecutionStatus("failed");
      setExecutionMessage(error?.message || "Unable to reach investigation backend.");
    }
  };

  const openFindingNode = useCallback((index: number) => {
    const finding = workflowFindings[index];
    if (!finding) return;
    setSelectedFindingIndex(index);
    setSelectedId(finding.workflowNodeId);
    setSelectedEdgeId(null);
    setShowNodeInspector(true);
  }, [workflowFindings]);

  const openFindingInNetwork = useCallback((finding: (typeof workflowFindings)[number]) => {
    setSelectedFindingIndex(Math.max(0, workflowFindings.findIndex((item) => item.id === finding.id)));
    if (finding.entityId) {
      const normalizedTitle = finding.title.trim().toLowerCase();
      const match = crossDocIntelligence?.reconciled_entities?.find((entity) => entity.canonical_name.trim().toLowerCase() === normalizedTitle);
      if (match) setSelectedEntity(match);
    }
    setViewMode("network");
  }, [crossDocIntelligence?.reconciled_entities, setSelectedEntity, setViewMode, workflowFindings]);

  const restoreHistoryEntry = useCallback((entry: any) => {
    const body = entry?.body;
    if (!body?.execution) return;
    const results = Array.isArray(body.execution.node_results) ? body.execution.node_results : [];
    const outputMap: Record<string, any> = {};
    results.forEach((result: any) => { outputMap[result.node_id] = result.output || {}; });
    setExecutionBody(body);
    setExecutionId(body.execution.execution_id || null);
    setExecutionStatus(body.execution.status === "COMPLETED" ? "completed" : "failed");
    setNodeOutputs(outputMap);
    setRunStep(results.length);
    setResultsTab("insights");
    setShowResults(true);
    setExecutionMessage(`Loaded saved result • ${body.execution.execution_id || entry.execution_id}`);
  }, []);


  return (
    <div className="flex-1 overflow-hidden bg-white text-slate-900">
      <div className="h-full flex flex-col sanket-workflow-shell">
        <div className="min-h-12 shrink-0 px-5 py-2 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-2 sanket-workflow-toolbar">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-teal-700 font-mono text-xs tracking-wider">
              <Sparkles className="w-4 h-4" />
              INVESTIGATION CANVAS
            </div>
            <span className="text-[9px] font-mono uppercase tracking-[0.25em] text-slate-500">
              workflow layer // evidence graph underneath
            </span>
            <span className="px-2 py-1 rounded bg-emerald-700/10 border border-emerald-700/25 text-[9px] font-mono text-emerald-700">
              VALIDATED WORKFLOW MODEL
            </span>
          </div>

          <div className="flex items-center gap-2 sanket-workflow-toolbar-actions">
            <button
              onClick={() => setShowAiPlanner(true)} title="Ask the AI planner to build a validated investigation workflow"
              className="h-8 px-3 rounded-md bg-teal-50 border border-teal-200 text-teal-800 hover:bg-teal-100 text-[10px] font-mono flex items-center gap-2"
            >
              <Sparkles className="w-3.5 h-3.5" /> AI PLAN
            </button>
            <button
              onClick={() => openCreateNodeBuilder()} title="Create a custom-named executable node from an allow-listed operation"
              className="h-8 px-3 rounded-md bg-white border border-slate-300 text-slate-700 hover:border-teal-600 hover:text-teal-800 text-[10px] font-mono flex items-center gap-2"
            >
              <PlusSquare className="w-3.5 h-3.5" /> CUSTOM NODE
            </button>
            <button
              onClick={saveWorkflow} title="Save this workflow locally for the active case"
              className="h-8 px-3 rounded-md bg-white border border-slate-300 text-slate-700 hover:border-teal-600 text-[10px] font-mono flex items-center gap-2"
            >
              <Save className="w-3.5 h-3.5" /> SAVE
            </button>
            <button
              onClick={loadWorkflow} title="Restore the saved workflow for the active case"
              className="h-8 px-3 rounded-md bg-white border border-slate-300 text-slate-700 hover:border-teal-600 text-[10px] font-mono flex items-center gap-2"
            >
              <Upload className="w-3.5 h-3.5" /> LOAD
            </button>
            <button
              onClick={validateWorkflow} title="Validate this workflow without executing it" disabled={executionStatus === "running"}
              className="h-8 px-3 rounded-md bg-white border border-slate-300 text-slate-700 hover:border-teal-600 hover:text-teal-800 disabled:opacity-30 text-[10px] font-mono flex items-center gap-2"
            >
              <Check className="w-3.5 h-3.5" /> VALIDATE
            </button>
            <button
              onClick={resetCanvas} title="Restore the default investigation workflow"
              className="h-8 px-3 rounded-md bg-[#FFFFFF] border border-slate-300 text-slate-700 hover:text-slate-900 hover:border-slate-400 text-[10px] font-mono flex items-center gap-2"
            >
              <RotateCcw className="w-3.5 h-3.5" /> RESET
            </button>
            <button
              onClick={duplicateSelected} title="Duplicate the selected workflow node without copying its connections"
              disabled={!selectedId}
              className="h-8 px-3 rounded-md bg-white border border-slate-300 text-slate-700 hover:border-teal-600 disabled:opacity-30 text-[10px] font-mono flex items-center gap-2"
            >
              <Plus className="w-3.5 h-3.5" /> DUPLICATE
            </button>
            <button
              onClick={removeSelected} title={selectedEdgeId ? "Delete the selected workflow connection" : "Delete the selected workflow node and its connections"}
              disabled={!selectedId && !selectedEdgeId}
              className="h-8 px-3 rounded-md bg-white border border-slate-300 text-slate-700 hover:text-rose-700 hover:border-rose-300 disabled:opacity-30 text-[10px] font-mono flex items-center gap-2"
            >
              <Trash2 className="w-3.5 h-3.5" /> {selectedEdgeId ? "DELETE CONNECTION" : "DELETE"}
            </button>
            <button
              onClick={() => { setResultsTab("insights"); setShowResults((value) => !value); }}
              title={showResults ? "Hide workflow results" : "Show workflow results and findings"}
              className={`h-8 px-3 rounded-md border text-[10px] font-mono flex items-center gap-2 ${showResults ? "bg-teal-50 border-teal-200 text-teal-800" : "bg-white border-slate-300 text-slate-700 hover:border-teal-600 hover:text-teal-800"}`}
            >
              <ListChecks className="w-3.5 h-3.5" /> RESULTS{workflowFindings.length > 0 ? ` · ${workflowFindings.length}` : ""}
            </button>
            <button
              onClick={exportInvestigationReport} title="Export the latest deterministic investigation report" disabled={!executionBody?.report?.markdown}
              className="h-8 px-3 rounded-md bg-white border border-slate-300 text-slate-700 hover:text-teal-800 hover:border-teal-600 disabled:opacity-40 text-[10px] font-mono flex items-center gap-2"
            >
              <Download className="w-3.5 h-3.5" /> REPORT
            </button>
            <button
              onClick={runWorkflow} title="Validate and execute this workflow against the active case"
              disabled={executionStatus === "running"}
              className="h-8 px-3 rounded-md bg-teal-700/10 border border-teal-700/30 text-teal-700 hover:bg-teal-700/15 disabled:opacity-50 text-[10px] font-mono flex items-center gap-2"
            >
              <Play className="w-3.5 h-3.5" /> {executionStatus === "running" ? `RUNNING ${runStep}/${nodes.length}` : "RUN WORKFLOW"}
            </button>
          </div>
          {savedAt && <div className="text-[8px] font-mono text-slate-500 w-full text-right -mt-1">Saved {new Date(savedAt).toLocaleTimeString()}</div>}
        </div>

        <div className="flex-1 min-h-0 flex">
          {showPalette && (
            <aside className="w-[245px] shrink-0 border-r border-slate-200 bg-[#FBFCFD] flex flex-col sanket-workflow-palette">
              <div className="px-4 py-3 border-b border-slate-200">
                <div className="text-[10px] font-mono tracking-[0.18em] text-slate-500 mb-2">ANALYSIS NODES</div>
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search node types..."
                    className="w-full h-8 pl-9 pr-3 rounded-md bg-[#FFFFFF] border border-slate-300 text-[11px] text-slate-800 placeholder:text-slate-400 outline-none focus:border-teal-600"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => openCreateNodeBuilder()}
                  className="mt-2 w-full h-8 rounded-md border border-teal-200 bg-teal-50 text-teal-800 hover:bg-teal-100 text-[9px] font-mono flex items-center justify-center gap-2"
                  title="Create a custom-named executable workflow node using an allow-listed investigation operation"
                >
                  <PlusSquare className="w-3.5 h-3.5" /> CREATE CUSTOM NODE
                </button>
              </div>

              <div className="p-3 space-y-2 overflow-y-auto">
                {filteredLibrary.map(([type, meta]) => {
                  const Icon = meta.icon;
                  return (
                    <button
                      key={type}
                      draggable
                      onDragStart={(event) => handlePaletteDragStart(event, type)}
                      onClick={() => addNode(type)} title={`${meta.description} Drag this node onto the canvas or click to add it.`}
                      className="w-full group rounded-lg border border-slate-200 bg-[#FFFFFF] hover:bg-[#F2F5F7] hover:border-slate-300 px-3 py-2.5 text-left transition"
                    >
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-md flex items-center justify-center border" style={{ borderColor: `${meta.color}55`, background: `${meta.color}12`, color: meta.color }}>
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="text-[10px] font-mono font-semibold text-slate-800 truncate">{meta.title}</div>
                          <div className="text-[8px] font-mono text-slate-500 mt-0.5 truncate">{meta.short} // {type}</div>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-slate-600 group-hover:text-teal-600" />
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-auto px-4 py-3 border-t border-slate-200 text-[9px] font-mono leading-relaxed text-slate-500">
                Drag nodes to reposition.<br />
                Drag from ● output to ● input to connect.<br />
                Click a connection to select it; Delete removes it.<br />
                The canvas edits the validated workflow model directly.
              </div>
            </aside>
          )}

          <div className="flex-1 min-w-0 flex flex-col">
            <div
              ref={canvasViewportRef}
              className="relative flex-1 overflow-auto bg-[radial-gradient(circle_at_center,rgba(15,118,110,0.045),transparent_58%)] sanket-workflow-canvas-viewport"
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerLeave={handlePointerUp}
              onDragOver={(event) => event.preventDefault()}
              onDrop={addDraggedPaletteNode}
            >
              <div className="sticky top-3 left-3 z-20 inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white/95 backdrop-blur px-3 py-2 text-[9px] font-mono text-slate-600 shadow-sm">
                <Grip className="w-3.5 h-3.5 text-teal-600" />
                CASE // LIVE ANALYTICAL WORKSPACE
              </div>
              {connectingFrom && (
                <div className="sticky top-3 left-1/2 -translate-x-1/2 z-30 inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1.5 text-[9px] font-mono text-teal-800 shadow-sm">
                  <Link2 className="w-3.5 h-3.5" />
                  DRAG TO AN INPUT PIN
                  <button type="button" onClick={() => cancelConnection("Connection cancelled.")} className="ml-1 text-teal-700 hover:text-slate-900" title="Cancel connection">×</button>
                </div>
              )}

              <div className="sticky top-3 right-3 z-30 ml-auto w-fit flex items-center gap-1 rounded-lg border border-slate-200 bg-white/95 px-1.5 py-1.5 shadow-sm">
                <button type="button" onClick={() => setManualZoom(zoom - 0.1)} className="w-7 h-7 rounded-md text-slate-600 hover:bg-slate-100 flex items-center justify-center" title="Zoom out"><ZoomOut className="w-3.5 h-3.5" /></button>
                <span className="w-12 text-center text-[9px] font-mono text-slate-600">{Math.round(zoom * 100)}%</span>
                <button type="button" onClick={() => setManualZoom(zoom + 0.1)} className="w-7 h-7 rounded-md text-slate-600 hover:bg-slate-100 flex items-center justify-center" title="Zoom in"><ZoomIn className="w-3.5 h-3.5" /></button>
                <button type="button" onClick={() => { setZoomMode("fit"); fitCanvas(); }} className="h-7 px-2 rounded-md border border-slate-200 text-[8px] font-mono text-slate-600 hover:border-teal-300 hover:text-teal-800 flex items-center gap-1" title="Fit the workflow to the available viewport"><Maximize2 className="w-3 h-3" /> FIT</button>
              </div>

              <div
                className="relative my-3 ml-4 sanket-workflow-stage-wrap"
                style={{ width: CANVAS_WIDTH * zoom, height: CANVAS_HEIGHT * zoom }}
                onPointerDown={(event) => {
                  if (event.target === event.currentTarget) {
                    setSelectedId(null);
                    setSelectedEdgeId(null);
                  }
                }}
              >
                <div
                ref={canvasRef}
                className="relative sanket-workflow-world"
                style={{ width: CANVAS_WIDTH, height: CANVAS_HEIGHT, transform: `scale(${zoom})`, transformOrigin: "top left" }}
                onPointerDown={(event) => {
                  if (event.target === event.currentTarget) {
                    setSelectedId(null);
                    setSelectedEdgeId(null);
                  }
                }}
              >
                <div
                  className="absolute inset-0 opacity-70"
                  style={{
                    backgroundImage:
                      "linear-gradient(rgba(100,116,139,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(100,116,139,0.08) 1px, transparent 1px)",
                    backgroundSize: "26px 26px",
                  }}
                />

                <svg className="absolute inset-0 w-full h-full overflow-visible pointer-events-none">
                  <defs>
                    <linearGradient id="flow-gradient" x1="0%" x2="100%">
                      <stop offset="0%" stopColor="#0F766E" stopOpacity="0.6" />
                      <stop offset="100%" stopColor="#6D5AA8" stopOpacity="0.55" />
                    </linearGradient>
                    <marker id="workflow-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
                      <path d="M 0 0 L 8 4 L 0 8 z" fill="#0F766E" />
                    </marker>
                  </defs>
                  {edges.map((edge) => {
                    const source = nodes.find((node) => node.id === edge.source);
                    const target = nodes.find((node) => node.id === edge.target);
                    if (!source || !target) return null;
                    return (
                      <path
                        key={edge.id}
                        d={curvePath(source, target)}
                        stroke={selectedEdgeId === edge.id ? "#0F766E" : "url(#flow-gradient)"}
                        strokeWidth={selectedEdgeId === edge.id ? 3 : 2}
                        fill="none"
                        opacity={selectedEdgeId === edge.id || selectedId === edge.source || selectedId === edge.target ? 0.95 : 0.58}
                        pointerEvents="stroke"
                        markerEnd="url(#workflow-arrow)"
                        className="cursor-pointer"
                        onClick={(event) => selectEdge(event, edge.id)}
                      />
                    );
                  })}
                  {connectingFrom && connectionCursor && (() => {
                    const source = nodes.find((node) => node.id === connectingFrom);
                    if (!source) return null;
                    const a = nodePortPoint(source, "out");
                    const b = connectionCursor;
                    const dx = Math.max(48, Math.abs(b.x - a.x) * 0.45);
                    return (
                      <path
                        d={`M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`}
                        stroke="#0F766E"
                        strokeWidth="3"
                        strokeDasharray="7 6"
                        fill="none"
                        opacity="0.9"
                      />
                    );
                  })()}
                </svg>

                {nodes.map((node) => {
                  const meta = NODE_META[node.type];
                  const Icon = meta.icon;
                  const selected = selectedId === node.id;
                  const isConnecting = connectingFrom === node.id;
                  return (
                    <div
                      key={node.id}
                      className={`absolute select-none rounded-xl border bg-[#FFFFFF] backdrop-blur-md shadow-md transition-[box-shadow,border-color] duration-150 ${
                        selected
                          ? "border-teal-700/50 shadow-[0_10px_26px_rgba(15,118,110,0.10)]"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                      style={{ left: node.x, top: node.y, width: NODE_WIDTH, height: NODE_HEIGHT }}
                      onPointerDown={(event) => startDrag(event, node)}
                      onClick={() => { setSelectedId(node.id); setSelectedEdgeId(null); }}
                    >
                      <button
                        aria-label="Connect output" title="Start a connection from this node to another node"
                        onPointerDown={(event) => beginConnectionDrag(event, node.id)}
                        onClick={(event) => handlePortClick(event as React.MouseEvent, node.id, "out")}
                        data-workflow-output="true"
                        className={`absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full border-2 flex items-center justify-center z-10 transition cursor-crosshair ${
                          isConnecting ? "bg-teal-700 border-teal-700 text-white scale-110" : "bg-white border-slate-500 text-teal-700 hover:border-teal-600 hover:scale-110"
                        }`}
                      >
                        <ArrowUpFromLine className="w-2.5 h-2.5 rotate-90" />
                      </button>
                      <button
                        aria-label="Connect input" title="Connect an upstream node to this input"
                        onPointerUp={(event) => completeConnection(event, node.id)}
                        onClick={(event) => handlePortClick(event, node.id, "in")}
                        data-workflow-input="true"
                        className={`absolute -left-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-white border-2 text-slate-400 hover:border-teal-600 hover:text-teal-700 flex items-center justify-center z-10 transition cursor-crosshair ${connectingFrom && connectingFrom !== node.id ? "border-teal-500 ring-4 ring-teal-100" : "border-slate-500"}`}
                      >
                        <ArrowDownToLine className="w-2.5 h-2.5 rotate-90" />
                      </button>

                      <div className="px-3 pt-3">
                        <div className="flex items-start gap-2.5">
                          <div className="w-8 h-8 rounded-lg border flex items-center justify-center shrink-0" style={{ borderColor: `${meta.color}55`, background: `${meta.color}10`, color: meta.color }}>
                            <Icon className="w-4 h-4" />
                          </div>
                          <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                              <span className="text-[8px] font-mono tracking-[0.18em] text-slate-500">{meta.short}</span>
                              {(node.label !== meta.title.toUpperCase() || node.description !== meta.description) && <span className="text-[8px] text-teal-700 font-mono">CUSTOM</span>}
                              {node.status === "ready" && <span className="text-[8px] text-emerald-700 font-mono">READY</span>}
                              {node.status === "selected" && <span className="text-[8px] text-teal-700 font-mono">ACTIVE</span>}
                            </div>
                            <div className="text-[11px] font-semibold text-slate-900 truncate mt-0.5">{node.label}</div>
                          </div>
                        </div>
                        <p className="text-[8px] leading-relaxed text-slate-500 mt-2 line-clamp-2">{node.description}</p>
                      </div>

                      <div className="absolute bottom-0 left-0 right-0 h-5 px-3 border-t border-slate-200 flex items-center justify-between text-[8px] font-mono text-slate-500">
                        <span>{node.id}</span>
                        <span className="truncate max-w-[90px]">{Object.keys(node.config).length} params</span>
                      </div>
                    </div>
                  );
                })}
                </div>
              </div>
            </div>

            <div className={`sanket-workflow-results ${showResults ? "is-open" : "is-collapsed"}`}>
              <div className="sanket-workflow-results__header">
                <div className="sanket-workflow-results__title">
                  <div className="flex items-center gap-2">
                    <ListChecks className="w-4 h-4 text-teal-700" />
                    <span>WORKFLOW RESULTS</span>
                    <span className={`sanket-workflow-status-pill sanket-workflow-status-pill--${executionStatus}`}>{executionStatus.toUpperCase()}</span>
                  </div>
                  <span className="sanket-workflow-results__sub">What the workflow discovered, how it was supported, and what remains for investigator review.</span>
                </div>
                <div className="sanket-workflow-results__actions">
                  {executionId && <span className="sanket-workflow-execution-id" title="Deterministic execution identifier">{executionId}</span>}
                  <button type="button" onClick={() => setShowNodeInspector((value) => !value)} className="sanket-workflow-results-icon-btn" title={showNodeInspector ? "Hide node inspector" : "Show node inspector"}>
                    <PanelRight className="w-3.5 h-3.5" />
                  </button>
                  <button type="button" onClick={() => setShowResults((value) => !value)} className="sanket-workflow-results-icon-btn" title={showResults ? "Collapse workflow results" : "Expand workflow results"}>
                    {showResults ? <ArrowDownToLine className="w-3.5 h-3.5" /> : <ArrowUpFromLine className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {showResults && (
                <div className="sanket-workflow-results__body">
                  <div className="sanket-workflow-results__main">
                    <div className="sanket-workflow-results__tabs" role="tablist" aria-label="Workflow results views">
                      {([
                        ["insights", "INSIGHTS"],
                        ["evidence", "EVIDENCE"],
                        ["run", "RUN"],
                        ["report", "REPORT"],
                      ] as const).map(([tab, label]) => (
                        <button key={tab} type="button" role="tab" aria-selected={resultsTab === tab} onClick={() => setResultsTab(tab)} className={resultsTab === tab ? "is-active" : ""}>{label}</button>
                      ))}
                    </div>

                    {resultsTab === "insights" && (
                      <div className="sanket-workflow-results__scroll">
                        {executionStatus === "idle" ? (
                          <div className="sanket-workflow-empty-results">
                            <Target className="w-5 h-5 text-teal-700" />
                            <div>
                              <strong>Run the investigation to produce findings.</strong>
                              <p>Each executable node contributes structured output. SANKET turns those outputs into leads, evidence references and a reproducible report.</p>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="sanket-workflow-result-metrics">
                              <div><span>LEADS</span><strong>{workflowFindings.length}</strong><small>bridge · key · anomaly</small></div>
                              <div><span>EVIDENCE LINKS</span><strong>{evidenceReferences.length || Number(provenanceSummary.total_items || 0)}</strong><small>traceable references</small></div>
                              <div><span>CONTRADICTIONS</span><strong>{Number(evidenceReview?.contradictions?.contradiction_count || 0)}</strong><small>remain visible for review</small></div>
                              <div><span>GRAPH</span><strong>{Number(executionSummary.entity_count || 0)}</strong><small>{Number(executionSummary.edge_count || 0)} relationships / edges</small></div>
                            </div>

                            {workflowFindings.length > 0 ? (
                              <div className="sanket-workflow-finding-list">
                                {workflowFindings.slice(0, 12).map((finding, index) => {
                                  const active = selectedFindingIndex === index;
                                  const score = Number.isFinite(Number(finding.score)) ? Math.round(Number(finding.score) * 100) : null;
                                  return (
                                    <button key={`${finding.id}-${index}`} type="button" onClick={() => openFindingNode(index)} className={`sanket-workflow-finding-card ${active ? "is-active" : ""}`}>
                                      <div className="sanket-workflow-finding-card__rail" data-kind={finding.kind} />
                                      <div className="min-w-0 flex-1">
                                        <div className="flex items-center gap-2 min-w-0">
                                          <span className="sanket-workflow-finding-card__kind">{finding.kind.toUpperCase()}</span>
                                          {finding.severity && <span className="sanket-workflow-finding-card__severity">{finding.severity}</span>}
                                          {finding.status && <span className="sanket-workflow-finding-card__status">{finding.status}</span>}
                                        </div>
                                        <strong>{finding.title}</strong>
                                        <p>{finding.explanation || finding.reasons?.join(" · ") || "Deterministic analytical lead surfaced by the selected workflow."}</p>
                                        <span className="sanket-workflow-finding-card__refs">{finding.relationshipIds.length} relationships · {finding.eventIds.length} events {finding.entityId ? `· ${finding.entityId}` : ""}</span>
                                      </div>
                                      {score !== null && <div className="sanket-workflow-finding-score"><strong>{score}</strong><span>score</span></div>}
                                    </button>
                                  );
                                })}
                              </div>
                            ) : (
                              <div className="sanket-workflow-empty-results is-compact">
                                <Check className="w-5 h-5 text-emerald-700" />
                                <div><strong>No analytical leads returned.</strong><p>The workflow completed, but the selected operations did not produce bridge, key-individual or anomaly findings for this case scope.</p></div>
                              </div>
                            )}

                            {workflowFindings[selectedFindingIndex] && (
                              <div className="sanket-workflow-finding-detail">
                                <div>
                                  <span className="sanket-card__meta">SELECTED FINDING</span>
                                  <h4>{workflowFindings[selectedFindingIndex].title}</h4>
                                  <p>{workflowFindings[selectedFindingIndex].explanation || workflowFindings[selectedFindingIndex].reasons?.join(" · ") || "Analytical lead produced by a deterministic node."}</p>
                                </div>
                                <div className="flex flex-wrap gap-2 mt-3">
                                  <button type="button" onClick={() => openFindingNode(selectedFindingIndex)} className="sanket-workflow-chip-btn"><Target className="w-3 h-3" /> OPEN NODE</button>
                                  {workflowFindings[selectedFindingIndex].entityId && <button type="button" onClick={() => openFindingInNetwork(workflowFindings[selectedFindingIndex])} className="sanket-workflow-chip-btn"><ExternalLink className="w-3 h-3" /> OPEN GRAPH</button>}
                                  {(workflowFindings[selectedFindingIndex].relationshipIds.length || workflowFindings[selectedFindingIndex].eventIds.length) > 0 && <button type="button" onClick={() => { setResultsTab("evidence"); setShowResults(true); }} className="sanket-workflow-chip-btn"><FileSearch className="w-3 h-3" /> VIEW EVIDENCE</button>}
                                </div>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}

                    {resultsTab === "evidence" && (
                      <div className="sanket-workflow-results__scroll">
                        <div className="sanket-workflow-result-metrics">
                          <div><span>PROVENANCE</span><strong>{Number(provenanceSummary.total_items || 0)}</strong><small>case-wide trace items</small></div>
                          <div><span>FIELD ITEMS</span><strong>{Number(provenanceSummary.field_items || 0)}</strong><small>source observations</small></div>
                          <div><span>FINDING ITEMS</span><strong>{Number(provenanceSummary.finding_items || 0)}</strong><small>linked analytical leads</small></div>
                          <div><span>CONFLICTS</span><strong>{Number(evidenceReview?.contradictions?.contradiction_count || 0)}</strong><small>not silently reconciled</small></div>
                        </div>
                        <div className="sanket-workflow-evidence-grid">
                          <div className="sanket-workflow-evidence-section">
                            <div className="sanket-card__meta">CONTRADICTIONS</div>
                            {contradictionItems.length ? contradictionItems.slice(0, 8).map((item: any, index: number) => (
                              <div className="sanket-workflow-evidence-row is-conflict" key={index}>
                                <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                                <div><strong>{String(item.code || item.type || "FIELD CONFLICT")}</strong><p>{String(item.message || item.description || item.detail || "Conflicting source observations remain open.")}</p></div>
                              </div>
                            )) : <div className="sanket-workflow-empty-inline">No contradictions were returned by the evidence review layer.</div>}
                          </div>
                          <div className="sanket-workflow-evidence-section">
                            <div className="flex items-center justify-between gap-2"><div className="sanket-card__meta">LATEST EVIDENCE LINKS</div><span className="text-[8px] font-mono text-slate-500">{evidenceReferences.length} refs</span></div>
                            {evidenceReferences.length ? evidenceReferences.slice(0, 10).map((item: any, index: number) => (
                              <div className="sanket-workflow-evidence-row" key={index}>
                                <FileSearch className="w-3.5 h-3.5 text-teal-700 shrink-0" />
                                <div><strong>{String(item.reference?.filename || item.object_id || "Evidence object")}</strong><p>Page {item.reference?.page ?? "—"} · {String(item.reference?.text_span || item.object_type || "source-linked evidence").slice(0, 140)}</p></div>
                              </div>
                            )) : <div className="sanket-workflow-empty-inline">Connect an Evidence Review node to inspect source references from the run.</div>}
                          </div>
                        </div>
                        <div className="sanket-workflow-evidence-actions">
                          <button type="button" onClick={() => setViewMode("evidence")} className="sanket-workflow-chip-btn"><FileSearch className="w-3 h-3" /> OPEN EVIDENCE REVIEW</button>
                          <button type="button" onClick={() => setViewMode("table")} className="sanket-workflow-chip-btn"><ListChecks className="w-3 h-3" /> OPEN LEDGER</button>
                        </div>
                      </div>
                    )}

                    {resultsTab === "run" && (
                      <div className="sanket-workflow-results__scroll">
                        <div className="sanket-workflow-run-header">
                          <div><span className="sanket-card__meta">EXECUTION</span><strong>{executionId || "Not run"}</strong><p>{executionMessage}</p></div>
                          <div className={`sanket-workflow-status-pill sanket-workflow-status-pill--${executionStatus}`}>{executionStatus.toUpperCase()}</div>
                        </div>
                        <div className="sanket-workflow-trace-list">
                          {nodes.map((node, index) => {
                            const result = Array.isArray(executionBody?.execution?.node_results) ? executionBody.execution.node_results.find((item: any) => item.node_id === node.id) : null;
                            const status = result?.status || (executionStatus === "idle" ? "QUEUED" : "NOT_RUN");
                            return (
                              <button type="button" key={node.id} onClick={() => { setSelectedId(node.id); setSelectedEdgeId(null); setShowNodeInspector(true); }} className={`sanket-workflow-trace-row ${result?.status === "FAILED" ? "is-failed" : status === "COMPLETED" ? "is-done" : ""}`}>
                                <span>{String(index + 1).padStart(2, "0")}</span><strong>{NODE_META[node.type].short}</strong><em>{status}</em><small>{result?.issues?.length ? `${result.issues.length} issue(s)` : `${Object.keys(result?.output || {}).length} output fields`}</small>
                              </button>
                            );
                          })}
                        </div>
                        {validationErrors.length > 0 && <div className="sanket-workflow-validation-list">{validationErrors.map((issue: any, index: number) => <div key={index}><AlertTriangle className="w-3 h-3" /> {issue.code ? `${issue.code}: ` : ""}{issue.message || String(issue)}</div>)}</div>}
                        <div className="sanket-workflow-history">
                          <div className="sanket-card__meta">RECENT LOCAL EXECUTIONS</div>
                          {executionHistory.length ? executionHistory.map((entry: any) => (
                            <button type="button" key={entry.execution_id} onClick={() => restoreHistoryEntry(entry)} className="sanket-workflow-history-row">
                              <Clock3 className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                              <div><strong>{entry.execution_id}</strong><span>{new Date(entry.created_at).toLocaleString()} · {entry.node_count} nodes · {entry.finding_count} leads</span></div>
                              <span>{String(entry.status).toUpperCase()}</span>
                            </button>
                          )) : <div className="sanket-workflow-empty-inline">No previous runs are saved in this browser for this case.</div>}
                        </div>
                      </div>
                    )}

                    {resultsTab === "report" && (
                      <div className="sanket-workflow-results__scroll">
                        {executionBody?.report?.markdown ? (
                          <>
                            <div className="sanket-workflow-report-toolbar">
                              <div><span className="sanket-card__meta">DETERMINISTIC INVESTIGATION REPORT</span><strong>{executionBody.report.title || "Investigation Report"}</strong><p>{executionBody.report.summary?.finding_count ?? workflowFindings.length} findings · {executionBody.report.provenance_count ?? Number(provenanceSummary.total_items || 0)} provenance items · {executionBody.report.contradiction_count ?? Number(evidenceReview?.contradictions?.contradiction_count || 0)} contradictions</p></div>
                              <button type="button" onClick={exportInvestigationReport} className="sanket-workflow-chip-btn"><Download className="w-3 h-3" /> EXPORT MARKDOWN</button>
                            </div>
                            <pre className="sanket-workflow-report-preview">{String(executionBody.report.markdown)}</pre>
                          </>
                        ) : (
                          <div className="sanket-workflow-empty-results"><FileSearch className="w-5 h-5 text-teal-700" /><div><strong>No report generated yet.</strong><p>Run a workflow with a REPORT node to generate the deterministic report and make it exportable.</p></div></div>
                        )}
                      </div>
                    )}
                  </div>

                  {showNodeInspector && (
                    <div className="sanket-workflow-results__inspector">
                      {selectedEdgeId && (() => {
                        const selectedEdge = edges.find((edge) => edge.id === selectedEdgeId);
                        const source = selectedEdge ? nodes.find((node) => node.id === selectedEdge.source) : null;
                        const target = selectedEdge ? nodes.find((node) => node.id === selectedEdge.target) : null;
                        if (!selectedEdge) return null;
                        return (
                          <div className="mb-3 rounded-lg border border-teal-200 bg-teal-50/70 p-3">
                            <div className="flex items-center justify-between gap-2"><div className="text-[8px] font-mono tracking-[0.16em] text-teal-800">SELECTED CONNECTION</div><button type="button" onClick={removeSelected} className="text-[8px] font-mono text-rose-700 hover:underline">DELETE</button></div>
                            <div className="mt-2 text-[10px] font-semibold text-slate-900">{source?.label || selectedEdge.source} <span className="text-teal-700">→</span> {target?.label || selectedEdge.target}</div>
                            <div className="mt-1 text-[8px] font-mono text-slate-500">{selectedEdge.id} · output → input</div>
                          </div>
                        );
                      })()}
                      <div className="flex items-center justify-between gap-2 mb-3"><div className="text-[10px] font-mono tracking-[0.18em] text-slate-500">NODE INSPECTOR</div>{selectedNode && <button type="button" onClick={() => openEditNodeBuilder(selectedNode)} className="sanket-workflow-inspector-edit"><Edit3 className="w-3 h-3" /> EDIT</button>}</div>
                      {selectedNode ? (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg border flex items-center justify-center" style={{ borderColor: `${NODE_META[selectedNode.type].color}55`, color: NODE_META[selectedNode.type].color, background: `${NODE_META[selectedNode.type].color}10` }}>{React.createElement(NODE_META[selectedNode.type].icon, { className: "w-4 h-4" })}</div><div className="min-w-0"><div className="text-xs font-semibold text-slate-900 truncate">{selectedNode.label}</div><div className="text-[8px] font-mono text-slate-500">{selectedNode.type}</div></div></div>
                          <div className="rounded-lg bg-[#FBFCFD] border border-slate-200 p-3">
                            <div className="text-[8px] uppercase tracking-wider font-mono text-slate-500 mb-2">Execution output</div>
                            {nodeOutputs[selectedNode.id] ? <pre className="sanket-workflow-inspector-output">{JSON.stringify(nodeOutputs[selectedNode.id], null, 2)}</pre> : <div className="text-[9px] font-mono text-slate-500">No output for this node in the current run.</div>}
                          </div>
                          <div className="rounded-lg bg-[#FBFCFD] border border-slate-200 p-3">
                            <div className="text-[8px] uppercase tracking-wider font-mono text-slate-500 mb-2">Configuration</div>
                            {Object.keys(selectedNode.config).length ? Object.entries(selectedNode.config).map(([key, value]) => <div key={key} className="flex items-center justify-between gap-3 py-1 text-[9px] font-mono"><span className="text-slate-500 truncate">{key}</span><span className="text-slate-800 truncate">{String(value)}</span></div>) : <div className="text-[9px] font-mono text-slate-500">No parameters configured.</div>}
                          </div>
                          <div className="flex items-center gap-2">
                            <button onClick={() => activateConnection(selectedNode.id)} title="Start a connection from this node to another node" className="flex-1 h-7 rounded-md bg-white border border-slate-300 hover:border-teal-600 text-[9px] font-mono text-slate-700 flex items-center justify-center gap-2"><Link2 className="w-3.5 h-3.5" /> START CONNECTION</button>
                            <button onClick={duplicateSelected} disabled={!selectedId} title="Duplicate selected node" className="h-7 px-2 rounded-md bg-white border border-slate-300 disabled:opacity-30 text-[9px] font-mono text-slate-700"><Plus className="w-3 h-3" /></button>
                            <button onClick={removeSelected} title="Remove selected node" className="h-7 w-8 rounded-md bg-rose-50 border border-rose-200 text-rose-700 flex items-center justify-center"><Trash2 className="w-3 h-3" /></button>
                          </div>
                        </div>
                      ) : <div className="text-[9px] font-mono text-slate-500">Select a node or connection to inspect it.</div>}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="absolute top-[76px] right-3 z-30 flex flex-col gap-2 sanket-workflow-floating-tools">
            <button onClick={() => setShowPalette((value) => !value)} title={showPalette ? "Hide the workflow node library" : "Show the workflow node library"} className="w-9 h-9 rounded-lg bg-[#FFFFFF]/95 border border-slate-200 backdrop-blur flex items-center justify-center text-slate-500 hover:text-teal-700">
              {showPalette ? <ArrowUpFromLine className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            </button>
            <div className="rounded-lg border border-slate-200 bg-[#FFFFFF]/95 backdrop-blur px-2.5 py-2 text-[8px] font-mono text-slate-500 space-y-1.5 shadow-sm">
              <div className="flex items-center gap-2"><Zap className="w-3 h-3 text-teal-600" /> SCOPED EXECUTION</div>
              <div className="flex items-center gap-2"><ShieldCheck className="w-3 h-3 text-emerald-700" /> EVIDENCE TRACE</div>
              <div className="flex items-center gap-2"><Check className="w-3 h-3 text-amber-700" /> REPRODUCIBLE FLOW</div>
            </div>
          </div>
        </div>
      </div>

      {showNodeBuilder && (
        <div className="fixed inset-0 z-[95] bg-slate-950/20 backdrop-blur-[2px] flex items-center justify-center p-6" role="dialog" aria-modal="true" aria-label="Custom workflow node builder">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 text-teal-800 text-xs font-semibold"><PlusSquare className="w-4 h-4" /> {nodeBuilderMode === "edit" ? "Edit workflow node" : "Create custom workflow node"}</div>
                <p className="mt-1 text-[10px] text-slate-500">Custom labels and descriptions sit on top of an allow-listed deterministic operation, so the node remains executable and auditable.</p>
              </div>
              <button type="button" onClick={() => setShowNodeBuilder(false)} className="w-8 h-8 rounded-md border border-slate-200 text-slate-500 hover:text-slate-900 flex items-center justify-center" title="Close node builder"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-5 grid gap-4">
              <div className="grid grid-cols-2 gap-3 sanket-node-builder-grid">
                <label className="block">
                  <span className="text-[9px] font-mono uppercase tracking-[0.14em] text-slate-500">Execution operation</span>
                  <select
                    value={nodeBuilderType}
                    onChange={(event) => { const type = event.target.value as WorkflowNodeType; setNodeBuilderType(type); setNodeBuilderDescription(NODE_META[type].description); setNodeBuilderConfigText(JSON.stringify(WORKFLOW_CONFIG_DEFAULTS[type], null, 2)); setNodeBuilderError(null); }}
                    className="mt-1 w-full h-9 rounded-lg border border-slate-300 bg-white px-3 text-[11px] text-slate-900 outline-none focus:border-teal-600"
                  >
                    {(Object.keys(NODE_META) as WorkflowNodeType[]).map((type) => <option key={type} value={type}>{NODE_META[type].title} · {type}</option>)}
                  </select>
                </label>
                <label className="block">
                  <span className="text-[9px] font-mono uppercase tracking-[0.14em] text-slate-500">Node label</span>
                  <input value={nodeBuilderLabel} onChange={(event) => setNodeBuilderLabel(event.target.value)} className="mt-1 w-full h-9 rounded-lg border border-slate-300 bg-white px-3 text-[11px] text-slate-900 outline-none focus:border-teal-600" placeholder="e.g. CONNECT + BRIDGE DETECTION" />
                </label>
              </div>

              <label className="block">
                <span className="text-[9px] font-mono uppercase tracking-[0.14em] text-slate-500">Description</span>
                <textarea value={nodeBuilderDescription} onChange={(event) => setNodeBuilderDescription(event.target.value)} rows={2} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-[11px] text-slate-900 outline-none focus:border-teal-600 resize-none" />
              </label>

              <label className="block">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[9px] font-mono uppercase tracking-[0.14em] text-slate-500">Configuration JSON</span>
                  <button type="button" onClick={() => setNodeBuilderConfigText(JSON.stringify(WORKFLOW_CONFIG_DEFAULTS[nodeBuilderType], null, 2))} className="text-[9px] font-mono text-teal-700 hover:underline">USE SAFE DEFAULTS</button>
                </div>
                <textarea value={nodeBuilderConfigText} onChange={(event) => setNodeBuilderConfigText(event.target.value)} rows={9} spellCheck={false} className="mt-1 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-[10px] leading-relaxed text-slate-900 outline-none focus:border-teal-600 resize-y" />
              </label>

              <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[9px] text-slate-600 leading-relaxed">
                <strong className="text-slate-800">How custom nodes work:</strong> you choose the analytical primitive, give it the investigator-facing name you want, configure it, then connect it using the input/output pins. A new primitive algorithm requires a backend allow-list addition; this builder never executes arbitrary code.
              </div>

              {nodeBuilderError && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-[10px] text-rose-800">{nodeBuilderError}</div>}

              <div className="flex justify-end gap-2 pt-1">
                <button type="button" onClick={() => setShowNodeBuilder(false)} className="h-9 px-4 rounded-lg border border-slate-300 bg-white text-[10px] font-mono text-slate-700">CANCEL</button>
                <button type="button" onClick={applyNodeBuilder} className="h-9 px-4 rounded-lg bg-teal-700 text-white text-[10px] font-mono">{nodeBuilderMode === "edit" ? "SAVE NODE" : "ADD NODE"}</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showAiPlanner && (
        <div className="fixed inset-0 z-[100] bg-slate-950/20 backdrop-blur-[2px] flex items-center justify-center p-6" role="dialog" aria-modal="true" aria-label="AI investigation planner">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
              <div><div className="flex items-center gap-2 text-teal-800 text-xs font-semibold"><Sparkles className="w-4 h-4" /> AI investigation planner</div><p className="mt-1 text-[10px] text-slate-500">Turn an investigative question into a transparent workflow. The AI does not execute the case analysis.</p></div>
              <button type="button" onClick={() => setShowAiPlanner(false)} className="w-8 h-8 rounded-md border border-slate-200 text-slate-500 hover:text-slate-900 flex items-center justify-center" title="Close planner"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-5 space-y-4">
              <textarea value={aiQuestion} onChange={(e) => setAiQuestion(e.target.value)} rows={4} placeholder="Example: Find possible intermediaries connecting separate communication communities during August." className="w-full rounded-xl border border-slate-300 px-3 py-3 text-sm text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-600 resize-none" />
              <div className="flex flex-wrap gap-2">
                {["Find possible bridge intermediaries", "Check unusual activity in the latest period", "Rank structurally important people"].map((q) => <button key={q} type="button" onClick={() => setAiQuestion(q)} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-[9px] text-slate-600 hover:border-teal-200 hover:text-teal-800">{q}</button>)}
              </div>
              {aiError && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-[10px] text-rose-800">{aiError}</div>}
              {aiPlan && <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2"><div className="flex items-center justify-between"><span className="text-[9px] font-mono tracking-[0.14em] text-slate-500">VALIDATED PLAN</span><span className="text-[9px] font-mono text-slate-500">{aiPlan.planner_model}</span></div><div className="text-[11px] font-medium text-slate-900">{aiPlan.workflow?.name || "AI workflow"}</div><p className="text-[10px] leading-relaxed text-slate-600">{aiPlan.explanation}</p><div className="text-[9px] text-slate-500">{Array.isArray(aiPlan.workflow?.nodes) ? aiPlan.workflow.nodes.length : 0} nodes · {Array.isArray(aiPlan.workflow?.edges) ? aiPlan.workflow.edges.length : 0} connections</div>{aiPlan.warnings?.length ? <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[9px] text-amber-800">{aiPlan.warnings.join(" • ")}</div> : null}</div>}
              <div className="flex justify-end gap-2 pt-1">
                <button type="button" onClick={() => setShowAiPlanner(false)} className="h-9 px-4 rounded-lg border border-slate-300 bg-white text-[10px] font-mono text-slate-700">CANCEL</button>
                {!aiPlan ? <button type="button" onClick={generateAiPlan} disabled={aiLoading || aiQuestion.trim().length < 5} className="h-9 px-4 rounded-lg bg-teal-700 text-white text-[10px] font-mono disabled:opacity-40">{aiLoading ? "PLANNING…" : "GENERATE PLAN"}</button> : <button type="button" onClick={applyAiPlan} className="h-9 px-4 rounded-lg bg-teal-700 text-white text-[10px] font-mono">APPLY TO CANVAS</button>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
