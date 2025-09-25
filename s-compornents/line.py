import os
from flask import Flask, request, abort
from dotenv import load_dotenv

# v3用のimport
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhook import WebhookHandler    # ← これが正しい
from linebot.v3.webhooks.models import MessageEvent, TextMessageContent

# envファイルのパスを ./compornents/key.env に変更
env_path = os.path.join(os.path.dirname(__file__), '../compornents/key.env')
load_dotenv(env_path)

CHANNEL_SECRET = os.getenv("ChannelSecret")
CHANNEL_ACCESS_TOKEN = os.getenv("ChannelAccessToken")

app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    reply_text = f"あなたのユーザーIDは: {user_id}"
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.reply_message(
            reply_token=event.reply_token,
            messages=[{"type": "text", "text": reply_text}]
        )

if __name__ == "__main__":
    app.run(port=5000)