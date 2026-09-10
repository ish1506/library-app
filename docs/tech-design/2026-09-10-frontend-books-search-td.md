# Frontend Catalogue Search and Date Filtering

## Goal

Extend the existing protected Books catalogue so authenticated users can search by title or author and filter by an inclusive publication-date range through the improved `GET /books` API. Users can combine the text query with either or both date bounds, apply or clear the filters explicitly, and see deterministic loading, empty, and error states without changing the existing detail or admin CRUD flows.

Success means the frontend sends only the active filters using the documented query parameter names, encodes user input safely, preserves the current role/session behavior, and provides an accessible responsive filter experience for both `ADMIN` and `USER` catalogue views.

## Current State

- `frontend/` is a React 19, TypeScript, Vite application with the protected catalogue implemented in `frontend/src/App.tsx`.
- `frontend/src/api/books.ts` has native-`fetch` methods for list, detail, create, update, and delete, but `listBooks(token)` cannot currently receive query parameters.
- The catalogue list is loaded by `refreshBooks` after login and after successful mutations. It renders loading, error, empty, and populated states; detail and admin CRUD views are already present.
- `frontend/src/api/books.ts` models `Book.date` as an epoch-second integer returned by the API. The search API accepts `date_from` and `date_to` as offset-aware ISO 8601 datetime strings.
- The backend supports `GET /books?q=<text>&date_from=<datetime>&date_to=<datetime>`. `q` is trimmed, must not be blank, searches title and author with PostgreSQL web-search syntax, and all supplied filters are combined with `AND`.
- Date bounds are inclusive and require a timezone offset. The frontend date inputs will expose calendar dates and convert them to UTC day boundaries before sending the request.
- `frontend/vite.config.ts` already proxies `/books`; no proxy change is required.
- Existing frontend tests use Vitest and React Testing Library with mocked `fetch` and mocked Books API methods. The worktree currently contains backend search changes and must not have those changes reverted or reformatted by frontend work.

## Decisions

- Place a filter form at the top of the existing catalogue list view, visible to both roles. It contains a text search field, `Publication date from`, `Publication date to`, an `Apply filters` button, and a `Clear filters` button.
- Use explicit apply/clear actions rather than firing a request on every keystroke. Keep draft form values separate from the applied filter state so users can edit controls without changing the displayed result until they submit.
- Trim `q` in the client before applying. An empty trimmed value is omitted from the request; the backend remains authoritative for validation and web-search syntax such as quoted phrases and minus-prefixed terms.
- Convert a selected `date_from` calendar value `YYYY-MM-DD` to `YYYY-MM-DDT00:00:00Z`. Convert `date_to` to `YYYY-MM-DDT23:59:59Z`, making the UI’s date-only range inclusive for all publication timestamps on the selected days.
- Reject a draft range where both dates are supplied and `date_from` is after `date_to` before making a request. Announce the error beside the filter form and keep the currently displayed results and applied filters unchanged.
- Build query strings with `URLSearchParams`; omit absent filters and never concatenate raw user input into the URL. The no-filter request remains exactly `/books`.
- Extend `listBooks` with an optional filters argument rather than adding a second list method. Preserve the existing bearer header, response guard, error normalization, and `VITE_API_BASE_URL` behavior.
- Reset the applied and draft filters when signing out. Successful create, update, delete, and retry operations refresh using the current applied filters so the user remains in the same catalogue context.
- Treat a successful filtered response with zero books as a distinct empty-search state, showing the active criteria and a clear action; retain the existing unfiltered empty-catalogue message when no filters are applied.
- Keep detail navigation, admin-only mutation controls, in-memory authentication, and the current role capability model unchanged. Do not add URL routing, persistent filter storage, pagination, sorting controls, autocomplete, fuzzy search, or frontend date formatting changes outside the filter controls.
- Handle `401` as the existing session-expired/sign-out path, `403` as a catalogue access error, and network/422/unexpected responses through the existing `BooksApiError` presentation path.

## Diagram

```mermaid
flowchart LR
    D[Draft filter form] -->|Apply| A[Applied filters]
    A -->|URLSearchParams| C[listBooks]
    C --> B[GET /books]
    B --> R[Filtered catalogue states]
    R -->|View details| V[Existing detail view]
```

## Implementation Steps

