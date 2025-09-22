# jobs/upsert_company.py
import os
import sqlite3
from typing import Mapping, Tuple, Dict, Any

DEFAULT_DB = os.getenv("CONNECT_DB", "/root/web_app_4dk/web_app_4dk/modules/1C_Connect.db")

UPSERT_SQL = """
INSERT INTO companies(author_id, connect_id, bitrix_id, author_name)
VALUES (?, ?, ?, ?)
ON CONFLICT(author_id) DO UPDATE SET
  connect_id=excluded.connect_id,
  bitrix_id=excluded.bitrix_id,
  author_name=excluded.author_name;
"""

def _exec_upsert(db_path: str, author_id: str, connect_id: str, bitrix_id: str, author_name: str) -> None:
    con = sqlite3.connect(db_path, timeout=5, isolation_level=None)
    try:
        con.execute("PRAGMA busy_timeout=3000")
        #con.execute("PRAGMA journal_mode=WAL")
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(UPSERT_SQL, (author_id, connect_id, bitrix_id, author_name))
            con.commit()
        except sqlite3.OperationalError:
            # Фолбэк: UPDATE -> INSERT (на случай старого SQLite или отсутствия UNIQUE(author_id))
            con.rollback()
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute(
                "UPDATE companies SET connect_id=?, bitrix_id=?, author_name=? WHERE author_id=?",
                (connect_id, bitrix_id, author_name, author_id)
            )
            if cur.rowcount == 0:
                con.execute(
                    "INSERT INTO companies(author_id, connect_id, bitrix_id, author_name) VALUES (?, ?, ?, ?)",
                    (author_id, connect_id, bitrix_id, author_name)
                )
            con.commit()
    finally:
        con.close()

def upsert_company_job(params: Mapping[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Главная функция-обработчик для словаря custom_webhooks.
    Возвращает (http_status, json_dict).
    """
    db_path    = str(params.get("db") or DEFAULT_DB).strip()
    author_id  = (params.get("author_id")   or "").strip()
    connect_id = (params.get("connect_id")  or "").strip()
    bitrix_id  = str(params.get("bitrix_id") or "").strip()
    author_name= (params.get("author_name") or "").strip()

    missing = [k for k, v in {
        "author_id": author_id,
        "connect_id": connect_id,
        "bitrix_id": bitrix_id,
        "author_name": author_name,
    }.items() if not v]
    if missing:
        return 400, {"ok": False, "error": f"missing params: {', '.join(missing)}"}

    try:
        _exec_upsert(db_path, author_id, connect_id, bitrix_id, author_name)
        return 200, {"ok": True, "author_id": author_id}
    except Exception as e:
        return 500, {"ok": False, "error": str(e)}
