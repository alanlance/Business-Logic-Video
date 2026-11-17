# Storyboard schema v1

Top-level object:

```json
{
  "title": "交易處理流程（示意）",
  "subtitle": "系統業務邏輯快速導覽",
  "language": "zh-TW",
  "example": true,
  "revision": "demo",
  "scenes": [
    {
      "title": "受理請求",
      "narration": "使用者送出交易請求，系統先檢查必要欄位。",
      "steps": ["使用者提出請求", "驗證輸入", "進入核心流程"],
      "focus": 1,
      "evidence_ids": [],
      "status": "DEMO"
    }
  ]
}
```

- `title`: required nonempty string.
- `scenes`: 2–12 scene objects.
- Each scene: `title`, `narration` 15–180 Chinese characters, `steps` array of 2–5 short, non-sensitive labels; `focus` 0-based highlighted step index, optional; `evidence_ids` array of rule IDs; `status` `CONFIRMED|DEMO|UNKNOWN`.
- For `example=false`, each `CONFIRMED` scene requires at least one `evidence_ids`; `UNKNOWN` scene must use explicit conditional language and is **not** permitted to state behavior as fact.
- Use only evidence IDs that exist in `05-evidence-register.md` and verify file/line references before rendering.
- Avoid secrets, personal data, actual transaction IDs, customer names, private endpoints, and credentials in all fields. Narrative is used verbatim for local TTS and SRT.
- Video pacing derives primarily from generated speech duration; `--target-seconds` is a pacing goal, not guaranteed when speech audio is longer. Output manifest records the exact total duration.
