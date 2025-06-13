# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description  : BMS报文翻译官
 Version      : 1.0
 Author       : liuyu 2543722345@qq.com
 Date         : 2023-02-09 09:17:00
 LastEditors  : liuyu 2543722345@qq.com
 LastEditTime : 2023-09-13 23:00:03
 FilePath     : \\bms-translator\\src\\main.py
 Copyright (C) 2023 by liuyu. All rights reserved.
'''

from decimal import Decimal
import json
import os
import re
import math
import sys
import tkinter as tk
from tkinter import messagebox
import struct
import csv
from check_sys import bms_check, path_check

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

csv_header = []

'''
 description: 读取json配置文件
 param {*} path 文件路径
 return {*} dict类型
'''
def read_json(path = 'bmsConfig·.json'):
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as fp:
            data = json.load(fp)
        return (data)
    else:
        messagebox.showerror('错误', '没有BMS配置文件, 下载配置文件请访问\nhttps://gitee.com/liuyu-git/bms-translator')
        return {}

'''
 description: pgn==0xec00, 多帧报文的开始 回应 结束的识别
 param {*} pgn  报文组编号
 param {*} bit  多帧报文的控制, 用于识别报文的开始 回应 结束
 param {*} dataRaw 报文源数据
 param {*} priority 报文组号的优先级
 return {*} 识别的多帧报文名称
'''
def set_more_frame_name(pgn, bit, dataRaw, priority):
    global data_js
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
    global data_js
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
                    return f'error{more_frame_config}'
                
    if receive_send not in [0xf456, 0x56f4]:
        return 'error'
    return '非标'

'''
 description: 检测数据是否为十六进制
 param {list} data = [数据, 十六进制正则表达式]
 return {bool}
'''
def hex_data_check(data: list) -> bool:
    for line in data:
        if re.match(line[1], line[0]) is None:
            return False
    if len(data[1][0])%2 != 0:
        return False
    return True

'''
 description: 解析帧ID 和 格式化报文源数据
 param {list} '名称', '帧ID', '数据长度', '数据(HEX)'
 return {string} 报文名称
'''
def param_msg_name(data:list):
    # 检测 帧ID 和 实际数据 是否为十六进制
    if hex_data_check([[data[1], '^0[xX][A-Fa-f0-9]{8}$|^[A-Fa-f0-9]{8}$'],
                    [str(data[3]).replace(' ',''), '^[A-Fa-f0-9]+$']]) is False:  
        return 'error'

    id = int(data[1], 16)          # 帧ID
    dataRaw = int(data[3].replace(' ',''), 16)      #数据(HEX)
    priority = (id >> 4*6) >> 2         # 优先级
    pgn = (id>>4*2) & 0xff00            # 获取组编号
    receive_send = (id & 0xffff)

    return find_bms_name(pgn, priority, receive_send, dataRaw)


'''
 description: 以字节划分的解析字段的翻译
 param {dict} json_dic: config.json 下的该报文的 对应的字段配置
 param {dict} format_dic: 该条报文下的解析基本信息
 param {str} key: 翻译报文下的具体字段名称; None: 报文中components字段翻译, 避免翻译多次字段名称
 param {int} byte: 对应具体字段的 数据
 param {int} index: 以匹配字符为参考系, 该字段在数据包中的位置
 return {str} 该字段的翻译结果
