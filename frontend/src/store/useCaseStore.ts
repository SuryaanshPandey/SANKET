import { create } from "zustand";

export type ViewMode = "dossier" | "network" | "investigation" | "geospatial" | "table" | "inspector" | "analytics" | "evidence";

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ExtractedFieldItem {
  id?: string;
  field_name: string;
  field_value: string;
  confidence: number;
  bounding_box?: BoundingBox | null;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  actor_id: string;
  timestamp: string;
  detail: Record<string, any>;
}

export interface DocumentItem {
  document_id: string;
  original_filename: string;
  file_hash_sha256: string;
  storage_path: string;
  preprocessed_storage_path: string;
  doc_type: string;
  overall_confidence: number;
  is_escalated: boolean;
  extracted_data: Record<string, any>;
  field_items: ExtractedFieldItem[];
  validation_flags: Array<Record<string, any>>;
  audit_trail: AuditLogEntry[];
}

export interface EntityOccurrence {
  document_id: string;
  filename: string;
  doc_type: string;
  role: string;
  confidence: number;
}

export interface ReconciledEntity {
  canonical_name: string;
  roles: string[];
  document_count: number;
  documents: string[];
  occurrences: EntityOccurrence[];
}

export interface TimelineEvent {
  raw_date: string;
  normalized_date?: string | null;
  document_id: string;
  filename: string;
  doc_type: string;
  label: string;
  detail: string;
}

export interface CrossReferenceItem {
  identifier_type: string;
  value: string;
  document_count: number;
  documents: string[];
}

export interface FinancialLedgerItem {
  label: string;
  value: number;
  currency: string;
  source_doc: string;
  doc_type: string;
}

export interface DiscrepancyFlag {
  flag_type: string;
  severity: "high" | "medium" | "low";
  documents_involved: string[];
  message: string;
}

export interface GraphContractEntity {
  id: string;
  type: string;
  name: string;
  normalized_name: string;
  role?: string | null;
  attributes?: Record<string, any>;
  confidence: number;
  source?: {
    document_id: string;
    filename: string;
    file_hash_sha256: string;
    page?: number;
    bounding_box?: BoundingBox | null;
    text_span?: string | null;
  };
}

export interface GraphContractEvent {
  id: string;
  type: string;
  title: string;
  source_entity?: string | null;
  target_entity?: string | null;
  timestamp?: string | null;
  timestamp_start?: string | null;
  timestamp_end?: string | null;
  attributes?: Record<string, any>;
  source?: {
    document_id: string;
    filename: string;
    file_hash_sha256: string;
    page?: number;
    bounding_box?: BoundingBox | null;
    text_span?: string | null;
  };
}

export interface GraphContractRelationship {
  id: string;
  source_entity: string;
  target_entity: string;
  relationship_type: string;
  confidence: number;
  evidence?: string | null;
}

export interface CaseGraphContract {
  contract_version: string;
  case_id?: string | null;
  batch_id?: string | null;
  total_documents: number;
  entities: GraphContractEntity[];
  events: GraphContractEvent[];
  relationships: GraphContractRelationship[];
  audit_chain?: Record<string, any>;
}

export interface CrossDocumentIntelligence {
  total_documents: number;
  doc_types: Record<string, number>;
  overall_case_confidence: number;
  reconciled_entities: ReconciledEntity[];
  master_timeline: TimelineEvent[];
  cross_references: CrossReferenceItem[];
  financial_ledger: {
    total_amount: number;
    currency: string;
    item_count: number;
    items: FinancialLedgerItem[];
  };
  discrepancies: DiscrepancyFlag[];
  case_summary: string;
}

export interface DatasetOption {
  key: string;
  name: string;
  category: string;
  description: string;
  count: number;
}

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CaseState {
  activeCaseId: string;
  batchId: string | null;
  caseTitle: string;
  status: "idle" | "loading" | "success" | "error";
  statusMessage: string;
  progressPercentage: number;
  estimatedSecondsRemaining: number;
  timeElapsedSeconds: number;
  currentStageName: string;
  currentStageDetail: string;
  totalDocumentsInBatch: number;
  documents: DocumentItem[];
  activeDocIndex: number;
  crossDocIntelligence: CrossDocumentIntelligence | null;
  graphContract: CaseGraphContract | null;
  viewMode: ViewMode;
  selectedEntity: ReconciledEntity | null;
  searchFilter: string;
  selectedDatasetKey: string;
  availableDatasets: DatasetOption[];

  // Actions
  setViewMode: (mode: ViewMode) => void;
  setActiveDocIndex: (index: number) => void;
  setSelectedEntity: (entity: ReconciledEntity | null) => void;
  setSearchFilter: (query: string) => void;
  setSelectedDatasetKey: (key: string) => void;
  loadCatalog: () => Promise<void>;
  loadSampleCaseBundle: () => Promise<void>;
  loadDiverseDataset: (datasetKey: string) => Promise<void>;
  restoreActiveCase: () => Promise<void>;
  processUploadedFiles: (files: File[]) => Promise<void>;
}

