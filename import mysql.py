import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import csv
from tkcalendar import DateEntry

# ---------- Theme colors (Pastel Lavender P2) ----------
BG = "#FBF9FD"           # app background (very light)
CARD = "#F5F2FA"         # card background
ACCENT = "#C9B6E4"       # pastel lavender (primary accent)
ACCENT_DARK = "#A884D0"  # darker accent for buttons
TEXT = "#2F2F2F"
SUCCESS = "#6FCF97"
ERROR = "#FF6B6B"
WARN = "#FFD28A"

PAD_X = 16
PAD_Y = 12
CARD_PAD = 12

# ---------- Utility: small rounded-like button using Canvas ----------
def create_tile(parent, text, emoji, command=None, width=22, height=5, bg=ACCENT, fg="white"):
    """Create a large tile button with emoji and text."""
    btn = tk.Button(parent, text=f"{emoji}\n\n{text}", font=("Segoe UI", 14, "bold"),
                    bg=bg, fg=fg, bd=0, relief="flat", activebackground=ACCENT_DARK,
                    command=command, wraplength=200, justify="center")
    btn.configure(height=height, width=width)
    return btn

class TechHavenDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("TechHaven POS — TechHaven Retail Dashboard")
        self.root.geometry("1200x750")
        self.root.configure(bg=BG)

        # Database connect
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="pythonuser",
                password="MyStrongPassword123!",
                database="techhaven"
            )
            self.cursor = self.db.cursor(buffered=True)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error connecting to MySQL:\n{err}")
            self.root.destroy()
            return

        # fonts
        self.h1 = ("Segoe UI", 18, "bold")
        self.h2 = ("Segoe UI", 14, "bold")
        self.font_main = ("Segoe UI", 11)

        # Top header
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=PAD_X, pady=(PAD_Y//2, 0))

        tk.Label(header, text="💜 TechHaven POS", font=self.h1, bg=BG, fg=TEXT).pack(side="left")
       

        # Right-side small controls
        ctrl = tk.Frame(header, bg=BG)
        ctrl.pack(side="right")
        tk.Button(ctrl, text="Home", bg=CARD, fg=TEXT, bd=0, padx=10, command=self.show_home).pack(side="left", padx=6)
        tk.Button(ctrl, text="Sales", bg=CARD, fg=TEXT, bd=0, padx=10, command=self.show_sales_view).pack(side="left", padx=6)
        tk.Button(ctrl, text="Products", bg=CARD, fg=TEXT, bd=0, padx=10, command=self.show_products_view).pack(side="left", padx=6)
        tk.Button(ctrl, text="Reports", bg=CARD, fg=TEXT, bd=0, padx=10, command=self.show_reports_view).pack(side="left", padx=6)

        # Main container
        self.container = tk.Frame(self.root, bg=BG)
        self.container.pack(expand=True, fill="both", padx=PAD_X, pady=PAD_Y)

        # Build views
        self.build_home_view()
        self.build_sales_view()
        self.build_products_view()
        self.build_reports_view()

        # Start on home
        self.show_home()

    # ------------------ View Builders ------------------
    def build_home_view(self):
        self.home_frame = tk.Frame(self.container, bg=BG)
        # Metrics row
        metrics = tk.Frame(self.home_frame, bg=BG)
        metrics.pack(fill="x", pady=(0, CARD_PAD))

        self.card_total_sales = self.make_card(metrics, "Total Sales Today", "$0.00")
        self.card_low_stock = self.make_card(metrics, "Products Low Stock", "0")
        self.card_total_products = self.make_card(metrics, "Total Products", "0")
        self.card_recent_sale = self.make_card(metrics, "Recent Sale", "—")

        # Tiles
        tiles = tk.Frame(self.home_frame, bg=BG)
        tiles.pack(pady=10)

        tile_sales = create_tile(tiles, "Open Sales", "💰", command=self.show_sales_view, bg=ACCENT)
        tile_products = create_tile(tiles, "Products", "📦", command=self.show_products_view, bg=ACCENT)
        tile_reports = create_tile(tiles, "Reports", "📑", command=self.show_reports_view, bg=ACCENT)

        tile_sales.grid(row=0, column=0, padx=20, pady=10)
        tile_products.grid(row=0, column=1, padx=20, pady=10)
        tile_reports.grid(row=0, column=2, padx=20, pady=10)

        # Quick recent sales list
        recent_frame = tk.Frame(self.home_frame, bg=BG)
        recent_frame.pack(fill="both", expand=True, pady=(20,0))

        tk.Label(recent_frame, text="Recent Sales", font=self.h2, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,8))
        self.recent_tree = ttk.Treeview(recent_frame, columns=("ID","Customer","Total","Date"), show="headings", height=6)
        for col,txt in [("ID","Sale ID"),("Customer","Customer"),("Total","Total"),("Date","Date")]:
            self.recent_tree.heading(col, text=txt)
            self.recent_tree.column(col, anchor="center")
        self.recent_tree.pack(expand=True, fill="both")
        self.style_treeview(self.recent_tree)

    def build_sales_view(self):
        self.sales_frame = tk.Frame(self.container, bg=BG)

        top = tk.Frame(self.sales_frame, bg=BG)
        top.pack(fill="x", pady=(0,10))

        tk.Label(top, text="Sales", font=self.h2, bg=BG, fg=TEXT).pack(side="left")
        tk.Button(top, text="Back Home", bg=CARD, bd=0, command=self.show_home).pack(side="right", padx=6)
        tk.Button(top, text="Add Sale", bg=ACCENT, fg="white", bd=0, padx=12, command=self.open_add_sale).pack(side="right", padx=6)
        tk.Button(top, text="Delete Sale", bg=ERROR, fg="white", bd=0, padx=12, command=self.delete_sale).pack(side="right", padx=6)
        tk.Button(top, text="View Details", bg=ACCENT_DARK, fg="white", bd=0, padx=12, command=self.view_sale_details).pack(side="right", padx=6)

        # Sales table
        self.sales_table = ttk.Treeview(self.sales_frame, columns=("ID", "Customer", "Total", "Date"), show="headings")
        self.sales_table.heading("ID", text="Sale ID")
        self.sales_table.heading("Customer", text="Customer")
        self.sales_table.heading("Total", text="Total Amount")
        self.sales_table.heading("Date", text="Sale Date")
        self.sales_table.pack(expand=True, fill="both")
        self.style_treeview(self.sales_table)
        self.load_sales()

    def build_products_view(self):
        self.products_frame = tk.Frame(self.container, bg=BG)

        top = tk.Frame(self.products_frame, bg=BG)
        top.pack(fill="x", pady=(0,10))

        tk.Label(top, text="Products", font=self.h2, bg=BG, fg=TEXT).pack(side="left")
        tk.Button(top, text="Back Home", bg=CARD, bd=0, command=self.show_home).pack(side="right", padx=6)
        tk.Button(top, text="Add Product", bg=ACCENT, fg="white", bd=0, padx=12, command=self.add_product).pack(side="right", padx=6)
        tk.Button(top, text="Edit Product", bg=WARN, fg="black", bd=0, padx=12, command=self.edit_product).pack(side="right", padx=6)
        tk.Button(top, text="Delete Product", bg=ERROR, fg="white", bd=0, padx=12, command=self.delete_product).pack(side="right", padx=6)

        # Products table
        self.products_table = ttk.Treeview(self.products_frame, columns=("ID","Name","Price","Qty"), show="headings")
        self.products_table.heading("ID", text="Product ID")
        self.products_table.heading("Name", text="Product Name")
        self.products_table.heading("Price", text="Price")
        self.products_table.heading("Qty", text="Quantity")
        self.products_table.pack(expand=True, fill="both")
        self.style_treeview(self.products_table)
        self.load_products()

    def build_reports_view(self):
        self.reports_frame = tk.Frame(self.container, bg=BG)

        top = tk.Frame(self.reports_frame, bg=BG)
        top.pack(fill="x", pady=(0,10))
        tk.Label(top, text="Reports", font=self.h2, bg=BG, fg=TEXT).pack(side="left")
        tk.Button(top, text="Back Home", bg=CARD, bd=0, command=self.show_home).pack(side="right", padx=6)

        # Date pickers + actions
        rp = tk.Frame(self.reports_frame, bg=BG)
        rp.pack(fill="x", pady=(0,10))

        tk.Label(rp, text="Start Date:", bg=BG).grid(row=0, column=0, padx=5, pady=5)
        self.start_entry = DateEntry(rp, date_pattern='yyyy-mm-dd')
        self.start_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(rp, text="End Date:", bg=BG).grid(row=0, column=2, padx=5, pady=5)
        self.end_entry = DateEntry(rp, date_pattern='yyyy-mm-dd')
        self.end_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(rp, text="Generate Report", bg=ACCENT, fg="white", bd=0, command=self.generate_date_range_report).grid(row=0, column=4, padx=8)
        tk.Button(rp, text="Export CSV", bg=SUCCESS, fg="white", bd=0, command=self.export_date_range_report).grid(row=0, column=5, padx=8)

        # Report table
        self.report_table = ttk.Treeview(self.reports_frame, columns=("ID","Customer","Total","Date"), show="headings")
        for col,txt in [("ID","Sale ID"),("Customer","Customer"),("Total","Total"),("Date","Date")]:
            self.report_table.heading(col, text=txt)
        self.report_table.pack(expand=True, fill="both")
        self.style_treeview(self.report_table)

    # ------------------ Small UI helpers ------------------
    def make_card(self, parent, title, value):
        card = tk.Frame(parent, bg=CARD, bd=0, relief="ridge", padx=16, pady=12)
        card.pack(side="left", expand=True, fill="both", padx=8)
        tk.Label(card, text=title, bg=CARD, fg="gray", font=self.font_main).pack(anchor="w")
        lbl = tk.Label(card, text=value, bg=CARD, fg=TEXT, font=("Segoe UI", 20, "bold"))
        lbl.pack(anchor="w", pady=(10,0))
        return lbl

    def style_treeview(self, tree):
        # light alternating rows
        tree.tag_configure('oddrow', background="#FFFFFF")
        tree.tag_configure('evenrow', background="#F7F5FB")

    # ------------------ Navigation ------------------
    def hide_all(self):
        for f in (self.home_frame, self.sales_frame, self.products_frame, self.reports_frame):
            f.pack_forget()

    def show_home(self):
        self.hide_all()
        self.home_frame.pack(expand=True, fill="both")
        self.refresh_home()

    def show_sales_view(self):
        self.hide_all()
        self.sales_frame.pack(expand=True, fill="both")
        self.load_sales()

    def show_products_view(self):
        self.hide_all()
        self.products_frame.pack(expand=True, fill="both")
        self.load_products()

    def show_reports_view(self):
        self.hide_all()
        self.reports_frame.pack(expand=True, fill="both")

    # ------------------ Data load / metrics ------------------
    def load_sales(self):
        for row in self.sales_table.get_children():
            self.sales_table.delete(row)
        self.cursor.execute("SELECT * FROM sales ORDER BY sale_date DESC")
        rows = self.cursor.fetchall()
        for idx,row in enumerate(rows):
            tag = "evenrow" if idx%2==0 else "oddrow"
            self.sales_table.insert("",tk.END,values=row,tags=(tag,))

    def load_products(self):
        for row in self.products_table.get_children():
            self.products_table.delete(row)
        self.cursor.execute("SELECT * FROM products")
        rows = self.cursor.fetchall()
        for idx,row in enumerate(rows):
            tag = "evenrow" if idx%2==0 else "oddrow"
            self.products_table.insert("",tk.END,values=row,tags=(tag,))

    def refresh_home(self):
        # Total sales today
        today = date.today()
        try:
            self.cursor.execute("SELECT IFNULL(SUM(total_amount),0) FROM sales WHERE sale_date=%s", (today,))
            total_today = self.cursor.fetchone()[0] or 0.0
            self.card_total_sales.config(text=f"${total_today:,.2f}")
        except Exception:
            self.card_total_sales.config(text="—")

        # Low stock (<5)
        try:
            self.cursor.execute("SELECT COUNT(*) FROM products WHERE quantity <= 5")
            low = self.cursor.fetchone()[0]
            self.card_low_stock.config(text=str(low))
        except Exception:
            self.card_low_stock.config(text="—")

        # Total products
        try:
            self.cursor.execute("SELECT COUNT(*) FROM products")
            tp = self.cursor.fetchone()[0]
            self.card_total_products.config(text=str(tp))
        except Exception:
            self.card_total_products.config(text="—")

        # Recent sale
        try:
            self.cursor.execute("SELECT sale_id, customer_name, total_amount, sale_date FROM sales ORDER BY sale_date DESC, sale_id DESC LIMIT 1")
            row = self.cursor.fetchone()
            if row:
                sid, cust, tot, sdate = row
                self.card_recent_sale.config(text=f"{cust} — ${tot:.2f}")
            else:
                self.card_recent_sale.config(text="—")
        except Exception:
            self.card_recent_sale.config(text="—")

        # Populate recent sales table
        for r in self.recent_tree.get_children():
            self.recent_tree.delete(r)
        try:
            self.cursor.execute("SELECT sale_id, customer_name, total_amount, sale_date FROM sales ORDER BY sale_date DESC LIMIT 8")
            rows = self.cursor.fetchall()
            for idx,row in enumerate(rows):
                tag = "evenrow" if idx%2==0 else "oddrow"
                self.recent_tree.insert("", tk.END, values=row, tags=(tag,))
        except Exception:
            pass

    # ------------------ Sale CRUD ------------------
    def open_add_sale(self):
        win = tk.Toplevel(self.root)
        win.title("Add New Sale")
        win.geometry("900x520")
        win.configure(bg=BG)

        tk.Label(win, text="Add New Sale", font=self.h2, bg=BG).pack(pady=8)

        # Customer + date
        frm = tk.Frame(win, bg=BG)
        frm.pack(fill="x", padx=20)
        tk.Label(frm, text="Customer Name:", bg=BG).grid(row=0, column=0, sticky="w")
        customer_entry = tk.Entry(frm, font=self.font_main, width=30)
        customer_entry.grid(row=0, column=1, padx=10, pady=6)

        tk.Label(frm, text="Sale Date:", bg=BG).grid(row=0, column=2, sticky="w")
        date_entry = DateEntry(frm, date_pattern='yyyy-mm-dd')
        date_entry.grid(row=0, column=3, padx=10, pady=6)

        tk.Label(win, text="Select Products", font=self.font_main, bg=BG).pack(anchor="w", padx=20)

        # Product list with horizontal scrolling
        canvas = tk.Canvas(win, bg=BG, height=260)
        canvas.pack(fill="x", padx=20)
        hsb = tk.Scrollbar(win, orient="horizontal", command=canvas.xview)
        hsb.pack(fill="x", padx=20)
        canvas.configure(xscrollcommand=hsb.set)
        frame_inner = tk.Frame(canvas, bg=BG)
        canvas.create_window((0,0), window=frame_inner, anchor="nw")

        self.cursor.execute("SELECT product_id, product_name, price, quantity FROM products")
        products = self.cursor.fetchall()
        product_vars = []
        qty_vars = []
        col = 0
        for pid, name, price, qty in products:
            var = tk.IntVar()
            product_vars.append((var, pid, price))
            box = tk.Frame(frame_inner, bg=CARD, padx=8, pady=8)
            box.grid(row=0, column=col, padx=8, pady=8)
            tk.Checkbutton(box, text=f"{name}\n${price:.2f}\nStock: {qty}", variable=var, font=("Segoe UI",10), bg=CARD, wraplength=150, justify="center").pack()
            tk.Label(box, text="Qty:", bg=CARD).pack(pady=(6,0))
            qty_var = tk.IntVar(value=1)
            qty_vars.append(qty_var)
            tk.Entry(box, textvariable=qty_var, width=4).pack()
            col += 1

        frame_inner.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        def save_sale():
            customer = customer_entry.get().strip()
            sale_date_val = date_entry.get_date()
            if not customer:
                messagebox.showerror("Error","Enter customer name")
                return
            total_amount = 0
            items = []
            for (var,pid,price), qty_var in zip(product_vars, qty_vars):
                if var.get()==1:
                    quantity = qty_var.get()
                    if quantity<=0:
                        messagebox.showerror("Error","Quantity must be >0")
                        return
                    total_amount += price*quantity
                    items.append((pid, quantity))
            if not items:
                messagebox.showerror("Error","Select at least one product")
                return
            try:
                self.cursor.execute("INSERT INTO sales (customer_name,total_amount,sale_date) VALUES (%s,%s,%s)",
                                    (customer,total_amount,sale_date_val))
                sale_id = self.cursor.lastrowid
                for pid,quantity in items:
                    self.cursor.execute("INSERT INTO sale_items (sale_id,product_id,quantity_sold) VALUES (%s,%s,%s)",
                                        (sale_id,pid,quantity))
                    self.cursor.execute("UPDATE products SET quantity=quantity-%s WHERE product_id=%s",(quantity,pid))
                self.db.commit()
            except mysql.connector.Error as err:
                self.db.rollback()
                messagebox.showerror("Database Error", f"Failed to save sale:\n{err}")
                return
            messagebox.showinfo("Saved","Sale added successfully")
            win.destroy()
            self.load_sales()
            self.load_products()
            self.refresh_home()

        tk.Button(win, text="Save Sale", bg=ACCENT_DARK, fg="white", bd=0, padx=12, command=save_sale).pack(pady=12)

    def delete_sale(self):
        selected_items = self.sales_table.selection()
        if not selected_items:
            messagebox.showerror("Error","Select sale(s) to delete")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete selected sale(s)? This will restore product stock."):
            return
        try:
            for item in selected_items:
                data = self.sales_table.item(item, "values")
                sale_id = data[0]
                self.cursor.execute("SELECT product_id, quantity_sold FROM sale_items WHERE sale_id=%s", (sale_id,))
                sold_rows = self.cursor.fetchall()
                for product_id, qty_sold in sold_rows:
                    self.cursor.execute("UPDATE products SET quantity = quantity + %s WHERE product_id = %s",
                                        (qty_sold, product_id))
                self.cursor.execute("DELETE FROM sale_items WHERE sale_id=%s", (sale_id,))
                self.cursor.execute("DELETE FROM sales WHERE sale_id=%s", (sale_id,))
            self.db.commit()
            messagebox.showinfo("Deleted","Selected sale(s) deleted and stock restored.")
            self.load_sales()
            self.load_products()
            self.refresh_home()
        except mysql.connector.Error as err:
            self.db.rollback()
            messagebox.showerror("Error", f"Cannot delete sale(s):\n{err}")

    def view_sale_details(self):
        selected = self.sales_table.selection()
        if not selected:
            messagebox.showerror("Error","Select sale to view details")
            return
        # take first selected
        data = self.sales_table.item(selected[0], "values")
        sale_id = data[0]
        customer = data[1]
        win = tk.Toplevel(self.root)
        win.title(f"Sale Details - {customer}")
        win.geometry("700x400")
        tree = ttk.Treeview(win, columns=("Product","Price","Quantity","Total"), show="headings")
        for col, text in [("Product","Product"),("Price","Price"),("Quantity","Quantity"),("Total","Total")]:
            tree.heading(col, text=text)
        tree.pack(expand=True, fill="both", padx=10, pady=10)
        try:
            self.cursor.execute("SELECT p.product_name, p.price, si.quantity_sold FROM sale_items si JOIN products p ON si.product_id=p.product_id WHERE si.sale_id=%s",(sale_id,))
            rows = self.cursor.fetchall()
            for r in rows:
                pname, price, qty = r
                tree.insert("", tk.END, values=(pname, f"${price:.2f}", qty, f"${price*qty:.2f}"))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load sale details:\n{e}")

    # ------------------ Product CRUD ------------------
    def add_product(self):
        win = tk.Toplevel(self.root)
        win.title("Add Product")
        win.geometry("360x280")
        tk.Label(win, text="Add Product", font=self.h2).pack(pady=8)

        frm = tk.Frame(win)
        frm.pack(padx=12, pady=6)
        tk.Label(frm, text="Product Name:").grid(row=0, column=0, sticky="w")
        name = tk.Entry(frm, width=30)
        name.grid(row=0, column=1, padx=6, pady=6)
        tk.Label(frm, text="Price:").grid(row=1, column=0, sticky="w")
        price = tk.Entry(frm, width=20)
        price.grid(row=1, column=1, padx=6, pady=6)
        tk.Label(frm, text="Quantity:").grid(row=2, column=0, sticky="w")
        qty = tk.Entry(frm, width=10)
        qty.grid(row=2, column=1, padx=6, pady=6)

        def save():
            n = name.get().strip()
            try:
                p = float(price.get())
                q = int(qty.get())
            except:
                messagebox.showerror("Error","Invalid price or quantity")
                return
            if not n:
                messagebox.showerror("Error","Enter product name")
                return
            try:
                self.cursor.execute("INSERT INTO products (product_name,price,quantity) VALUES (%s,%s,%s)", (n,p,q))
                self.db.commit()
            except mysql.connector.Error as err:
                self.db.rollback()
                messagebox.showerror("Error", f"Could not add product:\n{err}")
                return
            messagebox.showinfo("Saved","Product added")
            win.destroy()
            self.load_products()
            self.refresh_home()

        tk.Button(win, text="Save", bg=ACCENT_DARK, fg="white", bd=0, padx=12, command=save).pack(pady=10)

    def edit_product(self):
        selected = self.products_table.selection()
        if not selected:
            messagebox.showerror("Error","Select product to edit")
            return
        data = self.products_table.item(selected[0], "values")
        pid, name_val, price_val, qty_val = data

        win = tk.Toplevel(self.root)
        win.title("Edit Product")
        win.geometry("360x300")
        tk.Label(win, text="Edit Product", font=self.h2).pack(pady=8)

        frm = tk.Frame(win)
        frm.pack(padx=12, pady=6)
        tk.Label(frm, text="Product Name:").grid(row=0, column=0, sticky="w")
        name = tk.Entry(frm, width=30); name.grid(row=0, column=1, padx=6, pady=6); name.insert(0, name_val)
        tk.Label(frm, text="Price:").grid(row=1, column=0, sticky="w")
        price = tk.Entry(frm, width=20); price.grid(row=1, column=1, padx=6, pady=6); price.insert(0, price_val)
        tk.Label(frm, text="Quantity:").grid(row=2, column=0, sticky="w")
        qty = tk.Entry(frm, width=10); qty.grid(row=2, column=1, padx=6, pady=6); qty.insert(0, qty_val)

        def save():
            try:
                new_name = name.get().strip()
                new_price = float(price.get())
                new_qty = int(qty.get())
            except:
                messagebox.showerror("Error","Invalid price or quantity")
                return
            try:
                self.cursor.execute("UPDATE products SET product_name=%s, price=%s, quantity=%s WHERE product_id=%s",
                                    (new_name,new_price,new_qty,pid))
                self.db.commit()
            except mysql.connector.Error as err:
                self.db.rollback()
                messagebox.showerror("Error", f"Could not update product:\n{err}")
                return
            messagebox.showinfo("Saved","Product updated")
            win.destroy()
            self.load_products()
            self.refresh_home()

        tk.Button(win, text="Save", bg=ACCENT_DARK, fg="white", bd=0, padx=12, command=save).pack(pady=10)

    def delete_product(self):
        selected_items = self.products_table.selection()
        if not selected_items:
            messagebox.showerror("Error","Select product(s) to delete")
            return
        product_ids = [self.products_table.item(item, "values")[0] for item in selected_items]

        # check usage
        used = []
        try:
            for pid in product_ids:
                self.cursor.execute("SELECT COUNT(*) FROM sale_items WHERE product_id=%s", (pid,))
                cnt = self.cursor.fetchone()[0]
                if cnt > 0:
                    used.append(pid)
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Database error while checking product usage:\n{err}")
            return

        if used:
            messagebox.showerror("Cannot Delete", f"Product(s) {', '.join(map(str, used))} are present in sales and cannot be deleted.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected product(s)?"):
            return

        try:
            for pid in product_ids:
                self.cursor.execute("DELETE FROM products WHERE product_id=%s", (pid,))
            self.db.commit()
            messagebox.showinfo("Deleted","Product(s) deleted successfully.")
            self.load_products()
            self.refresh_home()
        except mysql.connector.Error as err:
            self.db.rollback()
            messagebox.showerror("Error",f"Cannot delete product(s):\n{err}")

    # ------------------ Reports ------------------
    def generate_date_range_report(self):
        start_date = self.start_entry.get_date()
        end_date = self.end_entry.get_date()
        for row in self.report_table.get_children():
            self.report_table.delete(row)
        try:
            self.cursor.execute("SELECT * FROM sales WHERE sale_date BETWEEN %s AND %s",(start_date,end_date))
            rows = self.cursor.fetchall()
            for idx,row in enumerate(rows):
                tag = "evenrow" if idx%2==0 else "oddrow"
                self.report_table.insert("",tk.END,values=row,tags=(tag,))
            messagebox.showinfo("Generated",f"Report generated for {start_date} to {end_date}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report:\n{e}")

    def export_date_range_report(self):
        start_date = self.start_entry.get_date()
        end_date = self.end_entry.get_date()
        try:
            self.cursor.execute("SELECT * FROM sales WHERE sale_date BETWEEN %s AND %s",(start_date,end_date))
            rows = self.cursor.fetchall()
            if not rows:
                messagebox.showinfo("No Data","No sales found to export")
                return
            filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files","*.csv")],
                                                    initialfile=f"sales_{start_date}_to_{end_date}.csv")
            if filename:
                with open(filename,"w",newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Sale ID","Customer","Total Amount","Sale Date"])
                    writer.writerows(rows)
                messagebox.showinfo("Exported",f"Report saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = TechHavenDashboard(root)
    root.mainloop()


