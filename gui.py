import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from database import get_databases
from query import run_query, export_to_csv

# 用于存储全局变量
databases = []
update_timer = None
selected_names = []  # 存储预查询结果中的选择项
query_template = """SELECT
aet.EVENTID as EventID,
sum(port.PERSPVALUE) as PerspValue,
sum(port.STDDEVC) as StdDevC,
sqrt(sum(square(port.STDDEVI))) as StdDevI,
sum(port.EXPVALUE) as ExpValue,
aet.RATE as Rate, 'RL' as PERSPCODE
FROM rdm_anlsevent aet
inner join rdm_port port
on aet.EVENTID = port.EVENTID and aet.ANLSID = port.ANLSID
inner join dbo.rdm_analysis anl
on aet.ANLSID = anl.ID
WHERE port.PERSPCODE = 'RL' and 
anl.NAME in ('MAAF_Group_2025')
GROUP BY aet.EVENTID, aet.RATE
ORDER BY PerspValue desc"""

def create_gui(root):
    main_frame = ttk.Frame(root, padding="20")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # 输入框和标签
    ttk.Label(main_frame, text="SQL Server:", font=("Arial", 12)).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
    server_entry = ttk.Entry(main_frame, width=35)
    server_entry.grid(row=1, column=0, pady=5)

    # 创建连接按钮
    connect_button = ttk.Button(main_frame, text="Connect",
                                command=lambda: on_connect_button_click(server_entry, database_combobox))
    connect_button.grid(row=1, column=1, padx=5, pady=5)

    # 数据库下拉框
    ttk.Label(main_frame, text="Database:", font=("Arial", 12)).grid(row=2, column=0, sticky=tk.W, pady=5)
    database_var = tk.StringVar(main_frame)
    database_combobox = ttk.Combobox(main_frame, textvariable=database_var, state="normal", width=30)
    database_combobox.grid(row=3, column=0, pady=5)
    database_combobox.bind("<KeyRelease>", lambda event: on_database_entry(event, database_combobox))

    # 预查询输入框和按钮
    ttk.Label(main_frame, text="Pre Query:", font=("Arial", 12)).grid(row=4, column=0, sticky=tk.W, pady=5)
    pre_query_text = tk.Text(main_frame, height=5, width=38)
    pre_query_text.grid(row=5, column=0, pady=5)

    # 初始化预查询框内容（默认筛选）
    default_pre_query = "SELECT * FROM rdm_analysis;"
    pre_query_text.insert(tk.END, default_pre_query)

    pre_query_button = ttk.Button(main_frame, text="Run Pre Query",
                                  command=lambda: on_pre_query_button_click(server_entry, database_var, pre_query_text, result_text))
    pre_query_button.grid(row=5, column=1, padx=5, pady=5)

    # 预查询结果显示框
    ttk.Label(main_frame, text="Pre Query Result:", font=("Arial", 12)).grid(row=6, column=0, sticky=tk.W, pady=5)
    global result_text  # 将 result_text 声明为全局变量
    result_text = tk.Text(main_frame, height=5, width=40)
    result_text.grid(row=7, column=0, pady=5)

    # 创建一个 LabelFrame 来包含 Radiobuttons
    retspcode_frame = ttk.LabelFrame(main_frame, text="RETSPCODE", padding=(10, 10))
    retspcode_frame.grid(row=7, column=1, padx=10, pady=5, sticky=tk.N)  # 放置在与 Pre Query Result 同一高度

    # 添加 Radiobuttons
    radio_var = tk.StringVar(value="GU")  # 设置默认值
    radio_buttons = ["GU", "GR", "RL", "RP", "SS"]

    for index, name in enumerate(radio_buttons):
        radio_button = ttk.Radiobutton(retspcode_frame, text=name, variable=radio_var, value=name)
        radio_button.grid(row=index, column=0, sticky=tk.W, padx=5, pady=2)  # 垂直排列

    # SQL查询输入框
    ttk.Label(main_frame, text="SQL Query:", font=("Arial", 12)).grid(row=8, column=0, sticky=tk.W, pady=5)
    global query_text  # 将 query_text 声明为全局变量
    query_text = tk.Text(main_frame, height=10, width=40)
    query_text.grid(row=9, column=0, pady=5)

    # 初始化SQL查询框内容
    default_query = """SELECT
aet.EVENTID as EventID,
sum(port.PERSPVALUE) as PerspValue,
sum(port.STDDEVC) as StdDevC,
sqrt(sum(square(port.STDDEVI))) as StdDevI,
sum(port.EXPVALUE) as ExpValue,
aet.RATE as Rate, 'RL' as PERSPCODE
FROM rdm_anlsevent aet
inner join rdm_port port
on aet.EVENTID = port.EVENTID and aet.ANLSID = port.ANLSID
inner join dbo.rdm_analysis anl
on aet.ANLSID = anl.ID
WHERE port.PERSPCODE = 'RL' and 
anl.NAME in ('MAAF_Group_2025')
GROUP BY aet.EVENTID, aet.RATE
ORDER BY PerspValue desc"""
    query_text.insert(tk.END, default_query)

    run_button = ttk.Button(main_frame, text="Run",
                            command=lambda: on_run_button_click(server_entry, database_var, query_text, radio_var))
    run_button.grid(row=9, column=1, padx=5, pady=5)

