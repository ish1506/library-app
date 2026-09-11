# Graph Report - library-app  (2026-09-11)

## Corpus Check
- 109 files · ~51,043 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 856 nodes · 1526 edges · 75 communities (66 shown, 9 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 83 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3a9c24b6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- User
- config.py
- devDependencies
- test_books.py
- model_validator
- App.tsx
- compilerOptions
- routers/auth.py
- seed_books.py
- formatter
- books.ts
- loans.ts
- Library Backend
- auth.ts
- test_seed_books.py
- App.test.tsx
- User Management Login API
- database_url
- tsconfig.json
- dev.sh
- test.sh
- library-backend
- Admin Book Catalogue API
- Book Catalogue Search and Date Filtering API
- Book Loans API
- Frontend Books Catalogue
- Frontend Catalogue Search and Date Filtering
- Frontend Loaning A Book
- Frontend Login
- Open Library Book Seed
- Book Reservations and In-App Notifications
- Async Database Client Refactor Plan
- plugins
- Developer Guide
- Code Review 1: Book Loans API
- Code Review 2: Book Loans API
- Code Review 1: Frontend Books Search
- Code Review 2: Frontend Books Search
- Code Review 3: Frontend Catalogue Search and Date Filtering
- Code Review 1: Async Database Client Refactor
- Frontend Books Search Implementation
- Persisted Late Fees
- opencode.json
- Library App
- Backend Agent Instructions
- reservations.ts
- BookListQuery
- compilerOptions
- Books Catalogue Sorting
- Books Sorting Backend Implementation
- get
- notifications.ts
- HTTPException
- Library App
- return_loan
- Library Frontend
- Development Setup
- Reservation Lifecycle
- Loan Lifecycle

## God Nodes (most connected - your core abstractions)
1. `User` - 68 edges
2. `App()` - 28 edges
3. `FakeSession` - 27 edges
4. `Role` - 24 edges
5. `Book` - 22 edges
6. `compilerOptions` - 18 edges
7. `BookLoan` - 15 edges
8. `create_access_token()` - 15 edges
9. `client_for()` - 15 edges
10. `compilerOptions` - 15 edges

## Surprising Connections (you probably didn't know these)
- `DuplicateIsbnError` --uses--> `Book`  [INFERRED]
  backend/tests/test_books.py → backend/app/models/book.py
- `FakeSession` --uses--> `Book`  [INFERRED]
  backend/tests/test_books.py → backend/app/models/book.py
- `ScalarResult` --uses--> `Book`  [INFERRED]
  backend/tests/test_books.py → backend/app/models/book.py
- `DuplicateIsbnError` --uses--> `Role`  [INFERRED]
  backend/tests/test_books.py → backend/app/models/enums.py
- `FakeSession` --uses--> `Role`  [INFERRED]
  backend/tests/test_books.py → backend/app/models/enums.py

## Import Cycles
- None detected.

## Communities (75 total, 9 thin omitted)

### Community 0 - "User"
Cohesion: 0.07
Nodes (67): Base, get_db(), AsyncSession, Book, BookLoan, BookReservation, LoanStatus, NotificationType (+59 more)

### Community 1 - "config.py"
Cohesion: 0.09
Nodes (18): get_settings(), Settings, LateFeePolicy, LibraryPolicy, load_policy(), BaseModel, ReservationPolicy, health_check() (+10 more)

### Community 2 - "devDependencies"
Cohesion: 0.05
Nodes (42): @biomejs/biome, dependencies, react, react-dom, devDependencies, @biomejs/biome, jsdom, oxlint (+34 more)

### Community 3 - "test_books.py"
Cohesion: 0.16
Nodes (22): book_payload(), client_for(), DuplicateIsbnError, FakeSession, Book, TestClient, ScalarResult, test_admin_can_create_list_get_update_and_delete_books() (+14 more)

### Community 5 - "App.tsx"
Cohesion: 0.10
Nodes (20): BookReservation, App(), availability(), DateFilterDraft, emptyDateFilters, emptyForm, filtersAreActive(), filterSummary() (+12 more)

### Community 6 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+16 more)

### Community 7 - "routers/auth.py"
Cohesion: 0.33
Nodes (7): login(), AsyncSession, post, LoginRequest, BaseModel, TokenResponse, TokenResponse

### Community 8 - "seed_books.py"
Cohesion: 0.29
Nodes (19): acquire_manifest(), choose_isbn(), comparable_title(), date_to_timestamp(), document_isbns(), isbn13(), load_books(), main() (+11 more)

### Community 9 - "formatter"
Cohesion: 0.09
Nodes (22): files, includes, formatter, attributePosition, bracketSameLine, bracketSpacing, enabled, formatWithErrors (+14 more)

### Community 10 - "books.ts"
Cohesion: 0.14
Nodes (19): apiBaseUrl, Book, BookCreate, BookListFilters, BooksApiError, BookSortBy, BookSortOrder, BookUpdate (+11 more)

### Community 11 - "loans.ts"
Cohesion: 0.19
Nodes (16): apiBaseUrl, BookLoan, borrowBook(), errorMessage(), isBookLoan(), isRecord(), listBookLoans(), listMyLoans() (+8 more)

### Community 12 - "Library Backend"
Cohesion: 0.15
Nodes (13): Book loans, Books catalogue, Configuration, Library Backend, Login, Optional: Refresh the Seed Data, Provision an account, Requirements (+5 more)

### Community 13 - "auth.ts"
Cohesion: 0.19
Nodes (13): apiBaseUrl, ApiError, isApiError(), isTokenResponse(), isValidationError(), login(), LoginCredentials, LoginResult (+5 more)

### Community 14 - "test_seed_books.py"
Cohesion: 0.27
Nodes (7): document(), row(), test_batch_reports_duplicate_isbn(), test_dry_run_does_not_open_session(), test_isbn_selection_and_normalization(), test_selection_prefers_exact_title_and_metadata(), test_transaction_failure_propagates_and_rolls_back()

### Community 15 - "App.test.tsx"
Cohesion: 0.15
Nodes (12): borrowBookMock, createReservationMock, getBookMock, listBookLoansMock, listBooksMock, listMyLoansMock, listMyReservationsMock, listUnreadNotificationsMock (+4 more)

### Community 16 - "User Management Login API"
Cohesion: 0.18
Nodes (10): Current State, Decisions, Diagram, Files and Interfaces, Goal, Handoff Notes, Implementation Steps, Risks and Open Questions (+2 more)

### Community 35 - "Admin Book Catalogue API"
Cohesion: 0.18
Nodes (10): Admin Book Catalogue API, Current State, Decisions, Diagram, Files and Interfaces, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 36 - "Book Catalogue Search and Date Filtering API"
Cohesion: 0.18
Nodes (10): Book Catalogue Search and Date Filtering API, Current State, Decisions, Files and Interfaces, Goal, Handoff Notes, Implementation Steps, Interface (+2 more)

### Community 37 - "Book Loans API"
Cohesion: 0.18
Nodes (10): Book Loans API, Current State, Decisions, Diagram, Files and Interfaces, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 38 - "Frontend Books Catalogue"
Cohesion: 0.18
Nodes (10): Current State, Decisions, Diagram, Files and Interfaces, Frontend Books Catalogue, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 39 - "Frontend Catalogue Search and Date Filtering"
Cohesion: 0.18
Nodes (10): Current State, Decisions, Diagram, Files and Interfaces, Frontend Catalogue Search and Date Filtering, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 40 - "Frontend Loaning A Book"
Cohesion: 0.18
Nodes (10): Current State, Decisions, Diagram, Files and Interfaces, Frontend Loaning A Book, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 41 - "Frontend Login"
Cohesion: 0.18
Nodes (10): Current State, Decisions, Diagram, Files and Interfaces, Frontend Login, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 42 - "Open Library Book Seed"
Cohesion: 0.18
Nodes (10): Current State, Decisions, Diagram, Files and Interfaces, Goal, Handoff Notes, Implementation Steps, Open Library Book Seed (+2 more)

### Community 43 - "Book Reservations and In-App Notifications"
Cohesion: 0.18
Nodes (10): Book Reservations and In-App Notifications, Current State, Decisions, Diagram, Files and Interfaces, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 44 - "Async Database Client Refactor Plan"
Cohesion: 0.20
Nodes (9): Async Database Client Refactor Plan, Current State, Decisions, Files and Interfaces, Goal, Handoff Notes, Implementation Steps, Risks and Open Questions (+1 more)

### Community 45 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 46 - "Developer Guide"
Cohesion: 0.25
Nodes (8): Cross-Entity Transitions, Developer Guide, Docker Runtime, Domain Model, Expiry Processing, Inventory Invariant, Notification Lifecycle, System Overview

### Community 47 - "Code Review 1: Book Loans API"
Cohesion: 0.29
Nodes (6): Code Review 1: Book Loans API, Findings, Plan Compliance, Residual Risk, Summary, Validation Gaps

### Community 48 - "Code Review 2: Book Loans API"
Cohesion: 0.29
Nodes (6): Code Review 2: Book Loans API, Findings, Prior-Finding Resolution, Residual Risk, Summary, Validation Gaps

### Community 49 - "Code Review 1: Frontend Books Search"
Cohesion: 0.29
Nodes (6): Code Review 1: Frontend Books Search, Findings, Plan Compliance, Residual Risk, Summary, Validation Gaps

### Community 50 - "Code Review 2: Frontend Books Search"
Cohesion: 0.29
Nodes (6): Code Review 2: Frontend Books Search, Findings, Plan Compliance, Residual Risk, Summary, Validation Gaps

### Community 51 - "Code Review 3: Frontend Catalogue Search and Date Filtering"
Cohesion: 0.29
Nodes (6): Code Review 3: Frontend Catalogue Search and Date Filtering, Findings, Plan Compliance, Residual Risk, Summary, Validation Gaps

### Community 52 - "Code Review 1: Async Database Client Refactor"
Cohesion: 0.29
Nodes (6): Code Review 1: Async Database Client Refactor, Findings, Plan Compliance, Residual Risk, Summary, Validation Gaps

### Community 53 - "Frontend Books Search Implementation"
Cohesion: 0.33
Nodes (5): Blockers/assumptions, Deviations, Files changed, Frontend Books Search Implementation, Validation

### Community 54 - "Persisted Late Fees"
Cohesion: 0.18
Nodes (10): Current State, Decisions, Diagram, Files and Interfaces, Goal, Handoff Notes, Implementation Steps, Persisted Late Fees (+2 more)

### Community 55 - "opencode.json"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

### Community 59 - "reservations.ts"
Cohesion: 0.18
Nodes (17): apiBaseUrl, cancelReservation(), confirmReservation(), createReservation(), errorMessage(), isBookLoan(), isBookReservation(), isRecord() (+9 more)

### Community 60 - "BookListQuery"
Cohesion: 0.15
Nodes (13): BookCreate, BookListQuery, BookResponse, BookUpdate, _normalize_isbn(), _parse_publication_date(), Any, BaseModel (+5 more)

### Community 61 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 62 - "Books Catalogue Sorting"
Cohesion: 0.18
Nodes (10): Books Catalogue Sorting, Current State, Decisions, Diagram, Files and Interfaces, Goal, Handoff Notes, Implementation Steps (+2 more)

### Community 63 - "Books Sorting Backend Implementation"
Cohesion: 0.33
Nodes (5): Blockers and Assumptions, Books Sorting Backend Implementation, Deviations, Files, Validation

### Community 65 - "notifications.ts"
Cohesion: 0.20
Nodes (13): apiBaseUrl, errorMessage(), isNotification(), isRecord(), listUnreadNotifications(), markNotificationRead(), Notification, NotificationsApiError (+5 more)

### Community 66 - "HTTPException"
Cohesion: 0.08
Nodes (47): borrow_book(), create_book(), delete_book(), get_book(), isbn_conflict(), list_book_loans(), loan_history_conflict(), AsyncSession (+39 more)

### Community 70 - "Library App"
Cohesion: 0.20
Nodes (10): Assumptions and Design Decisions, Catalogue Management, Documentation, Lending, Library App, Out of Scope and Potential Improvements, Reservations and Notifications, Supported Features (+2 more)

### Community 71 - "return_loan"
Cohesion: 0.24
Nodes (10): list_my_loans(), AsyncSession, BookLoan, get, post, return_loan(), calculate_late_fee_cents(), test_late_fee_uses_complete_periods() (+2 more)

### Community 72 - "Library Frontend"
Cohesion: 0.33
Nodes (6): Application Behavior, Checks, Configuration, Library Frontend, Requirements, Run Locally

### Community 73 - "Development Setup"
Cohesion: 0.29
Nodes (7): Configure the Backend, Development Setup, Install Dependencies, Prerequisites, Run Checks, Run the Application, Run with Docker Compose

### Community 76 - "Reservation Lifecycle"
Cohesion: 0.50
Nodes (4): Allocation Rules, Allowed Transitions, Reservation Lifecycle, States

### Community 86 - "Loan Lifecycle"
Cohesion: 0.50
Nodes (4): Allowed Transitions, Late-Fee State, Loan Lifecycle, States

## Knowledge Gaps
- **328 isolated node(s):** `Requirements`, `Run locally`, `Run tests`, `Configuration`, `Provision an account` (+323 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `HTTPException`, `test_books.py`, `return_loan`, `routers/auth.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `Book` connect `User` to `seed_books.py`, `test_books.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `BookListQuery` connect `BookListQuery` to `User`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `User` (e.g. with `Base` and `Role`) actually correct?**
  _`User` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `FakeSession` (e.g. with `Book` and `Role`) actually correct?**
  _`FakeSession` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Role` (e.g. with `User` and `AuthSession`) actually correct?**
  _`Role` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Book` (e.g. with `Base` and `AuthSession`) actually correct?**
  _`Book` has 9 INFERRED edges - model-reasoned connections that need verification._