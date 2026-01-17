from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    # This is what Render sees to know the service is alive
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
