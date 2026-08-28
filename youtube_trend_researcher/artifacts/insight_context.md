# Code Structure Insight — Context

Source artifacts: `artifacts`

## 1. Complexity hotspots (radon CC, rank C/D = complexity >= 11)

| Complexity | Rank | File | Block | Line |
|---|---|---|---|---|
| 17 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/tools/youtube_search.py` | search_videos (function) | 22 |
| 14 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/parse_instruction.py` | parse_instruction (function) | 105 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/graph.py` | run (function) | 84 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/__main__.py` | main (function) | 39 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/analyze_content.py` | _analyze_one (function) | 48 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/compile_report.py` | _render_analysis_block (function) | 75 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/tools/transcript.py` | fetch_transcript (function) | 14 |

## 2. Maintainability-index hotspots (radon MI, rank B/C)

_No low-maintainability modules found._

## 3. Isolated modules (imported by nobody)

- `youtube_trend_researcher.__main__`

## 4. Full summary (from analyze_structure.py)

# Structure Analysis Summary

- Source: `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher`
- Output: `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/artifacts`

## Most complex blocks (radon CC, top 15)

| Complexity | Rank | File | Block | Line |
|---|---|---|---|---|
| 17 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/tools/youtube_search.py` | search_videos (function) | 22 |
| 14 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/parse_instruction.py` | parse_instruction (function) | 105 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/graph.py` | run (function) | 84 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/__main__.py` | main (function) | 39 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/analyze_content.py` | _analyze_one (function) | 48 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/compile_report.py` | _render_analysis_block (function) | 75 |
| 12 | C | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/tools/transcript.py` | fetch_transcript (function) | 14 |
| 10 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/extract_common.py` | _parse_themes (function) | 67 |
| 7 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/analyze_content.py` | _parse_angles_table (function) | 23 |
| 7 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/compile_report.py` | compile_report (function) | 13 |
| 7 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/compile_report.py` | render_markdown (function) | 128 |
| 7 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/tools/parse.py` | extract_section (function) | 44 |
| 7 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/tools/transcript.py` | _parse_vtt (function) | 108 |
| 6 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/fetch_transcripts.py` | fetch_transcripts (function) | 11 |
| 6 | B | `/home/takumi/github/BLOG-TOOLS/youtube_trend_researcher/src/youtube_trend_researcher/nodes/plan_search.py` | plan_search (function) | 25 |

## Isolated modules (imported by nobody)

- `youtube_trend_researcher.__main__`

## 5. Available diagrams

- `pyreverse/classes_ytr.png` : present
- `pyreverse/classes_ytr.svg` : present
- `pyreverse/packages_ytr.png` : present
- `pyreverse/packages_ytr.svg` : present
- `pydeps_ytr.png` : present
- `pydeps_ytr.svg` : present
