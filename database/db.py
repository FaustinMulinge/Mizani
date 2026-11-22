import sqlite3
from pathlib import Path


# ---------------------------------------------------------
# DATABASE CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "finance.db"


def get_connection():
    """Open a database connection and enable foreign-key checks."""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ---------------------------------------------------------
# TABLE CREATION
# ---------------------------------------------------------

def create_users_table():
    connection = get_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        print("Users table created successfully!")
    finally:
        connection.close()


def verify_users_table():
    connection = get_connection()
    try:
        result = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'users'
        """).fetchone()

        if result:
            print("Verified: users table exists!")
            return True

        print("Users table not found!")
        return False
    finally:
        connection.close()


def create_categories_table():
    connection = get_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL,
                category_type TEXT NOT NULL
                    CHECK(category_type IN ('income', 'expense')),
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category_name, category_type)
            )
        """)
        connection.commit()
        print("Categories table created successfully!")
    finally:
        connection.close()


def create_transactions_table():
    connection = get_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                transaction_type TEXT NOT NULL
                    CHECK(transaction_type IN ('income', 'expense')),
                description TEXT,
                transaction_date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (category_id)
                    REFERENCES categories(category_id)
            )
        """)
        connection.commit()
        print("Transactions table created successfully!")
    finally:
        connection.close()


def create_budgets_table():
    connection = get_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                year INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (category_id)
                    REFERENCES categories(category_id),

                UNIQUE(user_id, category_id, month, year)
            )
        """)
        connection.commit()
        print("Budgets table created successfully!")
    finally:
        connection.close()


def initialize_database():
    """Create all tables and insert the standard categories."""
    create_users_table()
    verify_users_table()
    create_categories_table()
    insert_default_categories()
    create_transactions_table()
    create_budgets_table()


# ---------------------------------------------------------
# INTERNAL VALIDATION HELPERS
# ---------------------------------------------------------

def _valid_transaction_category(connection, category_id, transaction_type):
    """Return True only when the category exists and has the right type."""
    category = connection.execute("""
        SELECT category_type
        FROM categories
        WHERE category_id = ?
    """, (category_id,)).fetchone()

    return category is not None and category["category_type"] == transaction_type


def _valid_expense_category(connection, category_id):
    """Return True only when the category exists and is an expense category."""
    category = connection.execute("""
        SELECT category_type
        FROM categories
        WHERE category_id = ?
    """, (category_id,)).fetchone()

    return category is not None and category["category_type"] == "expense"


# ---------------------------------------------------------
# USER FUNCTIONS
# ---------------------------------------------------------

def insert_user(full_name, email, password_hash):
    connection = get_connection()
    try:
        existing_user = connection.execute("""
            SELECT user_id
            FROM users
            WHERE email = ?
        """, (email.strip(),)).fetchone()

        if existing_user:
            print("User already exists!")
            return None

        cursor = connection.execute("""
            INSERT INTO users (full_name, email, password_hash)
            VALUES (?, ?, ?)
        """, (full_name.strip(), email.strip(), password_hash))

        connection.commit()
        print("User registered successfully!")
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        print("User could not be registered:", error)
        return None
    finally:
        connection.close()


def get_user_by_email(email):
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()
    finally:
        connection.close()


def update_user_name(email, new_name):
    connection = get_connection()
    try:
        cursor = connection.execute("""
            UPDATE users
            SET full_name = ?
            WHERE email = ?
        """, (new_name.strip(), email))

        connection.commit()

        if cursor.rowcount:
            print("User updated successfully!")
            return True

        print("User not found.")
        return False
    finally:
        connection.close()


def delete_user(email):
    connection = get_connection()
    try:
        cursor = connection.execute("""
            DELETE FROM users
            WHERE email = ?
        """, (email,))

        connection.commit()

        if cursor.rowcount:
            print("User deleted successfully!")
            return True

        print("User not found.")
        return False
    finally:
        connection.close()


# ---------------------------------------------------------
# CATEGORY FUNCTIONS
# ---------------------------------------------------------

