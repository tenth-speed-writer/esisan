import csv
import sqlite3 as s3


def make_connection(path="esisan.db"):
    """Creates a SQLite connection. Assumes a local database file."""
    return s3.connect(path)


# Create types table
with open("typeids.csv", 'r',
          encoding='UTF-8') as type_ids:
    # Parse data to a list of lists
    reader = csv.reader(type_ids)
    rows = [[r[0], r[1]] for r in list(reader)]

    with make_connection() as conn:
        c = conn.cursor()

        # Create the table
        table_statement = """
        CREATE TABLE IF NOT EXISTS type_ids (
            type_id INTEGER PRIMARY KEY,
            name text NOT NULL
        )
        """
        c.execute(table_statement)

        # Insert rows
        row_statement = "INSERT OR REPLACE INTO type_ids VALUES (?, ?)"
        c.executemany(row_statement, rows)

        conn.commit()

# Create orders table
with make_connection() as conn:
    # We'll need to convert is_buy_order into a type='buy' or 'sell' field.
    # We'll also need a fetched_on timestamp.
    c = conn.cursor()
    sql = """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER NOT NULL,
            queried_on TEXT NOT NULL,
            
            location_id INTEGER,
            system_id INTEGER,
            type_id INTEGER,
            
            duration INTEGER,
            issued TEXT,
            range TEXT,
            type TEXT,
            
            price REAL,
            volume_total INTEGER,
            volume_remain INTEGER,
            min_volume INTEGER,
            
            
            PRIMARY KEY (order_id, queried_on),
            FOREIGN KEY (type_id) REFERENCES types(type_id)
        )
    """
    c.execute(sql)
    conn.commit()