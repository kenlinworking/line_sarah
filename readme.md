LINE Bot 訊息轉 MQTT 橋接器 (LINE to MQTT Bridge)這是一個基於 Python Flask 開發的 Webhook 伺服器，旨在接收來自 LINE 官方帳號的訊息事件，並將其封裝成 JSON 格式後轉發（Publish）至指定的 MQTT 主題（Topic）。這對於需要將 LINE 訊息整合進物聯網（IoT）架構或自動化流程的開發者非常有用。🌟 主要功能Webhook 接收：自動處理 LINE 平台的 Webhook 請求並驗證數位簽章（X-Line-Signature）。訊息轉化：支援文字訊息處理，並預留了圖片與語音訊息的擴充接口。MQTT 整合：將 LINE 訊息即時發佈到 MQTT Broker，方便後端訂閱者進行非同步處理。配置管理：使用 config.ini 管理所有敏感資訊與連線設定。🛠️ 環境準備1. 軟體需求Python 3.8+一個 MQTT Broker (例如 Mosquitto, EMQX, 或 HiveMQ)LINE Developer 帳號並建立一個 Messaging API Channel2. 安裝依賴庫pip install flask line-bot-sdk paho-mqtt configparser
⚙️ 配置文件設定請在專案根目錄建立一個 config.ini 文件，並填入以下內容：[Line]
CHANNEL_SECRET = 你的_LINE_CHANNEL_SECRET
CHANNEL_ACCESS_TOKEN = 你的_LINE_CHANNEL_ACCESS_TOKEN

[MQTT]
mqtthost = 127.0.0.1
mqttport = 1883
mqttuser = your_username
mqttpass = your_password
line_message_topic = home/line/messages
🚀 執行方式啟動 Webhook 伺服器：python app.py
伺服器預設會運行在 http://localhost:5001。公開 URL (開發測試用)：由於 LINE 需要一個公開的 HTTPS 網址，你可以使用 ngrok：ngrok http 5001
將產生的網址填入 LINE Developers Console 的 Webhook URL 欄位（例如：https://xxxx.ngrok-free.app/callback）。📊 MQTT Payload 格式發佈至 MQTT 的訊息採 JSON 格式，範例如下：{
  "reply_token": "nH7wFpWNLWvSjCP8HIn6v....",
  "user_id": "U1234567890abcdef...",
  "type": "text",
  "text": "這是用戶傳送的訊息內容",
  "image_url": null,
  "audio_url": null
}
📝 注意事項圖片與語音處理：目前程式碼中對於 image 與 audio 類型僅提供佔位符。實際應用時，需調用 LINE API 下載內容，儲存至雲端空間（如 S3）後，再將生成的 URL 放入 JSON 中。部署建議：在正式環境中，建議使用 gunicorn 配合 Nginx 進行部署，以提高並發處理能力。MQTT 連線：程式啟動時會自動嘗試連線 MQTT Broker，請確保 Broker 已開啟並允許對應的帳號密碼存取。授權 (License)此專案採用 MIT 授權。