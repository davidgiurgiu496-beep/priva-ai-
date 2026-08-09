import os
from flask import Flask, render_template_string, request
from huggingface_hub import InferenceClient
from duckduckgo_search import DDGS

app = Flask(__name__)

# Token-ul tău Hugging Face
HF_TOKEN = "Hf_dOhyzZHYtVFtGzMpaMDqbOBYWTswGWWQoc"

# Folosim un model ultra-stabil și rapid
MODEL_ID = "Qwen/Qwen2.5-72B-Instruct"
client = InferenceClient(MODEL_ID, token=HF_TOKEN)

def search_web(query):
    try:
        results = DDGS().text(query, max_results=2)
        if results:
            return "\n".join([f"- {r.get('body', '')}" for r in results])
    except Exception:
        pass
    return ""

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Priva AI</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #131314; color: white; margin: 0; padding: 20px; }
        #chat { max-width: 700px; margin: 0 auto; }
        .header { display: flex; align-items: center; gap: 12px; }
        .msg { padding: 12px 16px; margin: 10px 0; border-radius: 10px; line-height: 1.5; word-break: break-word; }
        .user { background: #282a2c; text-align: right; margin-left: 20%; }
        .ai { background: #1e1f20; text-align: left; border: 1px solid #333; margin-right: 20%; }
        .input-box { display: flex; gap: 8px; margin-top: 15px; }
        input { flex: 1; padding: 12px; background: #222; color: white; border: 1px solid #444; border-radius: 8px; font-size: 1rem; }
        button { padding: 12px 20px; background: #a8c7fa; color: #000; border: none; font-weight: bold; border-radius: 8px; cursor: pointer; }
    </style>
</head>
<body>
    <div id="chat">
        <div class="header">
            <h2>🔒 Priva AI</h2>
        </div>
        <p>🟢 Server activ & Conectat la Internet</p>
        <hr><br>
        <div id="history"></div>
        <br>
        <div class="input-box">
            <input type="text" id="in" placeholder="Scrie un mesaj..." onkeydown="if(event.key==='Enter') send()">
            <button onclick="send()">Trimite</button>
        </div>
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
            resDiv.innerText = 'Priva gândește...';
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
                resDiv.innerText = 'Eroare temporară de conexiune. Încearcă din nou.';
            }
            window.scrollTo(0, document.body.scrollHeight);
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
    if not user_msg:
        return {"reply": "Te rog introdu un mesaj valid."}
        
    web_context = search_web(user_msg)
    
    prompt = f"Informații recente de pe internet:\n{web_context}\n\nÎntrebare: {user_msg}" if web_context else user_msg
    
    messages = [
        {"role": "system", "content": "Ești Priva AI, un asistent util și politicos. Răspunde direct în limba utilizatorului."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = client.chat_completion(messages=messages, max_tokens=500)
        reply = response.choices[0].message.content
    except Exception as e:
        # Fallback pe alt model rapid dacă primul întâmpină probleme
        try:
            fallback_client = InferenceClient("meta-llama/Llama-3.2-1B-Instruct", token=HF_TOKEN)
            response = fallback_client.chat_completion(messages=messages, max_tokens=500)
            reply = response.choices[0].message.content
        except Exception:
            reply = "Modelul se încarcă pe server. Te rog trimite mesajul din nou în 5 secunde."

    return {"reply": reply}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