'''
def bytes_translation(json_dic:dict, format_dic:dict, key:str, byte:int, index:int): 
    global data_js
    text = ''
    # 选项翻译
    if 'options' in json_dic.keys():
        if str(byte) in json_dic['options'].keys():
            if key:
                text += f"{key}: {json_dic['options'][str(byte)]}; " 
            else:
                return json_dic['options'][str(byte)]
        else:
            return f"{key}: 无; "
    # 比率 偏移量 计算 翻译       
    elif 'ratio' in json_dic.keys():
        try:
            if Decimal(str(json_dic['offset'])) < 0 and "电流" in key:
                values = abs(Decimal(str(json_dic['offset']))) - Decimal(str(byte)) * Decimal(str(json_dic['ratio']))
            else:
                values = Decimal(str(byte)) * Decimal(str(json_dic['ratio'])) + Decimal(str(json_dic['offset']))
        except Exception:
            return f"{key}: 解析错误"
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
        # 压缩BCD码
        if json_dic['type'] == 'BCD':
            return hex(int(byte))[2:]
        # ascii码
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
                else:
                    s_data = int(s_data, 16)
                cell = bytes_translation(com, format_dic, None, s_data, index) # type: ignore
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
                        cell = bit_translation(com, None, byte, bit_Lenthg, [byte_start, byte_end]) # type: ignore
                        cell_list.append(str(cell))
                    byte_start, byte_end = 0, 0
            else:  
                for com in components:
                    range_list = com['bytes/bit']
                    byte_start = hexToBit(range_list[0]) - hexToBit(data_js[format_dic['name']]['format_list'][index]) - 1 # type: ignore
                    byte_end = byte_start + hexToBit(range_list[1]) # type: ignore
                    cell = bit_translation(com, None, byte, bit_Lenthg, [byte_start, byte_end]) # type: ignore
                    cell_list.append(str(cell))
            text += schema_to_str(json_dic['schema'], cell_list, key)
        else:
            text += f"{key}: 错误; "
    if text == '':
        text = f'{key}: 未解析; '
    return str(text)

'''
 description: 将components的解析结果，按照schema翻译模板进行翻译
 param {list} schema: [翻译顺序1: 正序; -1: 逆序, 翻译模板]
 param {list} cell_list: [components的解析结果]
 param {str} key: 字段名称
 return {str} 翻译结果
'''
def schema_to_str(schema:list, cell_list:list, key:str):
    text = ''
    way = int(schema[0])
    tran_packs = schema[1].split('~')
    text += f'{key}: '
    for cell, pack in zip(cell_list[::way], tran_packs[:-1]):
        text = text + pack + str(cell)
    text += f'{tran_packs[-1]}; '
    return text

'''
 description: 以位划分的解析字段的翻译
 param {dict} json_dic: 报文字段下的配置
 param {str} key: 字段名称
 param {int} byte: 字段数据, 这里是字节数据
 param {int} bit_Lenthg: 字节数据的长度
 param {list} range_list: 位数据在字节中的范围
 return {str} 翻译结果
'''
def bit_translation(json_dic:dict, key:str, byte:int, bit_Lenthg:int, range_list:list):
    text = ''
    bit_fun_str =  '0b'+ '0'* (bit_Lenthg - range_list[1])+ '1'* (range_list[1]-range_list[0]) + '0'* range_list[0] 
    bit_int = (byte & int(bit_fun_str, 2)) >> range_list[0] # 位运算 截取该字段的数据
    
    if 'options' in json_dic.keys():  
        if str(bit_int) in json_dic['options'].keys():
            if key:
                text += f"{key}: {json_dic['options'][str(bit_int)]}; " 
            else:
                return json_dic['options'][str(bit_int)]
        else:
            return f"bit解析错误-{key}options, bit_Lenthg:{bit_Lenthg}-byte:{byte}-range_list:{range_list}-{bit_int}-items{json_dic['options']}; "
    elif 'ratio' in json_dic.keys():
            if Decimal(str(json_dic['offset'])) < 0 and "电流" in key:
                values = abs(Decimal(str(json_dic['offset']))) - Decimal(str(bit_int)) * Decimal(str(json_dic['ratio']))
            else:
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

'''
 description: 将解析好的数据包 依次 按照config配置进行翻译
 param {dict} json_dic: 该报文的配置信息
 param {dict} format_dic: 该报文的解析信息
 param {list} data_keys: 报文下的字段名称列表
 param {list} pack: 对应该报文的数据包列表
 return {str} 该条报文的翻译结果
