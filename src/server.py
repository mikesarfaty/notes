import random
import datetime
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template
from .notessecrets import conn_string
from .models import Note, SharedLink
import string
from .configs import new_note_timeout

conn = psycopg2.connect(conn_string)
conn.autocommit = True

rate_limits = []
def rate_limit(ip):
    global rate_limits # pylint: disable=global-statement

    now = datetime.datetime.now()
    rate_limits = list(filter(lambda rate: rate['time'] > now, rate_limits))
    if ip in [rate['ip'] for rate in rate_limits]:
        return True
    rate_limits.append({'time': now + datetime.timedelta(seconds=new_note_timeout), 'ip': ip})
    return False

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/random')
def random_note():
    if rate_limit(request.remote_addr):
        return 'wait a few seconds for the next note'
    note = Note.random().json
    link = add_note_to_share(note['id'])
    return f'{note["title"]}\n{note["note"]}\n\n<a href=/share/{link}>share</a>'

@app.route('/share/<link_uid>')
def get_shared(link_uid):
    note = SharedLink(link_uid).note
    if note is None:
        return 'no such note exists<a href=/random>back</a>'

    note_json = note.json
    return f'{note_json["title"]}\n{note_json["note"]}'

def add_note_to_share(note_id):
    cur = conn.cursor()
    uid = ''.join(random.choice(string.ascii_lowercase) for _ in range(20))
    print(uid)
    cur.execute("""
    INSERT INTO shared_links (note_id, uid) VALUES (%s, %s)
    """, (note_id, uid,))
    return uid

