# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description  : BMS报文翻译官
 Version      : 1.0
 Author       : liuyu
 Date         : 2023-01-07 09:04:55
LastEditors: liuyu 2543722345@qq.com
LastEditTime: 2023-02-07 14:06:49
 FilePath     : \\BMS-translator\\src\\main.py
 Copyright (C) 2023 liuyu. All rights reserved.
'''
from decimal import Decimal
import json, os, re, time, math
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import struct
from check_sys import *

'''多帧报文名称识别-内部变量'''
more_frame_config = {
    'name': '',
    'reply': False,
    'start': False,
    'end': False,
    'total': 0,
    'count': 0,
    'total_bytes': 0
}
'''多帧报文解析-内部变量'''
more_analysis_config = {
    'name': '',
    'total_num': None,
    'index': None,
    'total_bytes': None,
    'data': '',
}
'''不定长报文解析-内部变量'''
unsized_frame_config = {
    'name': '',
    'total_num': None,
    'index': None,
    'total_bytes': None,
    'data': '',
    'format_str': '',
}
global data_js

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
def get_csv_data(path:str):
    header = ['序号','传输方向','时间标识','名称','帧ID','帧格式','帧类型','数据长度','数据(HEX)']
    if os.path.getctime(path) > os.path.getmtime(path):
        timeStamp = os.path.getmtime(path)
    else:
        timeStamp = os.path.getctime(path)
    create_time = time.strftime("%Y-%m-%d ", time.localtime(timeStamp))
    csv_df = pd.read_csv(path, encoding='GB2312', header=0, names=header)

    header.append('BMS报文翻译')
    csv_df = csv_df.reindex(columns=header)

    # csv_df['时间标识'] = create_time + csv_df['时间标识']

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
    return '非标'
            
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
                
    if receive_send not in [0xf456, 0x56f4]:
        return 'error'
    return '非标'

def hex_data_check(data):
    for line in data:
        if re.match(line[1], line[0]) == None:
            return False
    if len(data[1][0])%2 != 0:
        return False
    return True
'''
 description: 解析帧ID 和 格式化报文源数据
 param {*} data pandas.series 对象 csv文件数据
 return {*} 报文名称