def insert_default_categories():
    categories = [
        ("Salary", "income", "Monthly employment income"),
        ("Business", "income", "Income from business"),
        ("Freelance", "income", "Freelance earnings"),
        ("Investment", "income", "Returns from investments"),
        ("Food", "expense", "Food and groceries"),
        ("Transport", "expense", "Travel and commuting"),
        ("Rent", "expense", "House rent"),
        ("Education", "expense", "School fees and learning"),
        ("Healthcare", "expense", "Medical expenses"),
        ("Entertainment", "expense", "Leisure and entertainment"),
    ]

    connection = get_connection()
    try:
        connection.executemany("""
            INSERT OR IGNORE INTO categories
                (category_name, category_type, description)
            VALUES (?, ?, ?)
        """, categories)

        connection.commit()
        print("Default categories added successfully!")
    finally:
        connection.close()


def insert_category(category_name, category_type, description=None):
    if category_type not in ("income", "expense"):
        print("Category type must be 'income' or 'expense'.")
        return None

    connection = get_connection()
    try:
        cursor = connection.execute("""
            INSERT INTO categories
                (category_name, category_type, description)
            VALUES (?, ?, ?)
        """, (category_name.strip(), category_type, description))

        connection.commit()
        print("Category added successfully!")
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        print("Could not add category:", error)
        return None
    finally:
        connection.close()


def get_categories(category_type=None):
    connection = get_connection()
    try:
        if category_type is not None:
            if category_type not in ("income", "expense"):
                raise ValueError("category_type must be 'income' or 'expense'")

            return connection.execute("""
                SELECT *
                FROM categories
                WHERE category_type = ?
                ORDER BY category_name
            """, (category_type,)).fetchall()

        return connection.execute("""
            SELECT *
            FROM categories
            ORDER BY category_type, category_name
        """).fetchall()
    finally:
        connection.close()


def update_category(category_id, new_name, new_description=None):
    connection = get_connection()
    try:
        cursor = connection.execute("""
            UPDATE categories
            SET category_name = ?, description = ?
            WHERE category_id = ?
        """, (new_name.strip(), new_description, category_id))

        connection.commit()

        if cursor.rowcount:
            print("Category updated successfully!")
            return True

        print("Category not found.")
        return False

    except sqlite3.IntegrityError as error:
        print("Could not update category:", error)
        return False
    finally:
        connection.close()


def delete_category(category_id):
    connection = get_connection()
    try:
        cursor = connection.execute("""
            DELETE FROM categories
            WHERE category_id = ?
        """, (category_id,))

        connection.commit()

        if cursor.rowcount:
            print("Category deleted successfully!")
            return True

        print("Category not found.")
        return False

    except sqlite3.IntegrityError as error:
        print("Could not delete category. It may be in use:", error)
        return False
    finally:
        connection.close()


# ---------------------------------------------------------
# TRANSACTION FUNCTIONS
# ---------------------------------------------------------

