import os
from flask import Flask, render_template_string, request
from huggingface_hub import InferenceClient
from duckduckgo_search import DDGS

app = Flask(__name__)
client = InferenceClient("google/gemma-2-2b-it")

def search_web(query):
    try:
        results = DDGS().text(query, max_results=3)
        return "\n".join([f"- {r['body']}" for r in results])
    except Exception:
        return ""

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Priva AI</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { font-family: sans-serif; background: #131314; color: white; margin: 0; padding: 20px; }
        #chat { max-width: 700px; margin: 0 auto; }
        .header { display: flex; align-items: center; gap: 12px; }
        .header img { width: 40px; height: 40px; }
        .msg { padding: 12px 16px; margin: 10px 0; border-radius: 10px; line-height: 1.5; }
        .user { background: #282a2c; text-align: right; }
        .ai { background: #1e1f20; text-align: left; border: 1px solid #333; }
        input { width: 75%; padding: 12px; background: #222; color: white; border: 1px solid #444; border-radius: 8px; font-size: 1rem; }
        button { padding: 12px 18px; background: #a8c7fa; border: none; font-weight: bold; border-radius: 8px; cursor: pointer; font-size: 1rem; }
    </style>
</head>
<body>
    <div id="chat">
        <div class="header">
            <img src="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f512.png" alt="Logo">
            <h2>Priva AI</h2>
        </div>
        <p>🟢 Status: Connected to Internet | Online Server</p>
        <hr><br>
        <div id="history"></div>
        <br>
        <input type="text" id="in" placeholder="Ask Priva anything..." onkeydown="if(event.key==='Enter') send()">
        <button onclick="send()">Send</button>
    </div>

    <script>
        async function send() {
            let input = document.getElementById('in');
            let txt = input.value.trim();
            if(!txt) return;

            document.getElementById('history').innerHTML += `<div class="msg user">${txt}</div>`;
            input.value = '';
            
            let resDiv = document.createElement('div');
            resDiv.className = 'msg ai';
            resDiv.innerText = 'Priva is thinking...';
            document.getElementById('history').appendChild(resDiv);
            
            try {
                let r = await fetch('/chat', {
                    method: 'POST', 
                    headers: {'Content-Type':'application/json'}, 
                    body: JSON.stringify({msg: txt})
                });
                let data = await r.json();
                resDiv.innerHTML = marked.parse(data.reply);
            } catch(e) {
                resDiv.innerText = 'Error connecting to server. Try again.';
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("msg", "")
    web_context = search_web(user_msg)
    
    messages = [
        {"role": "system", "content": "You are Priva AI. Answer politely in the user's language."},
        {"role": "user", "content": f"Context from internet:\n{web_context}\n\nUser Question: {user_msg}" if web_context else user_msg}
    ]
    
    try:
        response = client.chat_completion(messages=messages, max_tokens=500)
        reply = response.choices[0].message.content
    except Exception:
        reply = "Server is busy, try again in a moment."

    return {"reply": reply}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
