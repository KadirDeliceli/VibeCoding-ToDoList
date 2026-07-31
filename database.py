from __future__ import annotations
import sqlite3
from contextlib import contextmanager

from models import Todo

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    category_id INTEGER NOT NULL DEFAULT 1,
    time_range TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);
"""

DEFAULT_CATEGORY = "Genel"


class Database:
    def __init__(self, path: str = "todos.db") -> None:
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.setup()

    def setup(self) -> None:
        self.conn.executescript(SCHEMA)

        if self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            self.conn.execute(
                "INSERT INTO categories (name) VALUES (?)", (DEFAULT_CATEGORY,)
            )

        # Migrate legacy `todos` table (pre-category) if present
        tables = [
            r[0]
            for r in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        if "todos" in tables:
            self.conn.execute(
                "INSERT INTO tasks (id, title, completed, created_at, category_id) "
                "SELECT id, title, completed, created_at, 1 FROM todos"
            )
            self.conn.execute("DROP TABLE todos")

        self.conn.commit()

    @contextmanager
    def tx(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    @property
    def default_category_id(self) -> int:
        row = self.conn.execute(
            "SELECT id FROM categories WHERE name = ?", (DEFAULT_CATEGORY,)
        ).fetchone()
        return row[0]

    # --- categories ---
    def add_category(self, name: str) -> int:
        with self.tx() as con:
            cur = con.execute(
                "INSERT INTO categories (name) VALUES (?)", (name,)
            )
            return cur.lastrowid

    def get_categories(self) -> list[tuple[int, str]]:
        return self.conn.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()

    def delete_category(self, category_id: int, category_name: str) -> None:
        default_categories = ["Genel", "Tümü"]
        if category_id == self.default_category_id or category_name in default_categories:
            return
        with self.tx() as con:
            con.execute(
                "UPDATE tasks SET category_id = ? WHERE category_id = ?",
                (self.default_category_id, category_id),
            )
            con.execute("DELETE FROM categories WHERE id = ?", (category_id,))

    # --- tasks ---
    def add(self, title: str, category_id: int | None = None, time_range: str | None = None) -> int:
        if category_id is None:
            category_id = self.default_category_id
        with self.tx() as con:
            cur = con.execute(
                "INSERT INTO tasks (title, completed, category_id, time_range) VALUES (?, 0, ?, ?)",
                (title, category_id, time_range),
            )
            return cur.lastrowid

    def get_all(self, category_id: int | None = None) -> list[Todo]:
        if category_id is None:
            cur = self.conn.execute(
                "SELECT id, title, completed, created_at, category_id, time_range "
                "FROM tasks ORDER BY id DESC"
            )
        else:
            cur = self.conn.execute(
                "SELECT id, title, completed, created_at, category_id, time_range "
                "FROM tasks WHERE category_id = ? ORDER BY id DESC",
                (category_id,),
            )
        return [Todo.from_row(r) for r in cur.fetchall()]

    def update(self, task_id: int, *, title: str | None = None,
                completed: bool | None = None,
                category_id: int | None = None,
                time_range: str | None = None) -> None:
        sets: list[str] = []
        params: list = []
        if title is not None:
            sets.append("title = ?")
            params.append(title)
        if completed is not None:
            sets.append("completed = ?")
            params.append(int(completed))
        if category_id is not None:
            sets.append("category_id = ?")
            params.append(category_id)
        if time_range is not None:
            sets.append("time_range = ?")
            params.append(time_range)
        if not sets:
            return
        params.append(task_id)
        with self.tx() as con:
            con.execute(
                f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", params
            )

    def delete(self, task_id: int) -> None:
        with self.tx() as con:
            con.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def close(self) -> None:
        self.conn.close()
