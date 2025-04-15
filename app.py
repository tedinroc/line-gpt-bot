import os
import openai
import redis
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# Line Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI 設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Redis 設定（用於連續對話）
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(redis_url)

# 幫助函式：取得用戶對話歷史
def get_history(user_id):
    history = r.get(user_id)
    if history:
        return history.decode("utf-8")
    return ""

def save_history(user_id, history):
    r.set(user_id, history, ex=3600)  # 保留1小時

# 文字訊息處理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    user_text = event.message.text
    history = get_history(user_id)
    prompt = history + f"\nUser: {user_text}\nAI:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",  # 如無 vision 權限可改用 gpt-4
            messages=[{"role": "system", "content": "你是一個友善的AI助理。"},
                      {"role": "user", "content": prompt}],
            max_tokens=500
        )
        ai_reply = response.choices[0].message["content"].strip()
        # 儲存對話歷史
        new_history = history + f"\nUser: {user_text}\nAI: {ai_reply}"
        save_history(user_id, new_history)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="發生錯誤，請稍後再試。")
        )

# 圖片訊息處理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id
    try:
        # 取得圖片內容
        message_content = line_bot_api.get_message_content(message_id)
        img = Image.open(BytesIO(message_content.content))
        # 將圖片轉為 bytes
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        # 呼叫 OpenAI Vision API
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": "你是一個會分析圖片的AI助理。"},
                {"role": "user", "content": [
                    {"type": "text", "text": "請描述這張圖片。"},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + img_bytes.hex()}}
                ]}
            ],
            max_tokens=500
        )
        ai_reply = response.choices[0].message["content"].strip()
        # 儲存對話歷史
        history = get_history(user_id)
        new_history = history + f"\nUser: [圖片]\nAI: {ai_reply}"
        save_history(user_id, new_history)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="圖片分析失敗，請稍後再試。")
        )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
