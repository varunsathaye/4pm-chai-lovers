# SmartTIA — Smart Test Impact Analysis Engine

## Executive Summary

SmartTIA is an intelligent Test Impact Analysis (TIA) engine that determines exactly which tests are affected by a given code change and executes only that minimal subset. Instead of running the entire test suite on every commit — which is slow, expensive, and wasteful — SmartTIA selects the smallest possible set of tests that can still guarantee no regression is missed.

The system proves its own effectiveness by computing **time-saved metrics**, showing the standard-run duration versus the smart-run duration, and calculating the percentage of the suite that was safely skipped.

## Problem Statement

Modern CI/CD pipelines suffer from a fundamental inefficiency: **every commit triggers a full test suite run**. As codebases grow, test suites balloon, and CI wait times become a bottleneck to developer velocity. The key insight is that most commits change only a small portion of the codebase, so only a correspondingly small portion of the test suite needs to re-execute.

However, naive text-matching approaches (grepping for function names) miss **transitive dependencies** — a test that calls function A which internally calls changed helper B will be incorrectly skipped, creating a false-negative risk that no safety-critical organization can accept.

## Solution

SmartTIA solves this with a **3-tier selection engine** that balances precision with safety:

| Tier | Method | What it detects | When it triggers |
|------|--------|----------------|-----------------|
| 1 | **Runtime Coverage** | Transitive/indirect dependencies via execution traces | When a coverage map exists for the baseline commit |
| 2 | **AST Static Mapping** | Direct imports and symbol references | When no coverage map is available |
| 3 | **Full Suite Fallback** | Everything (safety net) | When confidence is low — zero selected tests or unmapped changes |

## Key Capabilities

- **Coverage-based impact analysis** — records which lines each test touches at runtime, then intersects with diff analysis for precise selection
- **Cross-language support** — Python (full AST), C/C++/JavaScript/Go/Rust/Java (regex-based), with language-agnostic test file detection
- **Cross-file call-chain detection** — finds indirect callers of changed functions by scanning all source files
- **Requirements traceability (ISO 26262)** — maps tests to software requirements with ASIL safety ratings (A–D), suitable for automotive and other safety-critical domains
- **Time-saved metrics** — calculates `standard_run_time_seconds` vs `smart_run_time_seconds` and `time_saved_percentage`, optionally using a `test_timings.json` file when execution is skipped
- **GitHub OAuth integration** — authenticates users to clone private repositories
- **Dashboard visualizations** — real-time KPI cards, bar charts, donut charts, and per-file dependency trees
- **Dual-mode analysis** — Quick Map (lightweight static analysis, no execution) and Full Pipeline (clone, diff, map, execute)

## Supported Languages

| Language | Analysis Method | Test File Detection |
|----------|----------------|-------------------|
| Python | Full AST parsing | `.py` |
| C / C++ | Regex signature matching | `.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hpp`, `.hxx` |
| JavaScript / TypeScript | Regex fallback | `.js`, `.ts`, `.jsx`, `.tsx` |
| Java / Kotlin | Regex fallback | `.java`, `.kt` |
| Go / Rust | Regex fallback | `.go`, `.rs` |
| Ruby / Swift | Regex fallback | `.rb`, `.swift` |
| Shell scripts | — | `.sh`, `.bash` |
