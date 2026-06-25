# Frontend Components & Dashboard

## Technology Stack

| Library | Purpose | Version |
|---------|---------|---------|
| React | UI framework | 19.x |
| Vite | Build tool + dev server | — |
| Tailwind CSS | Utility-first CSS | 4.x |
| Recharts | Charts (bar, pie/donut) | 3.x |
| lucide-react | Icon library | — |
| framer-motion | Animations | — |

## Component Hierarchy

```
App.jsx
├── GithubAuthGuard
│   ├── GithubCallback          (route: /auth/callback)
│   ├── Login Screen            (unauthenticated)
│   └── [Dashboard]             (authenticated)
│       ├── Navbar
│       │   └── ProfileMenu
│       ├── InputForm
│       ├── Demo Buttons
│       ├── Error Banner
│       ├── EmptyState
│       ├── LoadingState
│       ├── MapResults          (from Quick Map)
│       └── [Pipeline Results]  (from full analysis)
│           ├── Header
│           ├── KPIs
│           ├── RequirementsImpact
│           ├── Charts
│           └── DependencyTrace
```

## Component Details

### App.jsx

**State management** — all local `useState`:

| State | Type | Purpose |
|-------|------|---------|
| `repoUrl`, `commitHash`, `baseCommit`, `sourceDir`, `testsDir` | strings | Form input values |
| `isAnalyzing` | boolean | Loading state flag |
| `hasResults` | boolean | Results available flag |
| `pipelineData` | object or null | Full analysis response |
| `mapData` | object or null | Quick Map response |
| `loadingStep` | number | Current loading animation step |
| `error` | string or null | Error message |
| `isAuthenticated` | boolean | Auth state |
| `githubToken` | string or null | OAuth token |
| `githubUser` | object or null | GitHub profile (login, avatar_url) |
| `demoScenarios` | object or null | Available demo scenarios |

**Key handlers:**

| Function | API Call | Purpose |
|----------|----------|---------|
| `handleAnalyze()` | `POST /api/analyze` | Full pipeline analysis |
| `handleQuickMap()` | `POST /api/analyze/map` | Static mapping only |
| `runDemo(key)` | `POST /api/analyze/demo` | Run demo scenario |

**Effects:**
- `isAnalyzing` → cycles `loadingStep` every 700ms for terminal animation
- Mount → checks `localStorage` for saved token + user info (auto-authenticate)
- `isAuthenticated` → fetches demo scenarios from `GET /api/analyze/demo/scenarios`

---

### InputForm.jsx

The main user input component for specifying the repository and commit range.

**Fields:**

| Field | Type | Placeholder |
|-------|------|-------------|
| Repository Path or URL | text input | `/Users/dev/target-app` or `https://github...` |
| Target Commit | text input | `a1b2c3d` |
| Base Commit (optional) | text input | `auto (parent)` |
| Source dir | text input | `src/` |
| Tests dir | text input | `tests` |

**Buttons:**
- **Quick Map** (indigo) — triggers `handleQuickMap()`, performs static analysis without test execution
- **Analyze Impact** (emerald, primary) — triggers `handleAnalyze()`, runs full pipeline

**Auth badge:** When a GitHub token is present, shows an "Authenticated with GitHub" badge below the form.

---

### Navbar.jsx

Sticky top navigation bar with glassmorphism styling (`backdrop-blur-xl`, `bg-slate-950/80`).

**Left section:**
- Green gradient `Zap` icon in a rounded square
- "SmartTIA" bold title
- "Test Impact Analysis" subtitle (hidden on mobile)

**Right section:**
- `ProfileMenu` component with user avatar and dropdown

Only rendered when `isAuthenticated` is true.

---

### ProfileMenu.jsx

User profile dropdown component with click-outside-to-close behavior.

**States:**
- **Loading/Fallback:** Shows a generic "G" avatar SVG when no user data exists
- **Authenticated:** Shows GitHub avatar + username
- **Dropdown open:** Shows username, `@handle`, and "Sign out" button

**Logout:** Clears `localStorage` (`github_token`, `github_user`), resets auth state, redirects to login screen.

---

### GithubAuthGuard.jsx

Authentication gate component with three rendering states:

| State | Renders |
|-------|---------|
| Route is `/auth/callback` | `GithubCallback` terminal screen |
| `isAuthenticated === true` | Children (dashboard) |
| `isAuthenticated === false` | Login prompt with GitHub OAuth button |

**Login screen features:**
- GitHub SVG logo
- "Connect Repository" heading
- "Connect with GitHub" button → OAuth URL
- "Continue in demo mode" bypass link → sets `isAuthenticated(true)` without a token

---

### GithubCallback.jsx

Terminal-style OAuth handshake screen with animated status messages.

