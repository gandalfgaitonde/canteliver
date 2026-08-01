import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

DATA_FILE = "contacts.json"


class ContactBookApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Contact Book")
        self.root.geometry("650x500")
        self.root.resizable(False, False)

        # Apply a clean theme style
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.contacts = self.load_contacts()

        self._build_ui()
        self.refresh_contact_list()

    # ------------------------------------------------------------------
    # File I/O Methods
    # ------------------------------------------------------------------
    def load_contacts(self):
        """Load contacts from a JSON file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as file:
                    return json.load(file)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_contacts(self):
        """Save current contacts list to a JSON file."""
        try:
            with open(DATA_FILE, "w") as file:
                json.dump(self.contacts, file, indent=4)
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")

    # ------------------------------------------------------------------
    # UI Layout & Components
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Left Frame: Form for Input / Operations
        form_frame = ttk.LabelFrame(self.root, text=" Contact Details ", padding=15)
        form_frame.place(x=15, y=15, width=280, height=470)

        ttk.Label(form_frame, text="Name:").pack(anchor="w", pady=(0, 2))
        self.entry_name = ttk.Entry(form_frame)
        self.entry_name.pack(fill="x", pady=(0, 10))

        ttk.Label(form_frame, text="Phone:").pack(anchor="w", pady=(0, 2))
        self.entry_phone = ttk.Entry(form_frame)
        self.entry_phone.pack(fill="x", pady=(0, 10))

        ttk.Label(form_frame, text="Email:").pack(anchor="w", pady=(0, 2))
        self.entry_email = ttk.Entry(form_frame)
        self.entry_email.pack(fill="x", pady=(0, 10))

        ttk.Label(form_frame, text="Address:").pack(anchor="w", pady=(0, 2))
        self.entry_address = ttk.Entry(form_frame)
        self.entry_address.pack(fill="x", pady=(0, 15))

        # Buttons
        btn_add = ttk.Button(form_frame, text="Add Contact", command=self.add_contact)
        btn_add.pack(fill="x", pady=3)

        btn_update = ttk.Button(
            form_frame, text="Update Selected", command=self.update_contact
        )
        btn_update.pack(fill="x", pady=3)

        btn_delete = ttk.Button(
            form_frame, text="Delete Selected", command=self.delete_contact
        )
        btn_delete.pack(fill="x", pady=3)

        btn_clear = ttk.Button(form_frame, text="Clear Fields", command=self.clear_fields)
        btn_clear.pack(fill="x", pady=3)

        # Right Frame: List View & Search
        list_frame = ttk.LabelFrame(self.root, text=" Saved Contacts ", padding=15)
        list_frame.place(x=310, y=15, width=325, height=470)

        # Search Bar
        search_subframe = ttk.Frame(list_frame)
        search_subframe.pack(fill="x", pady=(0, 10))

        ttk.Label(search_subframe, text="Search:").pack(side="left", padx=(0, 5))
        self.entry_search = ttk.Entry(search_subframe)
        self.entry_search.pack(side="left", fill="x", expand=True)
        self.entry_search.bind("<KeyRelease>", self.search_contacts)

        # Treeview (Table)
        columns = ("name", "phone")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Name")
        self.tree.heading("phone", text="Phone")
        self.tree.column("name", width=140)
        self.tree.column("phone", width=130)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_contact)

    # ------------------------------------------------------------------
    # CRUD & Helper Functions
    # ------------------------------------------------------------------
    def refresh_contact_list(self, data=None):
        """Populate the Treeview table with current or filtered contacts."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        target_contacts = data if data is not None else self.contacts
        for idx, contact in enumerate(target_contacts):
            self.tree.insert("", "end", iid=idx, values=(contact["name"], contact["phone"]))

    def clear_fields(self):
        """Clear all input entry widgets."""
        self.entry_name.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_address.delete(0, tk.END)
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def add_contact(self):
        """Add a new contact to the store and save."""
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        email = self.entry_email.get().strip()
        address = self.entry_address.get().strip()

        if not name or not phone:
            messagebox.showwarning("Validation Error", "Name and Phone fields are required!")
            return

        new_contact = {
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
        }

        self.contacts.append(new_contact)
        self.save_contacts()
        self.refresh_contact_list()
        self.clear_fields()
        messagebox.showinfo("Success", "Contact added successfully!")

    def on_select_contact(self, event):
        """Populate the input fields when a row is clicked."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        idx = int(selected_item[0])
        contact = self.contacts[idx]

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, contact.get("name", ""))

        self.entry_phone.delete(0, tk.END)
        self.entry_phone.insert(0, contact.get("phone", ""))

        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, contact.get("email", ""))

        self.entry_address.delete(0, tk.END)
        self.entry_address.insert(0, contact.get("address", ""))

    def update_contact(self):
        """Update the selected contact in the list."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a contact to update.")
            return

        idx = int(selected_item[0])
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()

        if not name or not phone:
            messagebox.showwarning("Validation Error", "Name and Phone fields cannot be empty!")
            return

        self.contacts[idx] = {
            "name": name,
            "phone": phone,
            "email": self.entry_email.get().strip(),
            "address": self.entry_address.get().strip(),
        }

        self.save_contacts()
        self.refresh_contact_list()
        self.clear_fields()
        messagebox.showinfo("Success", "Contact updated successfully!")

    def delete_contact(self):
        """Delete the selected contact."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a contact to delete.")
            return

        idx = int(selected_item[0])
        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete {self.contacts[idx]['name']}?"
        )
        if confirm:
            del self.contacts[idx]
            self.save_contacts()
            self.refresh_contact_list()
            self.clear_fields()
            messagebox.showinfo("Success", "Contact deleted.")

    def search_contacts(self, event):
        """Filter the displayed list based on search term."""
        query = self.entry_search.get().lower().strip()
        if not query:
            self.refresh_contact_list()
            return

        filtered = [
            c
            for c in self.contacts
            if query in c["name"].lower() or query in c["phone"].lower()
        ]
        self.refresh_contact_list(data=filtered)


if __name__ == "__main__":
    root = tk.Tk()
    app = ContactBookApp(root)
    root.mainloop()