import sqlite3 as sl


con = sl.connect('DataBase.db')

data = con.execute("select count(*) from sqlite_master where type='table' and name='first_table'")
for row in data:
    if row[0] == 0:
        with con:
            con.execute("""
            CREATE TABLE first_table (
            id INTEGER AUTO_INCREMENT PRIMARY_KEY,
            name VARCHAR(100)
            );
            """)
