# Video storyboard v1

```json
{
  "title":"新人快速上手：訂單系統（虛構案例）",
  "subtitle":"架構、業務流程與開發導覽",
  "language":"zh-TW", "example":true, "revision":"demo",
  "scenes":[
    {"chapter":"01 架構","title":"一分鐘看懂系統","narration":"這是一個虛構的示範系統...","steps":["使用者","API","業務服務","資料庫"],"focus":1,"evidence_ids":[],"status":"DEMO"}
  ]
}
```

For `example=false`, scenes with status `CONFIRMED` must contain 1+ claim IDs from `06-evidence-register.json`. `UNKNOWN` scenes are explicitly questions; never narrate their behavior as actual fact. `steps` must have 2–5 short labels, `focus` must be a valid zero-based index. 2–12 scenes for the bundled renderer. `chapter` optional. `narration` is directly used for local TTS and exported SRT. `example=true` must be labeled as illustrative onscreen. Never include sensitive source excerpts/URLs/names in a storyboard.