def insert_transaction(user_id, category_id, amount, transaction_type,
                       description, transaction_date):
    if transaction_type not in ("income", "expense"):
        print("Transaction type must be 'income' or 'expense'.")
        return None

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        print("Amount must be a valid number.")
        return None

    if amount <= 0:
        print("Amount must be greater than zero.")
        return None

    connection = get_connection()
    try:
        if not _valid_transaction_category(
            connection, category_id, transaction_type
        ):
            print("The selected category does not match the transaction type.")
            return None

        cursor = connection.execute("""
            INSERT INTO transactions (
                user_id, category_id, amount, transaction_type,
                description, transaction_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id, category_id, amount, transaction_type,
            description, transaction_date
        ))

        connection.commit()
        print("Transaction recorded successfully!")
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        print("Transaction could not be recorded:", error)
        return None
    finally:
        connection.close()


def get_transactions(user_id, transaction_type=None, category_id=None,
                     start_date=None, end_date=None):
    connection = get_connection()
    try:
        query = """
            SELECT
                t.transaction_id,
                t.user_id,
                t.category_id,
                t.amount,
                t.transaction_type,
                t.description,
                t.transaction_date,
                t.created_at,
                c.category_name
            FROM transactions AS t
            JOIN categories AS c
                ON t.category_id = c.category_id
            WHERE t.user_id = ?
        """

        parameters = [user_id]

        if transaction_type is not None:
            query += " AND t.transaction_type = ?"
            parameters.append(transaction_type)

        if category_id is not None:
            query += " AND t.category_id = ?"
            parameters.append(category_id)

        if start_date is not None:
            query += " AND t.transaction_date >= ?"
            parameters.append(start_date)

        if end_date is not None:
            query += " AND t.transaction_date <= ?"
            parameters.append(end_date)

        query += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"

        return connection.execute(query, parameters).fetchall()
    finally:
        connection.close()


def update_transaction(transaction_id, user_id, category_id, amount,
                       transaction_type, description, transaction_date):
    if transaction_type not in ("income", "expense"):
        print("Transaction type must be 'income' or 'expense'.")
        return False

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        print("Amount must be a valid number.")
        return False

    if amount <= 0:
        print("Amount must be greater than zero.")
        return False

    connection = get_connection()
    try:
        if not _valid_transaction_category(
            connection, category_id, transaction_type
        ):
            print("The selected category does not match the transaction type.")
            return False

        cursor = connection.execute("""
            UPDATE transactions
            SET category_id = ?,
                amount = ?,
                transaction_type = ?,
                description = ?,
                transaction_date = ?
            WHERE transaction_id = ?
              AND user_id = ?
        """, (
            category_id, amount, transaction_type, description,
            transaction_date, transaction_id, user_id
        ))

        connection.commit()

        if cursor.rowcount:
            print("Transaction updated successfully!")
            return True

        print("Transaction not found for this user.")
        return False

    except sqlite3.IntegrityError as error:
        print("Transaction could not be updated:", error)
        return False
    finally:
        connection.close()


def delete_transaction(transaction_id, user_id):
    connection = get_connection()
    try:
        cursor = connection.execute("""
            DELETE FROM transactions
            WHERE transaction_id = ?
              AND user_id = ?
        """, (transaction_id, user_id))

        connection.commit()

        if cursor.rowcount:
            print("Transaction deleted successfully!")
            return True

        print("Transaction not found for this user.")
        return False
    finally:
        connection.close()


# ---------------------------------------------------------
# FINANCIAL SUMMARY AND REPORT FUNCTIONS
# ---------------------------------------------------------

def get_financial_summary(user_id):
    connection = get_connection()
    try:
        result = connection.execute("""
            SELECT
                COALESCE(SUM(
                    CASE WHEN transaction_type = 'income'
                    THEN amount ELSE 0 END
                ), 0) AS total_income,

                COALESCE(SUM(
                    CASE WHEN transaction_type = 'expense'
                    THEN amount ELSE 0 END
                ), 0) AS total_expenses
            FROM transactions
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        total_income = result["total_income"]
        total_expenses = result["total_expenses"]

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses,
        }
    finally:
        connection.close()


def get_monthly_summary(user_id, month, year):
    if not 1 <= int(month) <= 12:
        raise ValueError("month must be between 1 and 12")

    connection = get_connection()
    try:
        result = connection.execute("""
            SELECT
                COALESCE(SUM(
                    CASE WHEN transaction_type = 'income'
                    THEN amount ELSE 0 END
                ), 0) AS total_income,

                COALESCE(SUM(
                    CASE WHEN transaction_type = 'expense'
                    THEN amount ELSE 0 END
                ), 0) AS total_expenses
            FROM transactions
            WHERE user_id = ?
              AND strftime('%m', transaction_date) = ?
              AND strftime('%Y', transaction_date) = ?
        """, (user_id, f"{int(month):02d}", str(year))).fetchone()

        total_income = result["total_income"]
        total_expenses = result["total_expenses"]

        return {
            "month": int(month),
            "year": int(year),
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses,
        }
    finally:
        connection.close()


