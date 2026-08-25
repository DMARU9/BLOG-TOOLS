# Tasks: YouTube Trend Researcher

**Input**: Design documents from `/specs/002-youtube-trend-researcher/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/ ✅ all present

**Tests**: Included. Constitution IV mandates tests for all tools, and quickstart.md defines pytest validation (V1–V5). Test tasks are placed per story and in Polish.

**Organization**: Tasks grouped by user story so each story can be implemented/tested/delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1–US4)
- Exact file paths included in descriptions

## Path Conventions

Single project under `YouTube_Trend_Researcher/`:
- `src/youtube_trend_researcher/` — package
- `tests/unit/`, `tests/integration/` — tests
- `cache/` — intermediate artifacts (DB-free persistence, FR-012)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure `YouTube_Trend_Researcher/` with `src/youtube_trend_researcher/`, `tests/unit/`, `tests/integration/`, `cache/` per plan.md
- [ ] T002 [P] Create `YouTube_Trend_Researcher/pyproject.toml` with dependencies: `langgraph`, `langchain`, `langchain-openai`, `yt-dlp`, `openai-whisper`, `pydantic`; dev: `pytest`, `ruff`, `mypy` (mirror `blog_writer/pyproject.toml` layout). NOTE: `youtube-comment-downloader` is excluded from v1 (comments out of scope per Clarification).
- [ ] T003 [P] Create `YouTube_Trend_Researcher/.env.example` with `OPENAI_API_KEY`, `OPENAI_BASE_URL=https://opencode.ai/zen/go/v1`, `YTR_MODEL=openai:mimo-v2.5`, and optional `YOUTUBE_API_KEY` (research.md R-3/R-6)
- [ ] T004 [P] Configure ruff and mypy in `YouTube_Trend_Researcher/pyproject.toml` (`[tool.ruff]`, `[tool.mypy]`) per Constitution IV

**Checkpoint**: Project scaffold and dependency manifest ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST complete before ANY user story

- [ ] T005 [P] Implement `src/youtube_trend_researcher/config.py` — `Config` pydantic model (youtube_api_key, openai_api_key, openai_base_url, model, cache_dir, transcript_language, max_retries) loading from env/.env (contracts/module-api.md)
- [ ] T006 [P] Implement `src/youtube_trend_researcher/tools/llm.py` — `build_model(role)` mirroring OpenDeepResearch: `init_chat_model(model, max_tokens, api_key, base_url)` with `configurable_fields=("model","max_tokens","api_key")`; default `openai:mimo-v2.5` @ `OPENAI_BASE_URL` (research.md R-3)
- [ ] T007 [P] Implement `src/youtube_trend_researcher/models.py` — Pydantic entities `ResearchInstruction`, `InstructionFilters`, `OutputSpec`, `VideoCandidate`, `Transcript`, `AnalysisFinding`, `CommonTheme`, `ResearchReport` per data-model.md
- [ ] T008 [P] Implement `src/youtube_trend_researcher/tools/youtube_search.py` — yt-dlp based search via `ytsearchN:` (date filtering applied post-hoc via `upload_date` parse, NOT `ytsearchdateN:`); map results to `VideoCandidate` (view_count, upload_date, channel_follower_count, like_count); exclude `channel_follower_count=None` videos (research.md R-1, FR-003/FR-004)
- [ ] T009 [P] Implement `src/youtube_trend_researcher/tools/transcript.py` — yt-dlp `subtitles`/`automatic_captions` then Whisper fallback for audio (GPU/CUDA assumed); return `Transcript(source="caption"|"whisper")` (FR-006)
- [ ] T010 [P] Implement `src/youtube_trend_researcher/tools/youtube_api.py` — optional YouTube Data API v3 fallback for `channel_follower_count` when hidden (non-blocking, FR-004)
- [ ] T011 [P] Implement `src/youtube_trend_researcher/tools/parse.py` — lightweight parser extracting structured data (Markdown/JSON) from LLM outputs for downstream nodes (Clarification: prompt-driven, not forced structured output)
- [ ] T012 [P] Implement `src/youtube_trend_researcher/prompts.py` — centralized LLM prompt strings for `parse_instruction`, `plan_searches`, `analyze_content`, `extract_common`, `compile_report` (plan.md structure; resolves U1)
- [ ] T013 [P] Implement cache persistence helper in `src/youtube_trend_researcher/cache.py` — `write_json`/`read_json` to `cache/` for intermediate artifacts (candidates, transcripts, analyses) (FR-012)
- [ ] T014 Implement `src/youtube_trend_researcher/state.py` — LangGraph `State` (instruction, candidates, transcripts, analyses, common_themes, report, notes) per data-model.md graph transitions

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - 自然言語指示からの自律リサーチ実行 (Priority: P1) 🎯 MVP