'''
def translation_fun(json_dic:dict, format_dic:dict, data_keys:list, pack:list) ->str:
    global data_js
    text = ''
    for index in range(len(pack)):
        key = data_keys[index]
        pack[index] = int.from_bytes(pack[index], 'little')
        if isinstance(json_dic['data'][key]['bytes/bit'][1], int):
            text += bytes_translation(json_dic['data'][key], format_dic, key, pack[index], index) # type: ignore
            
        elif isinstance(json_dic['data'][key]['bytes/bit'][1], float):
            bit_Lenthg = int(cut(format_dic['format_str'], 2)[index][0]) * 8
            range_list = json_dic['data'][key]['bytes/bit']
            byte_start = hexToBit(range_list[0]) - hexToBit(data_js[format_dic['name']]['format_list'][index]) - 1 # type: ignore
            byte_end = byte_start + hexToBit(range_list[1]) # type: ignore
            
            text += bit_translation(json_dic['data'][key], key, pack[index], bit_Lenthg, [byte_start, byte_end]) # type: ignore
        else:
            return f"json_error {json_dic['data'][key]['bytes/bit']}, {format_dic['format_str']}, {format_dic['name']}"
    
    return text[:-2]  # 去掉翻译后最后一个 "; "

'''
 description: "bytes/bit"字段下的数值, 更改成位的形式
 param {str} num: "bytes/bit"字段下的数值
 return {int} 位
'''
def hexToBit(num) -> int: # Removed type hint for num to allow flexibility
    if isinstance(num, float) :
        str_nums = str(num).split('.')
        if len(str_nums[1]) != 1 or int(str_nums[1]) >= 8:
            print('数据有问题！')
            return 0
        else:
            return int(str_nums[0]) * 8 + int(str_nums[1])
    elif isinstance(num, int):
        return num * 8
    elif isinstance(num, str): # Added check for string type
        if '.' in num:
            str_nums = str(num).split('.')
            if len(str_nums[1]) != 1 or int(str_nums[1]) >= 8:
                print('数据有问题！')
                return 0
            else:
                return int(str_nums[0]) * 8 + int(str_nums[1])
        else: # If it's a string without a decimal, try converting to int
            try:
                return int(num) * 8
            except ValueError:
                print('数据有问题！无法转换为整数。')
                return 0
    return 0

'''
 description: 将字符串obj前两位去掉, 按照步数为2进行划分, 将划分结果颠倒并补全长度, 使之长度为num
 param {str} obj: 要划分颠倒的字符串
 param {int} num: 设置返回字符串的长度
 return {str}
'''
def bit_overturn(obj:str, num:int) -> str:
    s_list = [(obj)[i:i+2] for i in range(2,len(obj),2)]
    s_str =  ''.join(s_list[::-1])
    if s_str == '0':
        return '0'* num
    if len(s_str) < num:
        return s_str + '0'*(num-len(s_str))
    if len(s_str) == num:
        return s_str
    else:
        return ''

'''
 description: 将字符串obj 按照给定长度划分成列表
 param {str} obj: 字符串
 param {int} sec: 步长
 return {list} 分隔后的列表
'''
def cut(obj:str, sec:int) ->list:
    obj = obj.replace(' ','')
    return [obj[i:i+sec] for i in range(0,len(obj),sec)]


'''
 description: 单帧报文的解析
 param {dict} json_dic: 该报文的配置信息
 param {str} name: 该报文的名称
 param {int} length: 该报文的长度
 param {str} dataRaw: 该报文未解析的数据
 return {str} 翻译结果