# ---------------------------------------------------------
# BUDGET FUNCTIONS
# ---------------------------------------------------------

def insert_budget(user_id, category_id, amount, month, year):
    try:
        amount = float(amount)
        month = int(month)
        year = int(year)
    except (TypeError, ValueError):
        print("Amount, month and year must be valid numbers.")
        return None

    if amount <= 0:
        print("Budget amount must be greater than zero.")
        return None

    if not 1 <= month <= 12:
        print("Month must be between 1 and 12.")
        return None

    connection = get_connection()
    try:
        if not _valid_expense_category(connection, category_id):
            print("A budget can only be assigned to an expense category.")
            return None

        cursor = connection.execute("""
            INSERT INTO budgets
                (user_id, category_id, amount, month, year)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, category_id, amount, month, year))

        connection.commit()
        print("Budget added successfully!")
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        print("Could not add budget:", error)
        return None
    finally:
        connection.close()


def get_budgets(user_id, month=None, year=None):
    connection = get_connection()
    try:
        query = """
            SELECT
                budgets.*,
                categories.category_name
            FROM budgets
            JOIN categories
                ON budgets.category_id = categories.category_id
            WHERE budgets.user_id = ?
        """

        parameters = [user_id]

        if month is not None:
            query += " AND budgets.month = ?"
            parameters.append(month)

        if year is not None:
            query += " AND budgets.year = ?"
            parameters.append(year)

        query += " ORDER BY budgets.year DESC, budgets.month DESC"

        return connection.execute(query, parameters).fetchall()
    finally:
        connection.close()


def get_budget_status(user_id, month, year):
    month = int(month)
    year = int(year)

    connection = get_connection()
    try:
        return connection.execute("""
            SELECT
                b.budget_id,
                b.category_id,
                b.amount AS budget_amount,
                c.category_name,

                COALESCE(SUM(t.amount), 0) AS amount_spent,

                b.amount - COALESCE(SUM(t.amount), 0)
                    AS remaining_budget,

                ROUND(
                    COALESCE(SUM(t.amount), 0) * 100.0 / b.amount,
                    2
                ) AS percentage_spent

            FROM budgets AS b
            JOIN categories AS c
                ON b.category_id = c.category_id

            LEFT JOIN transactions AS t
                ON t.category_id = b.category_id
                AND t.user_id = b.user_id
                AND t.transaction_type = 'expense'
                AND strftime('%m', t.transaction_date) = ?
                AND strftime('%Y', t.transaction_date) = ?

            WHERE b.user_id = ?
              AND b.month = ?
              AND b.year = ?

            GROUP BY b.budget_id
            ORDER BY c.category_name
        """, (
            f"{month:02d}", str(year), user_id, month, year
        )).fetchall()
    finally:
        connection.close()


def update_budget(budget_id, user_id, new_amount):
    try:
        new_amount = float(new_amount)
    except (TypeError, ValueError):
        print("Budget amount must be a valid number.")
        return False

    if new_amount <= 0:
        print("Budget amount must be greater than zero.")
        return False

    connection = get_connection()
    try:
        cursor = connection.execute("""
            UPDATE budgets
            SET amount = ?
            WHERE budget_id = ?
              AND user_id = ?
        """, (new_amount, budget_id, user_id))

        connection.commit()

        if cursor.rowcount:
            print("Budget updated successfully!")
            return True

        print("Budget not found.")
        return False
    finally:
        connection.close()


def delete_budget(budget_id, user_id):
    connection = get_connection()
    try:
        cursor = connection.execute("""
            DELETE FROM budgets
            WHERE budget_id = ?
              AND user_id = ?
        """, (budget_id, user_id))

        connection.commit()

        if cursor.rowcount:
            print("Budget deleted successfully!")
            return True

        print("Budget not found.")
        return False
    finally:
        connection.close()


# ---------------------------------------------------------
# RUN THIS FILE DIRECTLY TO INITIALIZE THE DATABASE
# ---------------------------------------------------------

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")
