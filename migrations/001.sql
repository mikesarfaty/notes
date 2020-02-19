CREATE TABLE shared_links (
    id serial PRIMARY KEY,
    note_id int NOT NULL,
    uid TEXT NOT NULL,
    view_count int DEFAULT 0 NOT NULL
);

CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    note TEXT NOT NULL
);

