import sqlite3


def connect_database(table_name) -> sqlite3.Connection:
    connect = sqlite3.connect('1C_Connect.db')
    data = connect.execute(f"select count(*) from sqlite_master where type='table' and name='{table_name}'")
    for row in data:
        if row[0] == 0:
            with connect:
                connect.execute("""
                CREATE TABLE logs (
                event_type TEXT,
                event_source TEXT,
                message_type INTEGER,
                author_id TEXT,
                treatment_id TEXT,
                line_id TEXT,
                message_id TEXT,
                message_time TEXT,
                user_id TEXT,
                additional_info TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE tasks (
                treatment_id TEXT,
                task_id TEXT,
                responsible_id TEXT,
                line_id TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE companies (
                author_id TEXT,
                connect_id TEXT,
                bitrix_id TEXT,
                author_name TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE users (
                connect_id TEXT,
                bitrix_id TEXT,
                name TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE line_names (
                line_id TEXT,
                line_name TEXT
                );
                """)

    return connect


def add_table_column_db():
    connect = connect_database('tasks')
    sql = 'ALTER TABLE tasks ADD line_id TEXT'
    with connect:
        connect.execute(sql)


if __name__ == '__main__':
    add_table_column_db()