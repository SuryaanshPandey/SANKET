/**
 * Clarity Forensic Document Extraction Platform - Frontend Controller
 */

// Application State
const state = {
  currentDocId: null,
  dossierData: null,
  activeView: 'preprocessed', // 'preprocessed' | 'original'
  highlightedIndex: null,
};

// DOM Elements
const docImage = document.getElementById('doc-image');
const bboxOverlay = document.getElementById('bbox-overlay');
const imageStage = document.getElementById('stage');
const emptyState = document.getElementById('empty-state');
const pipelineProgress = document.getElementById('pipeline-progress');
const progressStepTitle = document.getElementById('progress-step-title');

// Buttons & Inputs
const fileUpload = document.getElementById('file-upload');
const btnSample = document.getElementById('btn-sample');
const tabPreprocessed = document.getElementById('tab-preprocessed');
const tabOriginal = document.getElementById('tab-original');
const btnCopyJson = document.getElementById('btn-copy-json');
const btnDownloadJson = document.getElementById('btn-download-json');

// Dossier Fields
const valDocId = document.getElementById('val-doc-id');
const valDocHash = document.getElementById('val-doc-hash');
const badgeDocType = document.getElementById('badge-doc-type');
const badgeConfidence = document.getElementById('badge-confidence');
const badgeEscalated = document.getElementById('badge-escalated');

const gateCard = document.getElementById('gate-card');
const gateStatus = document.getElementById('gate-status');
const flagsList = document.getElementById('flags-list');
const gateIcon = document.getElementById('gate-icon');

const listAmounts = document.getElementById('list-amounts');
const listDates = document.getElementById('list-dates');
const listParties = document.getElementById('list-parties');
const listIdentifiers = document.getElementById('list-identifiers');
const auditTimeline = document.getElementById('audit-timeline');
const valRawText = document.getElementById('val-raw-text');

// Metrics
const mDeskew = document.getElementById('m-deskew');
const mClahe = document.getElementById('m-clahe');
const mPersp = document.getElementById('m-persp');

// ============================================================================
// Event Listeners
// ============================================================================
fileUpload.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    processDocumentFile(file);
  }
});

btnSample.addEventListener('click', async () => {
  try {
    showProgress('Fetching Sample Invoice...');
    const response = await fetch('/api/v1/samples/invoice');
    if (!response.ok) throw new Error('Failed to fetch sample invoice');
    const blob = await response.blob();
    const sampleFile = new File([blob], 'sample_invoice.jpg', { type: 'image/jpeg' });
    processDocumentFile(sampleFile);
  } catch (err) {
    hideProgress();
    alert('Error loading sample invoice: ' + err.message);
  }
});

