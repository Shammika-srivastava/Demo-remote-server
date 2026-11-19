from datetime import date
from typing import Optional
from fastmcp import FastMCP
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

CATEGORIES = [
    "Food",
    "Transport",
    "Utilities",
    "Entertainment",
]

mcp = FastMCP("ExpenseTracker")


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)


init_db()


@mcp.tool()
def list_categories() -> list[str]:
    """Return valid expense categories. Choose the closest matching category."""
    return CATEGORIES


@mcp.tool()
def add_expense(
    date: date,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = "",
) -> dict:
    """Add an expense using an exact category from list_categories."""
    if category not in CATEGORIES:
        raise ValueError(
            f"Invalid category. Choose one of: {', '.join(CATEGORIES)}"
        )

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            INSERT INTO expenses (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date.isoformat(), amount, category, subcategory, note),
        )
        return {"status": "ok", "id": cur.lastrowid}


@mcp.tool()
def delete_expense(expense_id: int) -> dict:
    """Delete an expense by its ID."""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,),
        )
        if cur.rowcount == 0:
            return {"status": "not_found", "id": expense_id}
        return {"status": "ok", "deleted_id": expense_id}


@mcp.tool()
def list_expenses(start_date: date, end_date: date) -> list[dict]:
    """List expenses between the inclusive start and end dates."""
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date.")

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        columns = [description[0] for description in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


@mcp.tool()
def summarize(
    start_date: date,
    end_date: date,
    category: Optional[str] = None,
) -> list[dict]:
    """Summarize expenses by category within an inclusive date range."""
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date.")

    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        if category is not None:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        columns = [description[0] for description in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


@mcp.resource("expense://categories", mime_type="application/json")
def categories_resource() -> str:
    """Return the valid categories as JSON."""
    return json.dumps(CATEGORIES)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)