**Goal**: Given a natural-language instruction, autonomously run search → filter → transcript → analysis → common-extraction → report, returning a final `ResearchReport` with no human input.

**Independent Test**: Run instruction "Claude Codeで会社を回す方法を解説している動画で伸びているものを10個ピックアップして" with mocked tools; assert `ResearchReport` contains candidates + analyses + common_themes + sources (spec.md US1 Acceptance 1–3).

### Implementation for User Story 1

- [ ] T015 [US1] Implement `src/youtube_trend_researcher/nodes/parse_instruction.py` — LLM extracts structured `ResearchInstruction` (topic, filters, output) from raw text (FR-001)
- [ ] T016 [US1] Implement `src/youtube_trend_researcher/nodes/search_videos.py` — run a single search using `tools/youtube_search.py` from instruction topic (foundation for US2 multi-angle) (FR-003/FR-004)
- [ ] T017 [US1] Implement `src/youtube_trend_researcher/nodes/filter_candidates.py` — apply `InstructionFilters` (date window, subscriber_max, views_min, velocity_ratio, max_results) to candidates (FR-005)
- [ ] T018 [US1] Implement `src/youtube_trend_researcher/nodes/fetch_transcripts.py` — for filtered candidates, fetch transcripts via `tools/transcript.py` (caption→Whisper GPU); record source/none in `notes` (FR-006)
- [ ] T019 [US1] Implement `src/youtube_trend_researcher/nodes/analyze_content.py` — LLM per-video `trending_reason` + `evidence` from transcript, parsed via `tools/parse.py` (FR-007, prompt-driven). **Max 2 concurrent LLM calls** (Clarification).
- [ ] T020 [US1] Implement `src/youtube_trend_researcher/nodes/extract_common.py` — LLM aggregate `AnalysisFinding`s into `CommonTheme` list using video transcripts only (no comments) (FR-008)
- [ ] T021 [US1] Implement `src/youtube_trend_researcher/nodes/compile_report.py` — assemble `ResearchReport` (candidates, analyses, common_themes, sources, notes), default markdown (FR-009/FR-010)
- [ ] T022 [US1] Implement `src/youtube_trend_researcher/graph.py` — wire `StateGraph` parse→search→filter→fetch→analyze→extract→compile→END (single-angle) and provide `run()` entry
- [ ] T023 [US1] Implement `src/youtube_trend_researcher/__init__.py` skeleton `research()` that invokes graph and returns `ResearchReport` (full flow, US1 MVP)

**Checkpoint**: US1 fully functional end-to-end (single search angle). Independently testable.

---

## Phase 4: User Story 2 - 複数角度からの自律的探索 (Priority: P1)

**Goal**: From the topic, auto-generate multiple search angles/queries, search repeatedly, merge/dedupe, and reflect to add angles when coverage is insufficient — never depending on a single query.

**Independent Test**: Given a topic instruction, assert multiple queries are generated, searched, and merged into a unified candidate list (spec.md US2 Acceptance 1–2).

### Implementation for User Story 2

- [ ] T024 [US2] Implement `src/youtube_trend_researcher/nodes/plan_searches.py` — LLM generates multiple search angles/queries from topic (FR-003) (research.md R-2 graph)
- [ ] T025 [US2] Extend `src/youtube_trend_researcher/nodes/search_videos.py` to iterate over queries from `plan_searches`, collecting candidates
- [ ] T026 [US2] Add dedupe/merge of candidates across queries (by `video_id`) into a unified candidate list (Acceptance US2-2)
- [ ] T027 [US2] Add reflect loop in `src/youtube_trend_researcher/graph.py` — re-plan additional angles when candidate pool is insufficient (ODR-style reflect, max **3 iterations** per Clarification U2) (research.md R-2)
- [ ] T028 [US2] Integration test in `tests/integration/test_multi_angle.py` — verify multiple queries generated and merged (Acceptance US2)

**Checkpoint**: US1 AND US2 both work; multi-angle autonomous exploration functional.

---

## Phase 5: User Story 3 - 外部リクエスト・実行・アウトプット取得のインターフェース (Priority: P2)

**Goal**: External request → execute → obtain output, without a GUI (CLI + module API).

**Independent Test**: Invoke via `python -m youtube_trend_researcher "<instruction>"` and via `research()` import; assert structured report returned with exit 0 (spec.md US3 Acceptance 1–3).

### Implementation for User Story 3

