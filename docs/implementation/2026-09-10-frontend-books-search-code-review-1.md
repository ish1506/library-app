# Code Review 1: Frontend Books Search

## Summary

The requested frontend search implementation is not present in the reviewed code. The worktree is `main` at `f0d3e35`; the frontend catalogue implementation is the earlier `7fd333f` commit. The requested design and implementation-note paths are absent. The current frontend supports catalogue CRUD, but it has no search or date filters, no filter URL construction, and no inclusive date-range validation/conversion. Existing tests pass, but they cover only a small subset of the required behaviour and do not protect the requested feature or several existing flows.

## Findings

- **Severity:** High
  **Issue:** The requested frontend search/filter feature is missing.
  **Evidence:** `frontend/src/api/books.ts:89-95` exposes `listBooks(token)` with no query parameters; `frontend/src/App.tsx:274-279` renders only the catalogue heading/list and has no query inputs, draft/applied filter state, apply action, clear action, or filtered-empty state.
  **Recommendation:** Implement the planned `q`, `date_from`, and `date_to` flow in the frontend, keeping filter state separate from applied state and passing only applied values to `listBooks`.

- **Severity:** High
  **Issue:** Inclusive UTC date filtering and reversed-range validation are absent.
  **Evidence:** `frontend/src/App.tsx:43-45` only formats CRUD write dates as midnight UTC; it does not convert a selected inclusive `date_to` calendar day to the end of that UTC day, nor validate `date_from <= date_to`. No filter date inputs or corresponding tests exist.
  **Recommendation:** Convert calendar bounds explicitly in UTC, with the upper bound inclusive through the end of the selected UTC day, reject reversed ranges before requesting, and test dates around timezone offsets and exact boundary timestamps.

- **Severity:** High
  **Issue:** Stale asynchronous requests can overwrite newer UI state.
  **Evidence:** `frontend/src/App.tsx:139-150` applies every `refreshBooks` result directly to `books`, and `frontend/src/App.tsx:153-166` applies every `openDetail` result directly to `selectedBook`. There is no request sequence, session identity check, or `AbortController`. A slow earlier list/detail request can replace a later result, including after navigation or sign-out; a refresh started before sign-out can also set loading/error state afterward.
  **Recommendation:** Abort or sequence list/detail requests and ignore results that no longer match the active session, view, and request parameters. Cover out-of-order list, detail, retry, and post-mutation responses with tests.

- **Severity:** Medium
  **Issue:** CRUD refreshes do not preserve the active filter context because filtering is not implemented, and refresh failures can leave the UI in an ambiguous state.
  **Evidence:** `frontend/src/App.tsx:227-228` and `:242-245` navigate to the list and call unparameterized `refreshBooks(session)`. The code does not retain any applied search/date criteria, and it does not define whether a failed post-mutation refresh should keep the mutation result visible or display the prior list.
  **Recommendation:** Keep applied filters as the single source of truth for initial loads, retry, and post-create/update/delete refreshes. Test successful CRUD followed by filtered refresh, refresh failure, and retry.

- **Severity:** Medium
  **Issue:** Accessibility coverage and implementation are incomplete for request errors and the delete confirmation.
  **Evidence:** The signed-in request error at `frontend/src/App.tsx:273` has `role="alert"` but is not connected to the focused `errorSummary` ref used by login at `:259`; the delete dialog at `:283` has no focus placement, focus trap, Escape handling, or `aria-describedby`. Numeric validation messages at `:282` have no `id` and their inputs have no `aria-describedby`.
  **Recommendation:** Move focus to actionable request errors where appropriate, give every field error a stable association, and implement an accessible confirmation dialog with initial focus, return focus, and keyboard dismissal. Add keyboard and screen-reader-oriented tests.

- **Severity:** Medium
  **Issue:** Existing login and CRUD/detail behaviour has insufficient regression protection.
  **Evidence:** `frontend/src/App.test.tsx` contains 5 tests and no create, update, delete, retry, 401, 403, 404, 409, 422, network, stale-request, or validation tests. The catalogue change removed prior coverage for invalid credentials, pending login, and API-error focus from the test file. The only detail test uses epoch `0` and does not exercise non-midnight or timezone-sensitive values.
  **Recommendation:** Restore the existing login regression tests and add UI tests for all planned states and mutation paths, including rejected requests and out-of-order promises.

- **Severity:** Low
  **Issue:** URL encoding cannot currently be verified because the API client has no query builder.
  **Evidence:** `frontend/src/api/books.ts:89-90` always requests the literal `/books`; `frontend/src/api/books.test.ts` checks only that unparameterized path. Search terms containing spaces, punctuation, or non-ASCII characters therefore have no supported encoded request path.
  **Recommendation:** Construct query parameters with `URLSearchParams` rather than string interpolation, omit empty values, and test encoding for spaces, reserved characters, and Unicode.

- **Severity:** Low
  **Issue:** Role decoding is an unverified UI hint, but the implementation relies on it without a dedicated test for malformed or unsupported tokens.
  **Evidence:** `frontend/src/App.tsx:32-40` decodes the JWT payload locally and `:111-114` rejects unsupported roles. This is acceptable only as capability selection because API calls still carry the bearer token, but no test covers malformed base64, missing claims, or a forged role followed by a forbidden mutation.
  **Recommendation:** Keep server authorization authoritative and add focused tests proving malformed/unsupported tokens fail closed and `403` responses remain handled.

## Plan Compliance

- **Not compliant:** The requested frontend search design path `docs/tech-design/2026-09-10-frontend-books-search-td.md` is absent. The available `docs/tech-design/2026-09-10-book-catalogue-search-td.md` is backend-only and explicitly excludes frontend changes.
- **Not compliant:** `listBooks` does not accept optional encoded filters, and the UI has no draft/applied filters, apply/clear controls, filtered-empty state, inclusive UTC conversion, or reversed-range validation.
- **Not compliant:** Search/date API tests, UI filter tests, stale-request tests, retry/filter-refresh tests, and README documentation for the frontend search slice are absent.
- **Partially compliant with the earlier catalogue scope:** bearer requests, role-gated CRUD controls, 204 delete handling, basic list/detail states, and a development `/books` proxy are implemented. The current API client preserves the documented CRUD shapes and validates book response shapes.

## Validation Gaps

- The requested design and implementation note could not be inspected because neither requested file exists on the current branch or `feature/books-search`.
- `frontend/npm run test -- --run` passed: 3 files and 11 tests.
- `frontend/npm run build` passed, including TypeScript compilation.
- `frontend/npm run lint` did not produce a normal lint result; the repository wrapper reported `ESLint output (JSON parse failed: EOF while parsing a value at line 1 column 0)`. A direct lint invocation should be run to determine whether this is tooling/output-wrapper failure or a source issue.
- No live browser, keyboard, mobile-layout, or backend integration validation was demonstrated.
- No test validates the backend search contract, inclusive date boundaries, URL encoding, or the required user/admin behaviour with filtered results.

## Residual Risk

The reviewed frontend can regress existing login/detail/admin/user behaviour without detection, and it does not implement the requested search slice at all. Even after adding filters, request races and refresh semantics need explicit handling because the current component launches overlapping asynchronous operations and uses shared state without cancellation or identity checks. The backend search design also documents a separate API contract; frontend implementation should be aligned with the actual deployed OpenAPI and backend validation rules before release.