const setInitialLoadingState = (docCount: number, set: any, message: string) => {
  set({
    status: "loading",
    batchId: null,
    statusMessage: message,
    progressPercentage: 1,
    estimatedSecondsRemaining: 0,
    timeElapsedSeconds: 0,
    totalDocumentsInBatch: docCount,
    currentStageName: "Queued",
    currentStageDetail: "The ingestion job has been accepted by the backend.",
  });
};

const fetchBatchResult = async (batchId: string) => {
  const response = await fetch(`${API_BASE}/api/v1/batches/${batchId}`);
  if (!response.ok) throw new Error(`Failed to fetch completed batch (${response.status})`);
  return response.json();
};

const fetchCaseDossier = async (caseId: string) => {
  const response = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(caseId)}/dossier`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Failed to fetch case dossier (${response.status})`);
  return response.json();
};

const fetchCaseGraphContract = async (caseId: string): Promise<CaseGraphContract | null> => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(caseId)}/graph-contract`, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch (_) {
    return null;
  }
};

const pollBatch = async (batchId: string, set: any): Promise<any> => {
  while (true) {
    const response = await fetch(`${API_BASE}/api/v1/batches/${batchId}/status`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Failed to read ingestion status (${response.status})`);
    const status = await response.json();
    const total = Number(status.total_documents || 0);
    const processed = Number(status.processed_count || 0);
    set({
      progressPercentage: Number(status.progress_percentage || 0),
      estimatedSecondsRemaining: 0,
      timeElapsedSeconds: Number(status.elapsed_seconds || 0),
      totalDocumentsInBatch: total,
      currentStageName: String(status.current_stage || "Processing"),
      currentStageDetail: String(status.stage_detail || "Processing evidence..."),
      statusMessage: processed < total ? `Processing document ${Math.min(processed + 1, total)} of ${total}` : "Finalizing evidence reconciliation...",
    });
    if (status.status === "completed" || status.completed) return fetchBatchResult(batchId);
    if (status.status === "failed") throw new Error(status.error_message || "Batch ingestion failed");
    await new Promise((resolve) => setTimeout(resolve, 800));
  }
};

