export FLASK_APP=src/server.py
export FLASK_ENV=development
export NOTES_ENV=dev

source /data/venvs/notes/bin/activate
flask run
