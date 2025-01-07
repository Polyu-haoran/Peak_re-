import pyodbc
from tkinter import messagebox

def get_databases(server):
    connection_string = f'DRIVER={{SQL Server}};SERVER={server};Trusted_Connection=yes;'
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE state_desc = 'ONLINE'")
            return sorted([row[0] for row in cursor.fetchall()])
    except Exception as e:
        messagebox.showerror("Connection Error", f"Error retrieving databases: {str(e)}")
        return []