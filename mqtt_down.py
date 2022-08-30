import asyncio
import asyncer
import binascii
from bleak import BleakClient
import paho.mqtt.client as mqtt
import pyotp
import json


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


async def ble_connect(address):
	# async with BleakClient(address) as client:
	client = BleakClient(address)
	await client.connect()

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

	return (client, command_characteristic)


# ble_client, command_characteristic = asyncer.syncify(ble_connect)(address)
loop_ = asyncio.get_event_loop()
co_ = ble_connect(address)
ble_client, command_characteristic = loop_.run_until_complete(co_)
print(ble_client)


totp = pyotp.TOTP('base32secret3232')

lastKey = None

async def doOutput(message):
	global lastKey

	if (message["value"] != lastKey):
		lastKey = message["value"]

		print("testtesttest")
		try:
			await ble_client.write_gatt_char(command_characteristic, pack_frame(16, bytes([30])), False)
		except Exception as e:
			print(e)

endpoint_name = "test/output/electrical"

machine_id = "supertestpleaseign"

mqttc = mqtt.Client(machine_id, clean_session=False)
mqttc.connect("broker.hivemq.com", 1883)
mqttc.subscribe(endpoint_name, qos=1)

def on_disconnect(client, userdata, rc):
	if rc != 0:
		print("Unexpected MQTT disconnection. Will auto-reconnect")

def on_message(client, userdata, msg):
	if msg.topic == endpoint_name:
		try:
			message = json.loads(msg.payload.decode())
			if totp.verify(message["value"]):
				# asyncer.syncify(doOutput)(message)
				loop_ = asyncio.get_event_loop()
				co_ = doOutput(message)
				loop_.run_until_complete(co_)
		except json.JSONDecodeError:
			pass
		
#mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_disconnect = on_disconnect
mqttc.loop_forever()
