# Graph Report - library-app  (2026-09-11)

## Corpus Check
- 86 files · ~37,237 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 658 nodes · 1043 edges · 59 communities (52 shown, 7 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 50 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9794c1b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- books.py
- User
- devDependencies
- test_books.py
- Library Application Product Requirements Document
- App.tsx
- compilerOptions
- field_validator
- seed_books.py
- compilerOptions
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
- Reservation Lifecycle
- Code Review 1: Book Loans API
- Code Review 2: Book Loans API
- Code Review 1: Frontend Books Search
- Code Review 2: Frontend Books Search
- Code Review 3: Frontend Catalogue Search and Date Filtering
- Code Review 1: Async Database Client Refactor
- Frontend Books Search Implementation
- Bugs
- opencode.json
- Library App
- Backend Agent Instructions

## God Nodes (most connected - your core abstractions)
1. `User` - 51 edges
2. `FakeSession` - 24 edges
3. `Role` - 20 edges
4. `App()` - 19 edges
5. `compilerOptions` - 18 edges
6. `Book` - 17 edges
7. `compilerOptions` - 15 edges
8. `Library Application Product Requirements Document` - 14 edges
9. `create_access_token()` - 13 edges
10. `client_for()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Book` --uses--> `Base`  [INFERRED]
  backend/app/models/book.py → backend/app/database.py
- `Role` --uses--> `Base`  [INFERRED]
  backend/app/models/user.py → backend/app/database.py
- `User` --uses--> `Base`  [INFERRED]
  backend/app/models/user.py → backend/app/database.py
- `AuthSession` --uses--> `Book`  [INFERRED]
  backend/tests/test_book_loans.py → backend/app/models/book.py
- `LoanFixture` --uses--> `Book`  [INFERRED]
  backend/tests/test_book_loans.py → backend/app/models/book.py

## Import Cycles
- None detected.

## Communities (59 total, 7 thin omitted)

### Community 0 - "books.py"
Cohesion: 0.06
Nodes (56): get_settings(), Settings, Base, get_db(), AsyncSession, BookLoan, LoanStatus, book_search_vector() (+48 more)

### Community 1 - "User"
Cohesion: 0.12
Nodes (30): Role, User, login(), AsyncSession, post, LoginRequest, BaseModel, TokenResponse (+22 more)

### Community 2 - "devDependencies"
Cohesion: 0.05
Nodes (38): dependencies, react, react-dom, devDependencies, jsdom, oxlint, @testing-library/jest-dom, @testing-library/react (+30 more)

### Community 3 - "test_books.py"
Cohesion: 0.15
Nodes (20): Book, book_payload(), client_for(), ConstraintDiagnostic, DuplicateIsbnError, FakeSession, Book, TestClient (+12 more)

### Community 4 - "Library Application Product Requirements Document"
Cohesion: 0.06
Nodes (32): Acceptance Criteria, Acceptance Criteria, Acceptance Criteria, Acceptance Criteria, Assumptions, Core Requirements, Core Requirements, Core Requirements (+24 more)

### Community 5 - "App.tsx"
Cohesion: 0.10
Nodes (19): Book, BookCreate, BookListFilters, BookLoan, LoanStatus, App(), availability(), DateFilterDraft (+11 more)

### Community 6 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+16 more)

### Community 7 - "field_validator"
Cohesion: 0.19
Nodes (10): BookCreate, BookListQuery, BookResponse, BookUpdate, _normalize_isbn(), _parse_publication_date(), Any, BaseModel (+2 more)

### Community 8 - "seed_books.py"
Cohesion: 0.29
Nodes (19): acquire_manifest(), choose_isbn(), comparable_title(), date_to_timestamp(), document_isbns(), isbn13(), load_books(), main() (+11 more)

### Community 9 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 10 - "books.ts"
Cohesion: 0.20
Nodes (14): apiBaseUrl, BooksApiError, BookUpdate, createBook(), deleteBook(), errorMessage(), getBook(), isBook() (+6 more)

### Community 11 - "loans.ts"
Cohesion: 0.22
Nodes (14): apiBaseUrl, borrowBook(), errorMessage(), isBookLoan(), isRecord(), listBookLoans(), listMyLoans(), LoansApiError (+6 more)

### Community 12 - "Library Backend"
Cohesion: 0.13
Nodes (13): Book loans, Books catalogue, Configuration, Library Backend, Login, Provision an account, Requirements, Run locally (+5 more)

### Community 13 - "auth.ts"
Cohesion: 0.19
Nodes (13): apiBaseUrl, ApiError, isApiError(), isTokenResponse(), isValidationError(), login(), LoginCredentials, LoginResult (+5 more)

### Community 14 - "test_seed_books.py"
Cohesion: 0.27
Nodes (7): document(), row(), test_batch_reports_duplicate_isbn(), test_dry_run_does_not_open_session(), test_isbn_selection_and_normalization(), test_selection_prefers_exact_title_and_metadata(), test_transaction_failure_propagates_and_rolls_back()

### Community 15 - "App.test.tsx"
Cohesion: 0.22
Nodes (8): borrowBookMock, getBookMock, listBookLoansMock, listBooksMock, listMyLoansMock, loginMock, signIn(), token()

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

### Community 46 - "Reservation Lifecycle"
Cohesion: 0.29
Nodes (6): Allocation Rules, Allowed Transitions, Developer Guide, Inventory Invariant, Reservation Lifecycle, States

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

### Community 54 - "Bugs"
Cohesion: 0.50
Nodes (3): Backend, Bugs, Frontend

### Community 55 - "opencode.json"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

## Knowledge Gaps
- **272 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `library-backend`, `dev.sh script`, `test.sh script` (+267 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `books.py`, `test_books.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `Book` connect `test_books.py` to `books.py`, `seed_books.py`, `User`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `FakeSession` connect `test_books.py` to `User`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `User` (e.g. with `Base` and `AuthSession`) actually correct?**
  _`User` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `FakeSession` (e.g. with `Book` and `Role`) actually correct?**
  _`FakeSession` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Role` (e.g. with `Base` and `AuthSession`) actually correct?**
  _`Role` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `library-backend` to the rest of the system?**
  _272 weakly-connected nodes found - possible documentation gaps or missing edges._