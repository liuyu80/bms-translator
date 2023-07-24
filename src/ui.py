from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import *
from tkinter.messagebox import *
import json
import os
import sys

version = 'v0.2.3'
win_width = 0
win_height = 0
file_path = ''


def creat_window():
    win_width = str(int(root.winfo_screenwidth() / 4))
    win_height = str(int(root.winfo_screenheight() / 2))
    root.title('BMS翻译官 ' + version)
    root.geometry(f'{win_width}x{win_height}')
    return [win_width, win_height]


def creat_entry():
    print(win_height, win_width)
    # 帧ID位置 的选项
    id_label = Label(root, text='帧ID所在的列', font=('黑体', 12))
    id_label.place(relx=0.1, y=25)
    var_id = IntVar()
    even_numbers_1 = [x for x in range(1, 10)]
    frame_id_place = Combobox(root, textvariable=var_id, values=even_numbers_1)
    frame_id_place.place(relx=0.1, y=50, width=100)
    frame_id_place.set('1')
    # 帧数据位置的选项
    data_label = Label(root, text='帧数据所在的列', font=('黑体', 12))
    data_label.place(relx=0.55, y=25)
    var_data = IntVar()
    even_numbers_2 = [x for x in range(1, 10)]
    frame_date_place = Combobox(
        root, textvariable=var_data, values=even_numbers_2)
    frame_date_place.place(relx=0.55, y=50, width=120)
    return [frame_id_place, frame_date_place]


def path_check(path):
    if path == '':
        showwarning('警告', '路径为空')
        return 0
    file_path, file_name = os.path.split(path)
    name, style = os.path.splitext(file_name)
    if style not in ('.CSV', '.csv'):
        showwarning('警告', '文件名不正确')
        return 0
    if name[-2:] == '-译':
        showwarning('警告', '该文件已翻译, 请选择要翻译的报文文件')
        return 0
    return 1


def open_file_manager():
    global file_path
    file_path = askopenfilename()


def parse_file():
    id = id_place.get()
    data = data_place.get()
    if id == '':
        showwarning('警告', '请给出帧ID的位置')
    elif data == '':
        showwarning('警告', '请给出帧数据的位置')
    elif id == data:
        showerror('错误', '帧ID和帧数据列数相同')
    else:
        if path_check(file_path):
            print('正在解析')


def creat_btn():
    file_btn = Button(root, text='选择文件', command=open_file_manager)
    file_btn.place(relx=0.3, y=200)

    parse_btn = Button(root, text='开始解析', command=parse_file)
    parse_btn.place(relx=0.5, y=200)


if __name__ == "__main__":
    root = Tk()
    root.iconbitmap('./config/bms.ico')
    win_width, win_height = creat_window()
    id_place, data_place = creat_entry()
    
    creat_btn()

    root.mainloop()
