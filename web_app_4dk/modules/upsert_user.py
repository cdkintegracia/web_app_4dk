import os
import sqlite3
from typing import Mapping, Tuple, Dict, Any

DEFAULT_DB = os.getenv("CONNECT_DB", "/root/web_app_4dk/web_app_4dk/modules/1C_Connect.db")

UPSERT_SQL = """
INSERT INTO users(connect_id, bitrix_id, name)
VALUES (?, ?, ?)
ON CONFLICT(connect_id) DO UPDATE SET
  bitrix_id=excluded.bitrix_id,
  name=excluded.name;
"""

def _exec_upsert_user(db_path: str, connect_id: str, bitrix_id: str, name: str) -> None:
    con = sqlite3.connect(db_path, timeout=5, isolation_level=None)
    try:
        con.execute("PRAGMA busy_timeout=3000")
        #con.execute("PRAGMA journal_mode=WAL")
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(UPSERT_SQL, (connect_id, bitrix_id, name))
            con.commit()
        except sqlite3.OperationalError:
            con.rollback()
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute(
                "UPDATE users SET bitrix_id=?, name=? WHERE connect_id=?",
                (bitrix_id, name, connect_id)
            )
            if cur.rowcount == 0:
                con.execute(
                    "INSERT INTO users(connect_id, bitrix_id, name) VALUES (?, ?, ?)",
                    (connect_id, bitrix_id, name)
                )
            con.commit()
    finally:
        con.close()

def upsert_user_job(req: Mapping[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Главная функция-обработчик для пользователей.
    Возвращает (http_status, json_dict).
    """
    db_path    = str(req.get("db") or DEFAULT_DB).strip()
    connect_id = (req.get("connect_id") or "").strip()
    bitrix_id  = (req.get("bitrix_id") or "").strip()
    name       = (req.get("name") or "").strip()

    missing = [k for k, v in {
        "connect_id": connect_id,
        "bitrix_id": bitrix_id,
        "name": name,
    }.items() if not v]
    if missing:
        return 400, {"ok": False, "error": f"missing params: {', '.join(missing)}"}
    try:
        _exec_upsert_user(db_path, connect_id, bitrix_id, name)
        return 200, {"ok": True, "connect_id": connect_id}
    except Exception as e:
        return 500, {"ok": False, "error": str(e)}