const selectSampleDoc = document.getElementById('select-sample-doc');
if (selectSampleDoc) {
  selectSampleDoc.addEventListener('change', async (e) => {
    const url = e.target.value;
    if (!url) return;
    const selectedText = e.target.options[e.target.selectedIndex].text;
    try {
      showProgress(`Loading ${selectedText}...`);
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Failed to load ${selectedText}`);
      const blob = await response.blob();
      const ext = url.endsWith('.jpg') ? 'jpg' : 'png';
      const sampleFile = new File([blob], `sample_${Date.now()}.${ext}`, { type: blob.type });
      processDocumentFile(sampleFile);
    } catch (err) {
      hideProgress();
      alert('Error: ' + err.message);
    } finally {
      selectSampleDoc.selectedIndex = 0;
    }
  });
}

const btnSampleFir = document.getElementById('btn-sample-fir');
if (btnSampleFir) {
  btnSampleFir.addEventListener('click', async () => {
    try {
      showProgress('Loading Indian FIR Report...');
      const response = await fetch('/api/v1/samples/fir');
      if (!response.ok) throw new Error('Failed to fetch sample FIR');
      const blob = await response.blob();
      const sampleFile = new File([blob], 'indian_police_fir.png', { type: 'image/png' });
      processDocumentFile(sampleFile);
    } catch (err) {
      hideProgress();
      alert('Error loading sample FIR: ' + err.message);
    }
  });
}

tabPreprocessed.addEventListener('click', () => setImageView('preprocessed'));
tabOriginal.addEventListener('click', () => setImageView('original'));

btnCopyJson.addEventListener('click', () => {
  if (!state.dossierData) return;
  navigator.clipboard.writeText(JSON.stringify(state.dossierData, null, 2));
  alert('Evidence dossier JSON copied to clipboard.');
});

btnDownloadJson.addEventListener('click', () => {
  if (!state.dossierData) return;
  const blob = new Blob([JSON.stringify(state.dossierData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `evidence_dossier_${state.currentDocId || 'doc'}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

valDocHash.addEventListener('click', () => {
  if (state.dossierData?.file_hash_sha256) {
    navigator.clipboard.writeText(state.dossierData.file_hash_sha256);
    alert('Full SHA-256 hash copied to clipboard.');
  }
});

// Drag & drop support on viewport
const viewport = document.getElementById('viewport');
viewport.addEventListener('dragover', (e) => {
  e.preventDefault();
  viewport.style.borderColor = 'var(--accent-cyan)';
});
viewport.addEventListener('dragleave', () => {
  viewport.style.borderColor = 'transparent';
});
viewport.addEventListener('drop', (e) => {
  e.preventDefault();
  viewport.style.borderColor = 'transparent';
  if (e.dataTransfer.files.length > 0) {
    processDocumentFile(e.dataTransfer.files[0]);
  }
});

// ============================================================================
// Core Extraction Workflow
// ============================================================================
async function processDocumentFile(file) {
  showProgress('Starting Evidentiary Pipeline...');
  animateProgressSteps();

  const formData = new FormData();
  formData.append('file', file);
  formData.append('case_id', 'CASE-2026-INV');
  formData.append('actor_id', 'lead_investigator');
  formData.append('run_dual_validation', 'false');
  formData.append('auto_escalate', 'false');

  try {
    const response = await fetch('/api/v1/documents/process', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let msg = 'Extraction failed';
      try {
        const errJson = await response.json();
        msg = errJson.detail || msg;
      } catch (_) {}
      throw new Error(msg);
    }

    const data = await response.json();
    state.currentDocId = data.document_id;
    state.dossierData = data;

    renderDossier(data);
    setImageView('preprocessed');
  } catch (err) {
    alert('Extraction Notice: ' + err.message);
    console.error(err);
  } finally {
    hideProgress();
  }
}

// ============================================================================
// UI Rendering
// ============================================================================
function renderDossier(data) {
  // 1. Custody Header
  valDocId.textContent = data.document_id.substring(0, 13) + '...';
  valDocHash.textContent = data.file_hash_sha256;
  badgeDocType.textContent = (data.doc_type || 'OTHER').toUpperCase();
  
  const confPct = Math.round((data.overall_confidence || 0.95) * 100);
  badgeConfidence.textContent = `${confPct}% Confidence`;
  badgeConfidence.className = `badge ${confPct >= 85 ? 'badge-confidence' : 'badge-status'}`;

  badgeEscalated.textContent = data.is_escalated ? 'ESCALATED (THINKING)' : 'STANDARD RUN';

  // 2. Quality Gates & Validation
  renderQualityGates(data.validation_flags);

  // 3. Extracted Fields
  renderExtractedEntities(data.field_items);

  // 4. Audit Trail
  renderAuditTrail(data.audit_trail);

  // 5. Raw Text
  valRawText.textContent = data.extracted_data?.raw_text || 'No transcription extracted.';

  // Metrics from audit log if available
  const prepEvent = data.audit_trail.find(a => a.action === 'preprocessing');
  if (prepEvent && prepEvent.detail && prepEvent.detail.metrics) {
    const m = prepEvent.detail.metrics;
    mDeskew.textContent = `${m.deskew_angle_degrees || 0.0}°`;
    mPersp.textContent = m.perspective_corrected ? 'Corrected' : 'Planar';
  }
}

function renderQualityGates(flags) {
  flagsList.innerHTML = '';
  if (!flags || flags.length === 0) {
    gateStatus.textContent = '✓ All Quality Gates Passed (0 Flags)';
    gateStatus.className = 'gate-status pass';
    gateIcon.textContent = '✓';
    gateIcon.style.color = 'var(--accent-green)';
  } else {
    gateStatus.textContent = `⚠ ${flags.length} Flag(s) Requiring Investigator Review`;
    gateStatus.className = 'gate-status warning';
    gateIcon.textContent = '⚠';
    gateIcon.style.color = 'var(--accent-amber)';

    flags.forEach(flag => {
      const li = document.createElement('li');
      li.className = 'flag-item';
      li.textContent = `[${flag.type || 'FLAG'}] ${flag.message || JSON.stringify(flag)}`;
      flagsList.appendChild(li);
    });
  }
}

function renderExtractedEntities(fieldItems) {
  // Clear lists
  listAmounts.innerHTML = '';
  listDates.innerHTML = '';
  listParties.innerHTML = '';
  listIdentifiers.innerHTML = '';

  let hasAmounts = false, hasDates = false, hasParties = false, hasIdentifiers = false;

  fieldItems.forEach((item, index) => {
    const card = document.createElement('div');
    card.className = 'field-item-card';
    card.dataset.index = index;

    const confPct = Math.round(item.confidence * 100);
    const badgeClass = confPct >= 85 ? 'field-badge' : 'field-badge warning';

    card.innerHTML = `
      <div class="field-meta">
        <span class="field-label">${escapeHtml(item.field_name)}</span>
        <span class="field-value">${escapeHtml(item.field_value)}</span>
      </div>
      <span class="${badgeClass}">${confPct}%</span>
    `;

    // Hover to highlight bounding box
    card.addEventListener('mouseenter', () => highlightField(index));
    card.addEventListener('mouseleave', () => unhighlightField());

    if (item.field_name.startsWith('amount:')) {
      listAmounts.appendChild(card);
      hasAmounts = true;
    } else if (item.field_name.startsWith('date:')) {
      listDates.appendChild(card);
      hasDates = true;
    } else if (item.field_name.startsWith('party:') || item.field_name.startsWith('party_')) {
      listParties.appendChild(card);
      hasParties = true;
    } else {
      listIdentifiers.appendChild(card);
      hasIdentifiers = true;
    }
  });

  if (!hasAmounts) listAmounts.innerHTML = '<div class="field-placeholder">No amounts detected</div>';
  if (!hasDates) listDates.innerHTML = '<div class="field-placeholder">No dates detected</div>';
  if (!hasParties) listParties.innerHTML = '<div class="field-placeholder">No parties detected</div>';
  if (!hasIdentifiers) listIdentifiers.innerHTML = '<div class="field-placeholder">No identifiers detected</div>';
}

function renderAuditTrail(auditTrail) {
  auditTimeline.innerHTML = '';
  if (!auditTrail || auditTrail.length === 0) {
    auditTimeline.innerHTML = '<div class="audit-placeholder">No audit events recorded.</div>';
    return;
  }

  auditTrail.forEach(entry => {
    const row = document.createElement('div');
    row.className = 'audit-entry';
    const timeStr = entry.timestamp.substring(11, 19);
    const detailStr = JSON.stringify(entry.detail || {});

    row.innerHTML = `
      <div class="audit-top">
        <span class="audit-action">${escapeHtml(entry.action)}</span>
        <span class="audit-time">${timeStr} UTC</span>
      </div>
      <div class="audit-detail">${escapeHtml(detailStr.length > 80 ? detailStr.substring(0, 77) + '...' : detailStr)}</div>
    `;
    auditTimeline.appendChild(row);
  });
}

// ============================================================================
// Image & Bounding Box Overlay
// ============================================================================
function setImageView(viewType) {
  if (!state.currentDocId) return;
  state.activeView = viewType;

  if (viewType === 'preprocessed') {
    tabPreprocessed.classList.add('active');
    tabOriginal.classList.remove('active');
    docImage.src = `/api/v1/documents/${state.currentDocId}/image?type=preprocessed`;
    bboxOverlay.style.display = 'block';
  } else {
    tabOriginal.classList.add('active');
    tabPreprocessed.classList.remove('active');
    docImage.src = `/api/v1/documents/${state.currentDocId}/image?type=raw`;
    // Hide bounding boxes on raw if distorted
    bboxOverlay.style.display = 'none';
  }

  docImage.onload = () => {
    emptyState.style.display = 'none';
    imageStage.style.display = 'block';
    renderBoundingBoxes();
  };
}

function renderBoundingBoxes() {
  bboxOverlay.innerHTML = '';
  if (!state.dossierData || !state.dossierData.field_items) return;

  state.dossierData.field_items.forEach((item, index) => {
    if (!item.bounding_box) return;

    const box = item.bounding_box;
    // Normalized 0-1000 coordinates convert to percentages
    const left = (box.x / 1000) * 100;
    const top = (box.y / 1000) * 100;
    const width = (box.w / 1000) * 100;
    const height = (box.h / 1000) * 100;

    const rect = document.createElement('div');
    rect.className = `bbox-rect ${item.field_name.startsWith('amount:') ? 'bbox-amount' : ''}`;
    rect.dataset.index = index;
    rect.style.left = `${left}%`;
    rect.style.top = `${top}%`;
    rect.style.width = `${width}%`;
    rect.style.height = `${height}%`;
    rect.title = `${item.field_name}: ${item.field_value} (${Math.round(item.confidence * 100)}%)`;

    rect.addEventListener('mouseenter', () => highlightField(index));
    rect.addEventListener('mouseleave', () => unhighlightField());

    bboxOverlay.appendChild(rect);
  });
}

function highlightField(index) {
  // Highlight bounding box
  document.querySelectorAll('.bbox-rect').forEach(el => {
    if (parseInt(el.dataset.index) === index) {
      el.classList.add('highlighted');
    } else {
      el.classList.remove('highlighted');
    }
  });

  // Highlight card
  document.querySelectorAll('.field-item-card').forEach(el => {
    if (parseInt(el.dataset.index) === index) {
      el.classList.add('active');
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      el.classList.remove('active');
    }
  });
}

function unhighlightField() {
  document.querySelectorAll('.bbox-rect').forEach(el => el.classList.remove('highlighted'));
  document.querySelectorAll('.field-item-card').forEach(el => el.classList.remove('active'));
}

// ============================================================================
// Progress Stepper Animation
// ============================================================================
let stepInterval = null;

function showProgress(title) {
  progressStepTitle.textContent = title;
  pipelineProgress.style.display = 'flex';
}

function hideProgress() {
  pipelineProgress.style.display = 'none';
  if (stepInterval) clearInterval(stepInterval);
}

function animateProgressSteps() {
  const steps = [
    { id: 'step-hash', title: 'Computing SHA-256 & Immutable Storage...' },
    { id: 'step-prep', title: 'OpenCV Deskew, Perspective & CLAHE...' },
    { id: 'step-cls', title: 'Classifying Document with Qwen3-VL...' },
    { id: 'step-vlm', title: 'Structured Extraction & Bounding Boxes...' },
    { id: 'step-val', title: 'Quality Gates & Arithmetic Verification...' },
  ];

  let current = 0;
  steps.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) {
      el.className = 'step-item';
    }
  });

  if (document.getElementById(steps[0].id)) {
    document.getElementById(steps[0].id).className = 'step-item active';
  }

  if (stepInterval) clearInterval(stepInterval);

  stepInterval = setInterval(() => {
    if (current < steps.length - 1) {
      const prevEl = document.getElementById(steps[current].id);
      if (prevEl) prevEl.className = 'step-item completed';
      current++;
      const nextEl = document.getElementById(steps[current].id);
      if (nextEl) nextEl.className = 'step-item active';
      progressStepTitle.textContent = steps[current].title;
    }
  }, 2500);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