def on_database_entry(event, database_combobox):
    global update_timer
    if update_timer is not None:
        database_combobox.after_cancel(update_timer)

    update_timer = database_combobox.after(800, lambda: update_database_combobox(database_combobox))

def update_database_combobox(database_combobox):
    input_text = database_combobox.get().strip().lower()
    if not input_text:
        database_combobox['values'] = databases
        return

    filtered_databases = [db for db in databases if input_text in db.lower()]

    if filtered_databases:
        database_combobox['values'] = filtered_databases
        database_combobox.set(filtered_databases[0])
    else:
        database_combobox['values'] = []
        database_combobox.set("")

def on_connect_button_click(server_entry, database_combobox):
    server = server_entry.get().strip()
    if not server:
        messagebox.showwarning("Input Error", "Please enter a SQL Server.")
        return

    global databases
    databases = get_databases(server)
    if databases:
        database_combobox['values'] = databases
        database_combobox.set(databases[0])
    else:
        messagebox.showwarning("No Databases", "No databases found on this server.")

def on_pre_query_button_click(server_entry, database_var, pre_query_text, result_text):
    server = server_entry.get().strip()
    database = database_var.get()
    pre_query = pre_query_text.get("1.0", tk.END).strip()

    if not server or not database or not pre_query:
        messagebox.showwarning("Input Error", "Please fill all the fields.")
        return

    df = run_query(server, database, pre_query)
    if df is not None:
        # 清空结果框
        result_text.delete("1.0", tk.END)

        # 使用 Listbox 显示多选结果
        listbox = tk.Listbox(result_text, selectmode=tk.MULTIPLE, height=10, width=45)
        for name in df['NAME']:  # 假设预查询结果中有 'NAME' 列
            listbox.insert(tk.END, name)
        listbox.pack()

        # 添加多选完成后的按钮
        select_button = ttk.Button(result_text, text="Select", command=lambda: on_select_names(listbox))
        select_button.pack()

def on_select_names(listbox):
    global selected_names
    selected_names = [listbox.get(i) for i in listbox.curselection()]  # 获取用户选择的项
    print(f"Selected names: {selected_names}")  # 打印选择的名称
    messagebox.showinfo("Selection", f"You have selected: {', '.join(selected_names)}")

    # 在 SQL 查询框中更新内容
    query_text.delete("1.0", tk.END)  # 清空当前查询
    for name in selected_names:
        # 替换 SQL 查询中的 anl.NAME
        updated_query = f"""SELECT
aet.EVENTID as EventID,
sum(port.PERSPVALUE) as PerspValue,
sum(port.STDDEVC) as StdDevC,
sqrt(sum(square(port.STDDEVI))) as StdDevI,
sum(port.EXPVALUE) as ExpValue,
aet.RATE as Rate, 'RL' as PERSPCODE
FROM rdm_anlsevent aet
inner join rdm_port port
on aet.EVENTID = port.EVENTID and aet.ANLSID = port.ANLSID
inner join dbo.rdm_analysis anl
on aet.ANLSID = anl.ID
WHERE port.PERSPCODE = 'RL' and 
anl.NAME in ('{name}')
GROUP BY aet.EVENTID, aet.RATE
ORDER BY PerspValue desc\n\n"""
        query_text.insert(tk.END, updated_query)  # 添加到 SQL 查询框中

def on_run_button_click(server_entry, database_var, query_text, radio_var):
    server = server_entry.get().strip()
    database = database_var.get()
    # query_template = query_text.get("1.0", tk.END).strip()

    if not server or not database or not query_template:
        messagebox.showwarning("Input Error", "Please fill all the fields.")
        return

    selected_retspcode = radio_var.get()

    print(f"Query template: {query_template}")  # 打印查询模板

    success_message = []
    for name in selected_names:
        print(f"Generating query for: {name}")  # 调试输出
        # 生成新的查询
        updated_query = query_template.replace("RL", selected_retspcode).replace("anl.NAME in ('MAAF_Group_2025')", f"anl.NAME in ('{name}')")

        print(f"Running query for {name}: {updated_query}")  # 调试输出

        # 运行查询
        df = run_query(server, database, updated_query)

        if df is not None:
            # 构建文件名
            file_name = f"{database}——{selected_retspcode}——{name}.csv"
            # 弹出保存文件对话框，选择保存路径
            save_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                     filetypes=[("CSV files", "*.csv")],
                                                     initialfile=file_name)
            if save_path:  # 用户选择了文件名
                export_to_csv(df, save_path)  # 导出 CSV 文件
                success_message.append(f"Data for {name} exported successfully to {save_path}")

    # 只弹出一个成功信息的弹窗
    if success_message:
        messagebox.showinfo("Success", "\n".join(success_message))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("SQL Query Tool")
    create_gui(root)
    root.mainloop()