import tkinter as tk
from gui import *
import sv_ttk
import pandas as pd
import pyodbc
import gui
import pandas
import database
import tkinter
import query



# 创建主窗口
def main():
    root = tk.Tk()
    root.title("SQL Query Executor")
    create_gui(root)
    sv_ttk.set_theme("light")
    root.mainloop()

if __name__ == "__main__":
    print("executed")
    main()