'''
def param_msg_name(data):
    # 检测 帧ID 和 实际数据 是否为十六进制
    if hex_data_check([[data['帧ID'], '^0[xX][A-Fa-f0-9]{8}$|^[A-Fa-f0-9]{8}$'],
                    [str(data['数据(HEX)']).replace(' ',''), '^[A-Fa-f0-9]+$']]) is False:  
        return 'error'
    if data['数据长度'] != len(str(data['数据(HEX)']).replace(' ',''))/2:  #检测文件中数据长度和数据实际长度是否一致
        return 'error'
    id = int(data['帧ID'], 16)          # 帧ID
    dataRaw = int(data['数据(HEX)'].replace(' ',''), 16)      #数据(HEX)
    priority = (id >> 4*6) >> 2         # 优先级
    pgn = (id>>4*2) & 0xff00            # 获取组编号
    receive_send = (id & 0xffff)

    return find_bms_name(pgn, priority, receive_send, dataRaw)

def bytes_translation(json_dic, format_dic, key, byte, index):
    text = ''
    # 选项翻译
    if 'options' in json_dic.keys():
        if str(byte) in json_dic['options'].keys():
            if key:
                text += f"{key}: {json_dic['options'][str(byte)]}; " 
            else:
                return json_dic['options'][str(byte)]
        else:
            return f"{key}: 解析错误-bytesOptions; "
    # 比率 偏移量 计算 翻译       
    elif 'ratio' in json_dic.keys():
        values = Decimal(str(byte)) * Decimal(str(json_dic['ratio'])) + Decimal(str(json_dic['offset']))
        if key:
            text += f"{key}: {values}{json_dic['unit_symbol']}; "
        else:
            return f"{values}{json_dic['unit_symbol']}"
    # 根据类型进行翻译
    elif "type" in json_dic.keys():
        if json_dic['type'] == "int":
            if key:
                text += f"{key}: {byte}; "
            else:
                return byte
        if json_dic['type'] == "ascii":
            range_list = json_dic["bytes/bit"]
            ascii_str = format_dic['data'][(range_list[0]-1)*2: (range_list[0]+range_list[1]-1)*2].replace(' ', '')
            if ascii_str.lower() not in ['ffffff', '00000000']:   #充电机所在区域编码 6f 为无
                if key:
                    text += f"{key}: "
                    for cell in cut(ascii_str, 2):
                        text += f"{chr(int(cell, 16))}"
                    text += '; '
                else:
                    alone = ''
                    for cell in cut(ascii_str, 2):
                        alone += f"{chr(int(cell, 16))}"
                    return alone
            else: 
                if key:
                    text += f"{key}: 无; "
                else:
                    return '无'
    # 组合体翻译
    elif 'components' in json_dic.keys():
        components = json_dic['components']
        cell_list = []
        # 字节组合体翻译
        if isinstance(components[0]["bytes/bit"][0], int):
            s_str = bit_overturn(hex(byte), (json_dic["bytes/bit"][1])*2)
            for com in components:
                range_list = [com['bytes/bit'][0]-json_dic["bytes/bit"][0]]
                range_list.append( range_list[0] + com['bytes/bit'][1])
                s_data = s_str[range_list[0]*2: range_list[1]*2]
                if len(s_data) > 2:
                    s_data = bit_overturn("xx"+ s_data, com['bytes/bit'][1]*2)
                cell = bytes_translation(com, format_dic, None, s_data, index)
                cell_list.append(cell)
            text += schema_to_str(json_dic['schema'], cell_list, key)
        # bit组合体翻译
        elif isinstance(components[0]["bytes/bit"][0], float):
            bit_Lenthg = int(cut(format_dic['format_str'], 2)[index][0]) * 8
            if format_dic['unsized']:
                byte_start, byte_end = 0, 0
                for _ in range(0, len(format_dic['format_list']), len(components)):
                    for com in components:
                        range_list = com['bytes/bit']
                        byte_start = byte_end
                        byte_end = byte_start + hexToBit(range_list[1])
                        cell = bit_translation(com, None, byte, bit_Lenthg, [byte_start, byte_end])
                        cell_list.append(str(cell))
                    byte_start, byte_end = 0, 0
            else:  
                for com in components:
                    range_list = com['bytes/bit']
                    byte_start = hexToBit(range_list[0]) - hexToBit(data_js[format_dic['name']]['format_list'][index]) - 1 
                    byte_end = byte_start + hexToBit(range_list[1])
                    cell = bit_translation(com, None, byte, bit_Lenthg, [byte_start, byte_end])
                    cell_list.append(str(cell))
            text += schema_to_str(json_dic['schema'], cell_list, key)
        else:
            text += f"{key}: 错误; "
    if text == '':
        text = f'{key}: 未解析; '
    return str(text)

def schema_to_str(schema, cell_list, key):
    text = ''
    way = int(schema[0])
    tran_packs = schema[1].split('~')
    text += f'{key}: '
    for cell, pack in zip(cell_list[::way], tran_packs[:-1]):
        text = text + pack + str(cell)
    text += f'{tran_packs[-1]}; '
    return text

def bit_translation(json_dic, key, byte, bit_Lenthg, range_list):
    text = ''
    bit_fun_str =  '0b'+ '0'* (bit_Lenthg - range_list[1])+ '1'* (range_list[1]-range_list[0]) + '0'* range_list[0] 
    bit_int = (byte & int(bit_fun_str, 2))>> range_list[0]
    
    if 'options' in json_dic.keys():  
        if str(bit_int) in json_dic['options'].keys():
            if key:
                text += f"{key}: {json_dic['options'][str(bit_int)]}; " 
            else:
                return json_dic['options'][str(bit_int)]
        else:
            return f"bit解析错误-{key}options, bit_Lenthg:{bit_Lenthg}-byte:{byte}-range_list:{range_list}-{bit_int}-items{json_dic['options']}; "
    elif 'ratio' in json_dic.keys():
        values = Decimal(str(bit_int)) * Decimal(str(json_dic['ratio'])) + Decimal(str(json_dic['offset']))
        if key:
            text += f"{key}: {values}{json_dic['unit_symbol']}; "
        else: 
            return f"{values}{json_dic['unit_symbol']}"
    elif "type" in json_dic.keys():
        if json_dic['type'] == "int":
            if key:
                text += f"{key}: {byte}; "
            else:
                return byte
    if text == '':
        if key:
            text = f'{key}: 未解析; ' 
        else:
            return '未解析'
    else:
        return text
    
def translation_fun(json_dic, format_dic, data_keys, pack) ->str:
    text = ''
    for index in range(len(pack)):
        key = data_keys[index]
        pack[index] = int.from_bytes(pack[index], 'little')
        if isinstance(json_dic['data'][key]['bytes/bit'][1], int):
            text += bytes_translation(json_dic['data'][key], format_dic, key, pack[index], index)
            
        elif isinstance(json_dic['data'][key]['bytes/bit'][1], float):
            bit_Lenthg = int(cut(format_dic['format_str'], 2)[index][0]) * 8
            range_list = json_dic['data'][key]['bytes/bit']
            byte_start = hexToBit(range_list[0]) - hexToBit(data_js[format_dic['name']]['format_list'][index]) - 1 
            byte_end = byte_start + hexToBit(range_list[1])
            
            text += bit_translation(json_dic['data'][key], key, pack[index], bit_Lenthg, [byte_start, byte_end])
        else:
            return f"json_error {json_dic['data'][key]['bytes/bit']}, {format_dic['format_str']}, {format_dic['name']}"
    
    return text[:-2]  # 去掉翻译后最后一个;

def hexToBit(num:str) -> int:
    if isinstance(num, float) :
        str_nums = str(num).split('.')
        if len(str_nums[1]) != 1 or int(str_nums[1]) >= 8:
            print('数据有问题！')
        else:
            return int(str_nums[0]) * 8 + int(str_nums[1])
    elif isinstance(num, int):
        return num * 8
    elif '.' in num:
        str_nums = str(num).split('.')
        if len(str_nums[1]) != 1 or int(str_nums[1]) >= 8:
            print('数据有问题！')
        else:
            return int(str_nums[0]) * 8 + int(str_nums[1])

def bit_overturn(obj, num) -> str:
    s_list = [(obj)[i:i+2] for i in range(2,len(obj),2)]
    s_str =  ''.join(s_list[::-1])
    if s_str == '0':
        return '0'* num
    if len(s_str) < num:
        return s_str + '0'*(num-len(s_str))
    if len(s_str) == num:
        return s_str
    else:
        return None

def cut(obj, sec):
    obj = obj.replace(' ','')
    return [obj[i:i+sec] for i in range(0,len(obj),sec)]

def one_frame_analysis(json_dic, name, length, dataRaw):
    format_dic = {
        'total_bytes': json_dic['total_bytes'],
        'length': int(length),
        'format_str': '',
        "format_list": json_dic['format_list'],
        'data': str(dataRaw),
        'name': name,
        'unsized': False,
        'tran_text': f'{name}报文-> ',
    }
    if format_dic['total_bytes']:
        if format_dic['total_bytes'] > format_dic['length']:
            return f'解析错误-与配置文件的长度不符 {name}_total_bytes: {format_dic["total_bytes"]}'

    format_dic['format_str'], total_num = format_list_to_str(
        format_dic['format_list'], format_dic['total_bytes'], length, json_dic['data'])

    if length != total_num and format_dic['total_bytes'] != total_num:
        return f'解析失败-长度不一致{format_dic["format_str"]}'
    data_keys = list(json_dic['data'].keys())
    format_dic['data'] = format_dic['data'].replace(' ','')[:total_num*2]
    data = int(format_dic['data'], 16).to_bytes(total_num, byteorder="big", signed=False)
    pack = list(struct.unpack(format_dic['format_str'], data))
    
    format_dic['tran_text'] += translation_fun(json_dic, format_dic, data_keys, pack)
    # return (pack ,format_dic['format_list'] ,format_dic['format_str'], format_dic['tran_text'])
    return format_dic['tran_text']

def more_frame_analysis(json_dic, name, index, dataRaw):
    more_analysis_config['name'] = name
    text = ''
    if index in ['start', 'reply', 'end']:
        if len(dataRaw) != 8*2+7:
            text += f'{name}-{index}-长度解析错误'
            return text
        else:
            data_list = cut(dataRaw, 2)
    if index == 'start':
        more_analysis_config['total_num'] = int(data_list[3], 16)
        more_analysis_config['total_bytes'] = int(data_list[2]+data_list[1], 16)
        text += f'{name}-{index}-> 总包数: {more_analysis_config["total_num"]}, 总字节数: {more_analysis_config["total_bytes"]}'
        return text
    elif index == 'reply':
        if int(data_list[1], 16) == more_analysis_config['total_num']:
            text += f'{name}-{index}-> 总包数: {int(data_list[1], 16)}, 下面接收第{int(data_list[2], 16)}包'
            return text
        else:
            text += f'{name}-{index}-> 回应包数不正确, 总包数: {int(data_list[1], 16)}, 下面接收第{int(data_list[2], 16)}包'
            return text
    elif index == 'end':
        if int(data_list[3], 16) == more_analysis_config['total_num'] and \
            int(data_list[2]+data_list[1], 16) == more_analysis_config['total_bytes']: 
            more_analysis_config['name'] = ''
            more_analysis_config['total_num'] = None
            more_analysis_config['total_bytes'] = None
            text += f'{name}-{index}-> 接收完成，总包数: {int(data_list[3], 16)}, 总字节数: {int(data_list[2]+data_list[1], 16)}'
            return text
        else:
            more_analysis_config['name'] = ''
            more_analysis_config['total_num'] = None
            more_analysis_config['total_bytes'] = None
            text += f'{name}-{index}-> 数据错误，总包数: {int(data_list[3], 16)}, 总字节数: {int(data_list[2]+data_list[1], 16)}'
            return text
    else:
        if int(index) < more_analysis_config['total_num']:
            more_analysis_config['data'] += dataRaw[2:]
            return f'{name}报文-> 第{index}包'
        elif int(index) == more_analysis_config['total_num']:
            more_analysis_config['data'] += dataRaw[2:]
            length = more_analysis_config['total_bytes']
            data = more_analysis_config['data'][:(length)*2+length]
            more_analysis_config['data'] = ''
            if 'max_count' in json_dic.keys():
                json_dic['total_bytes'] = more_analysis_config['total_bytes']
                json_dic['format_list'], format_str, total_num = unsized_format(json_dic)
                return unsized_frame_analysis(json_dic, name, length, data, format_str, total_num)
            return one_frame_analysis(json_dic, name, length, data)
        else:
            return '包数不正确, 解析错误'

def format_list_to_str(format_list, total_bytes, length, json_dic):
    total_num = 0
    format_str = ''
    min_len = min([length, total_bytes])
    for num ,cell in enumerate(format_list):
        if min_len == total_num:
            break
        if cell == format_list[-1]:
            values = list(json_dic.keys())
            values = math.ceil(json_dic[values[-1]]['bytes/bit'][1])
            
            format_str += f'{values}s'
        else:
            values = format_list[num+1]-format_list[num]
            format_str += f'{values}s'
        total_num += values
    return (format_str, total_num)

def unsized_format(json_dic):
    format_list = [1]
    temp_list = []
    total_bytes = 0
    if json_dic['total_bytes']:
        for key in json_dic['data'].keys():
           temp_list.append(json_dic['data'][key]['bytes/bit'][1])
        while total_bytes != json_dic['total_bytes']:
            for temp in temp_list:
                format_list.append(format_list[-1]+temp)
                total_bytes += temp
        format_list = format_list[:-1]
        format_str, total_num = format_list_to_str(format_list, total_bytes, total_bytes, json_dic['data'])

    return (format_list, format_str, total_num)

def unsized_frame_analysis(json_dic, name, length, data, format_str, total_num):
    format_dic = {
        'total_bytes': json_dic['total_bytes'],
        'length': int(length),
        'format_str': format_str,
        "format_list": json_dic['format_list'],
        'data': str(data),
        'name': name,
        'unsized': True,
        'tran_text': f'{name}报文-> ',
    }
    text = ''
    if length != total_num:
        return f'解析失败-长度不一致{format_str}'
    data_keys = list(json_dic['data'].keys()) * int(len(cut(format_str, 2))/len(list(json_dic['data'].keys())))
    data = data.replace(' ','')[:total_num*2]
    data = int(data, 16).to_bytes(total_num, byteorder="big", signed=False)
    pack = list(struct.unpack(format_str, data))
    text += translation_fun(json_dic, format_dic, data_keys, pack)

    tran_list = text.split(f'{data_keys[0]}: ')
    format_dic['tran_text'] += f'{data_keys[0]}: '
    for cell in tran_list[1:]:
        cell = cell.replace('; ', '')
        format_dic['tran_text'] += cell + ', '
    return format_dic['tran_text'][:-2]

def analysis_dataRaw(data):
    if data['名称'].find("非标") != -1:
        return '非标未识别'
    elif data['名称'] == 'error':
        return '解析错误'

    elif data['名称'].find("-") != -1:
        name, index = data['名称'].split('-')
        return more_frame_analysis(data_js[name], name, index, data['数据(HEX)'])

    if data['名称'] in data_js.keys():
        if 'max_count' in data_js[data['名称']].keys():
            return f"{data['名称']}不定长报文未解析"
        return one_frame_analysis(data_js[data['名称']], data[0], data[1], data['数据(HEX)'])
 
'''
 description: 给名称一列赋值
 param {*} df pandas.Dataframe 对象 csv文件的数据
 return {*} pandas.Dataframe