**Flow:**
1. Parse `?code=` from URL parameters
2. POST to `POST /api/auth/github` with the code
3. Receive `access_token`
4. Call `onTokenReceived(token)` (stores in React state + localStorage)
5. Fetch GitHub user profile from `https://api.github.com/user`
6. Store user info in localStorage
7. Animated status updates: "Initializing..." → "Authenticating..." → "Exchanging code..." → "Fetching GitHub profile..." → "Synchronizing..." → "Authentication successful!"
8. Redirect to `/` via `window.history.replaceState`

**Error handling:** Shows `[GITHUB ERROR]` or `[FATAL]` messages in red for invalid codes or network failures.

---

### LoadingState.jsx

Terminal-window styled loading animation with 5 steps:

```
$ SmartTIA Engine
> Cloning repository...
> Parsing diff into Abstract Syntax Tree...
> Mapping impacted source functions to tests...
> Executing impacted subset on simulated HIL bench...
> Measuring full-regression baseline & generating impact matrix...
_
```

Steps transition from dark gray (pending) to emerald green (completed) every 700ms.

---

### EmptyState.jsx

Initial state displayed when no analysis has been run yet. Shows a "Ready to Analyze Test Impact" prompt.

---

### Dashboard Components

#### Header.jsx

Pipeline run summary card:

| Element | Source |
|---------|--------|
| Zap icon + "Smart TIA Output" | Static |
| Commit hash (monospace) | `pipeline_run.commit_hash` |
| Commit message | `pipeline_run.commit_message` |
| Pipeline status | `pipeline_run.status` with green checkmark or red indicator |
| Timestamp | `pipeline_run.timestamp` |

---

#### KPIs.jsx

Four-column key performance indicator grid:

**1. Time Saved (2-column emerald gradient card)**
- Big percentage number: `metrics.time_saved_percentage`
- Subtitle: "Time Saved vs Standard"

**2. Execution Time**
- Smart run time: `metrics.smart_run_time_seconds` + `s` suffix
- Strikethrough original: `metrics.standard_run_time_seconds`

**3. Suite Efficiency**
- Executed count: `metrics.tests_executed`
- Total count: `/ {metrics.total_tests_in_suite} tests`
- Skipped count: `{metrics.tests_skipped} test(s) skipped safely`

---

#### Charts.jsx

Two-column chart layout:

**Left: Time Comparison Bar Chart (Recharts)**
- Horizontal bar chart
- Two bars: "Standard CI" (zinc/gray) vs "Smart TIA" (emerald/green)
- X-axis: time in seconds
- Responsive container with custom tooltip styling

**Right: Suite Avoidance Donut Chart (Recharts)**
- Donut/ring chart
- Two segments: "Executed" (green) and "Skipped" (zinc/gray)
- Inner radius: 65, outer radius: 90
- Legend with counts and labels

---

#### RequirementsImpact.jsx

Safety-critical traceability panel with multiple sections:

**1. Selection Method Badge**
- "Coverage-based" (emerald) — Tier 1
- "AST static" (indigo) — Tier 2
- "Safety fallback" (amber) — Tier 3

**2. Confidence Badge**
- "High Confidence" (emerald) — when tests selected with high confidence
- "Low Confidence" (amber) — when fallback was triggered

**3. Highest ASIL Touched**
- Color-coded badge: D=rose, C=orange, B=amber, A=sky, QM=zinc
- Sourced from `traceability.highest_asil`

**4. HIL Tests Avoided**
- Count of expensive HIL tests skipped
- `metrics.hil_tests_skipped`

**5. Safety Net Warning**
- Shown when `analysis.fallback_reason` is set
- Warning icon + fallback explanation

**6. Changed Source Files**
- List of `analysis.modified_files` with `FileCode2` icon

**7. Impacted Software Requirements**
- For each requirement: ID, title, component tag, ASIL badge, test count
- Sourced from `traceability.impacted_requirements`

---

#### DependencyTrace.jsx

Two-section traceability view:

**Section 1: All Test Files Overview**
- Grid of pills showing every test file in the suite
- Selected files: green highlight with checkmark badge
- Non-selected files: muted styling
- Counter: `X / Y selected`
- Sourced from `analysis.all_test_files` and `analysis.selected_tests`

**Section 2: Per-Source Breakdown**
- For each modified source file (from `dependency_trace`):
  - "Source Modified Node" header with file path (indigo monospace)
  - Connecting dashed lines in tree layout
  - "Impacted Tests Validated" section
  - Each test entry shows:
    - Status icon (green checkmark for passed, red server for failed)
    - Test name (monospace)
    - Level badge (UNIT=zinc, SIL=amber, HIL=rose)
    - Requirement badge (indigo)
    - ASIL badge (orange, hidden for QM)
    - Status text (passed/failed, colored)
    - Duration in ms (with clock icon)

---

#### MapResults.jsx

Quick Map output display with four sections:

**1. Header** — Commit hash with base reference

**2. Overview Cards** (3-column grid)
- Source files changed count (indigo)
- Functions impacted count (amber)
- Test files impacted count (emerald)

**3. Changed Functions** — List of impacted function signatures

**4. Impacted Test Files** — List with checkmarks + per-source breakdown tree
