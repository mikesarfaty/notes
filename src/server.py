import random
import datetime
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template
from .notessecrets import conn_string

rate_limits = []
def rate_limit(ip):
    global rate_limits # pylint: disable=global-statement

    now = datetime.datetime.now()
    rate_limits = list(filter(lambda rate: rate['time'] > now, rate_limits))
    if ip in [rate['ip'] for rate in rate_limits]:
        return True
    rate_limits.append({'time': now + datetime.timedelta(seconds=5), 'ip': ip})
    return False

app = Flask(__name__)
conn = psycopg2.connect(conn_string)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/random')
def random_note():
    if rate_limit(request.remote_addr):
        return 'wait a few seconds for the next note'
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM notes')
    all_notes = cur.fetchall()
    note = random.choice(all_notes)
    return f'{note["title"]}\n{note["note"]}'
