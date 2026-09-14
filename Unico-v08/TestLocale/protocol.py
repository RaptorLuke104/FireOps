"""Wire layout shared with wasm/protocol.h. Little endian, pack(1)."""
import struct, uuid
VERSION=2
MAX_FIRES=32
HEADER=struct.Struct('<IIII40s40s')
CELL=struct.Struct('<Idddf')
PACKET_SIZE=HEADER.size+MAX_FIRES*CELL.size
ACK=struct.Struct('<IIIIII')
def guid_bytes(value):
    return str(uuid.UUID(value)).upper().encode().ljust(40,b'\0') if value else bytes(40)
def pack_snapshot(state, flame, smoke, seq, test=False, altitude_bias=0):
    cells=state.get('fires',[])[:MAX_FIRES]
    data=HEADER.pack(VERSION,seq,len(cells),int(test),guid_bytes(flame),guid_bytes(smoke))
    for c in cells:
        data+=CELL.pack(c['id'],c['lat'],c['lon'],c['alt']+altitude_bias,c['hp'])
    return data+bytes((MAX_FIRES-len(cells))*CELL.size)
