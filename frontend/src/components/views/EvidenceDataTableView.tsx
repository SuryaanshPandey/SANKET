"use client";

import React, { useMemo, useState } from "react";
import { ArrowUpDown, Download, ExternalLink, Filter, Search } from "lucide-react";
import { useReactTable, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, flexRender, type ColumnDef, type SortingState } from "@tanstack/react-table";
import { useCaseStore } from "@/store/useCaseStore";

interface FieldRow { documentId: string; sourceDoc: string; docType: string; fieldName: string; fieldValue: string; confidence: number; boundingBox?: { x: number; y: number; w: number; h: number } | null; }

export const EvidenceDataTableView: React.FC = () => {
  const { documents, setActiveDocIndex, setViewMode } = useCaseStore();
  const [globalFilter, setGlobalFilter] = useState("");
  const [docTypeFilter, setDocTypeFilter] = useState("ALL");
  const [sorting, setSorting] = useState<SortingState>([]);

  const data = useMemo<FieldRow[]>(() => documents.flatMap((doc) => (doc.field_items || []).map((field) => ({ documentId: doc.document_id, sourceDoc: doc.original_filename, docType: doc.doc_type || "other", fieldName: field.field_name, fieldValue: field.field_value, confidence: field.confidence, boundingBox: field.bounding_box }))), [documents]);
  const filteredData = useMemo(() => docTypeFilter === "ALL" ? data : data.filter((row) => row.docType.toLowerCase() === docTypeFilter.toLowerCase()), [data, docTypeFilter]);
  const docTypes = useMemo(() => ["ALL", ...Array.from(new Set(data.map((row) => row.docType)))], [data]);

  const columns = useMemo<ColumnDef<FieldRow>[]>(() => [
    { accessorKey: "sourceDoc", header: ({ column }) => <button type="button" className="sanket-table-sort" title="Sort by source document" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Source <ArrowUpDown size={11} /></button>, cell: (info) => <span className="sanket-table-source">{String(info.getValue())}</span> },
    { accessorKey: "docType", header: "Type", cell: (info) => <span className="sanket-table-type">{String(info.getValue()).replaceAll("_", " ")}</span> },
    { accessorKey: "fieldName", header: ({ column }) => <button type="button" className="sanket-table-sort" title="Sort by field name" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Field <ArrowUpDown size={11} /></button>, cell: (info) => <span className="sanket-table-field">{String(info.getValue())}</span> },
    { accessorKey: "fieldValue", header: "Value", cell: (info) => <span className="sanket-table-value">{String(info.getValue()) || "—"}</span> },
    { accessorKey: "confidence", header: ({ column }) => <button type="button" className="sanket-table-sort" title="Sort by extraction confidence" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Confidence <ArrowUpDown size={11} /></button>, cell: (info) => { const confidence = Number(info.getValue()); return <span className={`sanket-pill ${confidence < .85 ? "sanket-pill--warn" : "sanket-pill--ok"}`}>{Math.round(confidence * 100)}%</span>; } },
    { accessorKey: "boundingBox", header: "Source position", cell: (info) => { const box = info.getValue() as FieldRow["boundingBox"]; return box ? <span className="sanket-table-bbox">{box.x},{box.y},{box.w},{box.h}</span> : <span className="sanket-table-muted">No bbox</span>; } },
    { id: "inspect", header: "", enableSorting: false, cell: ({ row }) => <button type="button" className="sanket-table-open" onClick={() => { const index = documents.findIndex((doc) => doc.document_id === row.original.documentId); if (index >= 0) setActiveDocIndex(index); setViewMode("inspector"); }} title="Open source document"><ExternalLink size={13} /></button> },
  ], [documents, setActiveDocIndex, setViewMode]);

  const table = useReactTable({ data: filteredData, columns, state: { sorting, globalFilter }, onSortingChange: setSorting, onGlobalFilterChange: setGlobalFilter, getCoreRowModel: getCoreRowModel(), getFilteredRowModel: getFilteredRowModel(), getSortedRowModel: getSortedRowModel(), getPaginationRowModel: getPaginationRowModel(), initialState: { pagination: { pageSize: 15 } } });

  const exportCSV = () => {
    const escape = (value: string) => `"${String(value).replaceAll('"', '""')}"`;
    const lines = [["Source Document", "Document Type", "Field Identifier", "Extracted Value", "Confidence", "Bounding Box"].join(","), ...filteredData.map((row) => [escape(row.sourceDoc), escape(row.docType), escape(row.fieldName), escape(row.fieldValue), row.confidence, escape(row.boundingBox ? `${row.boundingBox.x},${row.boundingBox.y},${row.boundingBox.w},${row.boundingBox.h}` : "")].join(","))];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `sanket_evidence_ledger_${Date.now()}.csv`; link.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="sanket-ledger">
      <div className="sanket-ledger__toolbar">
        <div className="sanket-ledger__search-wrap"><Search size={14} /><input value={globalFilter} onChange={(e) => setGlobalFilter(e.target.value)} placeholder="Search evidence, names, identifiers…" title="Search across evidence fields and values" aria-label="Search evidence ledger" /></div>
        <div className="sanket-ledger__filters"><Filter size={13} /><select value={docTypeFilter} onChange={(e) => setDocTypeFilter(e.target.value)} aria-label="Filter document type" title="Filter the ledger by document type">{docTypes.map((type) => <option key={type} value={type}>{type === "ALL" ? "All sources" : type.replaceAll("_", " ")}</option>)}</select><span>{table.getFilteredRowModel().rows.length} records</span><button type="button" className="sanket-button" title="Download the filtered evidence ledger as CSV" onClick={exportCSV}><Download size={13} /> Export CSV</button></div>
      </div>

      <div className="sanket-ledger__table-wrap">
        <table className="sanket-table">
          <thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id}>{header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead>
          <tbody>{table.getRowModel().rows.map((row) => <tr key={row.id}>{row.getVisibleCells().map((cell) => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody>
        </table>
      </div>

      <div className="sanket-ledger__footer"><span>Page {table.getState().pagination.pageIndex + 1} of {Math.max(1, table.getPageCount())}</span><div><button type="button" className="sanket-button" title="Go to the previous ledger page" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()}>Previous</button><button type="button" className="sanket-button" title="Go to the next ledger page" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()}>Next</button></div></div>
    </div>
  );
};
