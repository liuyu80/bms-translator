# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description  : BMS报文翻译官
 Version      : 1.0
 Author       : liuyu
 Date         : 2023-01-07 09:04:55
 LastEditors  : liuyu
 LastEditTime : 2023-01-07 16:17:16
 FilePath     : \\BMS-translator\\main.py
 Copyright (C) 2023 liuyu. All rights reserved.
'''

import json, os, csv, struct, time
import pandas as pd


more_frame_config = {
    'name': '',
    'reply': False,
    'start': False,
    'end': False,
    'total': 0,
    'count': 0,
    'total_bytes': 0
}

def read_json(path = 'bmsConfig·.json'):
    with open(path, "r", encoding='utf-8') as fp:
        data = json.load(fp)
        return (data)

def get_csv_data(path):
    header = ['序号','传输方向','时间标识','名称','帧ID','帧格式','帧类型','数据长度','数据(HEX)']
    if os.path.getctime(path) > os.path.getmtime(path):
        timeStamp = os.path.getmtime(path)
    else:
        timeStamp = os.path.getctime(path)
    create_time = time.strftime("%Y-%m-%d ", time.localtime(timeStamp))
    csv_df = pd.read_csv(path, encoding='GB2312', header=0, names=header)

    header.append('BMS报文翻译')
    csv_df = csv_df.reindex(columns=header)

    csv_df['时间标识'] = create_time + csv_df['时间标识']
    # print(csv_df.head())
    return csv_df
    
def set_more_frame_name(pgn, bit, dataRaw, priority):
    if bit == 0x10:
        more_frame_config['start'] = True
        more_frame_config['end'] = False
        more_frame_config['reply'] = False
    elif bit == 0x11:
        more_frame_config['total'] = dataRaw & 0xff000000000000
        more_frame_config['reply'] = True
        more_frame_config['start'] = False
    elif bit == 0x13:
        more_frame_config['end'] = True
        more_frame_config['start'] = False
        more_frame_config['reply'] = False
        more_frame_config['total'] = 0
        more_frame_config['count'] = 0
        more_frame_config['name'] = ''
        more_frame_config['total_bytes'] = 0


    for key in data_js.keys():
        if int(data_js[key]['PGN'], 16) == pgn and \
        data_js[key]['priority'] == priority:
            more_frame_config['name'] = key
            if more_frame_config['start']:
                return key + '-start'
            elif more_frame_config['reply']:
                return key + '-reply'
            elif more_frame_config['end']:
                more_frame_config['end'] = False
                return key + '-end'
    return '非标未识别'
            


def find_bms_name(id, pgn, priority, receive_send, dataLength, dataRaw):
    if pgn == 0xec00: 
        pgn = dataRaw & 0xffff
        control_bit = dataRaw >> 4*14
        return set_more_frame_name(pgn, control_bit, dataRaw, priority)
        
    for key in data_js.keys():
        if int(data_js[key]['PGN'], 16) == pgn and \
        data_js[key]['priority'] == priority and \
        int(data_js[key]['receive_send'], 16) == receive_send:
            return key
        if pgn == 0xeb00:
            if more_frame_config['name']:
                more_frame_config['count'] += 1
                return f"{more_frame_config['name']}-{more_frame_config['count']}"

    return '非标未识别'

def param_msg_name(data):
    id = int(data['帧ID'], 16)               #帧ID
    dataLength = data['数据长度']                #数据长度
    dataRaw = int(data['数据(HEX)'].replace(' ',''), 16)      #数据(HEX)
    priority = (id >> 4*6) >> 2         #优先级
    pgn = (id>>4*2) & 0xff00            #获取组编号
    receive_send = (id & 0xffff)
    print(f'{pgn:x}, {priority:d}, {receive_send:x}, {dataLength:d}, {dataRaw:x}')
    return find_bms_name(data['序号'], pgn, priority, receive_send, dataLength, dataRaw)


def set_msg_name(df):
    df['名称'] = df.loc[ : , ['序号', '帧ID', '数据长度', '数据(HEX)']].apply(param_msg_name, axis=1)
    return df


if __name__ == "__main__":
    global data_js
    data_js = read_json()
    csv_df = get_csv_data('BVIN1枪.CSV')

    csv_df = set_msg_name(csv_df)
    

    csv_df.to_csv('1.csv', index =None)
    
    