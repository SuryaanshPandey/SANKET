"""Rich Command Line Interface for Clarity Document Extraction & Multi-Document Intelligence."""

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clarity.config import settings
from clarity.db.session import init_db
from clarity.pipeline.batch import BatchExtractionPipeline
from clarity.pipeline.runner import DocumentExtractionPipeline
from clarity.vlm.client import VLMClient

console = Console()


def render_pipeline_output(res, as_json: bool = False):
    """Render single document extraction dossier."""
    if as_json:
        payload = {
            "document_id": res.document_id,
            "original_filename": res.original_filename,
            "file_hash_sha256": res.file_hash_sha256,
            "storage_path": res.storage_path,
            "preprocessed_storage_path": res.preprocessed_storage_path,
            "doc_type": res.doc_type,
            "overall_confidence": res.overall_confidence,
            "is_escalated": res.is_escalated,
            "extracted_data": res.extracted_data,
            "field_items": res.field_items,
            "validation_flags": res.validation_report.flags,
            "audit_trail": res.audit_trail,
        }
        print(json.dumps(payload, indent=2))
        return

    # Header Panel
    console.print(
        Panel.fit(
            f"[bold cyan]CLARITY EVIDENCE-GRADE EXTRACTION DOSSIER[/bold cyan]\n"
            f"[dim]Document ID:[/dim] [green]{res.document_id}[/green]\n"
            f"[dim]Original File:[/dim] {res.original_filename}\n"
            f"[dim]SHA-256 Hash:[/dim] [yellow]{res.file_hash_sha256}[/yellow]\n"
            f"[dim]Classified Type:[/dim] [magenta]{res.doc_type.upper()}[/magenta]\n"
            f"[dim]Overall Confidence:[/dim] [{'green' if res.overall_confidence >= 0.85 else 'red'}]{res.overall_confidence:.2f}[/]\n"
            f"[dim]Escalated:[/dim] [{'red' if res.is_escalated else 'blue'}]{'YES' if res.is_escalated else 'NO'}[/]",
            title="Evidence Summary",
            border_style="cyan",
        )
    )

    # 1. Extracted Fields Table
    table_fields = Table(title="Extracted Structured Fields", border_style="bright_blue", show_lines=True)
    table_fields.add_column("Field Identifier", style="bold white", width=25)
    table_fields.add_column("Extracted Value", style="bright_green")
    table_fields.add_column("Confidence", justify="right", width=12)
    table_fields.add_column("Bounding Box (x, y, w, h)", style="dim", width=28)

    for item in res.field_items:
        conf = item["confidence"]
        conf_style = "green" if conf >= 0.85 else "red bold"
        bbox = item.get("bounding_box")
        bbox_str = f"({bbox['x']}, {bbox['y']}, {bbox['w']}, {bbox['h']})" if bbox else "N/A"
        table_fields.add_row(
            item["field_name"],
            str(item["field_value"]),
            f"[{conf_style}]{conf:.2f}[/]",
            bbox_str,
        )

    console.print(table_fields)

    # 2. Validation & Quality Gates Table
    if res.validation_report.flags:
        table_val = Table(title="Quality Gates & Flagged Issues", border_style="red", show_lines=True)
        table_val.add_column("Flag Type", style="bold red", width=25)
        table_val.add_column("Affected Field / Scope", style="yellow", width=25)
        table_val.add_column("Diagnostic Message", style="white")

        for flag in res.validation_report.flags:
            table_val.add_row(
                flag.get("type", "flag"),
                str(flag.get("field", "general")),
                flag.get("message", json.dumps(flag)),
            )
        console.print(table_val)
    else:
        console.print("[bold green]✓ All Quality Gates & Arithmetic Cross-Checks Passed (0 Flags).[/bold green]\n")

    # 3. Cryptographic Audit Trail Table
    table_audit = Table(title="Cryptographic Chain of Custody (Audit Log)", border_style="magenta", show_lines=True)
    table_audit.add_column("Timestamp (UTC)", style="dim", width=24)
    table_audit.add_column("Action", style="bold cyan", width=22)
    table_audit.add_column("Actor", style="white", width=14)
    table_audit.add_column("Audit Detail Summary", style="dim white")

    for log in res.audit_trail:
        detail_snippet = json.dumps(log["detail"])
        if len(detail_snippet) > 80:
            detail_snippet = detail_snippet[:77] + "..."
        table_audit.add_row(
            log["timestamp"][:19].replace("T", " "),
            log["action"],
            log["actor_id"],
            detail_snippet,
        )

    console.print(table_audit)


