# Tasks: ブログ作成エージェント

**Branch**: `001-blog-writing-agent` | **Date**: 2026-08-06 | **Spec**: [spec.md](./spec.md)

## Overview

VS Code Copilot エージェント機能を活用したブログ作成フローの構築。ツールアプリは Python で、フロー管理は `.github/agents/` のエージェント定義で実現する。

---

## Phase 0: Setup

- [X] T001 プロジェクト構造の初期化
  - Create `src/blog_writer/__init__.py`
  - Create `src/blog_writer/config.py`
  - Create `tests/__init__.py` and `tests/conftest.py`
  - Create `pyproject.toml` に依存関係を定義（pytrends, searchstack, markdownlint）

- [X] T002 依存関係のインストール確認
  - Run `uv sync` to install Python dependencies
  - Run `npm list -g markdownlint-cli` to verify markdownlint
  - Run `pip list | grep -E "pytrends|searchstack|website-seo-audit"` to verify pip packages

- [ ] T003 既存リソースの確認
  - Verify `.github/agents/blog-reviewer.agent.md` exists and is functional
  - Verify `.github/scripts/blog-reviewer/server.sh` works with `bash .github/scripts/blog-reviewer/server.sh start/stop`

---

## Phase 1: Foundational Tools

### T004 trend_analyzer.py 作成
- Create `src/blog_writer/trend_analyzer.py`
- Implement pytrends-based trend analysis with rate limiting (sleep 5s)
- Return `TrendResult` with interest_over_time, related_queries, trend_score
- Add CLI interface: `python -m blog_writer.trend_analyzer <topic>`

### T005 project_analyzer.py 作成
- Create `src/blog_writer/project_analyzer.py`
- Implement README parsing and directory structure analysis
- Return `ProjectInfo` with name, description, tech_stack, readme_summary
- Add CLI interface: `python -m blog_writer.project_analyzer <path>`

### T006 seo_checker.py 作成
- Create `src/blog_writer/seo_checker.py`
- Implement title length (30-60 chars), description length (120-160 chars) validation
- Implement heading structure validation (H1 count, H2/H3 order)
- Implement alt text coverage check
- Add CLI interface: `python -m blog_writer.seo_checker <file>`

### T007 markdown_validator.py 作成
- Create `src/blog_writer/markdown_validator.py`
- Implement frontmatter schema validation
- Implement markdownlint integration (subprocess call)
- Add CLI interface: `python -m blog_writer.markdown_validator <file>`

### T008 ツールアプリのユニットテスト作成
- Create `tests/unit/test_trend_analyzer.py`
- Create `tests/unit/test_project_analyzer.py`
- Create `tests/unit/test_seo_checker.py`
- Create `tests/unit/test_markdown_validator.py`
- Run `pytest tests/unit/ -v` to verify all tests pass

---

## Phase 2: Agent Definitions (US1: 基本ブログ生成)

### T009 blog-writer.agent.md 作成
- Create `.github/agents/blog-writer.agent.md` with YAML frontmatter
- Define description, tools (read, search, execute, web, edit), user-invocable: true
- Add SessionStart hook to start open_deep_research server
- Add Stop hook to stop open_deep_research server
- Write execution steps: input parsing → trend analysis → research → writing → quality check → output

### T010 blog-writer.prompt.md 作成
- Create `.github/prompts/blog-writer.prompt.md`
- Include style guide rules (tone, structure, Mermaid diagrams)
- Include frontmatter template
- Include writing guidelines

### T011 blog-style-guide.md 作成
- Create `.github/styles/blog-style-guide.md`
- Define tone: "です・ます" form, friendly
- Define structure: intro → target reader → TOC → main → summary → references
- Define Mermaid diagram guidelines
- Define SEO rules

### T012 blog-researcher.agent.md 作成
- Create `.github/agents/blog-researcher.agent.md` as sub-agent (user-invocable: false)
- Define research steps: trend analysis → open_deep_research API call
- Reference `.github/scripts/blog-reviewer/server.sh` for server management
- Add rate limiting for pytrends (sleep 5s between requests)

