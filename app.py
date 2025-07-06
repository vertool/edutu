from flask import Flask, render_template, request, redirect, url_for, session
import requests
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'kashmir_edu_vote_secret'

TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('CHAT_ID')
DB_FILE = 'votes.db'

# --- Database Setup ---
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE votes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vote TEXT NOT NULL,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        contact TEXT NOT NULL,
                        UNIQUE(email)
                    )''')
        conn.commit()
        conn.close()

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

@app.route('/')
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM votes WHERE vote='yes'")
    yes_count = c.fetchone()[0]  # should be 6
    c.execute("SELECT COUNT(*) FROM votes WHERE vote='no'")
    no_count = c.fetchone()[0]   # should be 1
    conn.close()
    return render_template('index.html', yes=yes_count, no=no_count)

    
@app.route('/vote', methods=['POST'])
def vote():
    vote = request.form.get('vote')
    if vote in ['yes', 'no']:
        session['vote'] = vote
        return redirect(url_for('details'))
    return redirect(url_for('index'))

@app.route('/details')
def details():
    if 'vote' not in session:
        return redirect(url_for('index'))
    return render_template('details.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'vote' not in session:
        return redirect(url_for('index'))

    name = request.form.get('name')
    email = request.form.get('email')
    contact = request.form.get('contact')

    if not all([name, email, contact]):
        return "All fields required!", 400

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO votes (vote, name, email, contact) VALUES (?, ?, ?, ?)",
                  (session['vote'], name, email, contact))
        conn.commit()
        conn.close()

        # Send vote to Telegram
        message = f"""🗳️ <b>New Vote Submitted</b>\n
    <b>Vote:</b> {session['vote'].capitalize()}
    <b>Name:</b> {name}
    <b>Email:</b> {email}
    <b>Contact:</b> {contact}"""
        send_telegram_message(message)

        session.pop('vote', None)
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        return "You have already voted!", 400


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5050)
