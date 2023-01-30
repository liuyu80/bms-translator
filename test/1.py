import struct, bitstring

data = '04 00 A0 0F 00 00 FD'
data = int(data.replace(' ','')[:7*2], 16).to_bytes(7, byteorder="big", signed=False)
print(data)
# print(struct.unpack('3s', data))
pack = (struct.unpack('1s 1s 1s 1s 1s 1s 1s', data))
for cell in pack:
    print(int.from_bytes(cell, 'little'), '  ')

print(pack)
# # data = int(data.replace(' ',''), 16)
# b = '0'*7 + bin(int.from_bytes(pack[2], 'little'))[2:]
# print(b, type(b))
# b = b
# print(b,int(b[-12:], 2))
# print(int(b[12:], 2))


# pack = struct.pack('')