export const useCaseStore = create<CaseState>((set, get) => ({
  activeCaseId: "CASE-2026-DL-184",
  batchId: null,
  caseTitle: "Vasant Vihar Theft & Recovery Investigation",
  status: "idle",
  statusMessage: "Ready for evidentiary ingestion",
  progressPercentage: 0,
  estimatedSecondsRemaining: 0,
  timeElapsedSeconds: 0,
  currentStageName: "System Idle",
  currentStageDetail: "Ready to ingest forensic evidence",
  totalDocumentsInBatch: 0,
  documents: [],
  activeDocIndex: 0,
  crossDocIntelligence: null,
  graphContract: null,
  viewMode: "dossier",
  selectedEntity: null,
  searchFilter: "",
  selectedDatasetKey: "police_case",
  availableDatasets: [
    {
      key: "police_case",
      name: "Forensic Police Dossier",
      category: "Forensic & Legal",
      description: "5 connected case records: FIR, Seizure Memo, Arrest Memo, Injury Certificate, Ballistics Report",
      count: 5,
    },
    {
      key: "receipts",
      name: "ICDAR SROIE Scanned Receipts",
      category: "Kaggle / ICDAR Benchmark",
      description: "Authentic scanned retail and supermarket receipts with OCR and field items",
      count: 3,
    },
    {
      key: "invoices",
      name: "Commercial B2B Tax Invoices",
      category: "Corporate & Finance",
      description: "Itemized tax invoices with line items, HSN codes, and arithmetic reconciliation",
      count: 2,
    },
    {
      key: "financial",
      name: "Bank Account & Payment Statements",
      category: "Banking & Audits",
      description: "Transaction ledgers, debit/credit entries, account balances, and IFSC records",
      count: 2,
    },
    {
      key: "contracts",
      name: "Legal Contracts & NDAs",
      category: "Legal & Corporate",
      description: "Non-Disclosure and Service Agreements with clauses, parties, and effective dates",
      count: 2,
    },
    {
      key: "degraded",
      name: "Scanner Degraded / Skewed Test",
      category: "Stress Testing",
      description: "Low-contrast, noisy, and rotated document scans testing the OpenCV preprocessing pipeline",
      count: 2,
    },
  ],

  setViewMode: (mode) => set({ viewMode: mode }),
  setActiveDocIndex: (index) => set({ activeDocIndex: index }),
  setSelectedEntity: (entity) => set({ selectedEntity: entity }),
  setSearchFilter: (query) => set({ searchFilter: query }),
  setSelectedDatasetKey: (key) => set({ selectedDatasetKey: key }),

  loadCatalog: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/samples/catalog`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          set({ availableDatasets: data });
        }
      }
    } catch (_) {}
  },

  restoreActiveCase: async () => {
    try {
      const dossier = await fetchCaseDossier(get().activeCaseId);
      const graphContract = await fetchCaseGraphContract(get().activeCaseId);
      set({
        caseTitle: dossier.cross_document_intelligence?.case_title || get().caseTitle,
        documents: dossier.documents || [],
        crossDocIntelligence: dossier.cross_document_intelligence || null,
        graphContract,
        activeDocIndex: 0,
        status: dossier.documents?.length ? "success" : "idle",
        statusMessage: dossier.documents?.length ? `${dossier.documents.length} document(s) restored from case memory` : "Ready for evidentiary ingestion",
        progressPercentage: dossier.documents?.length ? 100 : 0,
        totalDocumentsInBatch: dossier.documents?.length || 0,
      });
    } catch (_) {
      // A fresh case legitimately has no persisted dossier yet.
    }
  },

  loadSampleCaseBundle: async () => {
    return get().loadDiverseDataset("police_case");
  },

  loadDiverseDataset: async (datasetKey: string) => {
    const ds = get().availableDatasets.find((d) => d.key === datasetKey) || { name: datasetKey, count: 5 };
    setInitialLoadingState(ds.count, set, `Starting ${ds.name}...`);
    set({ selectedDatasetKey: datasetKey });
    try {
      const formData = new FormData();
      formData.append("actor_id", "lead_investigator");
      const res = await fetch(`${API_BASE}/api/v1/samples/load-dataset/${datasetKey}/start`, { method: "POST", body: formData });
      if (!res.ok) {
        let msg = `Server returned HTTP ${res.status}`;
        try { msg = (await res.json()).detail || msg; } catch (_) {}
        throw new Error(msg);
      }
      const started = await res.json();
      set({ batchId: started.batch_id, activeCaseId: started.case_id || get().activeCaseId, caseTitle: started.title || ds.name });
      const data = await pollBatch(started.batch_id, set);
      const graphContract = await fetchCaseGraphContract(data.case_id || started.case_id || get().activeCaseId);
      set({
        status: "success",
        statusMessage: `Dataset '${data.title || ds.name}' ingested: ${data.total_documents} document(s) extracted`,
        batchId: data.batch_id,
        activeCaseId: data.case_id || `CASE-${datasetKey.toUpperCase()}`,
        caseTitle: data.title || ds.name,
        documents: data.documents || [],
        crossDocIntelligence: data.cross_document_intelligence,
        graphContract,
        activeDocIndex: 0,
        progressPercentage: 100,
        estimatedSecondsRemaining: 0,
      });
    } catch (err: any) {
      set({ status: "error", statusMessage: err.message || "Failed to load dataset", progressPercentage: 0 });
    }
  },

  processUploadedFiles: async (files: File[]) => {
    if (!files.length) return;
    setInitialLoadingState(files.length, set, `Starting ingestion of ${files.length} document(s)...`);
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));
      formData.append("case_id", get().activeCaseId || "CASE-CUSTOM-2026");
      formData.append("actor_id", "lead_investigator");
      formData.append("run_dual_validation", "false");
      formData.append("auto_escalate", "false");
      const res = await fetch(`${API_BASE}/api/v1/documents/batch-process/start`, { method: "POST", body: formData });
      if (!res.ok) {
        let msg = `HTTP error ${res.status}`;
        try { msg = (await res.json()).detail || msg; } catch (_) {}
        throw new Error(msg);
      }
      const started = await res.json();
      set({ batchId: started.batch_id, totalDocumentsInBatch: started.total_documents });
      const data = await pollBatch(started.batch_id, set);
      const graphContract = await fetchCaseGraphContract(data.case_id || get().activeCaseId);
      set({
        status: "success",
        statusMessage: `Ingestion complete: ${data.successful_count} document(s) extracted`,
        batchId: data.batch_id,
        activeCaseId: data.case_id || get().activeCaseId,
        caseTitle: data.title || get().caseTitle,
        documents: data.documents || [],
        crossDocIntelligence: data.cross_document_intelligence,
        graphContract,
        activeDocIndex: 0,
        progressPercentage: 100,
        estimatedSecondsRemaining: 0,
      });
      // Refresh from the persisted dossier so extracted-field IDs and human-review metadata are available immediately.
      await get().restoreActiveCase();
    } catch (err: any) {
      set({ status: "error", statusMessage: err.message || "Extraction failed", progressPercentage: 0 });
    }
  },
}));
