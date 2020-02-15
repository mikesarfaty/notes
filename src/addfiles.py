import os
import psycopg2
import psycopg2.extras
from notessecrets import conn_string

conn = psycopg2.connect(conn_string)

def main():
    directory = os.environ.get('NOTESDIR', None)
    added = []
    skipped = []
    if directory is None:
        print('dir is none, not doing anything')
    else:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        for base, dirs, files in os.walk(f'./{directory}'):
            for file_ in files:
                with open(f'{directory}/{file_}') as cur_file:
                    lines = cur_file.readlines()
                    title = lines[0][:-1] # strip newline
                    cur.execute("SELECT * FROM notes WHERE title=%s", (title,))
                    if cur.fetchone() is not None:
                        skipped.append(title)
                        continue
                    added.append(title)
                    cur.execute("""
                    INSERT INTO notes (title, note) VALUES (%s, %s)
                    """, (title, "".join(lines[1:])))
        conn.commit()
        print(f'added {", ".join(added or ["None"])}')
        print(f'skipped {", ".join(skipped)}')
                    

if __name__ == '__main__':
    main()
