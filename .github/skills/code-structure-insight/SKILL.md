---
name: code-structure-insight
description: Python コードの静的構造解析結果から、人間向けの「関連図の解説」と「改善提案」を生成します。pyreverse/pydeps/radon が吐いた artifacts（クラス図・依存図・複雑度・孤立モジュール）を読み、浮いているソースの発見や設計の煩雑さの改善点を言語化します。Use when: コードの関連図を理解したい、設計の問題点を洗い出したい、リファクタ箇所を特定したい、analyze_structure.py の出力を解釈したい、architecture review、structure analysis、code map、依存関係の可視化。
---

# Code Structure Insight

Python ソースコードの静的解析結果から、**人間が理解しやすい関連図の解説**と、
**改善につながる提案**を生成するスキルです。

## 前提

このスキルは `trend_researcher/script/analyze_structure.py` の出力（`artifacts/`）を
読み込んで動作します。事前に構造解析が実行されていない場合は、以下を実行してください。

```bash
cd trend_researcher
export PATH="$PWD/.venv/bin:$PATH"
python script/analyze_structure.py
```

（または通常の `git commit` で pre-commit フックが自動実行します）

## ワークフロー

### 1. コンテキストの収集

`scripts/build_context.py` を使って `artifacts/` を1つの markdown にまとめます。

```bash
cd trend_researcher
export PATH="$PWD/.venv/bin:$PATH"
python ../.github/skills/code-structure-insight/scripts/build_context.py \
    --artifacts artifacts \
    --out artifacts/insight_context.md
```

これにより以下が統合されます：
- `summary.md` （複雑度トップ15 ＋ 孤立モジュール）
- `radon_cc.json` （全関数の循環複雑度）
- `radon_mi.json` （保守性指標）
- `isolated_modules.txt` （誰からも import されていないモジュール）
- `pyreverse/classes_trend_researcher.dot` と `pydeps_trend_researcher.svg` の存在確認

### 2. 人間向けレポートの生成（このスキルの本体）

収集した `insight_context.md` をもとに、以下の構成でレポートを作成してください。

#### 構成テンプレート

1. **全体像（関連図の解説）**
   - `pydeps_trend_researcher.png` / `pydeps_trend_researcher.svg` を参照し、モジュール間の依存の流れを文章で説明
   - 中心的なモジュール（多くから依存されているもの）と末端のモジュールを指摘
   - クラス中心の構造は `classes_trend_researcher.png` を補足として参照

2. **浮いているソース（孤立モジュール）**
   - `isolated_modules.txt` の一覧をもとに、使われていない/使われていないはずのモジュールを列挙
   - 各モジュールについて「本当に不要か」「エントリーポイントか」「未接続のバグか」を判定
   - 例: `__main__` は起動専用で正常。`cache` のようにどこからも import されていないものは
     未使用コード or 配線漏れの疑いとして改善を提案

3. **設計の煩雑さ（複雑度ハイライト）**
   - `radon_cc.json` から複雑度ランク C/D（複雑度 11 以上）の関数を抽出
   - 各関数について「なぜ複雑か（分岐の多さ/長い処理）」を推察し、リファクタの方向性を提示
   - 保守性指標 `radon_mi.json` が低い（B 以下）モジュールも併記

4. **改善の優先順位（優先度付き TODO）**
   - 影響度 × 労力で優先順位を付け、具体的な次アクションをリスト化
   - 孤立モジュールの処理、複雑度上位関数の分割、依存の循環/集中の解消など

### 3. 出力

- チャットで人間が読める形に要約して提示
- 必要に応じて `artifacts/insight_report.md` にも保存してコミットに含める

## 注意事項

- 複雑度はあくまで「分岐の多さ」の指標。ビジネスロジックの重さとは別次元。
- pyreverse のクラス図は「クラス」しか描かない。関数ベースのノード群
  （`nodes/`, `tools/`）の振る舞いは pydeps の依存図で捉える。
- 存在しない関係を「ある」と断言しないこと。必ず artifacts の実データに基づくこと。
