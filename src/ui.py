from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import *
from tkinter.messagebox import *
from main import *
import json
import os
import time
import sys


version = 'v0.2.3'
win_width = 0
win_height = 0
file_path = ''


def creat_window():
    win_width = int(root.winfo_screenwidth() / 4)
    win_height = int(root.winfo_screenheight() / 4)
    root.title('BMS翻译官 ' + version)
    root.geometry(f'{win_width}x{win_height}+{int(root.winfo_screenwidth()/3)}+{int(root.winfo_screenheight()/3)}')
    return [win_width, win_height]

def save_config():
    config['timestamp'] = int(time.time())
    config['id_place'] = id_place.get()
    config['data_place'] = data_place.get()
    config['split'] = split_entry.get()
    config['valid_row'] = valid_entry.get()
    with open('./config/config', 'w', encoding='utf-8') as fp:
        json.dump(config, fp)

def creat_entry():
    # 帧ID位置 的选项
    id_label = Label(root, text='帧ID所在的列', font=('黑体', 11))
    id_label.place(relx=0.09, y=25)
    var_id = IntVar()
    even_numbers_1 = [x for x in range(1, 10)]
    frame_id_place = Combobox(root, textvariable=var_id, values=even_numbers_1)
    frame_id_place.place(relx=0.1, y=50, width=100)
    frame_id_place.set('1')

    # 帧数据位置的选项
    data_label = Label(root, text='帧数据所在的列', font=('黑体', 11))
    data_label.place(relx=0.35, y=25)
    var_data = IntVar()
    even_numbers_2 = [x for x in range(1, 10)]
    frame_date_place = Combobox(
        root, textvariable=var_data, values=even_numbers_2)
    frame_date_place.place(relx=0.35, y=50, width=120)

    # 数据分隔符
    split_label = Label(root, text='数据分隔符', font=('黑体', 11))
    split_label.place(relx=0.65, y=25)
    var_split = StringVar()
    split_entry = Combobox(root, textvariable=var_split,
                           values=['tab(\\t)', '英文逗号(,)'])
    split_entry.place(relx=0.65, y=50, width=100)

    # 选择有效数据行
    valid_num_label = Label(root, text='有效数据开始行', font=('黑体', 11))
    valid_num_label.place(relx=0.09, y=90)
    var_valid = IntVar()
    even_numbers_3 = [x for x in range(1, 5)]
    valid_num_entry = Combobox(
        root, textvariable=var_valid, values=even_numbers_3)
    valid_num_entry.place(relx=0.1, y=90+25, width=110)

    # 文件路径显示

    def on_entry_click(event):
        if file_path_entry.get() == "文件路径":
            file_path_entry.delete(0, "end")
            file_path_entry.config(fg="gray")

    def on_focusout(event):
        if file_path_entry.get() == "":
            file_path_entry.insert(0, "文件路径")
            file_path_entry.config(fg="gray")

    file_path_entry = Entry(root)
    file_path_entry.place(relx=0.1, y=170, width=(int(win_width)/3) * 2)
    file_path_entry.insert(0, "文件路径")
    file_path_entry.bind("<FocusIn>", on_entry_click)
    file_path_entry.bind("<FocusOut>", on_focusout)
    return [frame_id_place, frame_date_place, split_entry, valid_num_entry, file_path_entry]


def ui_path_check(path):
    if path == '':
        showwarning('警告', '路径为空')
        return 0
    file_path, file_name = os.path.split(path)
    name, style = os.path.splitext(file_name)
    if style not in ('.CSV', '.csv', '.xls', '.XLS'):
        showwarning('警告', '文件名不正确')
        return 0
    if name[-2:] == '-译':
        showwarning('警告', '该文件已翻译, 请选择要翻译的报文文件')
        return 0
    return 1


def open_file_manager():
    global file_path
    file_path = askopenfilename()
    file_path_entry.insert(0, file_path)


def read_csv(path, split_s, valid_num):
    with open(path, "r", encoding=get_text_encoding(path)) as file:
        csv_reader = csv.reader(file, delimiter=split_s)
        data = []
        for line in csv_reader:
            data.append(line)

    return data[valid_num-1:]


def creat_csv(path, data_df, splite_s):
    file_path, file_name = os.path.split(path)  # 路径切割, 得到路径和文件名
    # 生成新的文件 保存解析后的数据
    csv_name = ''.join(file_name.split(
        '.')[:-1]) + '-译.' + file_name.split('.')[-1]
    with open(os.path.join(file_path, csv_name), 'w', newline='', encoding='utf-8') as file:
        # 使用制表符作为分隔符创建 CSV 的 writer 对象
        writer = csv.writer(file, delimiter=splite_s)
        # 写入数据行
        for row in data_df:
            writer.writerow(row)
    os.startfile(os.path.join(file_path, csv_name))  # 自动使用系统默认应用打开该文件


def parse_file():
    save_config()
    id = id_place.get()
    data_p = data_place.get()
    split_s = split_entry.get()
    valid_s = valid_entry.get()
    if id == '':
        showwarning('警告', '请给出帧ID的位置')
    elif data_p == '':
        showwarning('警告', '请给出帧数据的位置')
    elif id == data_p:
        showerror('错误', '帧ID和帧数据列数相同')
    elif split_s == '':
        showwarning('警告', "请选择数据分隔符")
    elif valid_s == '':
        showwarning('警告', "请选择有效数据从哪行开始")
    else:
        if ui_path_check(file_path):
            print('正在解析')
            if split_s[0] == 't':
                split_s = '\t'
            elif split_s[0] == '英':
                split_s = ','

            df_data = read_csv(file_path, split_s, int(valid_s))
            if len(df_data[3]) < 2:
                showerror('错误', '请选择正确的文件')
            df_data = main_prase(df_data, id, data_p)
            creat_csv(file_path, df_data, split_s)


def creat_btn():
    file_btn = Button(root, text='选择文件', command=open_file_manager)
    file_btn.place(relx=0.3, y=210)

    parse_btn = Button(root, text='开始解析', command=parse_file)
    parse_btn.place(relx=0.5, y=210)


def read_config(path):
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as fp:
            data = json.load(fp)
        return (data)
    else:
        config = {
            "timestamp": 1,
            "id_place": 3,
            "data_place": 9,
            "split": "tab(\\t)",
            "valid_row": 2
        }
        with open(path, 'w', encoding='utf-8') as fp:
            json.dump(config, fp)
        return config

def set_config(config):
    if int(time.time()) - config['timestamp'] < 500: 
        id_place.set(config['id_place'])
        data_place.set(config['data_place'])
        split_entry.set(config['split'])
        valid_entry.set(config['valid_row'])
    else:
        id_place.set(3)
        data_place.set(9)


if __name__ == "__main__":
    root = Tk()
    root.resizable(False, False)
    if os.path.exists('./config/bms.ico'):
        root.iconbitmap('./config/bms.ico')
    win_width, win_height = creat_window()
    id_place, data_place, split_entry, valid_entry, file_path_entry = creat_entry()

    config = read_config('./config/config')
    set_config(config)
    creat_btn()
    root.mainloop()
 