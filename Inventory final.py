import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class StockMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Level Monitor System")
        self.root.geometry("1250x700")
        self.root.configure(bg='#f0f0f0')
        
        # Database setup
        self.db_name = "stock_data.db"
        self.init_db()
        
        # Load items from DB
        self.items = self.load_data()
        
        # GUI setup
        self.create_widgets()
        self.refresh_display()
        
    # ---------- DATABASE FUNCTIONS ----------
    def init_db(self):
        """Initialize database and create table if not exists."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                quantity INTEGER,
                min_level INTEGER,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                unit TEXT,
                price REAL,
                description TEXT,
                is_service INTEGER DEFAULT 0,
                duration TEXT,
                service_cost REAL
            )
        """)
        conn.commit()
        conn.close()

    def load_data(self):
        """Load all items from the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, sku, quantity, min_level, category, subcategory, unit,
                   price, description, is_service, duration, service_cost
            FROM stock_items
        """)
        rows = cursor.fetchall()
        conn.close()
        items = []
        for r in rows:
            items.append({
                'name': r[0],
                'sku': r[1],
                'quantity': r[2],
                'min_level': r[3],
                'category': r[4],
                'subcategory': r[5],
                'unit': r[6],
                'price': r[7],
                'description': r[8],
                'is_service': bool(r[9]),
                'duration': r[10],
                'service_cost': r[11]
            })
        return items

    def save_to_db(self, item, update=False):
        """Insert or update an item in the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if update:
            cursor.execute("""
                UPDATE stock_items
                SET name=?, quantity=?, min_level=?, category=?, subcategory=?, unit=?,
                    price=?, description=?, is_service=?, duration=?, service_cost=?
                WHERE sku=?
            """, (item['name'], item['quantity'], item['min_level'], item['category'],
                  item['subcategory'], item['unit'], item['price'], item['description'],
                  int(item['is_service']), item['duration'], item['service_cost'], item['sku']))
        else:
            cursor.execute("""
                INSERT INTO stock_items (name, sku, quantity, min_level, category, subcategory,
                                         unit, price, description, is_service, duration, service_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item['name'], item['sku'], item['quantity'], item['min_level'],
                  item['category'], item['subcategory'], item['unit'], item['price'],
                  item['description'], int(item['is_service']), item['duration'], item['service_cost']))
        conn.commit()
        conn.close()

    def delete_from_db(self, sku):
        """Delete an item by SKU."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stock_items WHERE sku=?", (sku,))
        conn.commit()
        conn.close()
    
    # ---------- GUI CREATION ----------
    def create_widgets(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x', padx=10, pady=10)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="Stock Level Monitor System", 
                 font=('Arial', 24, 'bold'), bg='#2c3e50', fg='white').pack(pady=20)
        
        # Statistics Frame
        stats_frame = tk.Frame(self.root, bg='#f0f0f0')
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.total_label = self.create_stat_card(stats_frame, "Total Items", "0", '#3498db', 0)
        self.low_label = self.create_stat_card(stats_frame, "Low Stock", "0", '#e67e22', 1)
        self.critical_label = self.create_stat_card(stats_frame, "Critical", "0", '#e74c3c', 2)
        self.healthy_label = self.create_stat_card(stats_frame, "Healthy", "0", '#27ae60', 3)
        
        # Alert Frame
        self.alert_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.alert_frame.pack(fill='x', padx=10, pady=5)
        
        # Control Frame
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(control_frame, text="Filter:", font=('Arial', 10), bg='#f0f0f0').pack(side='left', padx=5)
        self.filter_var = tk.StringVar(value='all')
        for text, val in [("All Items", 'all'), ("Low Stock", 'low'), ("Critical", 'critical')]:
            tk.Radiobutton(control_frame, text=text, variable=self.filter_var, value=val,
                           command=self.refresh_display, bg='#f0f0f0').pack(side='left', padx=5)
        
        tk.Button(control_frame, text="➕ Add Item/Service", command=self.add_item,
                  bg='#3498db', fg='white', font=('Arial', 10, 'bold'), padx=15, pady=5).pack(side='right', padx=5)
        
        # Table Frame
        table_frame = tk.Frame(self.root, bg='white')
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        columns = ('Status', 'Item', 'SKU', 'Category', 'Subcategory', 'Quantity', 'Min Level', 'Unit', 'Price', 'Stock %')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column('Status', width=80, anchor='center')
        self.tree.column('Item', width=150)
        self.tree.column('SKU', width=100)
        self.tree.column('Category', width=120)
        self.tree.column('Subcategory', width=120)
        self.tree.column('Quantity', width=100, anchor='center')
        self.tree.column('Min Level', width=100, anchor='center')
        self.tree.column('Unit', width=80, anchor='center')
        self.tree.column('Price', width=100, anchor='center')
        self.tree.column('Stock %', width=100, anchor='center')
        
        self.tree.tag_configure('critical', background='#ffcccc')
        self.tree.tag_configure('low', background='#ffe6cc')
        self.tree.tag_configure('good', background='#ccffcc')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-1>', self.edit_item)
        
    def create_stat_card(self, parent, title, value, color, column):
        frame = tk.Frame(parent, bg=color, relief='raised', bd=2)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky='ew')
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(frame, text=title, font=('Arial', 10), bg=color, fg='white').pack(pady=5)
        label = tk.Label(frame, text=value, font=('Arial', 20, 'bold'), bg=color, fg='white')
        label.pack(pady=5)
        return label
    
    # ---------- CORE LOGIC ----------
    def get_stock_status(self, item):
        if item['is_service']:
            return 'SERVICE', 'good'
        if item['quantity'] is None or item['min_level'] is None:
            return 'UNKNOWN', 'low'
        ratio = item['quantity'] / item['min_level']
        if ratio <= 0.5:
            return 'CRITICAL', 'critical'
        elif ratio <= 1.0:
            return 'LOW', 'low'
        else:
            return 'GOOD', 'good'
            
    def get_filtered_items(self):
        filter_type = self.filter_var.get()
        if filter_type == 'all':
            return self.items
        elif filter_type == 'low':
            return [i for i in self.items if not i['is_service'] and i['quantity'] <= i['min_level']]
        elif filter_type == 'critical':
            return [i for i in self.items if not i['is_service'] and i['quantity'] <= i['min_level'] * 0.5]
        return self.items
        
    def refresh_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        total = len(self.items)
        low_count = len([i for i in self.items if not i['is_service'] and i['quantity'] <= i['min_level']])
        critical_count = len([i for i in self.items if not i['is_service'] and i['quantity'] <= i['min_level'] * 0.5])
        healthy_count = total - low_count
        
        self.total_label.config(text=str(total))
        self.low_label.config(text=str(low_count))
        self.critical_label.config(text=str(critical_count))
        self.healthy_label.config(text=str(healthy_count))
        
        for widget in self.alert_frame.winfo_children():
            widget.destroy()
        if critical_count > 0:
            alert = tk.Frame(self.alert_frame, bg='#e74c3c', relief='raised', bd=2)
            alert.pack(fill='x', pady=5)
            tk.Label(alert, text=f"⚠️ CRITICAL ALERT: {critical_count} item(s) at critical levels!",
                     font=('Arial', 12, 'bold'), bg='#e74c3c', fg='white').pack(pady=10)
        
        for item in self.get_filtered_items():
            status, tag = self.get_stock_status(item)
            percentage = 100 if item['is_service'] else min((item['quantity'] / item['min_level']) * 100, 100)
            self.tree.insert('', 'end', values=(
                status, item['name'], item['sku'], item['category'],
                item['subcategory'], item['quantity'] if not item['is_service'] else '',
                item['min_level'] if not item['is_service'] else '', item['unit'] if not item['is_service'] else '',
                f"${item['price']:.2f}" if item['price'] else '',
                f"{percentage:.0f}%" if not item['is_service'] else ''
            ), tags=(tag,))
            
    # ---------- ITEM DIALOGS ----------
    def add_item(self):
        self.open_item_dialog()
        
    def edit_item(self, event=None):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select an item to edit")
            return
        item_values = self.tree.item(selection[0])['values']
        item = next((i for i in self.items if i['sku'] == item_values[2]), None)
        if item:
            self.open_item_dialog(item)
            
    def delete_item(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select an item to delete")
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this item?"):
            item_values = self.tree.item(selection[0])['values']
            sku = item_values[2]
            self.delete_from_db(sku)
            self.items = [i for i in self.items if i['sku'] != sku]
            self.refresh_display()
            
    def open_item_dialog(self, item=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Item/Service" if item is None else "Edit Item/Service")
        dialog.geometry("450x500")
        dialog.configure(bg='#ecf0f1')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # --- Fields ---
        fields = []
        labels = ['Item Name:', 'SKU:', 'Quantity:', 'Min Level:', 'Category:', 'Subcategory:', 'Unit:', 'Price:', 'Description:', 'Duration:', 'Service Cost:']
        keys = ['name', 'sku', 'quantity', 'min_level', 'category', 'subcategory', 'unit', 'price', 'description', 'duration', 'service_cost']
        
        for i, (label, key) in enumerate(zip(labels, keys)):
            tk.Label(dialog, text=label, bg='#ecf0f1', font=('Arial', 10)).grid(row=i, column=0, padx=10, pady=5, sticky='e')
            if key in ['unit']:
                field = ttk.Combobox(dialog, values=['pcs', 'kg', 'ltr', 'box'], width=27)
                field.set(item[key] if item else 'pcs')
            else:
                field = tk.Entry(dialog, width=30, font=('Arial', 10))
                if item and item.get(key) is not None:
                    field.insert(0, str(item[key]))
            field.grid(row=i, column=1, padx=10, pady=5)
            fields.append(field)
        
        is_service_var = tk.IntVar(value=1 if item and item.get('is_service') else 0)
        is_service_cb = tk.Checkbutton(dialog, text="Is Service?", variable=is_service_var, bg='#ecf0f1')
        is_service_cb.grid(row=11, column=0, columnspan=2, pady=10)
        
        def toggle_service_fields():
            if is_service_var.get():
                # Service → hide quantity/min_level/unit
                for idx in [2,3,6]:
                    fields[idx].config(state='disabled')
            else:
                for idx in [2,3,6]:
                    fields[idx].config(state='normal')
        is_service_cb.config(command=toggle_service_fields)
        toggle_service_fields()
        
        def save():
            try:
                name = fields[0].get().strip()
                sku = fields[1].get().strip()
                quantity = int(fields[2].get()) if not is_service_var.get() else None
                min_level = int(fields[3].get()) if not is_service_var.get() else None
                category = fields[4].get().strip()
                subcategory = fields[5].get().strip()
                unit = fields[6].get().strip() if not is_service_var.get() else ''
                price = float(fields[7].get()) if fields[7].get() else 0
                description = fields[8].get().strip()
                duration = fields[9].get().strip() if is_service_var.get() else ''
                service_cost = float(fields[10].get()) if is_service_var.get() and fields[10].get() else 0
                is_service = bool(is_service_var.get())
                
                if not all([name, sku, category, subcategory]):
                    messagebox.showerror("Error", "Please fill in all required fields")
                    return
                
                new_item = {
                    'name': name, 'sku': sku, 'quantity': quantity, 'min_level': min_level,
                    'category': category, 'subcategory': subcategory, 'unit': unit,
                    'price': price, 'description': description,
                    'is_service': is_service, 'duration': duration, 'service_cost': service_cost
                }
                
                if item:
                    self.save_to_db(new_item, update=True)
                    idx = next((i for i, x in enumerate(self.items) if x['sku'] == item['sku']), None)
                    if idx is not None:
                        self.items[idx] = new_item
                else:
                    if any(i['sku'] == sku for i in self.items):
                        messagebox.showerror("Error", "SKU already exists")
                        return
                    self.save_to_db(new_item)
                    self.items.append(new_item)
                
                self.refresh_display()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Enter valid numbers for quantity, min level, price, or service cost")
        
        btn_frame = tk.Frame(dialog, bg='#ecf0f1')
        btn_frame.grid(row=12, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="Save", command=save, bg='#27ae60', fg='white',
                 font=('Arial', 10, 'bold'), padx=20, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg='#95a5a6', fg='white',
                 font=('Arial', 10, 'bold'), padx=20, pady=5).pack(side='left', padx=5)
    
    def show_context_menu(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Edit", command=self.edit_item)
        menu.add_command(label="Delete", command=self.delete_item)
        menu.post(event.x_root, event.y_root)


if __name__ == '__main__':
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()
