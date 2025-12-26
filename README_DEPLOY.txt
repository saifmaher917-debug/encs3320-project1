ENCS3320 Project 1 - Deploy (Flask)

Run locally:
  pip install -r requirements.txt
  python app.py
Open:
  http://localhost:8099/en

Deploy on Render:
  Build Command: pip install -r requirements.txt
  Start Command: gunicorn app:app
