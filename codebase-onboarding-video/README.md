# Codebase Onboarding Video｜通用程式架構／業務邏輯新人教學技能包

**目的：讓新進工程師看完一段技術解說動畫，即能掌握系統做什麼、業務怎麼跑、程式在哪裡、如何安全修改及測試。**

這是獨立撰寫的 Codex Agent Skill，可套用 Java / Spring / JBoss / .NET / Python / Node.js / Go / PHP 等可讀取原始碼的專案；不需安裝 `codebase-discovery` 或其他第三方 Agent Skills。AI 分析由 Codex 執行；影片渲染由本套件腳本執行。

## 安裝到 Codex Desktop（macOS / Linux）

解壓縮 ZIP，打開終端機：

```bash
cd /path/to/codebase-onboarding-video
bash scripts/install.sh
```

或手動複製到 `~/.agents/skills/codebase-onboarding-video`，重新啟動 Codex。不同 Agent 的 Skills 掃描位置可能不同，需依產品設定安裝；本包不保證各工具的自動探索行為完全一致，但 `SKILL.md` 可移植。

### 影片環境（可選）

需要 Python 3.9+、Pillow、`ffmpeg`、`ffprobe`。請在隔離的 venv 中安裝 Pillow：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install Pillow
# macOS 且有 Homebrew：brew install ffmpeg
```

旁白：在 macOS 使用 `say -v '?'` 查詢可用語音；`--tts macos --voice '已安裝中文聲音名稱'`。沒有 macOS TTS 時可使用 `--tts none`，**影片會沒有旁白**、另產生 SRT 字幕。本包不呼叫雲端配音服務。若要更自然的語音，需另整合經授權的本機 TTS，不包含在本版。

## 新人教學工作指令

在 Codex Desktop 開啟任意程式碼專案，輸入：

> 使用 `codebase-onboarding-video`，以唯讀方式分析目前專案。我要讓新進工程師用一段約 3–5 分鐘、繁體中文旁白和 2D 動畫的影片，理解系統架構、主要業務流程、核心程式呼叫、資料庫與外部介接、開發修改位置，以及如何測試。請同時產生新人第一週學習路線、Mermaid 架構圖、附檔案行號的證據報告。無法確認的資訊明確標示，不要臆測或外傳機密。

若只要特定功能：

> 使用 `codebase-onboarding-video` 的 `transaction` 模式，講解「訂單取消」的業務規則、資料流、錯誤處理與測試方式，輸出 3 分鐘教學影片。

## 影片前的證據檢查

```bash
python3 scripts/check_evidence.py --repo /path/to/repository \
  --storyboard /path/to/video_storyboard.json \
  --evidence /path/to/06-evidence-register.json
```

此工具驗證引用 ID、檔案及行號是否存在；不會自行判定業務解讀是否正確。

## 示範影片（不需讀取任何真實專案）

```bash
python3 scripts/render_video.py examples/demo_storyboard.json \
  --out /tmp/onboarding-demo --tts macos --target-seconds 210
```

Linux / Windows 可改 `--tts none` 測試動畫與字幕。輸出 `overview.mp4`, `captions.srt`, `render_manifest.json` 與暫存 `assets/`。 `--target-seconds` 會延長場景停留，不會擅自加速語音；實際長度以輸出為準。

## 產出內容

| 檔案 | 用途 |
|---|---|
| 01-system-at-a-glance.md | 系統全貌及主要業務功能 |
| 02-architecture-map.md | 架構、模組與 Mermaid |
| 03-business-workflows.md | 業務規則、流程與例外 |
| 04-code-navigation.md | 呼叫鏈與原始碼位置 |
| 05-developer-first-week.md | 新人學習路線與實作練習 |
| 06-evidence-register.json | 證據索引、可信程度 |
| 07-open-questions.md | 待釐清的資訊 |
| video_storyboard.json | 影片分鏡與旁白稿 |
| video/overview.mp4 | 2D 動態技術介紹影片 |

## 安全與限制

- 預設不執行目標程式、不修改程式碼、不上傳到 TTS 供應商；本機 renderer 不會連線。
- **Codex 本身可能使用線上 AI 模型**，因此是否能分析內部銀行程式碼應先依組織政策確認。
- 影片腳本不會自動查核原始碼的引用是否正確；必須由 Agent 在渲染前逐一驗證證據登錄表。
- 目前是以 Pillow + FFmpeg 製作卡片、流程箭頭、逐步高亮與字幕的原創 2D 動畫模板；不是完整的 Remotion 影片編輯專案，也不具備人物演出、語音字級精準對齊或自行生成專業插畫的能力。
- 示範分鏡為虛構案例，不能視為任何特定公司系統的實際行為。
- 參考截圖僅用來掌握通俗化扁平技術解說風格，沒有內嵌原作者的畫面、Logo 或角色。

## 可擴充方向

Remotion 動態場景引擎、SVG 架構圖、LLM 產生多種視覺分鏡、Whisper 字幕對齊、本機高品質 TTS。此版先提供易移植、可實際執行的基礎工具鏈。
