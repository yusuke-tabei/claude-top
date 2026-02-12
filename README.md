# claude-top

A terminal monitor and HTML dashboard for tracking your [Claude Code](https://docs.anthropic.com/en/docs/claude-code) usage.

<!-- ![screenshot](screenshots/claude-top.png) -->

## Features

### CLI Monitor (`claude_top.py`)
- Real-time system stats (CPU, memory, load average)
- Hourly message rate tracking with color-coded bars
- Rate limit awareness — warns you before you hit the wall
- Per-model token usage breakdown (Sonnet, Opus 4.5, Opus 4.6)
- Themed TUI with color-coded bars, levels, and model breakdown
- Auto-refresh every 2 seconds, manual refresh with `r`

### HTML Dashboard (`claude_usage_chart.html`)
- Daily message / session / tool-call line charts
- Token usage by model over time
- Hour-of-day session distribution (bar chart)
- Load your own `stats-cache.json` via file picker — no data leaves your machine

## Requirements

- Python 3.6+
- macOS (uses `top -l 1` for system stats)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed (generates the data files)

## Data Sources

| File | Location | Contents |
|------|----------|----------|
| `stats-cache.json` | `~/.claude/stats-cache.json` | Aggregated usage stats (messages, tokens, sessions) |
| `history.jsonl` | `~/.claude/history.jsonl` | Per-message timestamps (used for rate-limit tracking) |

Both files are created automatically by Claude Code.

## Installation

```bash
git clone https://github.com/yusuke-tabei/claude-top.git
cd claude-top
```

No dependencies beyond Python 3 standard library.

## Usage

### Live monitor (refreshes every 2s)

```bash
python3 claude_top.py
```

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Force reload |
| `Ctrl-C` | Quit |

### One-shot mode (print and exit)

```bash
python3 claude_top.py --once
```

### HTML dashboard

Open `claude_usage_chart.html` in your browser, then click **"stats-cache.json を読み込む"** to load your data.

The file is at `~/.claude/stats-cache.json`.

## Claude Code Skill Integration

You can register claude-top as a Claude Code custom skill so that typing `/usage` in any project shows your stats.

Create `~/.claude/commands/usage.md`:

```markdown
Run the claude-top monitor in one-shot mode and display the result:

python3 ~/claude-top/claude_top.py --once
```

---

# claude-top (日本語)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) の使用量をターミナルUIとHTMLダッシュボードで監視するツールです。

## 機能

### CLIモニター (`claude_top.py`)
- リアルタイムのシステム情報（CPU、メモリ、ロードアベレージ）
- 1時間ごとのメッセージ送信数をカラーバーで表示
- レートリミットの警告（使いすぎると赤くなる）
- モデル別トークン使用量（ソネット、オーパス4.5、オーパス4.6）
- カラーバー、レベル、モデル別使用量の表示
- 2秒ごとに自動更新、`r`キーで手動リロード

### HTMLダッシュボード (`claude_usage_chart.html`)
- 日別メッセージ数/セッション数/ツールコール数の折れ線グラフ
- モデル別トークン使用量の推移
- 時間帯別セッション開始数（棒グラフ）
- ファイル選択ボタンから `stats-cache.json` を読み込み（データは外部に送信されません）

## 必要なもの

- Python 3.6以上
- macOS（システム情報の取得に `top -l 1` を使用）
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)（データファイルを生成）

## インストール

```bash
git clone https://github.com/yusuke-tabei/claude-top.git
cd claude-top
```

外部ライブラリ不要です。

## 使い方

### リアルタイム監視

```bash
python3 claude_top.py
```

### ワンショット表示

```bash
python3 claude_top.py --once
```

### HTMLダッシュボード

`claude_usage_chart.html` をブラウザで開き、**「stats-cache.json を読み込む」** ボタンから `~/.claude/stats-cache.json` を読み込んでください。

## Claude Code スキル連携

`~/.claude/commands/usage.md` を作成すると、どのプロジェクトでも `/usage` で使用量を確認できます。

```markdown
Run the claude-top monitor in one-shot mode and display the result:

python3 ~/claude-top/claude_top.py --once
```

## License

MIT
