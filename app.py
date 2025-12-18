import configparser
import json
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import paho.mqtt.client as mqtt

# --- 1. 配置載入 ---
config = configparser.ConfigParser()
try:
    # 讀取 config.ini，使用 UTF-8 編碼 (已修正)
    config.read('config.ini', encoding='utf-8')
except Exception as e:
    print(f"Error reading config.ini: {e}")
    # 在無法載入配置時，程式應停止
    exit(1)

# --- 2. 配置值提取 ---
# LINE 設定
LINE_SECRET = config['Line']['CHANNEL_SECRET']
LINE_ACCESS_TOKEN = config['Line']['CHANNEL_ACCESS_TOKEN']

# MQTT 設定
MQTT_HOST = config['MQTT']['mqtthost']
MQTT_PORT = int(config['MQTT']['mqttport'])
MQTT_USER = config['MQTT']['mqttuser']
MQTT_PASS = config['MQTT']['mqttpass']
LINE_MSG_TOPIC = config['MQTT']['line_message_topic']

# --- 3. 初始化客戶端 ---
app = Flask(__name__)
handler = WebhookHandler(LINE_SECRET)

# 初始化 LINE Messaging Client
line_api_config = Configuration(access_token=LINE_ACCESS_TOKEN)

# 初始化 MQTT Client (Webhook 負責發布)
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
try:
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_start() # 啟動背景線程來處理連線和重連
    print(f"MQTT Publisher connected to {MQTT_HOST}:{MQTT_PORT}")
except Exception as e:
    print(f"MQTT Connection Failed: {e}")


# --- 4. Flask Webhook 端點 ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel secret.")
        abort(400)

    return 'OK'

# --- 5. LINE 訊息事件處理器 ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """
    接收所有 LINE 訊息事件 (文字、圖片、語音等)，並將其轉換為標準格式發布到 MQTT。
    """
    message_type = event.message.type
    message_content = {
        "reply_token": event.reply_token,
        "user_id": event.source.user_id,
        "type": message_type,
        "text": None,
        "image_url": None, # 圖片和語音會使用外部 URL
        "audio_url": None
    }
    
    if message_type == "text":
        message_content["text"] = event.message.text
    elif message_type == "image":
        # ⚠️ 圖片處理: LINE API 要求先用 Messaging API 獲取內容，再上傳到您自己的伺服器
        # 為了簡化範例，我們假設您會在這裡完成圖片下載並取得可公開存取的 URL
        # 實際流程：取得 content_id -> 呼叫 API 獲取內容 -> 儲存 -> 取得 image_url
        message_content["text"] = "用戶發送了一張圖片。"
        message_content["image_url"] = "placeholder_url_for_your_image" 
        
    elif message_type == "audio":
        # ⚠️ 語音處理: 假設您已經完成了語音轉文字 (ASR) 流程，並獲得了文字內容
        message_content["text"] = "用戶發送了一段語音 (已轉錄為文字)。"
        message_content["audio_url"] = "placeholder_url_for_your_audio"

    # --- 發布到 MQTT ---
    payload = json.dumps(message_content)
    mqtt_client.publish(LINE_MSG_TOPIC, payload)
    print(f"Published to MQTT Topic {LINE_MSG_TOPIC}: {message_type} message from {message_content['user_id']}")

# --- 6. 運行 Flask ---
if __name__ == "__main__":
    # 在實際部署時，請使用 gunicorn 替代 app.run()
    # 例如: gunicorn -w 4 'app:app'
    app.run(port=5001)