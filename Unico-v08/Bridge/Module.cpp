// FireOps bridge adapted to the supplied SDK 1.7.3 StandaloneModule sample.
// Replaces Module.cpp; do NOT add another source defining module_init/module_deinit.
#include <MSFS/MSFS.h>
#include <MSFS/MSFS_WindowsTypes.h>
#include "VfxSdk.h"
#include <SimConnect.h>
#include "Module.h"
#include <cstring>
#include <cstdio>
#include <cmath>
#include "protocol.h"
#include "UnifiedParams.h"

static HANDLE sc=0;
static Snapshot desired{};
static BridgeAck ack{2,0,0,0,0,0};
using EffectId=decltype(fsVfxSpawnInWorld("",FsVec3d{0,0,0}));
static EffectId flame[32],smoke[32],testFx=FSVFXID_NULL;
static FireCell previous[32]{};
static unsigned stale=99;
static void destroy(EffectId& id){if(id!=FSVFXID_NULL && fsVfxIsValid(id))fsVfxDestroyInstance(id);id=FSVFXID_NULL;}
static void clear(){for(int i=0;i<32;i++){destroy(flame[i]);destroy(smoke[i]);}destroy(testFx);}
static void check(HRESULT hr,const char* op){if(FAILED(hr))fprintf(stderr, "[FireOps] %s HRESULT=%lx\n",op,(unsigned long)hr);}
static void ensure(EffectId& id,const char* guid,const FireCell& c){
    if(!guid[0]){destroy(id);return;}
    if(id!=FSVFXID_NULL && fsVfxIsValid(id)){ack.live++;return;}
    UnifiedValues v=unifiedValues(c.id);
    const char* names[6]={"FireScale","SmokeWidth","SmokeRise","SmokeDensity","FireOn","SmokeOn"};
    const float values[6]={v.fireScale,v.smokeWidth,v.smokeRise,v.smokeDensity,v.fireOn,v.smokeOn};
    char expressions[6][32];FsVfxGraphParam parameters[6];
    for(int k=0;k<6;k++){
        std::snprintf(expressions[k],sizeof(expressions[k]),"%.6f",double(values[k]));
        parameters[k].paramName=names[k];parameters[k].RPNExpression=expressions[k];
    }
    id=fsVfxSpawnInWorld(guid,FsVec3d{c.lat,c.lon,c.alt},FsVec3d{0,0,0},-1,parameters,6);
    if(id==FSVFXID_NULL)ack.failed++;else ack.live++;
}
static void tick(){
    ack.heartbeat++;ack.live=0;ack.failed=0;
    if(stale<6)++stale;
    if(stale>5){clear();}
    else {
        for(unsigned i=0;i<32;i++){
            const auto& c=desired.cells[i]; auto& old=previous[i];
            if(i>=desired.count || c.hp<=0){destroy(flame[i]);destroy(smoke[i]);continue;}
            if(old.id!=c.id || old.lat!=c.lat || old.lon!=c.lon || old.alt!=c.alt){destroy(flame[i]);destroy(smoke[i]);old=c;}
            ensure(flame[i],desired.flame,c); ensure(smoke[i],desired.smoke,c);
        }
        if(desired.test && desired.flame[0]){
            if(testFx==FSVFXID_NULL || !fsVfxIsValid(testFx))
                testFx=fsVfxSpawnOnSimObject(desired.flame,0,nullptr,FsVec3d{0,3,0},FsVec3d{0,0,0},-1,nullptr,0);
            if(testFx==FSVFXID_NULL)ack.failed++;else ack.live++;
        } else destroy(testFx);
    }
    ack.seq=desired.seq;
    check(SimConnect_SetClientData(sc,2,2,SIMCONNECT_CLIENT_DATA_SET_FLAG_DEFAULT,0,sizeof(ack),&ack),"ack");
}
static void CALLBACK dispatch(SIMCONNECT_RECV* msg,DWORD size,void*){
    switch(msg->dwID){
    case SIMCONNECT_RECV_ID_CLIENT_DATA:{
        auto* r=reinterpret_cast<SIMCONNECT_RECV_CLIENT_DATA*>(msg);
        if(size<sizeof(SIMCONNECT_RECV_CLIENT_DATA))break;
        const size_t payloadOffset = reinterpret_cast<const char*>(&r->dwData) - reinterpret_cast<const char*>(r);
        if(r->dwRequestID!=1 || size<payloadOffset+sizeof(Snapshot))break;
        Snapshot next{};std::memcpy(&next,&r->dwData,sizeof(next));
        if(next.version!=2 || next.test!=0 || next.count>1 || next.flame[39]!=0 || next.smoke[39]!=0)break;
        if(std::strcmp(next.flame,"C0F18F57-0F39-4EC1-8DED-E00C0597A908") || next.smoke[0])break;
        bool valid=true;
        for(unsigned i=0;i<next.count;i++){
            auto& c=next.cells[i];
            if(!std::isfinite(c.lat)||!std::isfinite(c.lon)||!std::isfinite(c.alt)||!std::isfinite(c.hp)||std::fabs(c.lat)>90||std::fabs(c.lon)>180)valid=false;
        }
        if(!valid)break;
        if(std::strcmp(desired.flame,next.flame)||std::strcmp(desired.smoke,next.smoke))clear();
        desired=next;stale=0;break;
    }
    case SIMCONNECT_RECV_ID_EVENT:{
        auto* r=reinterpret_cast<SIMCONNECT_RECV_EVENT*>(msg);
        if(r->uEventID==10)tick();
        if(r->uEventID==11){clear();stale=99;}
        break;
    }
    case SIMCONNECT_RECV_ID_EXCEPTION:{
        auto* r=reinterpret_cast<SIMCONNECT_RECV_EXCEPTION*>(msg);
        ack.lastException=r->dwException;
        fprintf(stderr, "[FireOps] SimConnect exception=%lu send=%lu index=%lu\n",(unsigned long)r->dwException,(unsigned long)r->dwSendID,(unsigned long)r->dwIndex);break;
    }
    default:break;
    }
}
extern "C" MSFS_CALLBACK void module_init(void){
    for(int i=0;i<32;i++){flame[i]=FSVFXID_NULL;smoke[i]=FSVFXID_NULL;}
    if(FAILED(SimConnect_Open(&sc,"FireOps WASM",0,0,0,0))){fprintf(stderr, "[FireOps] OPEN FAILED\n");return;}
    check(SimConnect_MapClientDataNameToID(sc,"FireOps.Snapshot.v2",1),"map snapshot");
    check(SimConnect_MapClientDataNameToID(sc,"FireOps.Ack.v2",2),"map ack");
    // WASM owns both areas; client must NOT CreateClientData again.
    check(SimConnect_CreateClientData(sc,1,sizeof(Snapshot),SIMCONNECT_CREATE_CLIENT_DATA_FLAG_DEFAULT),"create snapshot");
    check(SimConnect_CreateClientData(sc,2,sizeof(BridgeAck),SIMCONNECT_CREATE_CLIENT_DATA_FLAG_DEFAULT),"create ack");
    check(SimConnect_AddToClientDataDefinition(sc,1,0,sizeof(Snapshot),0,0),"define snapshot");
    check(SimConnect_AddToClientDataDefinition(sc,2,0,sizeof(BridgeAck),0,0),"define ack");
    check(SimConnect_RequestClientData(sc,1,1,1,SIMCONNECT_CLIENT_DATA_PERIOD_ON_SET,SIMCONNECT_CLIENT_DATA_REQUEST_FLAG_DEFAULT,0,0,0),"subscribe snapshot");
    check(SimConnect_SubscribeToSystemEvent(sc,10,"1sec"),"timer");
    check(SimConnect_SubscribeToSystemEvent(sc,11,"SimStop"),"sim stop");
    check(SimConnect_CallDispatch(sc,dispatch,nullptr),"dispatch"); // Once only in WASM.
    fprintf(stderr, "[FireOps] bridge initialized protocol=2 packet=1120\n");
}
extern "C" MSFS_CALLBACK void module_deinit(void){clear();if(sc)SimConnect_Close(sc);sc=0;}