def render_batch_output(batch_res, as_json: bool = False):
    """Render multi-document batch dossier and cross-document intelligence."""
    if as_json:
        payload = {
            "batch_id": batch_res.batch_id,
            "case_id": batch_res.case_id,
            "title": batch_res.title,
            "total_documents": batch_res.total_documents,
            "successful_count": batch_res.successful_count,
            "failed_count": batch_res.failed_count,
            "documents": batch_res.documents,
            "failed_documents": batch_res.failed_documents,
            "cross_document_intelligence": batch_res.cross_document_intelligence,
        }
        print(json.dumps(payload, indent=2))
        return

    intel = batch_res.cross_document_intelligence

    # Header Panel
    console.print(
        Panel.fit(
            f"[bold cyan]CLARITY MULTI-DOCUMENT CASE DOSSIER[/bold cyan]\n"
            f"[dim]Batch ID:[/dim] [green]{batch_res.batch_id}[/green]\n"
            f"[dim]Case ID:[/dim] [yellow]{batch_res.case_id or 'None'}[/yellow]\n"
            f"[dim]Batch Title:[/dim] {batch_res.title}\n"
            f"[dim]Documents Processed:[/dim] [bold white]{batch_res.successful_count}/{batch_res.total_documents}[/bold white] "
            f"([green]{batch_res.successful_count} OK[/green], [{'red' if batch_res.failed_count > 0 else 'dim'}]{batch_res.failed_count} Failed[/])\n"
            f"[dim]Overall Confidence:[/dim] [{'green' if intel.get('overall_case_confidence', 0.9) >= 0.85 else 'yellow'}]{intel.get('overall_case_confidence', 0.90):.2f}[/]\n"
            f"[dim]Synthesis:[/dim] [white]{intel.get('case_summary', '')}[/white]",
            title="Evidentiary Batch Overview",
            border_style="cyan",
        )
    )

    # 1. Document Summary Table
    t_docs = Table(title="Ingested Case Documents", border_style="bright_blue", show_lines=True)
    t_docs.add_column("Doc ID", style="dim", width=14)
    t_docs.add_column("Filename", style="bold white", width=28)
    t_docs.add_column("Classified Type", style="magenta", width=20)
    t_docs.add_column("Confidence", justify="right", width=12)
    t_docs.add_column("Flags", justify="center", width=8)
    t_docs.add_column("SHA-256 Hash", style="dim yellow", width=18)

    for doc in batch_res.documents:
        conf = doc.get("overall_confidence", 0.9)
        conf_style = "green" if conf >= 0.85 else "red"
        flags_count = len(doc.get("validation_flags", []))
        hash_short = doc.get("file_hash_sha256", "")[:16] + "..."
        t_docs.add_row(
            doc["document_id"][:12] + "..",
            doc["original_filename"],
            doc.get("doc_type", "other").upper(),
            f"[{conf_style}]{conf:.2f}[/]",
            f"[{'red' if flags_count > 0 else 'green'}]{flags_count}[/]",
            hash_short,
        )
    console.print(t_docs)

    # 2. Reconciled Cross-Document Entities Table
    entities = intel.get("reconciled_entities", [])
    if entities:
        t_ent = Table(title="Cross-Document Entity Reconciliation", border_style="green", show_lines=True)
        t_ent.add_column("Canonical Name", style="bold white", width=26)
        t_ent.add_column("Cross-Document Roles", style="bright_cyan", width=30)
        t_ent.add_column("Doc Count", justify="center", width=12)
        t_ent.add_column("Corroborating Documents", style="dim white")

        for ent in entities:
            roles_str = ", ".join(ent.get("roles", []))
            docs_str = ", ".join(ent.get("documents", []))
            t_ent.add_row(
                ent["canonical_name"],
                roles_str,
                str(ent["document_count"]),
                docs_str,
            )
        console.print(t_ent)

    # 3. Master Chronological Timeline
    timeline = intel.get("master_timeline", [])
    if timeline:
        t_time = Table(title="Master Chronological Evidentiary Timeline", border_style="yellow", show_lines=True)
        t_time.add_column("Event Date", style="bold yellow", width=16)
        t_time.add_column("Document Source", style="bright_blue", width=28)
        t_time.add_column("Doc Type", style="magenta", width=18)
        t_time.add_column("Event Description & Context", style="white")

        for event in timeline:
            date_display = event.get("normalized_date") or event.get("raw_date") or "Unknown"
            t_time.add_row(
                date_display,
                event.get("filename", ""),
                event.get("doc_type", "").upper(),
                event.get("detail", ""),
            )
        console.print(t_time)

    # 4. Cross-Reference Identifier Links
    cross_refs = intel.get("cross_references", [])
    if cross_refs:
        t_ref = Table(title="Cross-Referenced Identifiers & Codes", border_style="bright_cyan", show_lines=True)
        t_ref.add_column("Identifier Type", style="bold cyan", width=24)
        t_ref.add_column("Extracted Value", style="bold white", width=30)
        t_ref.add_column("Docs Linked", justify="center", width=12)
        t_ref.add_column("Corroborating Documents", style="dim white")

        for r in cross_refs:
            t_ref.add_row(
                r["identifier_type"],
                r["value"],
                str(r["document_count"]),
                ", ".join(r.get("documents", [])),
            )
        console.print(t_ref)

    # 5. Financial & Property Ledger
    fin = intel.get("financial_ledger", {})
    if fin and fin.get("items"):
        t_fin = Table(title=f"Consolidated Property & Financial Ledger (Total: {fin.get('currency', 'INR')} {fin.get('total_amount', 0.0):,.2f})", border_style="magenta", show_lines=True)
        t_fin.add_column("Item / Stated Value", style="bold white", width=35)
        t_fin.add_column("Amount / Value", justify="right", style="bright_green", width=18)
        t_fin.add_column("Source Document", style="dim white", width=28)

        for item in fin["items"]:
            curr = item.get("currency") or fin.get("currency", "INR")
            val_str = f"{curr} {item.get('value', 0.0):,.2f}"
            t_fin.add_row(
                item.get("label", "Property/Amount"),
                val_str,
                item.get("source_doc", ""),
            )
        console.print(t_fin)

    # 6. Discrepancies & Warnings
    discrepancies = intel.get("discrepancies", [])
    if discrepancies:
        t_disc = Table(title="Cross-Document Discrepancies & Evidentiary Inconsistencies", border_style="bold red", show_lines=True)
        t_disc.add_column("Severity", style="bold red", width=10)
        t_disc.add_column("Discrepancy Category", style="yellow", width=26)
        t_disc.add_column("Documents Involved", style="white", width=28)
        t_disc.add_column("Evidentiary Finding", style="bright_white")

        for d in discrepancies:
            t_disc.add_row(
                d.get("severity", "MEDIUM").upper(),
                d.get("flag_type", "DISCREPANCY"),
                ", ".join(d.get("documents_involved", [])),
                d.get("message", ""),
            )
        console.print(t_disc)
    else:
        console.print("[bold green]✓ Full Cross-Document Evidentiary Consistency Verified (0 Discrepancies).[/bold green]\n")


