import datetime
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# Try loading matplotlib; fall back gracefully if security policy blocks DLLs
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

DB_FILE = "finance_manager.db"


class FinanceManagerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Management System")
        self.root.geometry("1000x650")

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.init_db()
        self._build_ui()
        self.refresh_all()

    def init_db(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trans_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT
                )
            """
            )
            conn.commit()

    def add_transaction_db(self, trans_type, category, amount, date_str, description):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions (trans_type, category, amount, date, description)
                VALUES (?, ?, ?, ?, ?)
            """,
                (trans_type, category, amount, date_str, description),
            )
            conn.commit()

    def delete_transaction_db(self, trans_id):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            conn.commit()

    def fetch_all_transactions(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, trans_type, category, amount, date, description FROM transactions ORDER BY date DESC, id DESC"
            )
            return cursor.fetchall()

    def fetch_summary(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Income'")
            income = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Expense'")
            expense = cursor.fetchone()[0] or 0.0

            return income, expense, (income - expense)

    def fetch_expense_category_breakdown(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT category, SUM(amount) 
                FROM transactions 
                WHERE trans_type = 'Expense' 
                GROUP BY category
            """
            )
            return cursor.fetchall()

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_dashboard = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_dashboard, text=" Dashboard & Entry ")

        self.tab_analytics = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_analytics, text=" Expense Analytics ")

        # Top KPI Summary Cards
        kpi_frame = ttk.Frame(self.tab_dashboard)
        kpi_frame.pack(fill="x", pady=(0, 10))

        self.lbl_income = ttk.Label(
            kpi_frame, text="Income: $0.00", font=("Helvetica", 12, "bold"), foreground="green"
        )
        self.lbl_income.pack(side="left", expand=True)

        self.lbl_expense = ttk.Label(
            kpi_frame, text="Expense: $0.00", font=("Helvetica", 12, "bold"), foreground="red"
        )
        self.lbl_expense.pack(side="left", expand=True)

        self.lbl_savings = ttk.Label(
            kpi_frame, text="Net Savings: $0.00", font=("Helvetica", 12, "bold"), foreground="blue"
        )
        self.lbl_savings.pack(side="left", expand=True)

        content_frame = ttk.Frame(self.tab_dashboard)
        content_frame.pack(fill="both", expand=True)

        form_frame = ttk.LabelFrame(content_frame, text=" Add New Transaction ", padding=15)
        form_frame.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(form_frame, text="Type:").pack(anchor="w", pady=(0, 2))
        self.combo_type = ttk.Combobox(
            form_frame, values=["Income", "Expense"], state="readonly"
        )
        self.combo_type.set("Expense")
        self.combo_type.pack(fill="x", pady=(0, 10))

        ttk.Label(form_frame, text="Category:").pack(anchor="w", pady=(0, 2))
        self.combo_category = ttk.Combobox(
            form_frame,
            values=[
                "Salary",
                "Freelance",
                "Investments",
                "Food & Dining",
                "Rent & Utilities",
                "Shopping",
                "Entertainment",
                "Transport",
                "Healthcare",
                "Other",
            ],
        )
        self.combo_category.set("Food & Dining")
        self.combo_category.pack(fill="x", pady=(0, 10))

        ttk.Label(form_frame, text="Amount ($):").pack(anchor="w", pady=(0, 2))
        self.entry_amount = ttk.Entry(form_frame)
        self.entry_amount.pack(fill="x", pady=(0, 10))

        ttk.Label(form_frame, text="Date (YYYY-MM-DD):").pack(anchor="w", pady=(0, 2))
        self.entry_date = ttk.Entry(form_frame)
        self.entry_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_date.pack(fill="x", pady=(0, 10))

        ttk.Label(form_frame, text="Description:").pack(anchor="w", pady=(0, 2))
        self.entry_desc = ttk.Entry(form_frame)
        self.entry_desc.pack(fill="x", pady=(0, 15))

        btn_add = ttk.Button(form_frame, text="Add Transaction", command=self.add_transaction)
        btn_add.pack(fill="x", pady=5)

        btn_delete = ttk.Button(
            form_frame, text="Delete Selected", command=self.delete_transaction
        )
        btn_delete.pack(fill="x", pady=5)

        list_frame = ttk.LabelFrame(content_frame, text=" Recent Transactions ", padding=10)
        list_frame.pack(side="right", fill="both", expand=True)

        columns = ("id", "type", "category", "amount", "date", "desc")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("category", text="Category")
        self.tree.heading("amount", text="Amount ($)")
        self.tree.heading("date", text="Date")
        self.tree.heading("desc", text="Description")

        self.tree.column("id", width=30, anchor="center")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("category", width=110)
        self.tree.column("amount", width=80, anchor="e")
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("desc", width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.chart_container = ttk.Frame(self.tab_analytics, padding=20)
        self.chart_container.pack(fill="both", expand=True)

    def refresh_all(self):
        income, expense, savings = self.fetch_summary()
        self.lbl_income.config(text=f"Income: ${income:,.2f}")
        self.lbl_expense.config(text=f"Expense: ${expense:,.2f}")
        self.lbl_savings.config(text=f"Net Savings: ${savings:,.2f}")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.fetch_all_transactions():
            formatted_row = (row[0], row[1], row[2], f"${row[3]:,.2f}", row[4], row[5])
            self.tree.insert("", "end", values=formatted_row)

        self.render_chart()

    def add_transaction(self):
        trans_type = self.combo_type.get()
        category = self.combo_category.get().strip()
        amount_str = self.entry_amount.get().strip()
        date_str = self.entry_date.get().strip()
        description = self.entry_desc.get().strip()

        if not category or not amount_str or not date_str:
            messagebox.showwarning("Validation Error", "Category, Amount, and Date are required.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation Error", "Please enter a valid positive number.")
            return

        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Validation Error", "Date must be in YYYY-MM-DD format.")
            return

        self.add_transaction_db(trans_type, category, amount, date_str, description)
        self.entry_amount.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)

        self.refresh_all()
        messagebox.showinfo("Success", "Transaction recorded successfully!")

    def delete_transaction(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a transaction to delete.")
            return

        values = self.tree.item(selected_item[0], "values")
        trans_id = values[0]

        if messagebox.askyesno("Confirm Delete", f"Delete transaction ID #{trans_id}?"):
            self.delete_transaction_db(trans_id)
            self.refresh_all()
            messagebox.showinfo("Success", "Transaction removed.")

    def render_chart(self):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        breakdown = self.fetch_expense_category_breakdown()

        if MATPLOTLIB_AVAILABLE:
            fig, ax = plt.subplots(figsize=(6, 5), dpi=100)

            if not breakdown:
                ax.text(
                    0.5,
                    0.5,
                    "No Expense Data Available",
                    ha="center",
                    va="center",
                    fontsize=12,
                )
                ax.axis("off")
            else:
                categories = [row[0] for row in breakdown]
                amounts = [row[1] for row in breakdown]
                ax.pie(amounts, labels=categories, autopct="%1.1f%%", startangle=140)
                ax.set_title("Expense Distribution by Category", fontsize=14, pad=15)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            # Fallback UI view when Matplotlib is blocked by security policies
            lbl_title = ttk.Label(
                self.chart_container,
                text="Expense Summary (Matplotlib Blocked by Policy)",
                font=("Helvetica", 14, "bold"),
            )
            lbl_title.pack(anchor="w", pady=(0, 15))

            if not breakdown:
                ttk.Label(self.chart_container, text="No Expense Data Available").pack(
                    anchor="w"
                )
            else:
                total_exp = sum(row[1] for row in breakdown)
                for cat, val in breakdown:
                    pct = (val / total_exp) * 100
                    row_lbl = ttk.Label(
                        self.chart_container,
                        text=f"• {cat}: ${val:,.2f} ({pct:.1f}%)",
                        font=("Helvetica", 11),
                    )
                    row_lbl.pack(anchor="w", pady=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceManagerApp(root)
    root.mainloop()