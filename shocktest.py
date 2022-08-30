import asyncio
import binascii
from bleak import BleakClient
import struct

address = "68:35:32:39:29:7F"
DEV_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"

SHOCK_SERV_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
RESPONSE_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
COMMAND_CHAR_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"

def unpack_frame(inp):
    if len(inp) < 5:
        return (None, None)

    magic0, magic1, payload_len, type_ = inp[:4]

    if magic0 != 0xb4:
        return (None, None)
    if magic1 != 0x4b:
        return (None, None)

    payload = inp[4:4 + payload_len]
    csum = inp[4 + payload_len:]

    if len(payload) != payload_len:
        return (None, None)

    if len(csum) < 1:
        return (None, None)

    csum = csum[0]
    actual_sum = 0
    for b in inp[:4 + payload_len]:
        actual_sum += b
    if (actual_sum & 0xFF) != csum:
        return (None, None)

    return (type_, payload)

def pack_frame(type_, payload):
    pkt = b'\xb4\x4b' + bytes([len(payload), type_]) + payload

    csum = 0
    for b in pkt:
        csum += b
    pkt += bytes([csum & 0xff])

    return pkt

def fragment_packet(payload, key=1, num_keys=1, checksum_all=False):
    FRAG_SZ = 12
    tot_len = len(payload) + 4
    num_packets = (tot_len + FRAG_SZ - 1) // FRAG_SZ

    payload = struct.pack(">BH", num_keys, num_packets) + payload
    csum = 0
    for b in payload:
        csum += b
    if checksum_all:
        assert num_packets == 1
        csum += 1
        csum += key
    payload += bytes([csum & 0xff])

    frags = []
    for i in range(num_packets):
        pkt = payload[i * FRAG_SZ:(i + 1) * FRAG_SZ]
        pkt = struct.pack(">BH", key, i + 1) + pkt
        frags.append(pkt)

    return frags

async def main(address):
    async with BleakClient(address) as client:
        dev_name = await client.read_gatt_char(DEV_NAME_UUID)
        print("Model Number: {0}".format("".join(map(chr, dev_name))))

        services = await client.get_services()
        shock_service = services.get_service(SHOCK_SERV_UUID)
        print(shock_service)

        response_characteristic = shock_service.get_characteristic(RESPONSE_CHAR_UUID)
        command_characteristic = shock_service.get_characteristic(COMMAND_CHAR_UUID)
        print(response_characteristic, command_characteristic)

        def reply_cb(_handle, data):
            # print(f"resp {binascii.hexlify(data)}")

            resp_type, resp_payload = unpack_frame(data)
            if resp_type is None:
                print(f"INVALID resp {binascii.hexlify(data)}")
            else:
                print(f"resp type {resp_type} payload {binascii.hexlify(resp_payload)}")

        await client.start_notify(response_characteristic, reply_cb)

#         # await client.write_gatt_char(command_characteristic, b'\xb4\x4b\x00\x2a\x29', False)

#         # await client.write_gatt_char(command_characteristic, b'\xb4\x4b\x00\x10\x0f', False)
#         # await client.write_gatt_char(command_characteristic, b'\xb4\x4b\x01\x10\x30\x40', False)

        # await client.write_gatt_char(command_characteristic, b'\xb4\x4b\x01\x0f\x01\x10', False)

        # await client.write_gatt_char(command_characteristic, pack_frame(16, bytes([30])), False)

        # await client.write_gatt_char(command_characteristic, pack_frame(1, bytes([0, 0, 0, 0, 0, 0, 0, 0])), False)
        # await client.write_gatt_char(command_characteristic, pack_frame(43, bytes([0])), False)
        # await client.write_gatt_char(command_characteristic, pack_frame(44, b''), False)

        # await client.write_gatt_char(command_characteristic, pack_frame(1, bytes([0, 0, 0, 0, 0, 0, 0, 0])), False)
        # await client.write_gatt_char(command_characteristic, pack_frame(32, b''), False)

        # await client.write_gatt_char(command_characteristic, pack_frame(20, b''), False)
        # await client.write_gatt_char(command_characteristic, pack_frame(39, fragment_packet(b'\x3c\x00\x01\xff\xff\x20')[0]), False)

        # await client.write_gatt_char(command_characteristic, pack_frame(20, b''), False)
        # await client.write_gatt_char(command_characteristic, pack_frame(13, fragment_packet(b'\x01A')[0]), False)

        await client.write_gatt_char(command_characteristic, pack_frame(20, b''), False)
        await client.write_gatt_char(command_characteristic, pack_frame(6, fragment_packet(b'\x3c\x00\x01\xff\xff\x10', 1, 4, True)[0]), False)
        await client.write_gatt_char(command_characteristic, pack_frame(6, fragment_packet(b'\x3c\x00\x01\xff\xff\x20', 2, 4, True)[0]), False)
        await client.write_gatt_char(command_characteristic, pack_frame(6, fragment_packet(b'\x3c\x00\x01\xff\xff\x30', 3, 4, True)[0]), False)
        await client.write_gatt_char(command_characteristic, pack_frame(6, fragment_packet(b'\x3c\x00\x01\xff\xff\x40', 4, 4, True)[0]), False)
        # await asyncio.sleep(10)

asyncio.run(main(address))
