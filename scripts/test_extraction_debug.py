import time
import json
import pathlib
from clarity.preprocessing.pipeline import run_preprocessing_pipeline
from clarity.vlm.client import VLMClient

fir_path = pathlib.Path("samples/sample_fir_report.png")
print("Reading file:", fir_path)
raw_bytes = fir_path.read_bytes()

t0 = time.time()
prep_res = run_preprocessing_pipeline(raw_bytes)
t_prep = time.time() - t0
print(f"Preprocessing took {t_prep:.2f}s | Res: {prep_res.image_width}x{prep_res.image_height}")

client = VLMClient(timeout=300.0)

t1 = time.time()
print("Starting classification...")
cls_res = client.classify_document(prep_res.preprocessed_bytes)
t_cls = time.time() - t1
print(f"Classification took {t_cls:.2f}s | Result: {cls_res['document_type']}")

t2 = time.time()
print("Starting structured extraction (timeout=300s)...")
try:
    structured, meta = client.extract_structured(prep_res.preprocessed_bytes)
    t_ext = time.time() - t2
    print(f"Extraction took {t_ext:.2f}s!")
    print("Document type:", structured.document_type)
    print("Parties:", structured.parties)
    print("Identifiers:", structured.identifiers)
    print("Dates:", structured.dates)
    print("Amounts:", structured.amounts)
except Exception as e:
    print(f"Extraction failed after {time.time()-t2:.2f}s: {type(e).__name__}: {e}")
