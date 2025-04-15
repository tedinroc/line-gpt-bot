# Line GPT-4.1 智能對話機器人

## 功能說明
- 支援文字訊息分析（聊天、問答）
- 支援圖片分析（可描述、理解圖片內容）
- 具備連續對話能力（記住上下文，像真人一樣接續聊天）

## 使用方法
1. 申請 OpenAI API Key
2. 申請 Line Bot 並取得 Channel Secret 與 Access Token
3. 將這些金鑰填入 `.env` 或程式設定處
4. 安裝所需套件：
   ```
   pip install -r requirements.txt
   ```
5. 啟動伺服器：
   ```
   python app.py
   ```
6. 在 Line Developers 後台設定 Webhook URL，格式如：
   ```
   https://你的伺服器網址/callback
   ```

## 目錄結構
- app.py：主程式，Flask 伺服器，串接 Line 與 OpenAI
- requirements.txt：套件需求檔
- README.md：說明文件

## 注意事項
- 請妥善保管金鑰，不要外洩
- 圖片分析功能需使用 GPT-4.1 Vision 或 Google Vision API
- 連續對話功能建議使用 Redis 或簡易檔案記錄

---

如有任何問題，歡迎詢問！
