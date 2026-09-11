# Graph Report - library-app  (2026-09-11)

## Corpus Check
- 108 files · ~50,392 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 858 nodes · 1346 edges · 90 communities (67 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 41 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `81f425f6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- books.py
- schemas/auth.py
- devDependencies
- FakeSession
- BookLoan
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
- seed_user.py
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
- main.py
- notifications.ts
- BookLoan
- BookReservation
- BookReservation
- Library App
- test_late_fees.py
- Library Frontend
- Development Setup
- patch
- Reservation Lifecycle
- BookLoan
- BookReservation
- test_book_loans.py
- BookCreate
- BookListQuery
- BookUpdate
- SortBy
- test_book_reservations.py
- test_login.py
- test_database.py
- get
- Book

## God Nodes (most connected - your core abstractions)
1. `User` - 30 edges
2. `App()` - 28 edges
3. `FakeSession` - 24 edges
4. `compilerOptions` - 18 edges
5. `client_for()` - 15 edges
6. `BookReservation` - 15 edges
7. `compilerOptions` - 15 edges
8. `timestamp()` - 13 edges
9. `expire_ready_reservations()` - 13 edges
10. `BookLoan` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Book` --uses--> `Base`  [INFERRED]
  backend/app/models/book.py → backend/app/database.py
- `test_shutdown_disposes_async_engine()` --indirect_call--> `main()`  [INFERRED]
  backend/tests/test_lifespan.py → backend/scripts/seed_user.py
- `BookLoan` --uses--> `LoanStatus`  [INFERRED]
  backend/app/models/book_loan.py → backend/app/models/enums.py
- `BookReservation` --uses--> `ReservationStatus`  [INFERRED]
  backend/app/models/book_reservation.py → backend/app/models/enums.py
- `BookLoanResponse` --uses--> `LoanStatus`  [INFERRED]
  backend/app/schemas/book_loan.py → backend/app/models/enums.py

## Import Cycles
- None detected.

## Communities (90 total, 23 thin omitted)

### Community 0 - "books.py"
Cohesion: 0.07
Nodes (81): get_db(), AsyncSession, BookLoan, Base, BookReservation, Base, LoanStatus, NotificationType (+73 more)

### Community 1 - "schemas/auth.py"
Cohesion: 0.67
Nodes (3): LoginRequest, BaseModel, TokenResponse

### Community 2 - "devDependencies"
Cohesion: 0.05
Nodes (42): @biomejs/biome, dependencies, react, react-dom, devDependencies, @biomejs/biome, jsdom, oxlint (+34 more)

### Community 3 - "FakeSession"
Cohesion: 0.15
Nodes (23): book_payload(), client_for(), ConstraintDiagnostic, DuplicateIsbnError, FakeSession, TestClient, User, ScalarResult (+15 more)

### Community 5 - "App.tsx"
Cohesion: 0.10
Nodes (20): BookReservation, App(), availability(), DateFilterDraft, emptyDateFilters, emptyForm, filtersAreActive(), filterSummary() (+12 more)

### Community 6 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+16 more)

### Community 7 - "routers/auth.py"
Cohesion: 0.11
Nodes (13): get_settings(), Settings, Base, Book, login(), AsyncSession, post, create_access_token() (+5 more)

### Community 8 - "seed_books.py"
Cohesion: 0.17
Nodes (24): LateFeePolicy, LibraryPolicy, load_policy(), BaseModel, ReservationPolicy, acquire_manifest(), choose_isbn(), comparable_title() (+16 more)

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
Cohesion: 0.18
Nodes (11): Allowed Transitions, Cross-Entity Transitions, Developer Guide, Domain Model, Expiry Processing, Inventory Invariant, Late-Fee State, Loan Lifecycle (+3 more)

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

### Community 64 - "main.py"
Cohesion: 0.32
Nodes (7): health_check(), lifespan(), log_request(), reservation_expiry_worker(), get, middleware, Request

### Community 65 - "notifications.ts"
Cohesion: 0.20
Nodes (13): apiBaseUrl, errorMessage(), isNotification(), isRecord(), listUnreadNotifications(), markNotificationRead(), Notification, NotificationsApiError (+5 more)

### Community 70 - "Library App"
Cohesion: 0.20
Nodes (10): Assumptions and Design Decisions, Catalogue Management, Documentation, Lending, Library App, Out of Scope and Potential Improvements, Reservations and Notifications, Supported Features (+2 more)

### Community 72 - "Library Frontend"
Cohesion: 0.33
Nodes (6): Application Behavior, Checks, Configuration, Library Frontend, Requirements, Run Locally

### Community 73 - "Development Setup"
Cohesion: 0.33
Nodes (6): Configure the Backend, Development Setup, Install Dependencies, Prerequisites, Run Checks, Run the Application

### Community 76 - "Reservation Lifecycle"
Cohesion: 0.50
Nodes (4): Allocation Rules, Allowed Transitions, Reservation Lifecycle, States

### Community 79 - "test_book_loans.py"
Cohesion: 0.27
Nodes (8): AuthSession, loan_fixture(), LoanFixture, fixture, User, test_concurrent_borrowing_allows_only_final_copy(), test_loan_lifecycle_inventory_and_history(), test_loan_routes_require_authentication_and_roles()

### Community 84 - "test_book_reservations.py"
Cohesion: 0.32
Nodes (9): AuthSession, headers(), fixture, User, reservation_fixture(), ReservationFixture, test_concurrent_reservations_allocate_one_queue_slot(), test_reservation_lifecycle_notifications_and_expiry() (+1 more)

### Community 85 - "test_login.py"
Cohesion: 0.32
Nodes (8): client_for(), FakeSession, TestClient, User, test_login_logs_request_without_credentials(), test_malformed_login_body_is_rejected(), test_unknown_and_wrong_password_have_identical_401_responses(), test_user_and_admin_can_login()

## Knowledge Gaps
- **327 isolated node(s):** `ConstraintDiagnostic`, `$schema`, `.opencode/plugins/graphify.js`, `library-backend`, `dev.sh script` (+322 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `books.py` to `routers/auth.py`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `BookListQuery` connect `BookListQuery` to `books.py`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **What connects `ConstraintDiagnostic`, `$schema`, `.opencode/plugins/graphify.js` to the rest of the system?**
  _327 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `books.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06690511256048812 - nodes in this community are weakly interconnected._
- **Should `devDependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.046511627906976744 - nodes in this community are weakly interconnected._
- **Should `FakeSession` be split into smaller, more focused modules?**
  _Cohesion score 0.1492063492063492 - nodes in this community are weakly interconnected._
- **Should `App.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10256410256410256 - nodes in this community are weakly interconnected._