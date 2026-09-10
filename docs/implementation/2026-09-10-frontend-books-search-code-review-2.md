# Code Review 2: Frontend Books Search

## Summary

The current frontend implements the earlier Books catalogue CRUD slice, not the requested search/filter slice. There is no uncommitted diff for the named implementation files; their current content is the committed implementation at `7fd333f`. The requested design file `docs/tech-design/2026-09-10-frontend-books-search-td.md` is absent, so plan-specific compliance can only be assessed from the stated review requirements and the available catalogue plan.

The existing catalogue has basic authenticated list/detail/CRUD flows and passes the current unit tests and TypeScript build. It does not provide query parameters, URL encoding, inclusive UTC filter dates, draft/applied filter state, clear/apply actions, or race-safe asynchronous state handling.

## Findings

- **Severity: High**
  **Issue:** The requested search and date-filter feature is not implemented.
  **Path/evidence:** `frontend/src/api/books.ts:89-95` exposes only `listBooks(token)` and always requests `/books`. `frontend/src/App.tsx:274-279` renders the catalogue without search/date inputs, applied filters, clear/apply controls, or a filtered-empty state.
  **Recommendation:** Add an API options object and construct only applied `q`, `date_from`, and `date_to` parameters. Keep draft form values separate from applied values, and make initial load, retry, and mutation refresh use the applied state.

- **Severity: High**
  **Issue:** URL construction and encoding do not support the search contract.
  **Path/evidence:** `frontend/src/api/books.ts:90` uses a literal path with no query builder. The current numeric detail/mutation paths at `:98`, `:113`, and `:122` are safe for their typed numeric IDs, but there is no implementation or test for spaces, reserved characters, or Unicode search text.
  **Recommendation:** Use `URLSearchParams`, omit empty parameters, and test exact request URLs for whitespace, punctuation, Unicode, and simultaneous filters. Do not interpolate raw search text into a URL.

- **Severity: High**
  **Issue:** Inclusive UTC date semantics and reversed-range validation are absent.
  **Path/evidence:** `frontend/src/App.tsx:43-45` converts CRUD form dates only to UTC midnight. No filter dates exist, so the implementation neither validates `date_from <= date_to` nor converts an inclusive upper calendar date to the end of that UTC day.
  **Recommendation:** Validate the draft range before requesting and serialize the lower bound at UTC start-of-day and the inclusive upper bound at UTC end-of-day, according to the backend contract. Add boundary tests for midnight, final-second inclusion, reversed ranges, and local timezone offsets.

- **Severity: High**
  **Issue:** Overlapping asynchronous list/detail requests are not guarded against stale results.
  **Path/evidence:** `refreshBooks` at `frontend/src/App.tsx:139-150` always applies its response to `books`; `openDetail` at `:153-166` always applies its response to `selectedBook` and loading state. There is no request sequence, abort signal, session identity check, or view/parameter check. Sign-out at `:130-137` does not cancel requests already in flight.
  **Recommendation:** Abort or sequence list and detail requests and ignore results that no longer match the active session, view, and request parameters. Test out-of-order initial load, retry, filter apply, detail navigation, sign-out, and post-mutation responses.

- **Severity: Medium**
  **Issue:** Apply, clear, retry, and mutation-refresh semantics required for filters are missing.
  **Path/evidence:** `frontend/src/App.tsx:276` has an unparameterized retry only. Create/update and delete call `refreshBooks(session)` at `:227-228` and `:242-245`, with no filter context to preserve. There are no apply or clear actions and no defined behaviour for a failed refresh after a successful mutation.
  **Recommendation:** Treat applied filters as the single source of truth. Apply should request the new state, clear should reset draft and applied values, retry should repeat the current applied request, and successful mutations should refresh that same request. Define and test whether a refresh failure retains the mutation result or shows a stale list with an actionable error.

- **Severity: Medium**
  **Issue:** Existing authentication and CRUD flows have limited regression protection and some accessibility gaps.
  **Path/evidence:** `frontend/src/App.test.tsx` has only five UI tests and does not cover create, update, delete, 401 sign-out, 403/404/409/422 responses, network failures, retries, or stale requests. The signed-in alerts at `frontend/src/App.tsx:273`, `:276`, `:280`, and `:282-283` are not connected to the login error-summary focus mechanism; numeric field errors at `:282` lack stable IDs and `aria-describedby`. The delete dialog has no initial/return focus management, Escape handling, or `aria-describedby`.
  **Recommendation:** Preserve and extend login, role-gating, detail, and all mutation regression tests. Associate every field error with its input and make request errors and the confirmation dialog keyboard and screen-reader accessible.

- **Severity: Low**
  **Issue:** The current date display relies on a UTC conversion policy that is unrelated to, and may conflict with, the requested filter semantics.
  **Path/evidence:** `frontend/src/App.tsx:47-49` uses `toISOString().slice(0, 10)`, while the available catalogue plan describes the response date as an opaque integer and calls out unresolved date semantics. No tests cover timestamps near UTC date boundaries.
  **Recommendation:** Confirm the API's date meaning and keep display, create/update serialization, and search-bound serialization governed by one documented UTC policy. Add non-midnight boundary tests before relying on date labels.

## Plan Compliance

- **Not assessable against the named technical design:** `docs/tech-design/2026-09-10-frontend-books-search-td.md` does not exist in the current tree, and there is no working-tree diff for the named implementation files.
- **Not compliant with the requested search scope:** no search query, date filters, URL query construction, inclusive UTC bounds, reversed-range validation, draft/applied state, apply/clear controls, filtered-empty state, or filter-aware retry/mutation refresh exists.
- **Partially compliant with the available catalogue plan:** bearer-authenticated Books API operations, role-gated CRUD controls, basic list/detail/loading/empty/error states, 204 delete handling, responsive styling, and README scope notes are present.
- **Scope boundary:** The current implementation stays within the earlier frontend catalogue boundary and does not add loans, reservations, notifications, token persistence, or backend changes. That restraint is correct for the catalogue plan but does not satisfy the requested search slice.

## Validation Gaps

- `frontend/npm run test -- --run` passed: 3 files and 11 tests.
- `frontend/npm run build` passed, including TypeScript compilation.
- `frontend/npm run lint` did not produce a normal lint result; the repository wrapper reported `ESLint output (JSON parse failed: EOF while parsing a value at line 1 column 0)`. A direct lint invocation is needed to distinguish tooling failure from source findings.
- No test validates query URL encoding, omitted empty parameters, inclusive UTC boundaries, reversed ranges, draft versus applied state, clear/apply behaviour, filtered retry, or post-mutation filtered refresh.
- No test validates stale list/detail responses after navigation, retry, sign-out, filter changes, or mutations.
- No browser or assistive-technology validation demonstrates focus behaviour, dialog keyboard handling, mobile layout, or live announcements.
- No integration validation confirms the frontend request shape against the deployed backend search contract. The requested design file and any search-specific implementation note were unavailable for comparison.

## Residual Risk

The current product can regress existing login, role-gated CRUD, and detail behaviour without detection, and it cannot deliver the requested search experience. If filters are added without request identity handling, slow responses can still overwrite newer results or repopulate signed-out state. Date-range interoperability remains especially risky until the backend query contract and UTC boundary representation are confirmed. The current scope does not expose loan or other out-of-scope workflows, but that does not compensate for the missing search functionality.
