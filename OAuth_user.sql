CREATE TABLE OAuth_user (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    image_file TEXT NOT NULL
)