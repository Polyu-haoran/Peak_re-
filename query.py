import pandas as pd
from tkinter import messagebox
import pyodbc

def run_query(server, database, query):
    connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    try:
        with pyodbc.connect(connection_string) as conn:
            df = pd.read_sql(query, conn)
            if df.empty:
                messagebox.showinfo("No Data", "The query returned no results.")
            return df
    except Exception as e:
        messagebox.showerror("Query Error", f"An error occurred while executing the query: {str(e)}")
        return None

def export_to_csv(df, file_name):
    try:
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        messagebox.showinfo("Success", f"Data exported successfully to {file_name}")
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")