def main():
    parser = argparse.ArgumentParser(description="Clarity: Evidence-Grade Document Extraction & Cross-Document Intelligence")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Process command (supports 1 or multiple files)
    proc_parser = subparsers.add_parser("process", help="Process one or more document images through the evidence pipeline")
    proc_parser.add_argument("file_paths", type=str, nargs="+", help="Path(s) to document photo(s)/scan(s)")
    proc_parser.add_argument("--case-id", type=str, default=None, help="Associated investigation case ID")
    proc_parser.add_argument("--title", type=str, default=None, help="Batch title or case description")
    proc_parser.add_argument("--actor", type=str, default="investigator-1", help="Actor ID for audit log")
    proc_parser.add_argument("--model", type=str, default=None, help="VLM model to use (default from config)")
    proc_parser.add_argument("--no-dual-run", action="store_true", help="Skip secondary dual-run diff")
    proc_parser.add_argument("--no-escalate", action="store_true", help="Do not auto-escalate to thinking model")
    proc_parser.add_argument("--json", action="store_true", help="Output raw JSON instead of tables")

    # Batch command explicitly
    batch_parser = subparsers.add_parser("batch", help="Batch ingest and synthesize multiple documents in an investigation case")
    batch_parser.add_argument("file_paths", type=str, nargs="+", help="Paths to document images")
    batch_parser.add_argument("--case-id", type=str, default=None, help="Case ID for the batch")
    batch_parser.add_argument("--title", type=str, default=None, help="Case batch title")
    batch_parser.add_argument("--actor", type=str, default="lead-investigator", help="Actor ID for audit log")
    batch_parser.add_argument("--model", type=str, default=None, help="VLM model to use")
    batch_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Init DB command
    subparsers.add_parser("init-db", help="Initialize database schema tables")

    # Contract command
    contract_parser = subparsers.add_parser("contract", help="Generate or export standardized Graph Contract (entities, events, relationships)")
    contract_parser.add_argument("target", type=str, help="Document file path, document ID, or case ID")
    contract_parser.add_argument("--output", "-o", type=str, default=None, help="Save contract to output JSON file")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
        console.print("[bold green]✓ Database initialized successfully.[/bold green]")
        return

    if args.command == "contract":
        from clarity.engine import ClarityEngine

        engine = ClarityEngine(auto_init_db=True)
        target_path = Path(args.target)
        if target_path.exists():
            with console.status(f"[bold blue]Extracting Graph Contract from {target_path.name}...[/bold blue]"):
                contract = engine.extract_document(target_path)
        else:
            try:
                contract = engine.get_case_contract(args.target)
                if contract.total_documents == 0:
                    contract = engine.get_document_contract(args.target)
            except Exception:
                try:
                    contract = engine.get_document_contract(args.target)
                except Exception as e:
                    console.print(f"[bold red]Error: Target not found as file, case, or document ID: {e}[/bold red]")
                    sys.exit(1)

        payload = contract.model_dump()
        if args.output:
            out_p = Path(args.output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            console.print(f"[bold green]✓ Graph Contract exported to {out_p}[/bold green]")
        else:
            print(json.dumps(payload, indent=2))
        return

    if args.command in ["process", "batch"]:
        init_db()
        target_paths = []
        for p_str in args.file_paths:
            path = Path(p_str)
            if path.exists():
                target_paths.append(path)
            else:
                console.print(f"[bold red]Warning: File not found: {path}[/bold red]")

        if not target_paths:
            console.print("[bold red]Error: No valid input files found.[/bold red]")
            sys.exit(1)

        # If single file passed to 'process', run single-doc flow
        if len(target_paths) == 1 and args.command == "process":
            target_file = target_paths[0]
            with console.status(f"[bold blue]Processing {target_file.name} through evidence pipeline...[/bold blue]"):
                vlm = VLMClient(default_model=args.model) if args.model else None
                pipeline = DocumentExtractionPipeline(vlm_client=vlm)
                res = pipeline.process_file(
                    file_path_or_bytes=target_file,
                    case_id=args.case_id,
                    actor_id=args.actor,
                    run_dual_validation=not getattr(args, "no_dual_run", False),
                    auto_escalate=not getattr(args, "no_escalate", False),
                )
            render_pipeline_output(res, as_json=args.json)
            return

        # Multi-file batch flow
        files_payload = [(p.name, p) for p in target_paths]
        with console.status(f"[bold blue]Ingesting and analyzing batch of {len(files_payload)} document(s)...[/bold blue]"):
            vlm = VLMClient(default_model=args.model) if args.model else None
            batch_pipeline = BatchExtractionPipeline(vlm_client=vlm)
            batch_res = batch_pipeline.process_batch(
                files=files_payload,
                case_id=args.case_id,
                batch_title=args.title,
                actor_id=args.actor,
                run_dual_validation=not getattr(args, "no_dual_run", True),
                auto_escalate=not getattr(args, "no_escalate", True),
            )

        render_batch_output(batch_res, as_json=args.json)


if __name__ == "__main__":
    main()