'''
def one_frame_analysis(json_dic:dict, name:str, length:int, dataRaw:str):
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
    # data = int(format_dic['data'], 16).to_bytes(total_num, byteorder="big", signed=True)
    if len(format_dic['data']) < total_num*2:
        format_dic['data'] += (total_num*2-len(format_dic['data'])) * '0'
    if len(format_dic['data']) > total_num*2:
        format_dic['data'] = format_dic['data'][:total_num*2]
    data = bytes.fromhex(format_dic['data'])
    pack = list(struct.unpack(format_dic['format_str'], data))
    format_dic['format_str'] = format_dic['format_str'][1:]

    format_dic['tran_text'] += translation_fun(json_dic, format_dic, data_keys, pack)

    return format_dic['tran_text']


'''
 description: 多帧报文的翻译
 param {dict} json_dic: 该报文的配置信息
 param {str} name: 该报文的名称
 param {str} index: 该数据在 多帧报文的位置
 param {str} dataRaw: 未解析的数据
 return {str} 翻译结果
'''
def more_frame_analysis(json_dic:dict, name:str, index:str, dataRaw:str):
    more_analysis_config['name'] = name
    text = ''
    if index in ['start', 'reply', 'end']:
        if len(dataRaw.replace(' ', '')) != 8*2:
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
            text += f'{name}-{index}-> 接收完成，总包数: {int(data_list[3], 16)}, 总字节数: {int(data_list[2]+data_list[1], 16)}'
        else:
            text += f'{name}-{index}-> 数据错误，总包数: {int(data_list[3], 16)}, 总字节数: {int(data_list[2]+data_list[1], 16)}'
        # 多帧报文的最后一帧，全局变量归零
        more_analysis_config['name'] = ''
        more_analysis_config['total_num'] = None
        more_analysis_config['total_bytes'] = None
        return text
    else:
        # index是数值，将未解析的数据放在一起
        if int(index) < more_analysis_config['total_num']:
            more_analysis_config['data'] += dataRaw[2:]
            return f'{name}报文-> 第{index}包'
        
        # 最后一包数据，多帧数据合并 调用单帧报文解析函数
        elif int(index) == more_analysis_config['total_num']:
            more_analysis_config['data'] += dataRaw[2:]
            length = more_analysis_config['total_bytes']
            data = more_analysis_config['data'][:(length)*2+length]
            more_analysis_config['data'] = ''
            # 如果是不定长度的报文，多帧数据合并 调用 unsized_frame_analysis函数
            if 'max_count' in json_dic.keys():
                json_dic['total_bytes'] = more_analysis_config['total_bytes']
                #得到解析不定长报文的 解析信息
                json_dic['format_list'], format_str, total_num = unsized_format(json_dic) # type: ignore
                return unsized_frame_analysis(json_dic, name, data, format_str)
            return one_frame_analysis(json_dic, name, length, data)
        else:
            return '包数不正确, 解析错误'

'''
 description: 将各支段的间隙 转换成 解析匹配字符
 param {list} format_list: 给字段的位置列表
 param {int} total_bytes: 配置文件中的最大字段
 param {int} length: 报文实际长度
 param {dict} json_dic: 该报文的配置信息
 return {tuple} (解析匹配字符, 解析匹配字符含有的字节长度)
'''
def format_list_to_str(format_list:list, total_bytes:int, length:int, json_dic:dict):
    total_num = 0
    format_str = '!'
    min_len = min([length, total_bytes]) # 取最小长度
    for num ,cell in enumerate(format_list):
        if min_len == total_num:
            break
        if cell == format_list[-1]:
            values = list(json_dic.keys())
            # 向上取整
            values = math.ceil(json_dic[values[-1]]['bytes/bit'][1]) 
            format_str += f'{values}s'
        else:
            values = format_list[num+1]-format_list[num]
            format_str += f'{values}s'
        total_num += values
    return (format_str, total_num)

'''
 description: 获得不定长度的报文 解析匹配信息
 param {list} json_dic: 报文配置信息, 其中total_bytes是报文的实际长度
 return {*}