'''
def set_msg_name(df):
    df['名称'] = df.loc[ : , ['名称', '帧ID', '数据长度', '数据(HEX)']].apply(param_msg_name, axis=1)
    return df

def set_meaning(df):
    for key_data in data_js.keys():
        data_js[key_data]['format_list'] = []
        for key in data_js[key_data]['data'].keys():
            if int(data_js[key_data]['data'][key]['bytes/bit'][0]) in data_js[key_data]['format_list']:
                continue
            else:
                data_js[key_data]['format_list'].append(int(data_js[key_data]['data'][key]['bytes/bit'][0]))

    for key_data in data_js.keys():
        for key in data_js[key_data]['data'].keys():
            if "options" in data_js[key_data]['data'][key].keys():
                data_js[key_data]['data'][key]['options'] = options_to_dic(data_js[key_data]['data'][key]['options'], data_js[key_data]['data'][key]['bytes/bit'][1])
                
            if 'components' in data_js[key_data]['data'][key].keys():
                for index in range(len(data_js[key_data]['data'][key]['components'])):
                    if 'options' in data_js[key_data]['data'][key]['components'][index].keys():
                        data_js[key_data]['data'][key]['components'][index]['options'] = \
                            options_to_dic(data_js[key_data]['data'][key]['components'][index]['options'],
                                data_js[key_data]['data'][key]['components'][index]['bytes/bit'][1]
                            )

    df['BMS报文翻译'] = df.loc[ :, ['名称', '数据长度', '数据(HEX)']].apply(analysis_dataRaw, axis=1)
    return df

def options_to_dic(s_options, is_intNum):
    options = s_options.replace(' ','').split(';')
    options_dic = {}
    if isinstance(is_intNum, int):
        s_str = '0x'
        for cell in options:
            key_dic, values = cell.split(':')
            key_dic = str(int((s_str + key_dic), 16))
            options_dic[key_dic] = values
    else: 
        s_str = '0b'
        for cell in options:
            key_dic, values = cell.split(':')
            key_dic = str(int((s_str + key_dic), 2))
            options_dic[key_dic] = values
    return  options_dic

if __name__ == "__main__":
    root = tk.Tk()  # 窗体对象
    root.withdraw()  # 窗体隐藏
    path = tk.filedialog.askopenfilename()
    path_check(path)
    file_path, file_name = os.path.split(path)  #路径切割, 得到路径和文件名

    data_js = read_json('./config/bmsConfig.json')
    csv_df = get_csv_data(path)
    bms_check(data_js)

    csv_df = set_msg_name(csv_df)
    csv_df = set_meaning(csv_df)

    csv_name = file_name.split('.')[0] + '-译.' + file_name.split('.')[-1]
    xlsx_name = file_name.split('.')[0] + '-译.xlsx'
    csv_df.to_csv(os.path.join(file_path, csv_name), index =None)
    # csv_df.to_excel(os.path.join(file_path, xlsx_name), index =None)
    