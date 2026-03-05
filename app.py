import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template_string

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return render_template_string("""
<!DOCTYPE html>
<html>
<head><title>PPC Affiliate Platform</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:sans-serif; }
body { background:#0f172a; color:#e2e8f0; min-height:100vh; display:flex; align-items:center; justify-content:center; }
.card { text-align:center; padding:3rem; }
h1 { font-size:2.5rem; margin-bottom:1rem; color:#22d3ee; }
p { color:#94a3b8; margin-bottom:2rem; font-size:1.1rem; }
.btn { display:inline-block; margin:0.5rem; padding:0.75rem 1.5rem; border-radius:8px; font-weight:600; text-decoration:none; }
.primary { background:#22d3ee; color:#0f172a; }
.ghost { border:1px solid #22d3ee; color:#22d3ee; }
</style></head>
<body>
<div class="card">
  <h1>PPC Affiliate Platform</h1>
  <p>Advertisers get traffic. Affiliates earn per click.</p>
  <a href="/signup" class="btn primary">Get Started</a>
  <a href="/login" class="btn ghost">Log In</a>
</div>
</body>
</html>
        """)

    @app.route('/health')
    def health():
        return {"status": "ok"}, 200

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