'''
def unsized_format(json_dic:dict):
    format_list = [1]
    temp_list = []
    total_bytes = 0
    if 'total_bytes' in json_dic and json_dic['total_bytes']: # Check if 'total_bytes' exists and is not None/0
        for key in json_dic['data'].keys(): # type: ignore
           temp_list.append(json_dic['data'][key]['bytes/bit'][1]) # type: ignore
        while total_bytes != json_dic['total_bytes']: # type: ignore
            for temp in temp_list:
                format_list.append(format_list[-1]+temp)
                total_bytes += temp
        format_list = format_list[:-1]
        format_str, total_num = format_list_to_str(format_list, total_bytes, total_bytes, json_dic['data']) # type: ignore
    else: # Added else block to ensure all paths return values
        return (format_list, '', 0) # Return default values if 'total_bytes' is not present or is None/0

    return (format_list, format_str, total_num)

'''
 description: 不定长度报文的解析和翻译
 param {dict} json_dic: 该报文的配置信息
 param {str} name: 该报文的名称
 param {str} data: 该报文未解析的数据
 param {str} format_str: 该报文的 解析匹配字符
 return {*} 不定长度报文的翻译
'''
def unsized_frame_analysis(json_dic:dict, name:str, data:str, format_str:str):
    format_dic = {
        'total_bytes': json_dic['total_bytes'],
        'length': json_dic['total_bytes'],
        'format_str': format_str,
        "format_list": json_dic['format_list'],
        'data': str(data),
        'name': name,
        'unsized': True,
        'tran_text': f'{name}报文-> ',
    }
    total_num = json_dic['total_bytes'] # Removed unused 'length' variable
    text = ''
    data_keys = list(json_dic['data'].keys()) * int(len(cut(format_str, 2))/len(list(json_dic['data'].keys())))
    data = data.replace(' ','')[:total_num*2]
    data = int(data, 16).to_bytes(total_num, byteorder="big", signed=False) # type: ignore
    pack = list(struct.unpack(format_str, data)) # type: ignore
    text += translation_fun(json_dic, format_dic, data_keys, pack)

    tran_list = text.split(f'{data_keys[0]}: ')
    format_dic['tran_text'] += f'{data_keys[0]}: '
    for cell in tran_list[1:]:
        cell = cell.replace('; ', '')
        format_dic['tran_text'] += cell + ', '
    return format_dic['tran_text'][:-2]


'''
 description: 通过名称一列的内容给数据翻译
 param {*} data ['名称', '数据长度', '数据(HEX)']
 return {*} 翻译结果
'''
def analysis_dataRaw(data:list):
    global data_js
    # 分隔数据前一定要去除空格，不然影响解析
    data[2] = data[2].replace(' ', '')
    if data[0] == '非标':
        return '非标未识别'
    elif data[0] == 'error':
        return '解析错误'
    
    elif '-' in data[0]:
        name, index = data[0].split('-')
        try:
            s_re =  more_frame_analysis(data_js[name], name, index, data[2]) # type: ignore
        except Exception:
            s_re = '解析失败-002'
        return s_re

    if data[0] in data_js.keys(): # type: ignore
        if 'max_count' in data_js[data[0]].keys(): # type: ignore
            return f"{data[0]}不定长报文未解析"
        s_re =  one_frame_analysis(data_js[data[0]], data[0], data[1], data[2]) # type: ignore
        return s_re
'''
 description: 给名称一列赋值
 param {*} df csv文件的数据
 return {*} 文件数据
'''
def set_msg_name(df, id_place, data_place):
    data_place = int(data_place)
    id_place = int(id_place)
    for line in df:
        # 名称, 帧ID, 数据长度, 数据(HEX)
        name = param_msg_name(['', line[id_place-1], int(len(line[data_place-1].replace(' ', ''))), line[data_place-1]])
        line.insert(id_place-1, name)
    return df

'''
 description: 在报文下生成format_list字段为之后生成 解析匹配字符串提供方便, 
              给options字段解析成字典方便翻译工作, 给名称一列赋值
 param {*} df 文件数据
 return {*} 加上翻译列的文件数据