1. Add `BookListFilters` and an optional filters parameter to `frontend/src/api/books.ts`. Construct `/books` with `URLSearchParams`, sending `q`, `date_from`, and `date_to` only when present; preserve `/books` for an empty filter object.
2. Add API-client tests for no filters, title/author text queries, one-sided date bounds, combined filters, URL encoding of spaces/quotes/minus syntax, and omission of blank optional values. Keep bearer headers and existing response/error tests covered.
3. Add draft and applied filter state to `App.tsx`, plus a small conversion/validation helper for calendar dates and the inclusive UTC date bounds. Clear filter state as part of sign-out and initialize it when entering the catalogue.
4. Update `refreshBooks` and all mutation refresh paths to call `listBooks(token, appliedFilters)`. Ensure retry uses the same applied filters and that stale list errors/loading state cannot overwrite a newer successful apply operation.
5. Render the accessible filter form above the catalogue list. Use labels, controlled inputs, `aria-describedby` for range validation, `aria-live`/alert feedback for invalid ranges and request failures, disabled pending controls, and a clear action that immediately reloads the unfiltered catalogue.
6. Render separate unfiltered-empty and filtered-empty messages. Include a concise summary of active criteria and a clear-filters action without exposing raw implementation details or changing the existing book-card/detail markup.
7. Extend `App.test.tsx` for applying combined filters, clearing filters, one-sided bounds, invalid reversed ranges without a request, filtered empty results, preserving filters across retry/mutation refresh, and retaining admin/user control differences.
8. Update the root README frontend section with the available search/date filters, inclusive date semantics, and the explicit apply behavior. Do not modify backend documentation or the generated OpenAPI file in this frontend slice.

## Files and Interfaces

- `frontend/src/api/books.ts`: add `BookListFilters` and optional query-string construction to `listBooks`.
- `frontend/src/api/books.test.ts`: request construction, encoding, omission, and error-path coverage for list filters.
- `frontend/src/App.tsx`: draft/applied filter state, date conversion/validation, filtered refresh calls, filter form, and empty-state messaging.
- `frontend/src/App.test.tsx`: user-facing search, date-range, clear/retry, validation, and regression coverage.
- `frontend/src/App.css`: responsive filter layout, active-filter summary, validation styling, and mobile control layout consistent with the existing catalogue.
- `README.md`: frontend search and date-filter usage notes.

## Validation

- From `frontend/`, run `npm run lint`, `npm run test`, and `npm run build`.
- Verify no-filter list requests call `/books` without a trailing `?` or filter parameters.
- Verify text-only, lower-bound-only, upper-bound-only, and combined requests produce the expected encoded query string and always include the bearer token.
- Verify `date_from=2024-01-01` becomes `2024-01-01T00:00:00Z` and `date_to=2024-01-31` becomes `2024-01-31T23:59:59Z`.
- Verify blank text is omitted, reversed dates produce an accessible client-side error without a request, and clearing filters reloads the full catalogue.
- Verify filtered zero results, network failure, `401`, `403`, `422`, and malformed successful responses remain actionable and do not crash the app.
- Verify admin CRUD refreshes preserve active filters, user sessions still have no mutation controls, and sign-out clears filters and results.
- Manually test keyboard navigation, focus visibility, screen-reader announcements, narrow mobile layout, quoted/multi-word `q`, and a date range containing a boundary timestamp.

## Risks and Open Questions

- The UI intentionally treats date bounds as calendar days in UTC. If product users expect local-time boundaries, the API contract needs a timezone-aware UX decision rather than silently changing conversion rules.
- PostgreSQL `websearch_to_tsquery` supports token, phrase, and exclusion syntax but not arbitrary substring or typo matching; this plan exposes that behavior without adding client-side filtering.
- The current App component is a large stateful module. Keep this slice minimal; extract a reusable filter component only if the resulting JSX or tests become difficult to reason about.
- There is no pagination. Filtered requests still return the complete matching catalogue, consistent with the current endpoint contract.

## Handoff Notes

- Implement frontend files only. Do not change backend routes, migrations, indexes, OpenAPI output, or backend tests.
- Keep `listBooks` backward-compatible for existing callers by making filters optional.
- Do not debounce, persist, route, or cache filters in this slice.
- Preserve all existing worktree changes, especially the backend search implementation and its generated API documentation.
