# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description  : 
 Version      : 1.0
 Author       : liuyu
 Date         : 2023-01-07 09:04:55
 LastEditors  : liuyu
 LastEditTime : 2023-01-07 11:46:35
 FilePath     : \\BMS-translator\\main.py
 Copyright (C) 2023 liuyu. All rights reserved.
'''

import json, os, csv, struct, time
import pandas as pd
import numpy as np

def read_json(path = 'bmsConfig·.json'):
    with open(path, "r", encoding='utf-8') as fp:
        data = json.load(fp)
        return (data)

def get_csv_data(path):
    timeStamp = os.path.getmtime(path)
    create_time = time.strftime("%Y-%m-%d ", time.localtime(timeStamp))
    csv_df = pd.read_csv(path, encoding='GB2312', header=0, names=['序号','传输方向','时间标识','名称','帧ID','帧格式','帧类型','数据长度','数据(HEX)'])
    csv_df.set_index('序号', inplace = True)
    csv_df = csv_df.reindex(columns=['序号','传输方向','时间标识','名称','帧ID','帧格式','帧类型','数据长度','数据(HEX)', 'BMS报文翻译'])

    csv_df['时间标识'] = create_time + csv_df['时间标识']
    print(csv_df.head())
    return csv_df

def set_msg_name(df):
    pass

if __name__ == "__main__":
    global data_js
    data_js = read_json()
    csv_df = get_csv_data('BVIN1枪.CSV')


    