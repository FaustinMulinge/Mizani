
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from database import db


class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for each test
        self.temp_directory = tempfile.TemporaryDirectory()

        self.test_database = (
            Path(self.temp_directory.name) / "test_finance.db"
        )

        # Redirect database operations to the temporary database
        self.database_patch = patch(
            "database.db.DATABASE_PATH",
            self.test_database
        )

        self.database_patch.start()

        # Create all required tables
        db.initialize_database()

    def tearDown(self):
        # Restore the original database path
        self.database_patch.stop()

        # Delete the temporary database
        self.temp_directory.cleanup()

    def test_default_categories_exist(self):
        categories = db.get_categories()

        self.assertEqual(len(categories), 10)

    def test_user_registration(self):
        db.insert_user(
            "Test User",
            "test@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("test@example.com")

        self.assertIsNotNone(user)
        self.assertEqual(user["full_name"], "Test User")

    def test_duplicate_user_registration(self):
        db.insert_user(
            "Test User",
            "test@example.com",
            "test_password_hash"
        )

        db.insert_user(
            "Another User",
            "test@example.com",
            "another_password_hash"
        )

        user = db.get_user_by_email("test@example.com")

        self.assertEqual(user["full_name"], "Test User")


    def test_transaction_registration(self):
        # Register a test user
        db.insert_user(
            "Test User",
            "transactions@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("transactions@example.com")
        user_id = user["user_id"]

        # Record an income transaction
        db.insert_transaction(
            user_id,
            1,
            50000,
            "income",
            "November salary",
            "2026-11-22"
        )

        # Retrieve the financial summary
        summary = db.get_financial_summary(user_id)

        self.assertEqual(summary["total_income"], 50000)

    def test_financial_summary(self):
        # Register a test user
        db.insert_user(
            "Summary User",
            "summary@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("summary@example.com")
        user_id = user["user_id"]

        # Record income
        db.insert_transaction(
            user_id, 1, 50000, "income",
            "November salary", "2026-11-22"
        )

        # Record expenses
        db.insert_transaction(
            user_id, 5, 2000, "expense",
            "Food shopping", "2026-11-22"
        )

        summary = db.get_financial_summary(user_id)

        self.assertEqual(summary["total_income"], 50000)
        self.assertEqual(summary["total_expenses"], 2000)
        self.assertEqual(summary["balance"], 48000)


    def test_monthly_summary(self):
        # Register a test user
        db.insert_user(
            "Monthly User",
            "monthly@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("monthly@example.com")
        user_id = user["user_id"]

        # Record November income
        db.insert_transaction(
            user_id, 1, 50000, "income",
            "November salary", "2026-11-10"
        )

        # Record November expenses
        db.insert_transaction(
            user_id, 5, 5000, "expense",
            "November food", "2026-11-15"
        )

        # Record December income
        db.insert_transaction(
            user_id, 1, 60000, "income",
            "December salary", "2026-12-10"
        )

        # Retrieve November summary only
        summary = db.get_monthly_summary(user_id, 11, 2026)

        self.assertEqual(summary["total_income"], 50000)
        self.assertEqual(summary["total_expenses"], 5000)
        self.assertEqual(summary["balance"], 45000)


    def test_budget_registration_and_retrieval(self):
        # Register a test user
        db.insert_user(
            "Budget User",
            "budget@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("budget@example.com")
        user_id = user["user_id"]

        # Create a monthly Food budget
        db.insert_budget(
            user_id,
            5,
            10000,
            11,
            2026
        )

        # Retrieve the November 2026 budget
        budgets = db.get_budgets(
            user_id,
            month=11,
            year=2026
        )

        self.assertEqual(len(budgets), 1)
        self.assertEqual(budgets[0]["amount"], 10000)
        self.assertEqual(budgets[0]["category_name"], "Food")

    def test_budget_status_calculation(self):
        # Register a test user
        db.insert_user(
            "Budget Status User",
            "budgetstatus@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("budgetstatus@example.com")
        user_id = user["user_id"]

        # Create a Food budget of KSh 10,000
        db.insert_budget(
            user_id,
            5,
            10000,
            11,
            2026
        )

        # Record Food expenses of KSh 2,500
        db.insert_transaction(
            user_id,
            5,
            2500,
            "expense",
            "Food shopping",
            "2026-11-15"
        )

        # Retrieve the budget status
        status = db.get_budget_status(user_id, 11, 2026)

        self.assertEqual(len(status), 1)
        self.assertEqual(status[0]["budget_amount"], 10000)
        self.assertEqual(status[0]["amount_spent"], 2500)
        self.assertEqual(status[0]["remaining_budget"], 7500)
        self.assertEqual(status[0]["percentage_spent"], 25)


    def test_budget_update(self):
        # Register a test user
        db.insert_user(
            "Update User",
            "update@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("update@example.com")
        user_id = user["user_id"]

        # Create a monthly Food budget
        db.insert_budget(
            user_id,
            5,
            10000,
            11,
            2026
        )

        # Retrieve the budget
        budgets = db.get_budgets(
            user_id,
            month=11,
            year=2026
        )

        budget_id = budgets[0]["budget_id"]

        # Update the budget to KSh 15000
        db.update_budget(
            budget_id,
            user_id,
            15000
        )

        # Retrieve the updated budget
        updated_budgets = db.get_budgets(
            user_id,
            month=11,
            year=2026
        )

        self.assertEqual(
            updated_budgets[0]["amount"],
            15000
        )


    def test_budget_deletion(self):
        # Register a test user
        db.insert_user(
            "Delete User",
            "delete@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("delete@example.com")
        user_id = user["user_id"]

        # Create a monthly Food budget
        db.insert_budget(
            user_id,
            5,
            10000,
            11,
            2026
        )

        # Retrieve the budget
        budgets = db.get_budgets(
            user_id,
            month=11,
            year=2026
        )

        budget_id = budgets[0]["budget_id"]

        # Delete the budget
        db.delete_budget(budget_id, user_id)

        # Confirm that the budget no longer exists
        remaining_budgets = db.get_budgets(
            user_id,
            month=11,
            year=2026
        )

        self.assertEqual(len(remaining_budgets), 0)


    def test_category_insertion(self):
        # Add a new expense category
        db.insert_category(
            "Shopping",
            "expense",
            "Personal shopping expenses"
        )

        # Retrieve all expense categories
        categories = db.get_categories("expense")

        # Confirm that Shopping was added
        category_names = [
            category["category_name"]
            for category in categories
        ]

        self.assertIn("Shopping", category_names)


    def test_category_update(self):
        # Retrieve the existing Food category
        categories = db.get_categories("expense")

        food_category = next(
            category for category in categories
            if category["category_name"] == "Food"
        )

        category_id = food_category["category_id"]

        # Rename Food to Groceries
        db.update_category(
            category_id,
            "Groceries",
            "Household food and shopping expenses"
        )

        # Retrieve the updated category
        updated_categories = db.get_categories("expense")

        updated_category = next(
            category for category in updated_categories
            if category["category_id"] == category_id
        )

        # Verify the changes
        self.assertEqual(
            updated_category["category_name"],
            "Groceries"
        )

        self.assertEqual(
            updated_category["description"],
            "Household food and shopping expenses"
        )


    def test_category_deletion(self):
        # Add a category specifically for deletion
        db.insert_category(
            "Temporary",
            "expense",
            "Temporary category"
        )

        # Find the category
        categories = db.get_categories("expense")

        temporary_category = next(
            category for category in categories
            if category["category_name"] == "Temporary"
        )

        category_id = temporary_category["category_id"]

        # Delete the category
        db.delete_category(category_id)

        # Retrieve categories again
        updated_categories = db.get_categories("expense")

        category_names = [
            category["category_name"]
            for category in updated_categories
        ]

        self.assertNotIn("Temporary", category_names)

    def test_category_deletion_with_transactions(self):
        # Register a user
        db.insert_user(
            "Category User",
            "category@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("category@example.com")
        user_id = user["user_id"]

        # Add a category
        db.insert_category(
            "Test Category",
            "expense",
            "Category used for testing"
        )

        categories = db.get_categories("expense")

        test_category = next(
            category for category in categories
            if category["category_name"] == "Test Category"
        )

        category_id = test_category["category_id"]

        # Record a transaction using this category
        db.insert_transaction(
            user_id,
            category_id,
            1000,
            "expense",
            "Test expense",
            "2026-11-22"
        )

        # Attempt to delete the category
        db.delete_category(category_id)

        # Confirm the category still exists
        updated_categories = db.get_categories("expense")

        category_names = [
            category["category_name"]
            for category in updated_categories
        ]

        self.assertIn("Test Category", category_names)


    def test_transaction_update(self):
        # Register a user
        db.insert_user(
            "Transaction User",
            "transaction_update@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email(
            "transaction_update@example.com"
        )
        user_id = user["user_id"]

        # Record an initial expense
        db.insert_transaction(
            user_id,
            5,
            2000,
            "expense",
            "Food shopping",
            "2026-11-22"
        )

        # Retrieve the transaction
        transactions = db.get_transactions(user_id)

        transaction_id = transactions[0]["transaction_id"]

        # Update the transaction
        db.update_transaction(
            transaction_id,
            user_id,
            6,
            3000,
            "expense",
            "Transport expenses",
            "2026-11-22"
        )

        # Retrieve the updated transaction
        updated_transactions = db.get_transactions(user_id)

        updated_transaction = updated_transactions[0]

        self.assertEqual(updated_transaction["amount"], 3000)

        self.assertEqual(
            updated_transaction["category_name"],
            "Transport"
        )

        self.assertEqual(
            updated_transaction["description"],
            "Transport expenses"
        )


    def test_transaction_deletion(self):
        # Register a user
        db.insert_user(
            "Delete Transaction User",
            "delete_transaction@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email(
            "delete_transaction@example.com"
        )
        user_id = user["user_id"]

        # Record an expense
        db.insert_transaction(
            user_id,
            5,
            2000,
            "expense",
            "Food shopping",
            "2026-11-22"
        )

        # Retrieve the transaction
        transactions = db.get_transactions(user_id)

        transaction_id = transactions[0]["transaction_id"]

        # Delete the transaction
        db.delete_transaction(transaction_id, user_id)

        # Retrieve transactions again
        remaining_transactions = db.get_transactions(user_id)

        # Confirm deletion
        self.assertEqual(len(remaining_transactions), 0)


    def test_transaction_filter_by_type(self):
        # Register a user
        db.insert_user(
            "Filter User",
            "filter@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("filter@example.com")
        user_id = user["user_id"]

        # Record income
        db.insert_transaction(
            user_id, 1, 50000, "income",
            "Salary", "2026-11-10"
        )

        # Record expenses
        db.insert_transaction(
            user_id, 5, 2000, "expense",
            "Food", "2026-11-11"
        )

        db.insert_transaction(
            user_id, 6, 1000, "expense",
            "Transport", "2026-11-12"
        )

        # Retrieve expenses only
        expenses = db.get_transactions(
            user_id,
            transaction_type="expense"
        )

        # Verify results
        self.assertEqual(len(expenses), 2)

        for transaction in expenses:
            self.assertEqual(
                transaction["transaction_type"],
                "expense"
            )


    def test_transaction_filter_by_category(self):
        # Register a user
        db.insert_user(
            "Category Filter User",
            "category_filter@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email(
            "category_filter@example.com"
        )
        user_id = user["user_id"]

        # Record expenses in different categories
        db.insert_transaction(
            user_id, 5, 2000, "expense",
            "Food shopping", "2026-11-10"
        )

        db.insert_transaction(
            user_id, 6, 1000, "expense",
            "Transport fare", "2026-11-11"
        )

        # Retrieve Food transactions only
        food_transactions = db.get_transactions(
            user_id,
            category_id=5
        )

        # Verify results
        self.assertEqual(len(food_transactions), 1)

        self.assertEqual(
            food_transactions[0]["category_name"],
            "Food"
        )


    def test_transaction_filter_by_date(self):
        # Register a user
        db.insert_user(
            "Date Filter User",
            "date_filter@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email(
            "date_filter@example.com"
        )
        user_id = user["user_id"]

        # Record transactions on different dates
        db.insert_transaction(
            user_id, 5, 1000, "expense",
            "First expense", "2026-11-05"
        )

        db.insert_transaction(
            user_id, 5, 2000, "expense",
            "Second expense", "2026-11-15"
        )

        db.insert_transaction(
            user_id, 5, 3000, "expense",
            "Third expense", "2026-11-25"
        )

        # Retrieve transactions between November 10 and 20
        filtered_transactions = db.get_transactions(
            user_id,
            start_date="2026-11-10",
            end_date="2026-11-20"
        )

        # Verify that only the second expense is returned
        self.assertEqual(len(filtered_transactions), 1)

        self.assertEqual(
            filtered_transactions[0]["description"],
            "Second expense"
        )


    def test_user_deletion_cascade(self):
        # Register a user
        db.insert_user(
            "Cascade User",
            "cascade@example.com",
            "test_password_hash"
        )

        user = db.get_user_by_email("cascade@example.com")
        user_id = user["user_id"]

        # Record a transaction
        db.insert_transaction(
            user_id,
            5,
            2000,
            "expense",
            "Food shopping",
            "2026-11-22"
        )

        # Create a budget
        db.insert_budget(
            user_id,
            5,
            10000,
            11,
            2026
        )

        # Delete the user
        db.delete_user("cascade@example.com")

        # Confirm the user no longer exists
        deleted_user = db.get_user_by_email(
            "cascade@example.com"
        )

        self.assertIsNone(deleted_user)

        # Confirm the user's transactions were deleted
        transactions = db.get_transactions(user_id)

        self.assertEqual(len(transactions), 0)

        # Confirm the user's budgets were deleted
        budgets = db.get_budgets(user_id)

        self.assertEqual(len(budgets), 0)


if __name__ == "__main__":
    unittest.main()