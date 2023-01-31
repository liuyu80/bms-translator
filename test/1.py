import struct

data = 'FD'

data = int(data.replace(' ',''), 16).to_bytes(int(len(data)/2), byteorder="big", signed=False)
print(data)
# print(struct.unpack('3s', data))
pack = list(struct.unpack('1s', data))
for num in range(len(pack)):
    pack[num] = int.from_bytes(pack[num], 'little')


def cut(obj, sec):
    return [obj[i:i+sec] for i in range(0,len(obj),sec)]


range_list = [6.7, 0.2]
range_list = [int(str(range_list[0])[-1])-1, int(str(range_list[1])[-1])+ int(str(range_list[0])[-1])-1]

def bit_overturn(obj, num) -> str:
    s_list = [(obj)[i:i+2] for i in range(2,len(obj),2)]
    print(s_list)
    s_str =  ''.join(s_list[::-1])
    if s_str == '0':
        return '0'* num
    if len(s_str) < num:
        return s_str + '0'*(num-len(s_str))
    if len(s_str) == num:
        return s_str
    else:
        return None

def hexToBit(num) -> int:
    if isinstance(num, float):
        str_nums = str(num).split('.')
        if len(str_nums[1]) != 1 or int(str_nums[1]) >= 8:
            print('数据有问题！')
        else:
            return int(str_nums[0]) * 8 + int(str_nums[1])
    elif isinstance(num, int):
        return num * 8

print(hexToBit(7.1))