'''
def set_meaning(df, id_place, data_place):
    global data_js
    data_place = int(data_place)
    id_place = int(id_place)
    # 生成各报文 各支段下的位置间隙列表
    for key_data in data_js.keys(): # type: ignore
        data_js[key_data]['format_list'] = [] # type: ignore
        for key in data_js[key_data]['data'].keys(): # type: ignore
            if int(data_js[key_data]['data'][key]['bytes/bit'][0]) in data_js[key_data]['format_list']: # type: ignore
                continue
            else:
                data_js[key_data]['format_list'].append(int(data_js[key_data]['data'][key]['bytes/bit'][0])) # type: ignore
    # 将options字段的字符串 解析成 字典
    for key_data in data_js.keys(): # type: ignore
        for key in data_js[key_data]['data'].keys(): # type: ignore
            if "options" in data_js[key_data]['data'][key].keys(): # type: ignore
                data_js[key_data]['data'][key]['options'] = options_to_dic(data_js[key_data]['data'][key]['options'], data_js[key_data]['data'][key]['bytes/bit'][1]) # type: ignore
            if 'components' in data_js[key_data]['data'][key].keys(): # type: ignore
                for index in range(len(data_js[key_data]['data'][key]['components'])): # type: ignore
                    if 'options' in data_js[key_data]['data'][key]['components'][index].keys(): # type: ignore
                        data_js[key_data]['data'][key]['components'][index]['options'] = \
                            options_to_dic(data_js[key_data]['data'][key]['components'][index]['options'], # type: ignore
                                data_js[key_data]['data'][key]['components'][index]['bytes/bit'][1]) # type: ignore
    for line in df:
        # 名称, 数据长度, 数据(HEX)
        line.append(analysis_dataRaw([line[id_place-1], int(len(line[data_place].replace(' ', ''))), line[data_place]]))
    return df

'''
 description: 将options字段的字符串 解析成 字典
 param {str} s_options: options字段的字符串
 param {int} is_intNum: options字段所占用的大小
 return {*} 解析好的字典
'''
def options_to_dic(s_options:str, is_intNum:int):

    options = s_options.replace(' ','').split(';')
    options_dic = {}
    # 如果占用大小是字节
    if isinstance(is_intNum, int):
        s_str = '0x'
        for cell in options:
            key_dic, values = cell.split(':')
            key_dic = str(int((s_str + key_dic), 16))
            options_dic[key_dic] = values
    # 如果占用大小是位
    else: 
        s_str = '0b'
        for cell in options:
            key_dic, values = cell.split(':')
            key_dic = str(int((s_str + key_dic), 2))
            options_dic[key_dic] = values
    return  options_dic

'''
 description: 读取csv文件
 param {str} path: 文件路径
 return {list} 文件数据 get_text_encoding(path)
'''
def get_CSV_data(path:str):
    global csv_header
    maxlen = 0
    with open(path, "r", encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        data = []
        for line in csv_reader:
            if len(line) > maxlen:
                maxlen = len(line)
            data.append(line)
    return data

'''
 description: 将解析翻译好的文件数据, 以“UTF-8”编码重新写入一个csv格式的文件
 param {str} fileName: 新的文件名
 param {list} data: 文件数据
 param {list} head: 文件的表头
 return {*} None
'''
def write_csv(fileName:str, data:list, head:list):
    f = open(fileName,'w', encoding='utf-8', newline='')
    # 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(f)
    csv_writer.writerow(head)
    for line in data:
        csv_writer.writerow(line)
    f.close()

'''
 description: 通过文件表头自动判断文件的编码，并返回
 param {str} path: 文件路径
 return {str} 文件编码
'''

def main_prase(csv_df:list, id_place:int, data_place:int, bmsConfig:dict):
    global data_js

    data_js = bmsConfig

    csv_df = set_msg_name(csv_df, id_place, data_place)  # 获取名称列
    csv_df = set_meaning(csv_df, id_place, data_place)   # 获取翻译列

    return csv_df
    