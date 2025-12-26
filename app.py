import os
import hashlib
import secrets
from urllib.parse import parse_qs
from flask import Flask, request, send_from_directory, redirect, make_response

app = Flask(__name__, static_folder="www", static_url_path="")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WWW_DIR = os.path.join(BASE_DIR, "www")
DATA_FILE = os.path.join(BASE_DIR, "data.txt")

# In-memory sessions: session_id -> username
SESSIONS = {}

REDIRECTS = {
    "/chat": "https://chat.openai.com/",
    "/cf": "https://www.cloudflare.com/",
    "/rt": "https://ritaj.birzeit.edu/",
}

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def load_users() -> dict:
    users = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                u, h = line.split(":", 1)
                users[u.strip()] = h.strip()
    return users

def save_user(username: str, password_hash: str) -> None:
    # Append (simple storage like original project)
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{username}:{password_hash}\n")

def get_session_user() -> str | None:
    sid = request.cookies.get("session_id")
    if not sid:
        return None
    return SESSIONS.get(sid)

def set_session_cookie(resp, sid: str):
    # Similar to original: Path=/, HttpOnly
    resp.set_cookie("session_id", sid, path="/", httponly=True, samesite="Lax")
    return resp

def response_404():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    client_port = request.environ.get("REMOTE_PORT", "unknown")
    html = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Error 404</title></head>
<body>
  <h1 style="color:red;">The file is not found</h1>
  <p><b>saif janazrh - 1222937</b></p>
  <p>Client IP: {client_ip}</p>
  <p>Client Port: {client_port}</p>
</body>
</html>"""
    return html, 404, {"Content-Type": "text/html; charset=utf-8"}

@app.get("/")
def root():
    return redirect("/en", code=302)

@app.get("/en")
def en():
    return send_from_directory(WWW_DIR, "main_en.html")

@app.get("/ar")
def ar():
    return send_from_directory(WWW_DIR, "main_ar.html")

# Static pages (GET)
@app.get("/login.html")
def login_page():
    return send_from_directory(WWW_DIR, "login.html")

@app.get("/register.html")
def register_page():
    return send_from_directory(WWW_DIR, "register.html")

@app.get("/protected.html")
def protected_page():
    user = get_session_user()
    if not user:
        # Needs session -> redirect to login page (same behavior shown in UI)
        return redirect("/login.html", code=302)
    return send_from_directory(WWW_DIR, "protected.html")

@app.get("/logout")
def logout():
    sid = request.cookies.get("session_id")
    if sid and sid in SESSIONS:
        del SESSIONS[sid]
    resp = make_response(redirect("/login.html", code=302))
    resp.set_cookie("session_id", "", path="/", expires=0)
    return resp

# Redirect routes (307)
@app.get("/chat")
@app.get("/cf")
@app.get("/rt")
def redirects():
    return redirect(REDIRECTS[request.path], code=307)

# Forms (POST) - same endpoints as original
@app.post("/register")
def register_post():
    # Flask already parsed form
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()

    if not username or not password:
        msg = "Missing username or password."
    else:
        users = load_users()
        if username in users:
            msg = "Username already exists."
        else:
            save_user(username, sha256_hex(password))
            msg = "Registered successfully! You can login now."

    page = f"<html><body><h3>{msg}</h3><a href='/login.html'>Go to Login</a></body></html>"
    resp = make_response(page, 200)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

@app.post("/login")
def login_post():
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()

    users = load_users()
    ok = bool(username and password and username in users and users[username] == sha256_hex(password))

    if ok:
        sid = secrets.token_hex(16)
        SESSIONS[sid] = username

        # Return protected page and set cookie
        try:
            content = open(os.path.join(WWW_DIR, "protected.html"), "r", encoding="utf-8").read()
        except Exception:
            content = f"<html><body><h2>Welcome {username}</h2></body></html>"

        resp = make_response(content, 200)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return set_session_cookie(resp, sid)

    data = ("<html><body><h3 style='color:red;'>Login failed</h3>"
            "<a href='/login.html'>Try again</a></body></html>")
    resp = make_response(data, 401)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

# Serve any file inside www (css, images, etc.)
@app.get("/<path:filename>")
def serve_www(filename):
    full = os.path.join(WWW_DIR, filename)
    if os.path.isfile(full):
        return send_from_directory(WWW_DIR, filename)
    return response_404()

@app.errorhandler(404)
def not_found(_e):
    return response_404()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8099"))
    app.run(host="0.0.0.0", port=port)