### T013 blog-researcher.prompt.md 作成
- Create `.github/prompts/blog-researcher.prompt.md`
- Include research prompt template for open_deep_research
- Include trend analysis instructions
- Include project/directory analysis instructions

### T014 blog-quality-checker.agent.md 作成
- Create `.github/agents/blog-quality-checker.agent.md` as sub-agent (user-invocable: false)
- Define quality check steps: fact check → format check → SEO check
- Reference markdown_validator.py and seo_checker.py tools
- Include searchstack-aeo command execution

### T015 blog-quality-checker.prompt.md 作成
- Create `.github/prompts/blog-quality-checker.prompt.md`
- Include quality check instructions
- Include SEO validation rules
- Include report generation format

---

## Phase 3: User Story 2 (P2: 詳細指定付き記事生成)

### T016 blog-researcher にプロジェクト解析機能追加
- Update `.github/agents/blog-researcher.agent.md`
- Add step to call `python -m blog_writer.project_analyzer <path>` when directory_path is provided
- Add step to read README when project_name is provided
- Integrate project info into research results

### T017 blog-writer に補足情報処理追加
- Update `.github/agents/blog-writer.agent.md`
- Add input parsing for project_name, directory_path, detailed_spec
- Pass supplementary info to blog-researcher sub-agent
- Handle edge case: invalid directory path

---

## Phase 4: User Story 3 (P2: 品質レポート)

### T018 品質レポート出力機能追加
- Update `.github/agents/blog-quality-checker.agent.md`
- Add report generation step with structured output
- Include fact check results, format check results, SEO scores
- Output report to stdout with clear formatting

### T019 blog-writer にレポート表示追加
- Update `.github/agents/blog-writer.agent.md`
- Add final step to display quality report summary
- Include pass/fail status for each check
- Show SEO score and recommendations

---

## Phase 5: Polish & Testing

### T020 エンドツーエンドテスト
- Create `tests/integration/test_full_flow.py`
- Test basic flow: topic → blog post generation
- Test supplementary info flow: topic + project_name → enriched blog post
- Verify frontmatter validity, Mermaid diagram presence, SEO score

### T021 ドキュメント更新
- Update `quickstart.md` with usage examples
- Update `data-model.md` with final entity definitions
- Update `contracts/orchestrator-api.md` with agent interfaces

### T022 最終検証
- Run `pytest tests/ -v` to verify all tests pass
- Run `ruff check src/blog_writer/` to verify code quality
- Run `mypy src/blog_writer/` to verify type safety
- Manual test: run `/blog-writer "test topic"` in VS Code Copilot

---

## Task Dependencies

```
T001 → T002 → T003
  ↓
T004, T005, T006, T007 (parallel)
  ↓
T008
  ↓
T009, T010, T011 (parallel)
  ↓
T012, T013 (parallel)
  ↓
T014, T015 (parallel)
  ↓
T016, T017 (parallel)
  ↓
T018, T019 (parallel)
  ↓
T020 → T021 → T022
```

---

## Parallel Execution Opportunities

| Group | Tasks | Description |
|-------|-------|-------------|
| Tool Apps | T004, T005, T006, T007 | 各ツールアプリは独立して作成可能 |
| Agent Defs | T009, T010, T011 | メインエージェントとプロンプトは独立 |
| Sub-agents | T012, T013, T014, T015 | サブエージェントは独立して作成可能 |
| US2 Tasks | T016, T017 | 補足情報処理は独立して追加可能 |
| US3 Tasks | T018, T019 | レポート機能は独立して追加可能 |

---

## Success Criteria Validation

| Task | Validates SC |
|------|--------------|
| T004 | SC-001 (trend analysis speed) |
| T006, T007 | SC-002, SC-003 (format validation) |
| T009-T015 | SC-001, SC-004, SC-005, SC-007 |
| T016-T019 | SC-005, SC-006 |
| T020 | All SCs |

---

## Notes

- **open_deep_research server**: Always use `bash .github/scripts/blog-reviewer/server.sh start` before API calls, and `stop` after
- **pytrends rate limiting**: Sleep 5 seconds between requests to avoid 429 errors
- **searchstack-aeo**: Run both Markdown-based (after generation) and URL-based (after deployment) checks
