# SANKET / Clarity Investigation Engine — V1.10.2

## Frontend ingestion discoverability patch

V1.10.2 keeps the V1.10.1 professional minimal redesign while restoring a clearly discoverable ingestion entry point.

### Changes
- Persistent top-bar **Ingest documents** action.
- Clear zero-state for an empty case with **Load sample case** and **Ingest documents** actions.
- Existing drag-and-drop ingestion remains intact.
- Existing dataset selector remains intact.
- No backend/intelligence changes.
- All V1.10 capabilities remain accessible after ingestion.

### Acceptance target
- Backend test suite remains green.
- Next.js production build remains green.
- A user can start from an empty case and reach ingestion without hunting through the UI.
