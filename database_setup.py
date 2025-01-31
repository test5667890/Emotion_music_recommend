import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('sqlit.db')
c = conn.cursor()

# Create table Shopag with fullname and role columns (if not created)
c.execute('''
    CREATE TABLE IF NOT EXISTS Shopag (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )
''')

# Create table for songs with the necessary columns
c.execute('''
    CREATE TABLE IF NOT EXISTS Songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT NOT NULL,           -- Path to the image (album cover)
        title TEXT NOT NULL,           -- Song title
        artist TEXT NOT NULL,          -- Artist name
        song TEXT NOT NULL,            -- Path to the song file
        mode TEXT NOT NULL DEFAULT 'unknown'  -- Mode (default is 'unknown')
    )
''')

# Commit and close the connection
conn.commit()
conn.close()

print("Database and table 'Songs' created successfully.")
