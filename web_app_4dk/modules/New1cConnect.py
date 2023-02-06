import sqlite3
import dateutil.parser
from datetime import datetime


def connect_database(table_name) -> sqlite3.Connection:
    connect = sqlite3.connect('1C_Connect.db')
    data = connect.execute(f"select count(*) from sqlite_master where type='table' and name='{table_name}'")
    for row in data:
        if row[0] == 0:
            with connect:
                if table_name == 'logs':
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
    return connect


def write_logs_to_database(log):
    additional_info = ''
    if log['message_type'] == 1:
        additional_info = log['text']
    elif log['message_type'] == 53:
        additional_info = f"Длительность: log['rda']['duration']"
    elif log['message_type'] == 70:
        if 'preview_link_hi' in log['file']:
            additional_info = f"{log['file']['file_name']}\n{log['file']['preview_link_hi']}\n"
        else:
            additional_info = f"{log['file']['file_name']}\n{log['file']['file_path']}\n"
    elif log['message_type'] == 82:
        additional_info = f"Длительность обращения: {log['treatment']['treatment_duration']}\n"

    connect = connect_database('logs')
    sql = "INSERT INTO logs (event_type, event_source, message_type, author_id, treatment_id, line_id, message_id, message_time, user_id, additional_info) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    data = (
        log['event_type'],
        log['event_source'],
        log['message_type'],
        log['author_id'],
        log['treatment_id'],
        log['line_id'],
        log['message_id'],
        datetime.strftime(dateutil.parser.isoparse(log['message_time']), '%Y.%m.%d %H:%M:%S'),
        log['user_id'],
        additional_info,
    )
    with connect:
        connect.execute(sql, data)
    print('SQL записаны')
