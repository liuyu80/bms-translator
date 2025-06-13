import math, json, os, sys
import operator

need_keys = [
    "describe", "PGN", "priority", "total_bytes",
    "receive_send", "optional_count", "data"
]
receive_send_values = [0xf456, 0x56f4]

necessarykeys = [
    ["ratio", "offset", "unit_symbol"],
    ['components', 'schema']
]
def path_check(path):
    if path == '':
        print('路径为空')
        sys.exit()
    file_path, file_name = os.path.split(path)
    name, style = os.path.splitext(file_name)
    if style not in ('.CSV', '.csv'):
        print('文件名不正确')
        sys.exit()
    if name[-2:] == '-译':
        print('该文件已翻译, 请选择要翻译的报文文件')
        sys.exit()


def bms_check(dic):
    for key in dic.keys():
        for need in need_keys:
            if need not in dic[key].keys():
                print(f'{key}缺少{need}字段')
        if int(dic[key]['receive_send'], 16) not in receive_send_values:
            print(f"{key}的receive_send的值{dic[key]['receive_send']}不对")
            sys.exit()
        if dic[key]['priority'] > 7 or dic[key]['priority'] < 0:
            print(f"{key}的priority的值{dic[key]['priority']}不对")
            sys.exit()
        
        #data字段里的检查
        for cell in dic[key]['data'].keys():
            if "bytes/bit" not in dic[key]['data'][cell].keys():
                print(f"{key} 下的 {cell} 缺少bytes/bit字段")
            if "components" in dic[key]['data'][cell].keys():
                for line in dic[key]['data'][cell]["components"]:
                    if "bytes/bit" not in line.keys():
                        print(f"{key} 的 {cell} 的components 缺少bytes/bit字段")
                        sys.exit()
            for line in necessarykeys: 
                find_cell_keys = list(set(dic[key]['data'][cell].keys()) & set(line))
                if not operator.eq(sorted(find_cell_keys), sorted(line)):
                    if len(find_cell_keys):
                        print(f"{key} 下的 {cell} 有不正确字段")
                        sys.exit()

def beal_bytesBit(nums:list):
    if len(nums)> 2:
        print(nums,"大于2")
        return False
    if isinstance(nums[0], int) and isinstance(nums[1], int):
        return nums[0] + nums[1]
    if isinstance(nums[0], float) and isinstance(nums[1], float):
        bit1, bytes1 = math.modf(round(nums[1], 1))
        bit0, bytes0 = math.modf(round(nums[0], 1))
        bit0 *= 10
        bit1 *= 10
        if math.ceil(bit0 + bit1) >= 8:
            return round((bytes0 + bytes1 +1) + (math.ceil(bit0 + bit1) - 8)/10, 1)
        else:
            return round((bytes0 + bytes1) + (bit0 + bit1)/10, 1)
    print(nums,"数据类型不一致")
    return False

def read_json(path = 'bmsConfig.json'):
    with open(path, "r", encoding='utf-8') as fp:
        data = json.load(fp)
        return (data)

if __name__ == "__main__":
    global json_data
    json_data = read_json('./config/bmsConfig.json')
    # csv_df = get_csv_data('./data/BVIN1枪.CSV')
    bms_check(json_data)