- [ ] T029 [US3] Finalize `src/youtube_trend_researcher/__init__.py` `research()` async entry returning `ResearchReport`; raise `ConfigurationError`/`NoCandidatesError` per contracts/module-api.md
- [ ] T030 [US3] Implement `src/youtube_trend_researcher/__main__.py` CLI — argparse for `INSTRUCTION`, `--output`, `--format`, `--cache-dir`, `--config`; exit codes 0/1/2/3 per contracts/cli.md
- [ ] T031 [US3] Document module API usage in `YouTube_Trend_Researcher/README.md` (import `research`, `Config`) per contracts/module-api.md

**Checkpoint**: All user stories independently functional; external invocation works.

---

## Phase 6: User Story 4 - 指示に基づく絞り込みと多様な出力形式 (Priority: P3)

**Goal**: Interpret natural-language filter phrases and honor output-format directives (e.g., common points as a table).

**Independent Test**: Instruction "直近半年以内・登録者が少ないのに再生が伸びているものに絞って、共通点は表でまとめて" yields date/velocity-filtered candidates and a table for common points (SC-003/SC-004).

### Implementation for User Story 4

- [ ] T032 [US4] Enhance `src/youtube_trend_researcher/nodes/parse_instruction.py` to interpret NL filters ("直近半年", "登録者少ないのに再生が伸びている") into `InstructionFilters` (velocity_ratio, subscriber_max, published_after) (FR-005)
- [ ] T033 [US4] Enhance `src/youtube_trend_researcher/nodes/compile_report.py` to support `--format json` (report-schema.md) and markdown table for `common_themes` when `output.table_for` includes `common_points` (FR-009, SC-004)
- [ ] T034 [US4] Integration in `tests/integration/test_filter_format.py` — user example yields filtered (≤6mo, low-sub/high-view) candidates with common points as table (SC-003/SC-004)

**Checkpoint**: All four user stories complete and independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T035 [P] Unit tests for tools in `tests/unit/test_tools.py` — `youtube_search` parse, `transcript` fallback, `llm.build_model` (Constitution IV). NOTE: comments tool is out of v1 scope (no test).
- [ ] T036 [P] Unit tests for nodes in `tests/unit/test_nodes.py` — filter logic, `parse_instruction` structured output, report assembly
- [ ] T037 [P] Integration test end-to-end with mocked external services per quickstart V1 in `tests/integration/test_e2e_mock.py`
- [ ] T038 [P] Documentation in `YouTube_Trend_Researcher/README.md` — quickstart, `.env.example` notes, architecture diagram (plan.md project structure)
- [ ] T039 Run quickstart.md validation scenarios V2–V5; ensure `ruff`, `mypy`, `pytest` clean
- [ ] T040 Final consistency review of spec.md / plan.md / tasks.md; update `.github/copilot-instructions.md` reference if needed
- [ ] T041 [US1] Add an overall 100-minute execution timeout in `graph.py` so a partial `ResearchReport` is returned on overrun (Clarification)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — MVP
- **US2 (Phase 4)**: Depends on US1 (extends `search_videos`, `graph`)
- **US3 (Phase 5)**: Depends on US1 (wraps `research()`)
- **US4 (Phase 6)**: Depends on US1 (extends `parse_instruction`, `compile_report`)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — no dependency on other stories
- **US2 (P1)**: After US1 — extends search/graph
- **US3 (P2)**: After US1 — wraps flow
- **US4 (P3)**: After US1 — extends parse/compile

### Parallel Opportunities

- All Phase 1 tasks T002–T004 marked [P] run in parallel after T001
- All Foundational T005–T014 marked [P] run in parallel (independent files)
- US2/US3/US4 can each start after US1 independently (different files)
- Polish tests T035–T038 marked [P] run in parallel

### Suggested MVP Scope

**US1 only (Phase 3 + its Foundational deps)**: A single-angle autonomous research pipeline returning a `ResearchReport`. This delivers the core value (spec US1, SC-001/SC-002). US2–US4 layer multi-angle, external interface, and format refinements on top.

---

## Parallel Example: User Story 1

```bash
# After Foundational completes, US1 implementation tasks can be parallelized where independent:
# T015 (parse)        — independent, writes ResearchInstruction
# T017 (filter)       — depends on T016 (search) output shape, but code can be written in parallel
# T018 (transcripts)  — depends on T017 output shape, code independent
# T019 (analyze)      — independent node, depends on T018 shape
# T020 (common)       — independent node, depends on T019 shape
# T021 (compile)      — depends on all above shapes
# T022 (graph)        — depends on T015–T021 being present
```

Write nodes (T014–T020) in parallel, then wire graph (T021) and flow (T022).
