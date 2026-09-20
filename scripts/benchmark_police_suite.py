"""Benchmark Clarity on the complete suite of Indian Police Investigation Documents.

Runs end-to-end extraction and quality gate evaluation across:
1. First Information Report (FIR) - ICDAR 2023 Real Police Document
2. Seizure Memo / Panchnama (Sec 100/102 CrPC)
3. Arrest & Inspection Memo (Sec 41B CrPC & D.K. Basu)
4. Final Report / Charge Sheet (Sec 173 CrPC / IIF-5)
5. Medico-Legal Certificate (MLC & Injury Report)
6. Forensic Science Lab (FSL) Cyber 65B Certificate
"""

from pathlib import Path
import time
from clarity.pipeline.runner import DocumentExtractionPipeline
from clarity.vlm.client import VLMClient

test_docs = [
    ("FIR Report (ICDAR 2023)", Path("samples/sample_fir_report.png"), "fir_report"),
    ("Seizure Memo (Panchnama)", Path("samples/sample_seizure_memo.png"), "seizure_memo"),
    ("Arrest Memo (Sec 41B)", Path("samples/sample_arrest_memo.png"), "arrest_memo"),
    ("Charge Sheet (Sec 173)", Path("samples/sample_chargesheet.png"), "charge_sheet"),
    ("Medico-Legal (MLC)", Path("samples/sample_medical_legal.png"), "medical_legal"),
    ("Forensic Report (65B)", Path("samples/sample_forensic_report.png"), "forensic_report"),
]

def run_benchmark():
    pipeline = DocumentExtractionPipeline()
    results = []

    print("================================================================================")
    print("STARTING INDIAN POLICE INVESTIGATION SUITE BENCHMARK")
    print("================================================================================\n")

    for label, doc_path, expected_type in test_docs:
        if not doc_path.exists():
            print(f"Skipping {label}: File not found ({doc_path})")
            continue

        print(f"--> Processing: {label} ({doc_path.name})...")
        t0 = time.time()
        try:
            res = pipeline.process_file(
                file_path_or_bytes=doc_path,
                case_id=f"CASE-INSP-{expected_type.upper()}",
                actor_id="lead_investigator",
                run_dual_validation=False,
                auto_escalate=False,
            )
            elapsed = time.time() - t0

            # Count fields
            parties_count = len(res.extracted_data.get("parties", []))
            identifiers_count = len(res.extracted_data.get("identifiers", []))
            dates_count = len(res.extracted_data.get("dates", []))
            flags_count = len(res.validation_report.flags)

            cls_match = "✓ MATCH" if res.doc_type == expected_type else f"⚠ {res.doc_type}"

            results.append([
                label,
                cls_match,
                f"{res.overall_confidence*100:.0f}%",
                f"{parties_count} parties",
                f"{identifiers_count} ids",
                f"{dates_count} dates",
                f"{flags_count} flags",
                f"{elapsed:.1f}s",
            ])
            print(f"    Finished in {elapsed:.1f}s | Type: {res.doc_type} | Fields: {len(res.field_items)}")
        except Exception as e:
            print(f"    FAILED: {e}")
            results.append([label, "FAILED", "-", "-", "-", "-", "-", f"{time.time()-t0:.1f}s"])

    print("\n================================================================================")
    print("BENCHMARK RESULTS SUMMARY:")
    print("================================================================================")
    header = f"{'Document Type':<26} | {'Classification':<15} | {'Conf':<6} | {'Parties':<12} | {'Identifiers':<14} | {'Dates':<10} | {'Flags':<10} | {'Latency'}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r[0]:<26} | {r[1]:<15} | {r[2]:<6} | {r[3]:<12} | {r[4]:<14} | {r[5]:<10} | {r[6]:<10} | {r[7]}")


if __name__ == "__main__":
    run_benchmark()
