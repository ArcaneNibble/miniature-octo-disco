# GATT
service 0xFFF0 characteristic 0xFFF2 --> commands
service 0xFFF0 characteristic 0xFFF1 --> responses

# packet format (both commands and responses)
`0xB4 0x4B len type <payload> csum`
len -> number of bytes in payload
csum -> add all of the previous bytes in the packet and truncate to 1 byte

# fragmented bulk data (within payloads)
send cmd 0x14 first?
`cur_key_i cur_pkt_i_2bytes <inner> csum`
csum is sometimes over just inner, sometimes includes the `cur_` as well
fragmented into chunks of 12 bytes (at least when sending to the device)

inner contents:
`tot_keys tot_pkts_2bytes <real_payload>`

# strings
1 byte len + string (GB2312?)

# commands
## cmd 0x01		GET_DEVICE_MSG
payload is 8 bytes `BCD yyyyMMddHHmmss + day-of-week`
reply 0x02 and 0x0E
reply 0x02 RETURN_DEVICE_MSG
	`<mac address 6 bytes> <charge in bars?> <hardware ver> <production batch 4 bytes> <firmware ver> <init> <state (whether bark-stop is enabled)>`
reply 0x0E
	fragmented bulk data
 	`<pet name str>`

## reply 0x03	ACK
payload is 1 byte
	0x00 = ok
	0x01 = error? bad command?
	0x06 = error? bad checksum?
	0x0a = shock cooldown

## cmd 0x06		SET_CONFIG (bark stop training)
	fragmented bulk data
	`db voice_2bytes volume vibration shock`
	key 1 = repetitive
	key 2 = progressive 1st bark
	key 3 = progressive 2nd bark
	key 4 = progressive 3rd bark
	checksum DOES include current

## cmd 0x07		GET_CONFIG (bark stop training)
reply 0x08 RETRUN_CONFIG (RETURN_CONFIG?)
	fragmented bulk data
	`db voice_2bytes volume vibration shock`
	key 1 = repetitive
	key 2 = progressive 1st bark
	key 3 = progressive 2nd bark
	key 4 = progressive 3rd bark

## cmd 0x0A		GET_RECORD
payload is 7 bytes `BCD yyyyMMddHHmmss`
reply 0x0B RETRUN_RECORD (RETURN_RECORD?)
	fragmented bulk data
	`yyyy MM dd HH mm ss ??  db sound shock ultrasonic`

## cmd 0x0C		CLEAR_RECORD

## cmd 0x0D		SET_NAME
	fragmented bulk data
	`<pet name str>`
	checksum does NOT include current

## cmd 0x0F		TEST_SHOCK (vibrate)
payload is 1 byte of vibration intensity (1, 2, 3)

## cmd 0x10		TEST_ESHOCK (shock)
payload is 1 byte of shock intensity [1-99]

## cmd 0x11		SET_DB
payload is 7 bytes
`db open h1 m1 h2 m2 tzoff`
not sure what open or the times do?

## cmd 0x13		GET_DB
reply 0x12
`db open h1 m1 h2 m2 tzoff`
not sure what open or the times do?

## cmd 0x14		DATA_MODE
	seems to be sent before certain commands?

## cmd 0x15		TEST_DB (start/stop real-time db measurement)
payload is 1 byte 0/1
reply 0x16
	`cur_db <unk bytes 8b>`

## cmd 0x1b		SET_DB_STATE (set "stop barking" enable/disable/timer)
payload is 7 bytes
	00 00  00 00 00 00 00	disable
	01 01  00 00 00 00 00	enable now
	00 01  yy MM dd HH mm	enable later

## cmd 0x22		GET_ALL_CONFIG
reply 0x21
	AA BB XX XX XX XX XX CC DD EE FF GG HH II

## cmd 0x25		GET_VOICE_NAME
reply 0x24
	fragmented bulk data
	`<voice num 2 bytes> <voice name str>`

## cmd 0x27		SET_DEVICE_SETTING	(settings for the remote control button)
payload
	fragmented bulk data
	`db voice_2bytes volume vibration shock`

## cmd 0x28		GET_DEVICE_SETTING	(settings for the remote control button)
reply 0x29
	fragmented bulk data
	`db voice_2bytes volume vibration shock`

## cmd 0x2A		RUN_DEVICE	(remote control button)

## cmd 0x2B		SET_STATE_MODE (set training mode)
payload is 1 byte
	0 = repetitive
	1 = progressive

## cmd 0x2C		GET_STATE_MODE
reply 0x2D 1 byte


# examples
B4 4B 01 10 30 40 --> shock with intensity 48
