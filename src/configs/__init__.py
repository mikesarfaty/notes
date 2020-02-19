import os

if os.environ.get('NOTES_ENV').upper() == 'DEV':
    print('LOADING NOTES CONFIG: DEVELOPMENT')
    from .dev import new_note_timeout
else:
    print(f'UNRECOGNIZED NOTES CONFIG: {os.environ["NOTES_ENV"]}')
