import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import csv

# ---------------------------------
# SalesReport Class (OOP + MySQL)
# ---------------------------------
class SalesReport:
    def __init__(self, host="localhost", user="root", password="MyStrongPassword123!", database="techhaven"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect_db()
        self.create_sales_table()

    def connect_db(self):
        """Establish MySQL connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error connecting to MySQL:\n{err}")

    def create_sales_table(self):
        """Create the sales table if it does not exist"""
        query = """
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(100) NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            sale_date DATE NOT NULL
        )
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()

    def add_sample_sales(self):
        """Insert sample sales data (for testing)"""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM sales")  # clear old data

        sample_data = [
            ("Alice Johnson", 599.99, "2025-10-07"),
            ("Bob Singh", 1299.00, "2025-10-07"),
            ("Chris Lee", 299.50, "2025-10-06"),
            ("Diana Patel", 899.00, "2025-10-07"),
            ("Ethan James", 450.75, "2025-10-07")
        ]
        cursor.executemany(
            "INSERT INTO sales (customer_name, total_amount, sale_date) VALUES (%s, %s, %s)",
            sample_data
        )
        self.connection.commit()

    def generate_daily_report(self, report_date):
        """Retrieve daily sales summary"""
        cursor = self.connection.cursor()
        query = "SELECT COUNT(*), SUM(total_amount) FROM sales WHERE sale_date = %s"
        cursor.execute(query, (report_date,))
        result = cursor.fetchone()

        if result[0] == 0 or result[1] is None:
            return None, None
        else:
            self.export_to_csv(report_date)
            return result[0], float(result[1])

    def export_to_csv(self, report_date):
        """Export daily sales to CSV file"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM sales WHERE sale_date = %s", (report_date,))
        sales_data = cursor.fetchall()

        filename = f"daily_sales_{report_date}.csv"
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Sale ID", "Customer Name", "Amount", "Date"])
            writer.writerows(sales_data)

        messagebox.showinfo("Report Exported", f"Sales report saved as {filename}")

# ---------------------------------
# Dashboard GUI (Tkinter)
# ---------------------------------
class DashboardApp:
    def __init__(self, root, report_obj):
        self.root = root
        self.report_obj = report_obj
        self.root.title("TechHaven Retail Management System - Dashboard")
        self.root.geometry("600x420")

        tk.Label(root, text="📊 TechHaven Dashboard", font=("Arial", 18, "bold")).pack(pady=15)

        # Date entry field
        tk.Label(root, text="Enter Date (YYYY-MM-DD):", font=("Arial", 11)).pack()
        self.date_entry = tk.Entry(root, width=25)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(pady=5)

        # Generate Report Button
        tk.Button(root, text="Generate Daily Sales Report", bg="#007acc", fg="white",
                  font=("Arial", 11, "bold"), width=25, height=2,
                  command=self.show_daily_report).pack(pady=10)

        # Results Table
        self.tree = ttk.Treeview(root, columns=("Metric", "Value"), show="headings", height=5)
        self.tree.heading("Metric", text="Metric")
        self.tree.heading("Value", text="Value")
        self.tree.column("Metric", width=200)
        self.tree.column("Value", width=200)
        self.tree.pack(pady=10)

    def show_daily_report(self):
        report_date = self.date_entry.get().strip()
        total_transactions, total_revenue = self.report_obj.generate_daily_report(report_date)

        # Clear old table entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        if total_transactions is None:
            messagebox.showinfo("No Data", f"No sales found for {report_date}.")
        else:
            # Display new results
            self.tree.insert("", "end", values=("Date", report_date))
            self.tree.insert("", "end", values=("Total Transactions", total_transactions))
            self.tree.insert("", "end", values=("Total Sales Value", f"${total_revenue:.2f}"))

            messagebox.showinfo("Report Generated",
                                f"Report for {report_date} generated successfully!\n"
                                f"Total Sales: ${total_revenue:.2f}\n"
                                f"Transactions: {total_transactions}\n\n"
                                f"Report exported as CSV file.")

# ---------------------------------
# Run the App
# ---------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    report_obj = SalesReport(user="pythonuser", password="MyStrongPassword123!", database="techhaven")

    report_obj.add_sample_sales()  # Add demo data (you can comment this later)
    app = DashboardApp(root, report_obj)
    root.mainloop()
