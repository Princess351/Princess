import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
from decimal import Decimal
import json

class Database:
    """Handle all database operations"""
    
    def __init__(self):
        self.conn = sqlite3.connect('pos_system.db')
        self.create_tables()
        self.insert_sample_data()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                category TEXT
            )
        ''')
        
        # Services table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                duration INTEGER,
                category TEXT
            )
        ''')
        
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                loyalty_type TEXT DEFAULT 'Regular',
                points INTEGER DEFAULT 0,
                phone TEXT,
                email TEXT
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                total REAL,
                subtotal REAL,
                tax REAL,
                discount REAL,
                payment_method TEXT,
                date TEXT,
                items TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        self.conn.commit()
    
    def insert_sample_data(self):
        cursor = self.conn.cursor()
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM products')
        if cursor.fetchone()[0] == 0:
            # Sample products
            products = [
                ('Laptop', 899.99, 15, 'Electronics'),
                ('Wireless Mouse', 29.99, 50, 'Electronics'),
                ('USB Cable', 9.99, 100, 'Accessories'),
                ('Keyboard', 59.99, 30, 'Electronics'),
                ('Monitor', 299.99, 20, 'Electronics'),
                ('Coffee Mug', 12.99, 75, 'Home'),
                ('Notebook', 5.99, 200, 'Stationery'),
                ('Pen Set', 15.99, 150, 'Stationery')
            ]
            cursor.executemany('INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)', products)
            
            # Sample services
            services = [
                ('Computer Repair', 79.99, 60, 'Technical'),
                ('Software Installation', 49.99, 30, 'Technical'),
                ('Data Recovery', 149.99, 120, 'Technical'),
                ('Consultation', 99.99, 45, 'Professional'),
                ('Training Session', 199.99, 90, 'Professional')
            ]
            cursor.executemany('INSERT INTO services (name, price, duration, category) VALUES (?, ?, ?, ?)', services)
            
            # Sample customers
            customers = [
                ('John Smith', 'Regular', 50, '555-0101', 'john@email.com'),
                ('Sarah Johnson', 'VIP', 250, '555-0102', 'sarah@email.com'),
                ('Mike Brown', 'Student', 30, '555-0103', 'mike@email.com'),
                ('Emily Davis', 'VIP', 500, '555-0104', 'emily@email.com'),
                ('Alex Wilson', 'Regular', 100, '555-0105', 'alex@email.com')
            ]
            cursor.executemany('INSERT INTO customers (name, loyalty_type, points, phone, email) VALUES (?, ?, ?, ?, ?)', customers)
            
            self.conn.commit()
    
    def get_all_products(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY name')
        return cursor.fetchall()
    
    def get_all_services(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM services ORDER BY name')
        return cursor.fetchall()
    
    def get_all_customers(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY name')
        return cursor.fetchall()
    
    def update_stock(self, product_id, quantity):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (quantity, product_id))
        self.conn.commit()
    
    def add_transaction(self, customer_id, total, subtotal, tax, discount, payment_method, items):
        cursor = self.conn.cursor()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        items_json = json.dumps(items)
        cursor.execute('''
            INSERT INTO transactions (customer_id, total, subtotal, tax, discount, payment_method, date, items)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, total, subtotal, tax, discount, payment_method, date, items_json))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_customer_points(self, customer_id, points):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE customers SET points = points + ? WHERE id = ?', (points, customer_id))
        self.conn.commit()
    
    def process_return(self, transaction_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT items FROM transactions WHERE id = ?', (transaction_id,))
        result = cursor.fetchone()
        if result:
            items = json.loads(result[0])
            for item in items:
                if item['type'] == 'product':
                    cursor.execute('UPDATE products SET stock = stock + ? WHERE id = ?', 
                                 (item['quantity'], item['id']))
            self.conn.commit()
            return True
        return False

class POSSystem:
    """Main POS System Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Professional POS System")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")
        
        self.db = Database()
        self.cart = []
        self.selected_customer = None
        self.tax_rate = 0.10  # 10% tax rate
        
        # Color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'dark': '#34495e',
            'white': '#ffffff'
        }
        
        self.create_widgets()
        self.load_products()
        self.load_services()
        self.load_customers()
        self.update_totals()
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=self.colors['primary'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(header, text="🛒 POS System", 
                              font=("Arial", 20, "bold"), 
                              bg=self.colors['primary'], 
                              fg=self.colors['white'])
        title_label.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self.root, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Products & Services
        left_panel = tk.Frame(main_container, bg=self.colors['white'], relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Products section
        products_frame = tk.LabelFrame(left_panel, text="📦 Products", 
                                      font=("Arial", 11, "bold"),
                                      bg=self.colors['white'], fg=self.colors['primary'])
        products_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)
        
        # Products treeview
        products_scroll = ttk.Scrollbar(products_frame)
        products_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.products_tree = ttk.Treeview(products_frame, 
                                         columns=('ID', 'Name', 'Price', 'Stock', 'Category'),
                                         show='headings',
                                         yscrollcommand=products_scroll.set)
        products_scroll.config(command=self.products_tree.yview)
        
        self.products_tree.heading('ID', text='ID')
        self.products_tree.heading('Name', text='Product Name')
        self.products_tree.heading('Price', text='Price')
        self.products_tree.heading('Stock', text='Stock')
        self.products_tree.heading('Category', text='Category')
        
        self.products_tree.column('ID', width=50)
        self.products_tree.column('Name', width=200)
        self.products_tree.column('Price', width=80)
        self.products_tree.column('Stock', width=80)
        self.products_tree.column('Category', width=100)
        
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.products_tree.bind('<Double-1>', self.add_product_to_cart)
        
        # Services section
        services_frame = tk.LabelFrame(left_panel, text="🔧 Services", 
                                      font=("Arial", 11, "bold"),
                                      bg=self.colors['white'], fg=self.colors['primary'])
        services_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)
        
        services_scroll = ttk.Scrollbar(services_frame)
        services_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.services_tree = ttk.Treeview(services_frame,
                                         columns=('ID', 'Name', 'Price', 'Duration', 'Category'),
                                         show='headings',
                                         yscrollcommand=services_scroll.set)
        services_scroll.config(command=self.services_tree.yview)
        
        self.services_tree.heading('ID', text='ID')
        self.services_tree.heading('Name', text='Service Name')
        self.services_tree.heading('Price', text='Price')
        self.services_tree.heading('Duration', text='Duration (min)')
        self.services_tree.heading('Category', text='Category')
        
        self.services_tree.column('ID', width=50)
        self.services_tree.column('Name', width=200)
        self.services_tree.column('Price', width=80)
        self.services_tree.column('Duration', width=100)
        self.services_tree.column('Category', width=100)
        
        self.services_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.services_tree.bind('<Double-1>', self.add_service_to_cart)
        
        # Right panel - Cart & Checkout
        right_panel = tk.Frame(main_container, bg=self.colors['white'], relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Customer selection
        customer_frame = tk.Frame(right_panel, bg=self.colors['light'], relief=tk.RIDGE, bd=2)
        customer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(customer_frame, text="👤 Customer:", font=("Arial", 10, "bold"),
                bg=self.colors['light']).pack(side=tk.LEFT, padx=3, pady=3)
        
        self.customer_var = tk.StringVar(value="Walk-in Customer")
        self.customer_combo = ttk.Combobox(customer_frame, textvariable=self.customer_var,
                                          state='readonly', width=20, font=("Arial", 9))
        self.customer_combo.pack(side=tk.LEFT, padx=3, pady=3)
        self.customer_combo.bind('<<ComboboxSelected>>', self.on_customer_selected)
        
        self.loyalty_label = tk.Label(customer_frame, text="", font=("Arial", 9),
                                     bg=self.colors['light'], fg=self.colors['secondary'])
        self.loyalty_label.pack(side=tk.LEFT, padx=5)
        
        # Cart section
        cart_frame = tk.LabelFrame(right_panel, text="🛒 Shopping Cart", 
                                  font=("Arial", 11, "bold"),
                                  bg=self.colors['white'], fg=self.colors['primary'])
        cart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)
        
        cart_scroll = ttk.Scrollbar(cart_frame)
        cart_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cart_tree = ttk.Treeview(cart_frame,
                                     columns=('Item', 'Price', 'Qty', 'Total'),
                                     show='headings',
                                     yscrollcommand=cart_scroll.set)
        cart_scroll.config(command=self.cart_tree.yview)
        
        self.cart_tree.heading('Item', text='Item')
        self.cart_tree.heading('Price', text='Price')
        self.cart_tree.heading('Qty', text='Quantity')
        self.cart_tree.heading('Total', text='Total')
        
        self.cart_tree.column('Item', width=200)
        self.cart_tree.column('Price', width=80)
        self.cart_tree.column('Qty', width=70)
        self.cart_tree.column('Total', width=80)
        
        self.cart_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Cart buttons
        cart_btn_frame = tk.Frame(right_panel, bg=self.colors['white'])
        cart_btn_frame.pack(fill=tk.X, padx=5, pady=3)
        
        tk.Button(cart_btn_frame, text="🗑️ Remove", command=self.remove_from_cart,
                 bg=self.colors['danger'], fg=self.colors['white'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=2)
        
        tk.Button(cart_btn_frame, text="🔄 Clear", command=self.clear_cart,
                 bg=self.colors['warning'], fg=self.colors['white'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=2)
        
        # Totals section
        totals_frame = tk.Frame(right_panel, bg=self.colors['light'], relief=tk.RIDGE, bd=2)
        totals_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.subtotal_label = tk.Label(totals_frame, text="Subtotal: $0.00",
                                       font=("Arial", 10), bg=self.colors['light'])
        self.subtotal_label.pack(anchor=tk.E, padx=5, pady=1)
        
        self.discount_label = tk.Label(totals_frame, text="Discount: $0.00",
                                      font=("Arial", 10), bg=self.colors['light'],
                                      fg=self.colors['success'])
        self.discount_label.pack(anchor=tk.E, padx=5, pady=1)
        
        self.tax_label = tk.Label(totals_frame, text="Tax (10%): $0.00",
                                 font=("Arial", 10), bg=self.colors['light'])
        self.tax_label.pack(anchor=tk.E, padx=5, pady=1)
        
        self.total_label = tk.Label(totals_frame, text="Total: $0.00",
                                   font=("Arial", 14, "bold"), bg=self.colors['light'],
                                   fg=self.colors['primary'])
        self.total_label.pack(anchor=tk.E, padx=5, pady=3)
        
        # Payment section
        payment_frame = tk.Frame(right_panel, bg=self.colors['white'])
        payment_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(payment_frame, text="Payment:", font=("Arial", 10, "bold"),
                bg=self.colors['white']).pack(side=tk.LEFT, padx=3)
        
        self.payment_var = tk.StringVar(value="Cash")
        payment_methods = ["Cash", "Credit Card", "Debit Card", "Mobile"]
        for method in payment_methods:
            tk.Radiobutton(payment_frame, text=method, variable=self.payment_var,
                          value=method, bg=self.colors['white'],
                          font=("Arial", 9)).pack(side=tk.LEFT, padx=3)
        
        # Checkout buttons
        checkout_frame = tk.Frame(right_panel, bg=self.colors['white'])
        checkout_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(checkout_frame, text="💳 Process Payment", command=self.quick_payment,
                 bg=self.colors['success'], fg=self.colors['white'],
                 font=("Arial", 12, "bold"), relief=tk.RAISED, bd=3,
                 height=1).pack(fill=tk.X, pady=2)
        
        tk.Button(checkout_frame, text="↩️ Process Return", command=self.open_return_window,
                 bg=self.colors['warning'], fg=self.colors['white'],
                 font=("Arial", 10, "bold"), relief=tk.RAISED, bd=2).pack(fill=tk.X, pady=2)
    
    def load_products(self):
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        products = self.db.get_all_products()
        for product in products:
            self.products_tree.insert('', tk.END, values=(
                product[0], product[1], f"${product[2]:.2f}", product[3], product[4]
            ))
    
    def load_services(self):
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        
        services = self.db.get_all_services()
        for service in services:
            self.services_tree.insert('', tk.END, values=(
                service[0], service[1], f"${service[2]:.2f}", service[3], service[4]
            ))
    
    def load_customers(self):
        customers = self.db.get_all_customers()
        customer_list = ["Walk-in Customer"]
        for customer in customers:
            customer_list.append(f"{customer[1]} ({customer[2]})")
        self.customer_combo['values'] = customer_list
    
    def on_customer_selected(self, event):
        selection = self.customer_var.get()
        if selection == "Walk-in Customer":
            self.selected_customer = None
            self.loyalty_label.config(text="")
        else:
            name = selection.split(' (')[0]
            customers = self.db.get_all_customers()
            for customer in customers:
                if customer[1] == name:
                    self.selected_customer = customer
                    loyalty_type = customer[2]
                    points = customer[3]
                    self.loyalty_label.config(text=f"Points: {points}")
                    break
        self.update_totals()
    
    def add_product_to_cart(self, event):
        selection = self.products_tree.selection()
        if not selection:
            return
        
        item = self.products_tree.item(selection[0])
        values = item['values']
        
        product_id = values[0]
        name = values[1]
        price = float(values[2].replace('$', ''))
        stock = values[3]
        
        if stock <= 0:
            messagebox.showwarning("Out of Stock", f"{name} is out of stock!")
            return
        
        quantity = simpledialog.askinteger("Quantity", f"Enter quantity for {name}:",
                                          minvalue=1, maxvalue=stock)
        if quantity:
            cart_item = {
                'type': 'product',
                'id': product_id,
                'name': name,
                'price': price,
                'quantity': quantity,
                'total': price * quantity
            }
            self.cart.append(cart_item)
            self.update_cart_display()
            self.update_totals()
    
    def add_service_to_cart(self, event):
        selection = self.services_tree.selection()
        if not selection:
            return
        
        item = self.services_tree.item(selection[0])
        values = item['values']
        
        service_id = values[0]
        name = values[1]
        price = float(values[2].replace('$', ''))
        
        cart_item = {
            'type': 'service',
            'id': service_id,
            'name': name,
            'price': price,
            'quantity': 1,
            'total': price
        }
        self.cart.append(cart_item)
        self.update_cart_display()
        self.update_totals()
    
    def update_cart_display(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        for item in self.cart:
            self.cart_tree.insert('', tk.END, values=(
                item['name'],
                f"${item['price']:.2f}",
                item['quantity'],
                f"${item['total']:.2f}"
            ))
    
    def remove_from_cart(self):
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to remove")
            return
        
        index = self.cart_tree.index(selection[0])
        self.cart.pop(index)
        self.update_cart_display()
        self.update_totals()
    
    def clear_cart(self):
        if messagebox.askyesno("Clear Cart", "Are you sure you want to clear the cart?"):
            self.cart = []
            self.update_cart_display()
            self.update_totals()
    
    def calculate_discount(self, subtotal):
        if not self.selected_customer:
            return 0
        
        loyalty_type = self.selected_customer[2]
        
        discount_rates = {
            'Regular': 0.05,    # 5% discount
            'VIP': 0.15,        # 15% discount
            'Student': 0.10     # 10% discount
        }
        
        discount_rate = discount_rates.get(loyalty_type, 0)
        return subtotal * discount_rate
    
    def update_totals(self):
        subtotal = sum(item['total'] for item in self.cart)
        discount = self.calculate_discount(subtotal)
        subtotal_after_discount = subtotal - discount
        tax = subtotal_after_discount * self.tax_rate
        total = subtotal_after_discount + tax
        
        self.subtotal_label.config(text=f"Subtotal: ${subtotal:.2f}")
        self.discount_label.config(text=f"Discount: -${discount:.2f}")
        self.tax_label.config(text=f"Tax (10%): ${tax:.2f}")
        self.total_label.config(text=f"Total: ${total:.2f}")
    
    def generate_receipt(self, transaction_id, subtotal, discount, tax, total, payment_method, cash_received=None, change=None):
        """Generate and display receipt in a new window"""
        receipt_window = tk.Toplevel(self.root)
        receipt_window.title("Receipt")
        receipt_window.geometry("500x700")
        receipt_window.configure(bg=self.colors['white'])
        
        # Receipt frame
        receipt_frame = tk.Frame(receipt_window, bg=self.colors['white'], relief=tk.RIDGE, bd=2)
        receipt_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create receipt text
        receipt_text = tk.Text(receipt_frame, font=("Courier", 10), bg=self.colors['white'],
                              relief=tk.FLAT, wrap=tk.WORD, height=35)
        receipt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Build receipt content
        receipt_content = "=" * 50 + "\n"
        receipt_content += "       PROFESSIONAL POS SYSTEM\n"
        receipt_content += "         SALES RECEIPT\n"
        receipt_content += "=" * 50 + "\n\n"
        
        # Date and transaction info
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        receipt_content += f"Date: {current_time}\n"
        receipt_content += f"Transaction ID: #{transaction_id}\n"
        
        # Customer info
        if self.selected_customer:
            receipt_content += f"Customer: {self.selected_customer[1]}\n"
            receipt_content += f"Loyalty: {self.selected_customer[2]}\n"
            receipt_content += f"Points: {self.selected_customer[3]}\n"
        else:
            receipt_content += "Customer: Walk-in\n"
        
        receipt_content += "\n" + "-" * 50 + "\n"
        receipt_content += f"{'Item':<25} {'Qty':>5} {'Price':>8} {'Total':>10}\n"
        receipt_content += "-" * 50 + "\n"
        
        # Items
        for item in self.cart:
            name = item['name'][:24]  # Truncate long names
            qty = item['quantity']
            price = item['price']
            item_total = item['total']
            receipt_content += f"{name:<25} {qty:>5} ${price:>7.2f} ${item_total:>9.2f}\n"
        
        receipt_content += "-" * 50 + "\n\n"
        
        # Totals
        receipt_content += f"{'Subtotal:':<40} ${subtotal:>8.2f}\n"
        
        if discount > 0:
            discount_percent = (discount / subtotal) * 100
            receipt_content += f"{'Discount (' + f'{discount_percent:.0f}%' + '):':<40} -${discount:>7.2f}\n"
        
        receipt_content += f"{'Tax (10%):':<40} ${tax:>8.2f}\n"
        receipt_content += "=" * 50 + "\n"
        receipt_content += f"{'TOTAL:':<40} ${total:>8.2f}\n"
        receipt_content += "=" * 50 + "\n\n"
        
        # Payment details
        receipt_content += f"Payment Method: {payment_method}\n"
        
        if payment_method == "Cash" and cash_received is not None:
            receipt_content += f"Cash Received: ${cash_received:.2f}\n"
            receipt_content += f"Change: ${change:.2f}\n"
        
        # Points earned
        if self.selected_customer:
            points_earned = int(total)
            new_points = self.selected_customer[3] + points_earned
            receipt_content += f"\nPoints Earned: {points_earned}\n"
            receipt_content += f"Total Points: {new_points}\n"
        
        receipt_content += "\n" + "=" * 50 + "\n"
        receipt_content += "     Thank you for your business!\n"
        receipt_content += "        Please come again!\n"
        receipt_content += "=" * 50 + "\n"
        
        # Insert receipt content
        receipt_text.insert('1.0', receipt_content)
        receipt_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Buttons frame
        button_frame = tk.Frame(receipt_window, bg=self.colors['white'])
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def print_receipt():
            # Copy receipt to clipboard
            receipt_window.clipboard_clear()
            receipt_window.clipboard_append(receipt_content)
            
            # Try to print using system print dialog
            try:
                import tempfile
                import os
                import platform
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(receipt_content)
                    temp_file = f.name
                
                # Open print dialog based on OS
                system = platform.system()
                if system == 'Windows':
                    os.startfile(temp_file, 'print')
                elif system == 'Darwin':  # macOS
                    os.system(f'lpr {temp_file}')
                elif system == 'Linux':
                    os.system(f'lp {temp_file}')
                
                messagebox.showinfo("Print", "Receipt sent to printer!\nReceipt also copied to clipboard.")
            except Exception as e:
                messagebox.showinfo("Print", f"Receipt copied to clipboard!\nYou can paste it into any text editor to print.\n\n(Auto-print not available: {str(e)})")
        
        tk.Button(button_frame, text="🖨️ Print Receipt", command=print_receipt,
                 bg=self.colors['secondary'], fg=self.colors['white'],
                 font=("Arial", 11, "bold"), relief=tk.RAISED, bd=3).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        tk.Button(button_frame, text="✓ Close", command=receipt_window.destroy,
                 bg=self.colors['success'], fg=self.colors['white'],
                 font=("Arial", 11, "bold"), relief=tk.RAISED, bd=3).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    def process_payment_and_print(self):
        """Process payment and automatically print receipt"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to the cart first")
            return
        
        subtotal = sum(item['total'] for item in self.cart)
        discount = self.calculate_discount(subtotal)
        subtotal_after_discount = subtotal - discount
        tax = subtotal_after_discount * self.tax_rate
        total = subtotal_after_discount + tax
        
        payment_method = self.payment_var.get()
        cash_received = None
        change = None
        
        if payment_method == "Cash":
            cash_received = simpledialog.askfloat("Cash Payment",
                                                 f"Total: ${total:.2f}\nEnter cash received:",
                                                 minvalue=total)
            if cash_received is None:
                return
            
            change = cash_received - total
        
        # Update database
        customer_id = self.selected_customer[0] if self.selected_customer else None
        
        # Save transaction
        transaction_id = self.db.add_transaction(customer_id, total, subtotal, tax, discount,
                               payment_method, self.cart)
        
        # Update stock for products
        for item in self.cart:
            if item['type'] == 'product':
                self.db.update_stock(item['id'], item['quantity'])
        
        # Update customer points
        if self.selected_customer:
            points_earned = int(total)
            self.db.update_customer_points(customer_id, points_earned)
        
        # Generate receipt
        self.generate_receipt(transaction_id, subtotal, discount, tax, total, 
                            payment_method, cash_received, change)
        
        # Auto-print receipt
        self.auto_print_receipt(transaction_id, subtotal, discount, tax, total, 
                               payment_method, cash_received, change)
        
        # Show success message
        if payment_method == "Cash":
            messagebox.showinfo("Payment Successful",
                              f"Payment processed successfully!\n\n"
                              f"Total: ${total:.2f}\n"
                              f"Cash Received: ${cash_received:.2f}\n"
                              f"Change: ${change:.2f}\n\n"
                              f"Receipt has been sent to printer!")
        else:
            messagebox.showinfo("Payment Successful",
                              f"Payment processed successfully!\n\n"
                              f"Total: ${total:.2f}\n"
                              f"Payment Method: {payment_method}\n\n"
                              f"Receipt has been sent to printer!")
        
        # Reset
        self.cart = []
        self.update_cart_display()
        self.update_totals()
        self.load_products()
        self.load_customers()
    
    def auto_print_receipt(self, transaction_id, subtotal, discount, tax, total, payment_method, cash_received=None, change=None):
        """Automatically print receipt without showing window"""
        try:
            import tempfile
            import os
            import platform
            
            # Build receipt content
            receipt_content = "=" * 50 + "\n"
            receipt_content += "       PROFESSIONAL POS SYSTEM\n"
            receipt_content += "         SALES RECEIPT\n"
            receipt_content += "=" * 50 + "\n\n"
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            receipt_content += f"Date: {current_time}\n"
            receipt_content += f"Transaction ID: #{transaction_id}\n"
            
            if self.selected_customer:
                receipt_content += f"Customer: {self.selected_customer[1]}\n"
                receipt_content += f"Loyalty: {self.selected_customer[2]}\n"
                receipt_content += f"Points: {self.selected_customer[3]}\n"
            else:
                receipt_content += "Customer: Walk-in\n"
            
            receipt_content += "\n" + "-" * 50 + "\n"
            receipt_content += f"{'Item':<25} {'Qty':>5} {'Price':>8} {'Total':>10}\n"
            receipt_content += "-" * 50 + "\n"
            
            for item in self.cart:
                name = item['name'][:24]
                qty = item['quantity']
                price = item['price']
                item_total = item['total']
                receipt_content += f"{name:<25} {qty:>5} ${price:>7.2f} ${item_total:>9.2f}\n"
            
            receipt_content += "-" * 50 + "\n\n"
            receipt_content += f"{'Subtotal:':<40} ${subtotal:>8.2f}\n"
            
            if discount > 0:
                discount_percent = (discount / subtotal) * 100
                receipt_content += f"{'Discount (' + f'{discount_percent:.0f}%' + '):':<40} -${discount:>7.2f}\n"
            
            receipt_content += f"{'Tax (10%):':<40} ${tax:>8.2f}\n"
            receipt_content += "=" * 50 + "\n"
            receipt_content += f"{'TOTAL:':<40} ${total:>8.2f}\n"
            receipt_content += "=" * 50 + "\n\n"
            receipt_content += f"Payment Method: {payment_method}\n"
            
            if payment_method == "Cash" and cash_received is not None:
                receipt_content += f"Cash Received: ${cash_received:.2f}\n"
                receipt_content += f"Change: ${change:.2f}\n"
            
            if self.selected_customer:
                points_earned = int(total)
                new_points = self.selected_customer[3] + points_earned
                receipt_content += f"\nPoints Earned: {points_earned}\n"
                receipt_content += f"Total Points: {new_points}\n"
            
            receipt_content += "\n" + "=" * 50 + "\n"
            receipt_content += "     Thank you for your business!\n"
            receipt_content += "        Please come again!\n"
            receipt_content += "=" * 50 + "\n"
            
            # Create temporary file and print
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(receipt_content)
                temp_file = f.name
            
            # Send to printer
            system = platform.system()
            if system == 'Windows':
                os.startfile(temp_file, 'print')
            elif system == 'Darwin':  # macOS
                os.system(f'lpr {temp_file}')
            elif system == 'Linux':
                os.system(f'lp {temp_file}')
                
        except Exception as e:
            print(f"Auto-print error: {e}")
    
    def quick_payment(self):
        """Quick payment that directly generates receipt"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to the cart first")
            return
        
        subtotal = sum(item['total'] for item in self.cart)
        discount = self.calculate_discount(subtotal)
        subtotal_after_discount = subtotal - discount
        tax = subtotal_after_discount * self.tax_rate
        total = subtotal_after_discount + tax
        
        payment_method = self.payment_var.get()
        cash_received = None
        change = None
        
        if payment_method == "Cash":
            cash_received = simpledialog.askfloat("Cash Payment",
                                                 f"Total: ${total:.2f}\nEnter cash received:",
                                                 minvalue=total)
            if cash_received is None:
                return
            
            change = cash_received - total
        
        # Update database
        customer_id = self.selected_customer[0] if self.selected_customer else None
        
        # Save transaction
        transaction_id = self.db.add_transaction(customer_id, total, subtotal, tax, discount,
                               payment_method, self.cart)
        
        # Update stock for products
        for item in self.cart:
            if item['type'] == 'product':
                self.db.update_stock(item['id'], item['quantity'])
        
        # Update customer points
        if self.selected_customer:
            points_earned = int(total)
            self.db.update_customer_points(customer_id, points_earned)
        
        # Directly generate receipt
        self.generate_receipt(transaction_id, subtotal, discount, tax, total, 
                            payment_method, cash_received, change)
        
        # Reset cart
        self.cart = []
        self.update_cart_display()
        self.update_totals()
        self.load_products()
        self.load_customers()
    
    def process_payment_with_receipt(self):
        """Legacy method - redirects to quick payment"""
        self.quick_payment()
    
    def process_payment(self):
        """Legacy method - redirects to quick payment"""
        self.quick_payment()
    
    def open_return_window(self):
        return_window = tk.Toplevel(self.root)
        return_window.title("Process Return")
        return_window.geometry("500x400")
        return_window.configure(bg=self.colors['white'])
        
        tk.Label(return_window, text="Process Return/Refund",
                font=("Arial", 16, "bold"), bg=self.colors['white'],
                fg=self.colors['primary']).pack(pady=20)
        
        tk.Label(return_window, text="Enter Transaction ID:",
                font=("Arial", 12), bg=self.colors['white']).pack(pady=10)
        
        transaction_id_entry = tk.Entry(return_window, font=("Arial", 12), width=20)
        transaction_id_entry.pack(pady=5)
        
        def process_return():
            try:
                transaction_id = int(transaction_id_entry.get())
                if self.db.process_return(transaction_id):
                    messagebox.showinfo("Success", "Return processed successfully!")
                    self.load_products()
                    return_window.destroy()
                else:
                    messagebox.showerror("Error", "Transaction not found")
            except ValueError:
                messagebox.showerror("Error", "Invalid transaction ID")
        
        tk.Button(return_window, text="Process Return", command=process_return,
                 bg=self.colors['success'], fg=self.colors['white'],
                 font=("Arial", 12, "bold"), relief=tk.RAISED, bd=3).pack(pady=20)

def main():
    root = tk.Tk()
    app = POSSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()