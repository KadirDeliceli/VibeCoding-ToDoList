from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import customtkinter as ctk

from database import Database
from ui import TodoUI


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    db = Database("todos.db")
    app = TodoUI(db)
    app.mainloop()
    db.close()


if __name__ == "__main__":
    main()
