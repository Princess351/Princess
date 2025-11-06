import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3
import hashlib


class DatabaseManager:
    """Database management class for SQLite operations"""
    
    def __init__(self, db_name: str = "retail_management.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'staff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                address TEXT NOT NULL,
                category TEXT DEFAULT 'Regular',
                loyalty_points INTEGER DEFAULT 0,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                amount REAL NOT NULL,
                description TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        # Insert default user if not exists
        cursor.execute("SELECT * FROM users WHERE username = ?", ("sumi",))
        if cursor.fetchone() is None:
            password_hash = hashlib.sha256("sumi123".encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                ("sumi", password_hash, "Sumi Administrator", "admin")
            )
        
        conn.commit()
        conn.close()
    
    def verify_login(self, username: str, password: str) -> bool:
        """Verify user login credentials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        return user is not None
    
    def add_customer(self, name: str, contact: str, address: str, category: str) -> int:
        """Add a new customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO customers (name, contact, address, category) VALUES (?, ?, ?, ?)",
            (name, contact, address, category)
        )
        
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return customer_id
    
    def update_customer(self, customer_id: int, name: str, contact: str, 
                       address: str, category: str) -> bool:
        """Update existing customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE customers 
               SET name = ?, contact = ?, address = ?, category = ?
               WHERE customer_id = ?""",
            (name, contact, address, category, customer_id)
        )
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
    def delete_customer(self, customer_id: int) -> bool:
        """Delete a customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Delete transactions first
        cursor.execute("DELETE FROM transactions WHERE customer_id = ?", (customer_id,))
        
        # Delete customer
        cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """Get customer by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "customer_id": row[0],
                "name": row[1],
                "contact": row[2],
                "address": row[3],
                "category": row[4],
                "loyalty_points": row[5],
                "registration_date": row[6]
            }
        return None
    
    def search_customers(self, query: str) -> List[Dict]:
        """Search customers by name, contact, or ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT * FROM customers 
               WHERE name LIKE ? OR contact LIKE ? OR CAST(customer_id AS TEXT) = ?
               ORDER BY name""",
            (f"%{query}%", f"%{query}%", query)
        )
        
        customers = []
        for row in cursor.fetchall():
            customers.append({
                "customer_id": row[0],
                "name": row[1],
                "contact": row[2],
                "address": row[3],
                "category": row[4],
                "loyalty_points": row[5],
                "registration_date": row[6]
            })
        
        conn.close()
        return customers
    
    def get_all_customers(self) -> List[Dict]:
        """Get all customers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers ORDER BY name")
        
        customers = []
        for row in cursor.fetchall():
            customers.append({
                "customer_id": row[0],
                "name": row[1],
                "contact": row[2],
                "address": row[3],
                "category": row[4],
                "loyalty_points": row[5],
                "registration_date": row[6]
            })
        
        conn.close()
        return customers
    
    def add_transaction(self, customer_id: int, amount: float, description: str) -> int:
        """Add a transaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Add transaction
        cursor.execute(
            "INSERT INTO transactions (customer_id, amount, description) VALUES (?, ?, ?)",
            (customer_id, amount, description)
        )
        
        transaction_id = cursor.lastrowid
        
        # Update loyalty points (1 point per $10)
        points_earned = int(amount / 10)
        cursor.execute(
            "UPDATE customers SET loyalty_points = loyalty_points + ? WHERE customer_id = ?",
            (points_earned, customer_id)
        )
        
        # Check if customer should be upgraded to VIP
        cursor.execute(
            "SELECT loyalty_points, category FROM customers WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        
        if row and row[0] >= 1000 and row[1] != "VIP":
            cursor.execute(
                "UPDATE customers SET category = 'VIP' WHERE customer_id = ?",
                (customer_id,)
            )
        
        conn.commit()
        conn.close()
        
        return transaction_id
    
    def get_transactions(self, customer_id: int) -> List[Dict]:
        """Get all transactions for a customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM transactions WHERE customer_id = ? ORDER BY transaction_date DESC",
            (customer_id,)
        )
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                "transaction_id": row[0],
                "customer_id": row[1],
                "amount": row[2],
                "description": row[3],
                "transaction_date": row[4]
            })
        
        conn.close()
        return transactions
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total customers
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]
        
        # VIP customers
        cursor.execute("SELECT COUNT(*) FROM customers WHERE category = 'VIP'")
        vip_customers = cursor.fetchone()[0]
        
        # Total transactions
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM transactions")
        trans_row = cursor.fetchone()
        total_transactions = trans_row[0]
        total_revenue = trans_row[1]
        
        # Recent transactions
        cursor.execute(
            """SELECT COUNT(*), COALESCE(SUM(amount), 0) 
               FROM transactions 
               WHERE transaction_date >= date('now', '-7 days')"""
        )
        recent_row = cursor.fetchone()
        recent_transactions = recent_row[0]
        recent_revenue = recent_row[1]
        
        conn.close()
        
        return {
            "total_customers": total_customers,
            "vip_customers": vip_customers,
            "total_transactions": total_transactions,
            "total_revenue": total_revenue,
            "recent_transactions": recent_transactions,
            "recent_revenue": recent_revenue
        }


class LoginWindow:
    """Login window class"""
    
    def __init__(self, root, db_manager, on_success):
        self.root = root
        self.db_manager = db_manager
        self.on_success = on_success
        
        self.root.title("Retail Management System - Login")
        self.root.geometry("500x650")
        
        # Make window resizable
        self.root.resizable(True, True)
        self.root.minsize(400, 550)
        
        # Configure grid weights for responsive design
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Center window
        self.center_window()
        
        self.setup_ui()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup login UI"""
        # Main container with grid
        container = tk.Frame(self.root, bg="#1e3a5f")
        container.grid(row=0, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=2)
        container.rowconfigure(2, weight=0)
        container.columnconfigure(0, weight=1)
        
        # Logo/Title section
        title_frame = tk.Frame(container, bg="#1e3a5f")
        title_frame.grid(row=0, column=0, sticky="ew", pady=20)
        
        # System icon/logo
        logo_label = tk.Label(title_frame, text="🏪", font=("Arial", 60), bg="#1e3a5f", fg="white")
        logo_label.pack()
        
        title_label = tk.Label(
            title_frame, 
            text="RETAIL MANAGEMENT SYSTEM", 
            font=("Arial", 18, "bold"),
            bg="#1e3a5f",
            fg="white"
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Customer & Transaction Management",
            font=("Arial", 10),
            bg="#1e3a5f",
            fg="#a8c5e8"
        )
        subtitle_label.pack()
        
        # Center frame container
        center_container = tk.Frame(container, bg="#1e3a5f")
        center_container.grid(row=1, column=0, sticky="")
        
        # Login form frame
        form_frame = tk.Frame(center_container, bg="white", relief=tk.RAISED, bd=2)
        form_frame.pack(padx=40, pady=20)
        
        # Login header
        login_header = tk.Label(
            form_frame,
            text="Staff Login",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#1e3a5f"
        )
        login_header.pack(pady=20)
        
        # Username
        username_frame = tk.Frame(form_frame, bg="white")
        username_frame.pack(pady=10, padx=30, fill=tk.X)
        
        tk.Label(
            username_frame,
            text="👤 Username",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#333"
        ).pack(anchor=tk.W, pady=5)
        
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(
            username_frame,
            textvariable=self.username_var,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            width=30
        )
        username_entry.pack(fill=tk.X, ipady=8)
        username_entry.focus()
        
        # Password
        password_frame = tk.Frame(form_frame, bg="white")
        password_frame.pack(pady=10, padx=30, fill=tk.X)
        
        tk.Label(
            password_frame,
            text="🔒 Password",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#333"
        ).pack(anchor=tk.W, pady=5)
        
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(
            password_frame,
            textvariable=self.password_var,
            font=("Arial", 12),
            show="●",
            relief=tk.SOLID,
            bd=1,
            width=30
        )
        password_entry.pack(fill=tk.X, ipady=8)
        password_entry.bind("<Return>", lambda e: self.login())
        
        # Login button
        login_btn = tk.Button(
            form_frame,
            text="LOGIN",
            font=("Arial", 13, "bold"),
            bg="#1e3a5f",
            fg="white",
            activebackground="#2c5282",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.login,
            width=25,
            height=2
        )
        login_btn.pack(pady=25, padx=30)
        
        # Info label
        info_label = tk.Label(
            form_frame,
            text="Default Login: sumi / sumi123",
            font=("Arial", 9),
            bg="white",
            fg="#666"
        )
        info_label.pack(pady=(5, 20))
        
        # Footer
        footer_label = tk.Label(
            container,
            text="© 2024 Retail Management System v1.0",
            font=("Arial", 8),
            bg="#1e3a5f",
            fg="#a8c5e8"
        )
        footer_label.grid(row=2, column=0, pady=10, sticky="s")
    
    def login(self):
        """Handle login"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("Login Failed", "Please enter both username and password!")
            return
        
        if self.db_manager.verify_login(username, password):
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            self.root.destroy()
            self.on_success(username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password!")
            self.password_var.set("")


class RetailManagementGUI:
    """Main Retail Management GUI"""
    
    def __init__(self, root, db_manager, username):
        self.root = root
        self.db_manager = db_manager
        self.username = username
        self.selected_customer_id = None
        
        self.root.title("Retail Management System")
        self.root.geometry("1400x800")
        
        # Make window resizable with minimum size
        self.root.minsize(1000, 600)
        self.root.resizable(True, True)
        
        # Configure root grid weights
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        self.setup_ui()
        self.refresh_customer_list()
        self.update_dashboard()
    
    def setup_ui(self):
        """Setup main UI"""
        # Top bar
        self.setup_top_bar()
        
        # Main container with proper grid configuration
        main_container = tk.Frame(self.root)
        main_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_container.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=2)
        
        # Left panel - Dashboard & Form
        left_panel = tk.Frame(main_container)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_panel.rowconfigure(1, weight=1)
        left_panel.columnconfigure(0, weight=1)
        
        # Dashboard
        self.setup_dashboard(left_panel)
        
        # Customer form
        self.setup_form_panel(left_panel)
        
        # Right panel - Customer list
        right_panel = tk.Frame(main_container)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        
        self.setup_list_panel(right_panel)
    
    def setup_top_bar(self):
        """Setup top navigation bar"""
        top_bar = tk.Frame(self.root, bg="#1e3a5f", height=60)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)
        
        # Title
        title_label = tk.Label(
            top_bar,
            text="🏪 RETAIL MANAGEMENT SYSTEM",
            font=("Arial", 18, "bold"),
            bg="#1e3a5f",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # User info
        user_frame = tk.Frame(top_bar, bg="#1e3a5f")
        user_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(
            user_frame,
            text=f"👤 {self.username}",
            font=("Arial", 11),
            bg="#1e3a5f",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)
        
        logout_btn = tk.Button(
            user_frame,
            text="Logout",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.logout,
            padx=15,
            pady=5
        )
        logout_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_dashboard(self, parent):
        """Setup dashboard with statistics"""
        dashboard_frame = ttk.LabelFrame(parent, text="📊 Dashboard", padding="10")
        dashboard_frame.grid(row=0, column=0, sticky="ew", pady=5)
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.columnconfigure(1, weight=1)
        
        # Stats grid
        stats_frame = tk.Frame(dashboard_frame, bg="white")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        
        # Create stat cards
        self.total_customers_label = self.create_stat_card(
            stats_frame, "Total Customers", "0", "#3498db", 0, 0
        )
        self.vip_customers_label = self.create_stat_card(
            stats_frame, "VIP Customers", "0", "#9b59b6", 0, 1
        )
        self.total_transactions_label = self.create_stat_card(
            stats_frame, "Total Transactions", "0", "#2ecc71", 1, 0
        )
        self.total_revenue_label = self.create_stat_card(
            stats_frame, "Total Revenue", "$0.00", "#e67e22", 1, 1
        )
    
    def create_stat_card(self, parent, title, value, color, row, col):
        """Create a statistics card"""
        card = tk.Frame(parent, bg=color, relief=tk.RAISED, bd=2)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        tk.Label(
            card,
            text=title,
            font=("Arial", 10),
            bg=color,
            fg="white"
        ).pack(pady=(10, 5))
        
        value_label = tk.Label(
            card,
            text=value,
            font=("Arial", 18, "bold"),
            bg=color,
            fg="white"
        )
        value_label.pack(pady=(5, 10))
        
        return value_label
    
    def setup_form_panel(self, parent):
        """Setup customer actions panel"""
        actions_frame = ttk.LabelFrame(parent, text="📝 Customer Actions", padding="10")
        actions_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        actions_frame.columnconfigure(0, weight=1)
        
        # Action buttons
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(pady=10, fill=tk.X)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        register_btn = tk.Button(
            button_frame,
            text="Register Customer",
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_register_window,
            padx=12,
            pady=6
        )
        register_btn.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        
        delete_btn = tk.Button(
            button_frame,
            text="🗑️ Delete Customer",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_delete_window,
            padx=12,
            pady=6
        )
        delete_btn.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        
        update_btn = tk.Button(
            button_frame,
            text="✏️ Update Customer",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_update_window,
            padx=12,
            pady=6
        )
        update_btn.grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        
        # Transaction section
        transaction_frame = ttk.LabelFrame(actions_frame, text="💰 Add Transaction", padding="10")
        transaction_frame.pack(pady=10, fill=tk.X)
        transaction_frame.columnconfigure(1, weight=1)
        
        tk.Label(transaction_frame, text="Amount ($):", font=("Arial", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.amount_var = tk.StringVar()
        tk.Entry(transaction_frame, textvariable=self.amount_var, font=("Arial", 10)).grid(
            row=0, column=1, sticky="ew", pady=5, padx=5
        )
        
        tk.Label(transaction_frame, text="Description:", font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.trans_desc_var = tk.StringVar()
        tk.Entry(transaction_frame, textvariable=self.trans_desc_var, font=("Arial", 10)).grid(
            row=1, column=1, sticky="ew", pady=5, padx=5
        )
        
        tk.Button(
            transaction_frame,
            text="💳 Add Transaction",
            font=("Arial", 10, "bold"),
            bg="#16a085",
            fg="white",
            activebackground="#138d75",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_transaction,
            padx=15,
            pady=8
        ).grid(row=2, column=0, columnspan=2, pady=10)
    
    def setup_list_panel(self, parent):
        """Setup customer list panel"""
        list_frame = ttk.LabelFrame(parent, text="👥 Customer Directory", padding="10")
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
        # Search bar
        search_frame = tk.Frame(list_frame, bg="white", relief=tk.SOLID, bd=1)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        tk.Label(search_frame, text="🔍", font=("Arial", 14), bg="white").pack(
            side=tk.LEFT, padx=10
        )
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.search_customers())
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 11),
            relief=tk.FLAT,
            bg="white"
        )
        search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=5)
        
        refresh_btn = tk.Button(
            search_frame,
            text="🔄 Refresh",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.refresh_customer_list,
            padx=10,
            pady=5
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Treeview frame
        tree_frame = tk.Frame(list_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        # Define columns
        columns = ("ID", "Name", "Contact", "Address", "Category", "Points", "Discount")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Style configuration
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        
        # Column headings
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Customer Name")
        self.tree.heading("Contact", text="Contact")
        self.tree.heading("Address", text="Address")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Points", text="Loyalty Points")
        self.tree.heading("Discount", text="Discount")
        
        # Column widths
        self.tree.column("ID", width=60, anchor=tk.CENTER)
        self.tree.column("Name", width=180)
        self.tree.column("Contact", width=130)
        self.tree.column("Address", width=200)
        self.tree.column("Category", width=100, anchor=tk.CENTER)
        self.tree.column("Points", width=120, anchor=tk.CENTER)
        self.tree.column("Discount", width=100, anchor=tk.CENTER)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_customer_select)
        
        # Add row colors
        self.tree.tag_configure('oddrow', background='#f9f9f9')
        self.tree.tag_configure('evenrow', background='white')
        
        # Action buttons
        action_frame = tk.Frame(list_frame)
        action_frame.grid(row=2, column=0, pady=10)
        
        tk.Button(
            action_frame,
            text="📜 Transaction History",
            font=("Arial", 10, "bold"),
            bg="#8e44ad",
            fg="white",
            activebackground="#7d3c98",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.view_transaction_history,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            action_frame,
            text="📊 Customer Report",
            font=("Arial", 10, "bold"),
            bg="#d35400",
            fg="white",
            activebackground="#ba4a00",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.generate_report,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
    
    def open_register_window(self):
        """Open window to register new customer"""
        reg_window = tk.Toplevel(self.root)
        reg_window.title("Register New Customer")
        reg_window.geometry("400x400")
        reg_window.transient(self.root)
        reg_window.grab_set()
        
        row = 0
        
        tk.Label(reg_window, text="Name:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        name_entry = tk.Entry(reg_window, font=("Arial", 10))
        name_entry.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        tk.Label(reg_window, text="Contact:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        contact_entry = tk.Entry(reg_window, font=("Arial", 10))
        contact_entry.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        tk.Label(reg_window, text="Address:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        address_text = tk.Text(reg_window, width=25, height=3, font=("Arial", 10))
        address_text.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        tk.Label(reg_window, text="Category:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        category_combo = ttk.Combobox(reg_window, values=["Regular", "Student", "VIP"], state="readonly", font=("Arial", 10))
        category_combo.set("Regular")
        category_combo.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        submit_btn = tk.Button(
            reg_window,
            text="Register",
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=lambda: self.submit_register(
                reg_window,
                name_entry.get(),
                contact_entry.get(),
                address_text.get("1.0", tk.END),
                category_combo.get()
            )
        )
        submit_btn.grid(row=row, column=0, columnspan=2, pady=10)
    
    def submit_register(self, window, name, contact, address, category):
        if not name.strip() or not contact.strip() or not address.strip():
            messagebox.showerror("Validation Error", "All fields are required!")
            return
        
        try:
            customer_id = self.db_manager.add_customer(name.strip(), contact.strip(), address.strip(), category)
            messagebox.showinfo("Success", f"✅ Customer '{name.strip()}' added successfully!\n\nCustomer ID: {customer_id}")
            window.destroy()
            self.refresh_customer_list()
            self.update_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add customer:\n{str(e)}")
    
    def open_update_window(self):
        """Open window to update selected customer"""
        if self.selected_customer_id is None:
            messagebox.showwarning("Warning", "⚠️ Please select a customer first!")
            return
        
        customer = self.db_manager.get_customer(self.selected_customer_id)
        if not customer:
            messagebox.showerror("Error", "Customer not found!")
            return
        
        up_window = tk.Toplevel(self.root)
        up_window.title("Update Customer")
        up_window.geometry("400x400")
        up_window.transient(self.root)
        up_window.grab_set()
        
        row = 0
        
        tk.Label(up_window, text="Name:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        name_entry = tk.Entry(up_window, font=("Arial", 10))
        name_entry.insert(0, customer["name"])
        name_entry.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        tk.Label(up_window, text="Contact:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        contact_entry = tk.Entry(up_window, font=("Arial", 10))
        contact_entry.insert(0, customer["contact"])
        contact_entry.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        tk.Label(up_window, text="Address:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        address_text = tk.Text(up_window, width=25, height=3, font=("Arial", 10))
        address_text.insert("1.0", customer["address"])
        address_text.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        tk.Label(up_window, text="Category:*", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=8, padx=5)
        category_combo = ttk.Combobox(up_window, values=["Regular", "Student", "VIP"], state="readonly", font=("Arial", 10))
        category_combo.set(customer["category"])
        category_combo.grid(row=row, column=1, sticky="ew", pady=8, padx=5)
        row += 1
        
        submit_btn = tk.Button(
            up_window,
            text="Update",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            command=lambda: self.submit_update(
                up_window,
                self.selected_customer_id,
                name_entry.get(),
                contact_entry.get(),
                address_text.get("1.0", tk.END),
                category_combo.get()
            )
        )
        submit_btn.grid(row=row, column=0, columnspan=2, pady=10)
    
    def submit_update(self, window, customer_id, name, contact, address, category):
        if not name.strip() or not contact.strip() or not address.strip():
            messagebox.showerror("Validation Error", "All fields are required!")
            return
        
        try:
            if self.db_manager.update_customer(customer_id, name.strip(), contact.strip(), address.strip(), category):
                messagebox.showinfo("Success", "✅ Customer updated successfully!")
                window.destroy()
                self.refresh_customer_list()
                self.update_dashboard()
            else:
                messagebox.showerror("Error", "Customer not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update customer:\n{str(e)}")
    
    def open_delete_window(self):
        """Open window to confirm delete selected customer"""
        if self.selected_customer_id is None:
            messagebox.showwarning("Warning", "⚠️ Please select a customer first!")
            return
        
        customer = self.db_manager.get_customer(self.selected_customer_id)
        if not customer:
            messagebox.showerror("Error", "Customer not found!")
            return
        
        del_window = tk.Toplevel(self.root)
        del_window.title("Delete Customer")
        del_window.geometry("400x200")
        del_window.transient(self.root)
        del_window.grab_set()
        
        tk.Label(del_window, text=f"Name: {customer['name']}", font=("Arial", 10)).pack(pady=5)
        tk.Label(del_window, text=f"ID: {customer['customer_id']}", font=("Arial", 10)).pack(pady=5)
        tk.Label(del_window, text="This will delete all transactions!", font=("Arial", 10, "bold"), fg="red").pack(pady=10)
        
        button_frame = tk.Frame(del_window)
        button_frame.pack(pady=10)
        
        confirm_btn = tk.Button(
            button_frame,
            text="Confirm Delete",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            command=lambda: self.submit_delete(del_window, self.selected_customer_id)
        )
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            command=del_window.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def submit_delete(self, window, customer_id):
        try:
            if self.db_manager.delete_customer(customer_id):
                messagebox.showinfo("Success", "✅ Customer deleted successfully!")
                self.selected_customer_id = None
                window.destroy()
                self.refresh_customer_list()
                self.update_dashboard()
            else:
                messagebox.showerror("Error", "Failed to delete customer!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete customer:\n{str(e)}")
    
    def get_discount_rate(self, category: str) -> float:
        """Get discount rate based on customer category"""
        discount_rates = {
            "Regular": 0.0,
            "Student": 0.10,
            "VIP": 0.15
        }
        return discount_rates.get(category, 0.0)
    
    def on_customer_select(self, event):
        """Handle customer selection from list"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        self.selected_customer_id = int(item["values"][0])
    
    def refresh_customer_list(self):
        """Refresh the customer list"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add all customers
        customers = self.db_manager.get_all_customers()
        for idx, customer in enumerate(customers):
            discount_rate = self.get_discount_rate(customer["category"]) * 100
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            
            self.tree.insert("", tk.END, values=(
                customer["customer_id"],
                customer["name"],
                customer["contact"],
                customer["address"][:50] + "..." if len(customer["address"]) > 50 else customer["address"],
                customer["category"],
                customer["loyalty_points"],
                f"{discount_rate:.0f}%"
            ), tags=(tag,))
    
    def search_customers(self):
        """Search customers based on query"""
        query = self.search_var.get().strip()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not query:
            self.refresh_customer_list()
            return
        
        # Search and display results
        customers = self.db_manager.search_customers(query)
        for idx, customer in enumerate(customers):
            discount_rate = self.get_discount_rate(customer["category"]) * 100
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            
            self.tree.insert("", tk.END, values=(
                customer["customer_id"],
                customer["name"],
                customer["contact"],
                customer["address"][:50] + "..." if len(customer["address"]) > 50 else customer["address"],
                customer["category"],
                customer["loyalty_points"],
                f"{discount_rate:.0f}%"
            ), tags=(tag,))
    
    def add_transaction(self):
        """Add a transaction to selected customer"""
        if self.selected_customer_id is None:
            messagebox.showwarning("Warning", "⚠️ Please select a customer first!")
            return
        
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0!")
                return
            
            description = self.trans_desc_var.get().strip()
            if not description:
                messagebox.showerror("Error", "Description is required!")
                return
            
            customer = self.db_manager.get_customer(self.selected_customer_id)
            if not customer:
                messagebox.showerror("Error", "Customer not found!")
                return
            
            old_points = customer["loyalty_points"]
            old_category = customer["category"]
            
            self.db_manager.add_transaction(self.selected_customer_id, amount, description)
            
            # Get updated customer info
            updated_customer = self.db_manager.get_customer(self.selected_customer_id)
            points_earned = updated_customer["loyalty_points"] - old_points
            
            msg = f"✅ Transaction added successfully!\n\n"
            msg += f"💰 Amount: ${amount:.2f}\n"
            msg += f"⭐ Points earned: {points_earned}\n"
            msg += f"📊 Total points: {updated_customer['loyalty_points']}"
            
            if old_category != updated_customer["category"]:
                msg += f"\n\n🎉 Congratulations!\n"
                msg += f"Customer upgraded to {updated_customer['category']}!"
            
            messagebox.showinfo("Success", msg)
            
            self.amount_var.set("")
            self.trans_desc_var.set("")
            self.refresh_customer_list()
            self.update_dashboard()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount! Please enter a valid number.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add transaction:\n{str(e)}")
    
    def view_transaction_history(self):
        """View transaction history for selected customer"""
        if self.selected_customer_id is None:
            messagebox.showwarning("Warning", "⚠️ Please select a customer first!")
            return
        
        customer = self.db_manager.get_customer(self.selected_customer_id)
        if not customer:
            messagebox.showerror("Error", "Customer not found!")
            return
        
        # Create new window
        history_window = tk.Toplevel(self.root)
        history_window.title(f"Transaction History - {customer['name']}")
        history_window.geometry("900x500")
        history_window.transient(self.root)
        history_window.grab_set()
        
        # Configure grid
        history_window.rowconfigure(1, weight=1)
        history_window.columnconfigure(0, weight=1)
        
        # Header
        header_frame = tk.Frame(history_window, bg="#1e3a5f", height=80)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        
        tk.Label(
            header_frame,
            text=f"📜 Transaction History",
            font=("Arial", 16, "bold"),
            bg="#1e3a5f",
            fg="white"
        ).pack(pady=10)
        
        info_text = f"Customer: {customer['name']} | ID: {customer['customer_id']} | "
        info_text += f"Category: {customer['category']} | Points: {customer['loyalty_points']}"
        tk.Label(
            header_frame,
            text=info_text,
            font=("Arial", 11),
            bg="#1e3a5f",
            fg="white"
        ).pack()
        
        # Transaction list frame
        tree_frame = tk.Frame(history_window)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        columns = ("Date", "Amount", "Description")
        trans_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        trans_tree.heading("Date", text="Transaction Date")
        trans_tree.heading("Amount", text="Amount")
        trans_tree.heading("Description", text="Description")
        
        trans_tree.column("Date", width=200)
        trans_tree.column("Amount", width=150, anchor=tk.CENTER)
        trans_tree.column("Description", width=400)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=trans_tree.yview)
        trans_tree.configure(yscrollcommand=vsb.set)
        
        trans_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        
        # Add transactions
        transactions = self.db_manager.get_transactions(self.selected_customer_id)
        total_amount = 0
        
        if transactions:
            for idx, trans in enumerate(transactions):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                trans_tree.insert("", tk.END, values=(
                    trans["transaction_date"],
                    f"${trans['amount']:.2f}",
                    trans["description"]
                ), tags=(tag,))
                total_amount += trans["amount"]
            
            trans_tree.tag_configure('oddrow', background='#f9f9f9')
            trans_tree.tag_configure('evenrow', background='white')
        else:
            trans_tree.insert("", tk.END, values=("No transactions yet", "", ""))
        
        # Summary
        summary_frame = tk.Frame(history_window, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        summary_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        tk.Label(
            summary_frame,
            text=f"Total Transactions: {len(transactions)} | Total Amount: ${total_amount:.2f}",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        ).pack(pady=10)
        
        # Close button
        close_btn = tk.Button(
            history_window,
            text="Close",
            font=("Arial", 11, "bold"),
            bg="#95a5a6",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=history_window.destroy,
            padx=30,
            pady=10
        )
        close_btn.grid(row=3, column=0, pady=10)
    
    def generate_report(self):
        """Generate customer report"""
        if self.selected_customer_id is None:
            messagebox.showwarning("Warning", "⚠️ Please select a customer first!")
            return
        
        customer = self.db_manager.get_customer(self.selected_customer_id)
        if not customer:
            messagebox.showerror("Error", "Customer not found!")
            return
        
        transactions = self.db_manager.get_transactions(self.selected_customer_id)
        total_spent = sum(t["amount"] for t in transactions)
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title(f"Customer Report - {customer['name']}")
        report_window.geometry("650x750")
        report_window.transient(self.root)
        report_window.grab_set()
        
        # Configure grid
        report_window.rowconfigure(1, weight=1)
        report_window.columnconfigure(0, weight=1)
        
        # Header
        header_frame = tk.Frame(report_window, bg="#1e3a5f", height=80)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        
        tk.Label(
            header_frame,
            text="📊 Customer Report",
            font=("Arial", 18, "bold"),
            bg="#1e3a5f",
            fg="white"
        ).pack(pady=25)
        
        # Report content frame
        content_frame = tk.Frame(report_window, bg="white")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content_frame.rowconfigure(0, weight=1)
        content_frame.columnconfigure(0, weight=1)
        
        report_text = tk.Text(content_frame, font=("Courier", 10), wrap=tk.WORD, relief=tk.FLAT)
        report_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=report_text.yview)
        report_text.configure(yscrollcommand=report_scrollbar.set)
        
        report_text.grid(row=0, column=0, sticky="nsew")
        report_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Generate report content
        report = f"""
{'='*60}
                    CUSTOMER REPORT
{'='*60}

Customer Information:
{'─'*60}
Customer ID        : {customer['customer_id']}
Name               : {customer['name']}
Contact            : {customer['contact']}
Address            : {customer['address']}
Category           : {customer['category']}
Registration Date  : {customer['registration_date']}

Loyalty Program:
{'─'*60}
Loyalty Points     : {customer['loyalty_points']} points
Discount Rate      : {self.get_discount_rate(customer['category']) * 100:.0f}%
Status             : {'🌟 VIP Member' if customer['category'] == 'VIP' else '📋 Active'}

Transaction Summary:
{'─'*60}
Total Transactions : {len(transactions)}
Total Amount Spent : ${total_spent:.2f}
Average Transaction: ${(total_spent / len(transactions)):.2f if transactions else 0:.2f}

Recent Transactions:
{'─'*60}
"""
        
        # Add recent transactions
        if transactions:
            for trans in transactions[:5]:  # Last 5 transactions
                report += f"\n{trans['transaction_date'][:16]}\n"
                report += f"  Amount: ${trans['amount']:.2f}\n"
                report += f"  Description: {trans['description']}\n"
        else:
            report += "\nNo transactions yet.\n"
        
        report += f"\n{'='*60}\n"
        report += f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'='*60}\n"
        
        report_text.insert("1.0", report)
        report_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(
            report_window,
            text="Close",
            font=("Arial", 11, "bold"),
            bg="#95a5a6",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=report_window.destroy,
            padx=30,
            pady=10
        )
        close_btn.grid(row=2, column=0, pady=10)
    
    def update_dashboard(self):
        """Update dashboard statistics"""
        try:
            stats = self.db_manager.get_dashboard_stats()
            
            self.total_customers_label.config(text=str(stats["total_customers"]))
            self.vip_customers_label.config(text=str(stats["vip_customers"]))
            self.total_transactions_label.config(text=str(stats["total_transactions"]))
            self.total_revenue_label.config(text=f"${stats['total_revenue']:.2f}")
        except Exception as e:
            print(f"Error updating dashboard: {e}")
    
    def logout(self):
        """Handle logout"""
        result = messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?")
        if result:
            self.root.destroy()
            start_application()


def start_application():
    """Start the application with login"""
    db_manager = DatabaseManager()
    
    def on_login_success(username):
        """Callback after successful login"""
        main_root = tk.Tk()
        app = RetailManagementGUI(main_root, db_manager, username)
        main_root.mainloop()
    
    login_root = tk.Tk()
    login_app = LoginWindow(login_root, db_manager, on_login_success)
    login_root.mainloop()


if __name__ == "__main__":
    start_application()