# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description  : BMS报文翻译官
 Version      : 1.0
 Author       : liuyu
 Date         : 2023-01-07 09:04:55
 LastEditors  : liuyu
 LastEditTime : 2023-01-07 17:31:02
 FilePath     : \\BMS-translator\\main.py
 Copyright (C) 2023 liuyu. All rights reserved.
'''

import json, os, csv, time
import pandas as pd
from struct import unpack

'''多帧报文识别内部变量'''
more_frame_config = {
    'name': '',
    'reply': False,
    'start': False,
    'end': False,
    'total': 0,
    'count': 0,
    'total_bytes': 0
}

'''
 description: 读取json配置文件
 param {*} path 文件路径
 return {*} dict类型
'''
def read_json(path = 'bmsConfig·.json'):
    with open(path, "r", encoding='utf-8') as fp:
        data = json.load(fp)
        return (data)

'''
 description: 读取BMS报文csv文件
 param {*} path 文件路径
 return {*} pandas.Dataframe 对象
'''
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

'''
 description: pgn==0xec00, 多帧报文的开始 回应 结束的识别
 param {*} pgn  报文组编号
 param {*} bit  多帧报文的控制, 用于识别报文的开始 回应 结束
 param {*} dataRaw 报文源数据
 param {*} priority 报文组号的优先级
 return {*} 识别的多帧报文名称
'''
def set_more_frame_name(pgn, bit, dataRaw, priority):
    if bit == 0x10:
        more_frame_config['start'] = True
        more_frame_config['end'] = False
        more_frame_config['reply'] = False
    elif bit == 0x11:
        more_frame_config['total'] = (dataRaw & 0xff000000000000) >> 4*12
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
            
''' 
 description:  识别一帧报文<= 8 byte 和 多帧报文的数据帧
 param {*} pgn  报文组编号
 param {*} priority   报文组编号的优先级
 param {*} receive_send   报文的 目的地址 和 发送地址
 param {*} dataRaw  报文源数据
 return {*} 识别报文的名字
'''
def find_bms_name(pgn, priority, receive_send, dataRaw):
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
                more_frame_config['count'] = dataRaw >> 4 * 14
                if more_frame_config['count'] <= more_frame_config['total']:
                    return f"{more_frame_config['name']}-{more_frame_config['count']}"
                else:
                    return 'error'
    return '非标未识别'

'''
 description: 解析帧ID 和 格式化报文源数据
 param {*} data pandas.series 对象 csv文件数据
 return {*} 报文名称
'''
def param_msg_name(data):
    id = int(data['帧ID'], 16)               #帧ID
    dataLength = data['数据长度']                #数据长度
    dataRaw = int(data['数据(HEX)'].replace(' ',''), 16)      #数据(HEX)
    priority = (id >> 4*6) >> 2         #优先级
    pgn = (id>>4*2) & 0xff00            #获取组编号
    receive_send = (id & 0xffff)
    # print(f'{pgn:x}, {priority:d}, {receive_send:x}, {dataLength:d}, {dataRaw:x}')
    return find_bms_name(pgn, priority, receive_send, dataRaw)


def one_frame_analysis(json_dic, name, length, dataRaw):
    
    pass

def analysis_dataRaw(data):
    if data['名称'].find("非标") != -1:
        return '非标未识别'
    elif data['名称'] == 'error':
        return '解析错误'
    elif data['名称'].find("-") != -1:
        return '多帧报文'
    dataRaw = int(data['数据(HEX)'].replace(' ',''), 16)      #数据(HEX)
    if data['名称'] in data_js.keys():
        one_frame_analysis(data_js[data['名称']], data[0], data[1], data[2])
    

'''
 description: 给名称一列赋值
 param {*} df pandas.Dataframe 对象 csv文件的数据
 return {*} pandas.Dataframe
'''
def set_msg_name(df):
    df['名称'] = df.loc[ : , ['帧ID', '数据长度', '数据(HEX)']].apply(param_msg_name, axis=1)
    return df

def set_meaning(df):
    df['BMS报文翻译'] = df.loc[ :100 , ['名称', '数据长度', '数据(HEX)']].apply(analysis_dataRaw, axis=1)
    return df

if __name__ == "__main__":
    global data_js
    data_js = read_json()
    csv_df = get_csv_data('BVIN1枪.CSV')

    csv_df = set_msg_name(csv_df)
    csv_df = set_meaning(csv_df)

    csv_df.to_csv('1.csv', index =None)
    
    