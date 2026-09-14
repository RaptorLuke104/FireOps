#pragma once
#include <stdint.h>
#pragma pack(push,1)
struct FireCell { uint32_t id; double lat,lon,alt; float hp; };
struct Snapshot {
    uint32_t version,seq,count,test;
    char flame[40],smoke[40];
    FireCell cells[32];
};
struct BridgeAck { uint32_t version,seq,heartbeat,live,failed,lastException; };
#pragma pack(pop)
static_assert(sizeof(FireCell)==32,"FireCell ABI");
static_assert(sizeof(Snapshot)==1120,"Snapshot ABI");
static_assert(sizeof(BridgeAck)==24,"Ack ABI");
