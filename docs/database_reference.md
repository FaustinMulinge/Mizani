# Mizani Database Function Reference

**File:** `database/db.py`  
**Database:** SQLite  
**Database lead:** Database Management Team

## 1. Database Initialization

| Function | Description |
|---|---|
| `get_connection()` | Opens a database connection and enables foreign keys. |
| `create_users_table()` | Creates the users table. |
| `verify_users_table()` | Verifies that the users table exists and has the required structure. |
| `create_categories_table()` | Creates the categories table. |
| `create_transactions_table()` | Creates the transactions table. |
| `create_budgets_table()` | Creates the budgets table. |
| `initialize_database()` | Initializes all tables and inserts default categories. |

Initialize the database before using database functions:

```python
from database.db import initialize_database

initialize_database()
```

## 2. User Management

| Function | Parameters | Description |
|---|---|---|
| `insert_user()` | `full_name, email, password_hash` | Registers a new user. |
| `get_user_by_email()` | `email` | Retrieves a user using their email address. |
| `update_user_name()` | `email, new_name` | Updates a user's name. |
| `delete_user()` | `email` | Deletes a user and their associated transactions and budgets. |

Example:

```python
from database.db import insert_user, get_user_by_email

insert_user("John Doe", "john@example.com", "hashed_password")

user = get_user_by_email("john@example.com")
```

**Note:** Passwords must be hashed before being stored. The database does not handle password hashing.

## 3. Category Management

| Function | Parameters | Description |
|---|---|---|
| `insert_default_categories()` | None | Inserts predefined income and expense categories. |
| `insert_category()` | `category_name, category_type, description=None` | Creates a category. |
| `get_categories()` | `category_type=None` | Retrieves all categories or filters by income/expense. |
| `update_category()` | `category_id, new_name, new_description=None` | Updates a category. |
| `delete_category()` | `category_id` | Deletes a category if it is not being used by existing records. |

Valid category types:

- `income`
- `expense`

Example:

```python
from database.db import get_categories

income_categories = get_categories("income")
expense_categories = get_categories("expense")
all_categories = get_categories()
```

## 4. Transaction Management

| Function | Parameters | Description |
|---|---|---|
| `insert_transaction()` | `user_id, category_id, amount, transaction_type, description, transaction_date` | Records a transaction. |
| `get_transactions()` | `user_id, transaction_type=None, category_id=None, start_date=None, end_date=None` | Retrieves transactions with optional filters. |
| `update_transaction()` | `transaction_id, user_id, category_id, amount, transaction_type, description, transaction_date` | Updates an existing transaction belonging to the user. |
| `delete_transaction()` | `transaction_id, user_id` | Deletes a transaction belonging to the user. |

Valid transaction types:

- `income`
- `expense`

Example:

```python
from database.db import insert_transaction, get_transactions

insert_transaction(
    user_id=1,
    category_id=5,
    amount=500,
    transaction_type="expense",
    description="Lunch",
    transaction_date="2026-11-23"
)

transactions = get_transactions(1)
```

## 5. Financial Reports

| Function | Parameters | Description |
|---|---|---|
| `get_financial_summary()` | `user_id` | Calculates total income, expenses and balance. |
| `get_monthly_summary()` | `user_id, month, year` | Retrieves income and expense summaries for a specific month. |

Example:

```python
from database.db import get_financial_summary, get_monthly_summary

summary = get_financial_summary(1)

monthly = get_monthly_summary(1, 11, 2026)
```

## 6. Budget Management

| Function | Parameters | Description |
|---|---|---|
| `insert_budget()` | `user_id, category_id, amount, month, year` | Creates a budget for an expense category. |
| `get_budgets()` | `user_id, month=None, year=None` | Retrieves budgets, optionally filtered by month and year. |
| `get_budget_status()` | `user_id, month, year` | Calculates budget spending and remaining amounts. |
| `update_budget()` | `budget_id, user_id, new_amount` | Updates a budget amount. |
| `delete_budget()` | `budget_id, user_id` | Deletes a user's budget. |

Example:

```python
from database.db import insert_budget, get_budget_status

insert_budget(
    user_id=1,
    category_id=5,
    amount=5000,
    month=11,
    year=2026
)

status = get_budget_status(1, 11, 2026)
```

## 7. Database Rules

- All monetary amounts must be greater than zero.
- Transaction types must be either `income` or `expense`.
- Transactions must use a category matching their transaction type.
- Budgets can only be assigned to expense categories.
- Budget months must be between 1 and 12.
- Users cannot modify or delete another user's transactions or budgets through the user-scoped functions.
- Deleting a user automatically deletes their transactions and budgets.
- Categories cannot be deleted if they are referenced by transactions or budgets.
- Email addresses are unique and case-insensitive.
- Database connections enable foreign-key enforcement.

## 8. Integration Instructions

Teammates should import database functions into their modules instead of creating separate database connections or duplicating SQL queries.

Example:

```python
from database.db import insert_transaction, get_transactions
```

The database module is the central source of database operations for Mizani.
