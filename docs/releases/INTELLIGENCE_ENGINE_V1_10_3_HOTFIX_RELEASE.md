# SANKET Intelligence Engine — V1.10.3 Hotfix

## Fix
- Removed an extra comma in `frontend/src/store/useCaseStore.ts` that caused the Next.js/Turbopack parser to fail at line 346.

## Scope
- No backend behavior changed.
- No ingestion/progress logic changed.
- No intelligence or evidence behavior changed.
- This is a source-level frontend syntax correction only.

## Validation target
- Python test suite remains unchanged.
- Frontend `next build` must complete successfully on the user's Windows environment.
