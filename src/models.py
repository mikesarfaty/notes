import random
import psycopg2
import psycopg2.extras
from .notessecrets import conn_string

conn = psycopg2.connect(conn_string)
class Cursor:
    """
    An abstraction over psycopg2.Cursor

    A TR is:
            A dictionary in the shape of
            {
                id: int
                ...rest of the fields from self.table
            }
    """
    def __init__(self, table):
        self.table = table
        self.cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def id(self, item_id):
        """
        Retrieve an item by its id from this Cursor's table

        Args:
            item_id (int): The integer ID of the TR to retrieve

        Returns:
            TR: the result in the table
        """
        self.cur.execute(f'SELECT * FROM {self.table} WHERE id=%s', (item_id,))
        return self.cur.fetchone()

    def one(self, query, args):
        """
        Retrievs a TR by a custom query

        Args:
            query (str): A SQL Query
            args (List): The args to interpolate in

        Returns:
            TR or {} (if no query matches)
        """
        self.cur.execute(query, tuple(args))
        return self.cur.fetchone() or {}

    def many(self, query, args=None):
        """
        Retrieve a TR[] by a custom query

        Args:
            query (str): A SQL Query
            Args (List): The args to sub in, optional

        Returns: 
            TR[]
        """
        if (args):
            self.cur.execute(query, tuple(args))
        else:
            self.cur.execute(query)
        return self.cur.fetchall()

    def all(self):
        """
        Retrieve all TR[] from a table

        Returns:
            TR[]
        """
        self.cur.execute(f'SELECT * FROM {self.table}')
        return self.cur.fetchall()

    def incr(self, id_, field):
        """
        Increments the int value for field where id_ matches an id in a TR

        Args:
            id_ (int): The ID of the TR to increment
            field (str): The field to increment. Must be an integer field.
        """
        self.cur.execute(f'UPDATE {self.table} SET {field}={field} + 1 WHERE id={id_}')

    def delete(self, id_):
        """
        Deletes an entry from this Cursor's table where id_ matches a TR id

        Args:
            id_ (int): The ID of the TR to delete
        """
        self.cur.execute(f'DELETE FROM {self.table} WHERE id={id_}')


class CursorFactory:
    """
    Shortcut for creating new Cursors to specific tables
    """

    @property
    def notes(self):
        """
        The notes table Cursor
        """
        return Cursor('notes')

    @property
    def link(self):
        """
        The shared_links table Cursor
        """
        return Cursor('shared_links')

cf = CursorFactory()


class Note:
    """
    A Note represents a message with a title and body

    This maps common functionality for Notes to an abstracted object to
    make it easier to work with
    """
    def __init__(self, note_id):
        self.id_ = note_id
        self.__json = {'fetched': False, 'json': None}

    @staticmethod
    def all():
        """
        Retrieve all notes

        Returns:
            Note[]
        """
        return [Note(note['id']) for note in cf.notes.all()]

    @staticmethod
    def where(qargs):
        """
        Retrieve a filterd search of notes

        Returns:
            Note[]
        """
        where_query = ''
        for (col, val) in qargs.items():
            where_query += f'\n{{col}}={{val}}'
        return [Note(note['id']) for note in cf.notes.many(where_query)]

    @staticmethod
    def random():
        """
        Retrieve a random note

        Returns:
            Note
        """
        return Note(random.choice(cf.notes.all())['id'])

    @property
    def json(self):
        """
        Retrieve the json representation of a Note

        Returns:
            A dictionary in the shape
                {
                    title: str
                    note: str
                    ...all other fields in the notes table
                }
        """
        if not self.__json['fetched']:
            note_json = cf.notes.id(self.id_)
            self.__json = {
                'fetched': True,
                'json': note_json
                }
        return self.__json['json']


class SharedLink:
    """
    A SharedLink represents a link to a specific note. The links usually expire
    by having either a max view count, or a view count that exceeds two
    """
    def __init__(self, link):
        self.link = link
        self.id = None
        self.__json = {'fetched': False, 'note': None}

    @property
    def note(self):
        """
        Retrieves a note associated with this link

        Side Effects:
            Deletes the SharedLink if the linked Note is accessed more
            than max_view_count, defaultly 2

        Returns:
            Note?: the Note representation of the SharedLink
        """
        if not self.__json['fetched']:
            link = cf.link.one('''
                SELECT sl.id, n.id as note_id, sl.view_count 
                FROM shared_links sl 
                JOIN notes n ON sl.note_id=n.id 
                WHERE sl.uid=%s''', (self.link,))
            note = Note(link['note_id']) if link else None
            self.__json = {'fetched': True, 'note': note}
            self.id = link.get('id')

        if self.__json['note'] is None:
            return None

        if link['view_count'] >= link.get('max_view_count', 2):
            cf.link.delete(self.id)
            self.__json = {'fetched': True, 'note': None}
        else:
            self.incrview()

        return self.__json['note']

    def incrview(self):
        """
        Increments the view of this SharedLink
        """
        cf.link.incr(self.id, 'view_count')
