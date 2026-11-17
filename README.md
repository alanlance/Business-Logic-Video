# Business Logic Video Skill (Codex / macOS)

將陌生程式碼的業務邏輯整理成有證據的文件，再產生動畫影片、繁體中文字幕與旁白。**這是新整合的自訂 Skill，不是原始 GitHub Skills 的官方合併版本。**

## 一次安裝

1. 解壓縮 ZIP，取得 `business-logic-video-skill` 資料夾。
2. 將此資料夾複製到 `~/.agents/skills/business-logic-video`（Codex 使用者層級）。

```bash
mkdir -p ~/.agents/skills
cp -R /path/to/business-logic-video-skill ~/.agents/skills/business-logic-video
```

3. 若執行環境沒有必要套件，安裝 Python 3、Pillow 和 FFmpeg：

```bash
python3 -m pip install Pillow
brew install ffmpeg  # 已有 ffmpeg 可以略過；Homebrew 並非安裝 Skill 的必要條件
```

4. 重啟 Codex Desktop，開啟要分析的 Repository，輸入：

> 使用 business-logic-video 分析「某筆交易的處理流程」，只讀取必要原始碼。產生繁體中文業務懶人包、Mermaid、證據檔案行號，以及約 3 分鐘、有動畫、繁體中文字幕、macOS 本機旁白的 MP4。先檢查敏感資料，不得外傳程式碼；不明確的業務規則請標示待確認。

## 影片單獨測試

```bash
cd ~/.agents/skills/business-logic-video
python3 scripts/render_video.py examples/demo_storyboard.json --out /tmp/bl-video-demo --tts macos --target-seconds 180
```

`--tts macos` 使用 macOS 本機 `say`；以 `say -v '?'` 查詢系統已安裝中文語音，並使用 `--voice '聲音名稱'` 明確指定。聲音品質取決於 macOS 語音資源。**若選 `--tts none`，影片沒有旁白**，僅提供動畫與字幕。

影片工具輸出：`overview.mp4`、`captions.srt`、`render_manifest.json`、`assets/`。預設 720p、24 FPS。`--resolution 1920x1080` 可做高畫質，但會明顯增加計算時間。`--target-seconds` 是目標長度，遇到旁白本身較長時不會強制加速。

## 備註

- **資料安全**：不使用雲端 TTS，不預設對外傳送原始碼；Codex 模型服務本身的資料傳輸與使用政策仍取決於帳號、產品及組織設定。對受管制的銀行原始碼，請先確認公司內控和模型使用權限。
- 這個 Skill 負責指導 AI 解讀程式；影片程式只讀取已生成且人工可檢查的 JSON storyboard。**renderer 不會自動驗證故事板引用的原始碼行號**，需由 Codex 按 SKILL.md 的交付檢查完成。
- 動畫呈現是卡片式流程動態與步驟高亮，不是由程式自動產生任意 SVG/角色動畫。Mermaid 圖保留於說明文件。
- Skill 只整合工作方法，沒有拷貝第三方原始 SKILL.md 全文或原始腳本。來源與授權需另依各上游 Repository 確認。

## 參考的方法論來源

- DiUS/agent-toolkit — codebase-discovery
- meirm/reverse-engineering-skill — reverse-engineering-business-logic, tailor-bdd-skills-for-project
- Data-System-School/agent-skills — investigate-codebase
- NinjaSln-labs/agent-skills — deep-codebase-analysis
