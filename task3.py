import datetime
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# Try loading Matplotlib; handle AppLocker DLL restrictions gracefully
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

DB_FILE = "expense_tracker.db"


class ExpenseTrackerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker & Analytics System")
        self.root.geometry("1050x680")
        self.root.minsize(900, 600)

        # Apply GUI styling
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.init_db()
        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------
    # Data Storage (SQLite)
    # ------------------------------------------------------------------
    def init_db(self):
        """Initialize database schema for expenses."""
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    notes TEXT
                )
            """
            )
            conn.commit()

    def add_expense_db(self, amount, category, exp_date, notes):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO expenses (amount, category, expense_date, notes)
                VALUES (?, ?, ?, ?)
            """,
                (amount, category, exp_date, notes),
            )
            conn.commit()

    def delete_expense_db(self, exp_id):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (exp_id,))
            conn.commit()

    def fetch_all_expenses(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, amount, category, expense_date, notes FROM expenses ORDER BY expense_date DESC, id DESC"
            )
            return cursor.fetchall()

    def fetch_category_summary(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT category, SUM(amount) 
                FROM expenses 
                GROUP BY category 
                ORDER BY SUM(amount) DESC
            """
            )
            return cursor.fetchall()

    def fetch_monthly_summary(self):
        """Group expenses by YYYY-MM for trend analysis."""
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT strftime('%Y-%m', expense_date) as month, SUM(amount)
                FROM expenses
                GROUP BY month
                ORDER BY month ASC
            """
            )
            return cursor.fetchall()

    def fetch_total_spent(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount) FROM expenses")
            return cursor.fetchone()[0] or 0.0

    # ------------------------------------------------------------------
    # User Interface Setup
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Management & Input
        self.tab_manager = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_manager, text=" Expenses & Entries ")

        # Tab 2: Visualizations & Reports
        self.tab_reports = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_reports, text=" Visual Reports ")

        # --- TAB 1: FORM & LEDGER ---
        top_kpi = ttk.Frame(self.tab_manager)
        top_kpi.pack(fill="x", pady=(0, 10))

        self.lbl_total_spent = ttk.Label(
            top_kpi,
            text="Total Spending: $0.00",
            font=("Helvetica", 13, "bold"),
            foreground="#D9534F",
        )
        self.lbl_total_spent.pack(side="left")

        content_split = ttk.Frame(self.tab_manager)
        content_split.pack(fill="both", expand=True)

        # Left Column: Input Form
        form = ttk.LabelFrame(content_split, text=" Log New Expense ", padding=15)
        form.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(form, text="Amount ($):").pack(anchor="w", pady=(0, 2))
        self.entry_amount = ttk.Entry(form)
        self.entry_amount.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Category:").pack(anchor="w", pady=(0, 2))
        self.combo_category = ttk.Combobox(
            form,
            values=[
                "Groceries & Food",
                "Rent & Utilities",
                "Transportation",
                "Shopping & Retail",
                "Entertainment",
                "Healthcare",
                "Education",
                "Bills & Subscriptions",
                "Other",
            ],
        )
        self.combo_category.set("Groceries & Food")
        self.combo_category.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Date (YYYY-MM-DD):").pack(anchor="w", pady=(0, 2))
        self.entry_date = ttk.Entry(form)
        self.entry_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_date.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Notes:").pack(anchor="w", pady=(0, 2))
        self.entry_notes = ttk.Entry(form)
        self.entry_notes.pack(fill="x", pady=(0, 15))

        btn_submit = ttk.Button(form, text="Add Expense", command=self.add_expense)
        btn_submit.pack(fill="x", pady=4)

        btn_delete = ttk.Button(
            form, text="Delete Selected", command=self.delete_expense
        )
        btn_delete.pack(fill="x", pady=4)

        # Right Column: Data Table
        ledger = ttk.LabelFrame(content_split, text=" Expense Records ", padding=10)
        ledger.pack(side="right", fill="both", expand=True)

        cols = ("id", "amount", "category", "date", "notes")
        self.tree = ttk.Treeview(
            ledger, columns=cols, show="headings", selectmode="browse"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("amount", text="Amount ($)")
        self.tree.heading("category", text="Category")
        self.tree.heading("date", text="Date")
        self.tree.heading("notes", text="Notes")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("amount", width=90, anchor="e")
        self.tree.column("category", width=140)
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("notes", width=180)

        scroller = ttk.Scrollbar(ledger, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroller.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroller.pack(side="right", fill="y")

        # --- TAB 2: VISUAL REPORTS ---
        self.report_container = ttk.Frame(self.tab_reports, padding=10)
        self.report_container.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Actions & Handlers
    # ------------------------------------------------------------------
    def refresh_all(self):
        """Update KPI headers, data lists, and recalculate charts."""
        total = self.fetch_total_spent()
        self.lbl_total_spent.config(text=f"Total Spending: ${total:,.2f}")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.fetch_all_expenses():
            formatted_row = (row[0], f"${row[1]:,.2f}", row[2], row[3], row[4])
            self.tree.insert("", "end", values=formatted_row)

        self.render_visualizations()

    def add_expense(self):
        amount_str = self.entry_amount.get().strip()
        category = self.combo_category.get().strip()
        date_str = self.entry_date.get().strip()
        notes = self.entry_notes.get().strip()

        if not amount_str or not category or not date_str:
            messagebox.showwarning(
                "Input Error", "Amount, Category, and Date are required."
            )
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Input Error", "Please enter a valid positive number for amount."
            )
            return

        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Input Error", "Date must be formatted as YYYY-MM-DD."
            )
            return

        self.add_expense_db(amount, category, date_str, notes)

        # Reset inputs
        self.entry_amount.delete(0, tk.END)
        self.entry_notes.delete(0, tk.END)

        self.refresh_all()
        messagebox.showinfo("Success", "Expense entry recorded.")

    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Selection Error", "Please select an entry to delete."
            )
            return

        exp_id = self.tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", f"Delete record ID #{exp_id}?"):
            self.delete_expense_db(exp_id)
            self.refresh_all()

    def render_visualizations(self):
        """Render side-by-side Matplotlib charts or fallback summary widgets."""
        for widget in self.report_container.winfo_children():
            widget.destroy()

        cat_data = self.fetch_category_summary()
        month_data = self.fetch_monthly_summary()

        if MATPLOTLIB_AVAILABLE:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.5), dpi=100)

            # Chart 1: Category Distribution (Pie Chart)
            if cat_data:
                labels = [c[0] for c in cat_data]
                values = [c[1] for c in cat_data]
                ax1.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
                ax1.set_title("Spending by Category", fontsize=11, fontweight="bold")
            else:
                ax1.text(0.5, 0.5, "No Category Data", ha="center", va="center")
                ax1.axis("off")

            # Chart 2: Monthly Trends (Bar Chart)
            if month_data:
                months = [m[0] for m in month_data]
                totals = [m[1] for m in month_data]
                ax2.bar(months, totals, color="#4E79A7")
                ax2.set_title("Monthly Spending Trend", fontsize=11, fontweight="bold")
                ax2.tick_params(axis="x", rotation=30)
                ax2.set_ylabel("Total ($)")
            else:
                ax2.text(0.5, 0.5, "No Monthly Data", ha="center", va="center")
                ax2.axis("off")

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.report_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        else:
            # Fallback UI if AppLocker blocks Matplotlib binary DLL files
            fallback_frame = ttk.LabelFrame(
                self.report_container, text=" Expense Category Breakdown ", padding=15
            )
            fallback_frame.pack(fill="both", expand=True)

            if not cat_data:
                ttk.Label(fallback_frame, text="No expense records registered yet.").pack(
                    anchor="w"
                )
            else:
                total_spent = self.fetch_total_spent()
                for cat, val in cat_data:
                    pct = (val / total_spent) * 100 if total_spent > 0 else 0
                    row_box = ttk.Frame(fallback_frame)
                    row_box.pack(fill="x", pady=4)

                    ttk.Label(
                        row_box,
                        text=f"{cat}:",
                        font=("Helvetica", 10, "bold"),
                        width=25,
                    ).pack(side="left")

                    ttk.Label(
                        row_box, text=f"${val:,.2f} ({pct:.1f}%)", font=("Helvetica", 10)
                    ).pack(side="left", padx=10)

                    pbar = ttk.Progressbar(
                        row_box, orient="horizontal", mode="determinate", value=pct
                    )
                    pbar.pack(side="left", fill="x", expand=True, padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()