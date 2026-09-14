"""Minimal SimConnect ctypes adapter, Windows x64, official SDK DLL only."""
import ctypes as C, struct, time
from protocol import PACKET_SIZE, ACK
D=C.c_uint32; H=C.c_void_p; P=C.c_char_p
class Sim:
    def __init__(self,dll):
        if C.sizeof(H)!=8: raise RuntimeError('Richiesto Python 64 bit')
        self.dll=C.WinDLL(str(dll)); self.h=H(); self.telemetry=None; self.seen=0; self.ack=None; self.ack_seen=0
        signatures={
          'Open':[C.POINTER(H),P,H,D,H,D], 'Close':[H],
          'GetNextDispatch':[H,C.POINTER(H),C.POINTER(D)],
          'AddToDataDefinition':[H,D,P,P,D,C.c_float,D],
          'RequestDataOnSimObject':[H,D,D,D,D,D,D,D,D],
          'MapClientDataNameToID':[H,P,D],
          'AddToClientDataDefinition':[H,D,D,D,C.c_float,D],
          'RequestClientData':[H,D,D,D,D,D,D,D,D],
          'SetClientData':[H,D,D,D,D,D,H]}
        for name,args in signatures.items():
            f=getattr(self.dll,'SimConnect_'+name); f.argtypes=args; f.restype=C.c_int32
        self.call('Open',C.byref(self.h),b'FireOps Client',None,0,None,0)
        for name,unit in [('PLANE LATITUDE','degrees'),('PLANE LONGITUDE','degrees'),('PLANE ALTITUDE','meters'),('GROUND ALTITUDE','meters'),('PLANE ALT ABOVE GROUND','meters'),('GROUND VELOCITY','meters per second'),('SIM ON GROUND','bool')]:
            self.call('AddToDataDefinition',self.h,10,name.encode(),unit.encode(),4,0,0xFFFFFFFF) # FLOAT64
        self.call('RequestDataOnSimObject',self.h,10,10,0,4,0,0,0,0) # SECOND
        self.call('MapClientDataNameToID',self.h,b'FireOps.Snapshot.v1',1)
        self.call('MapClientDataNameToID',self.h,b'FireOps.Ack.v1',2)
        self.call('AddToClientDataDefinition',self.h,1,0,PACKET_SIZE,0,0)
        self.call('AddToClientDataDefinition',self.h,2,0,ACK.size,0,0)
        self.call('RequestClientData',self.h,2,2,2,3,0,0,0,0) # ON_SET
    def call(self,name,*args):
        hr=getattr(self.dll,'SimConnect_'+name)(*args)
        if hr<0: raise RuntimeError(f'{name}: HRESULT 0x{hr&0xffffffff:08X}')
    def poll(self):
        while True:
            ptr=H(); size=D()
            if self.dll.SimConnect_GetNextDispatch(self.h,C.byref(ptr),C.byref(size))<0: break
            b=C.string_at(ptr,size.value)
            if len(b)<12: continue
            kind=struct.unpack_from('<I',b,8)[0]
            if kind==1 and len(b)>=24:
                print('SimConnect EXCEPTION code/sendID/index:',struct.unpack_from('<III',b,12),flush=True)
            elif kind==3: raise ConnectionError('MSFS ha chiuso la connessione')
            elif kind==8 and len(b)>=96: # SIMOBJECT_DATA
                req=struct.unpack_from('<I',b,12)[0]
                if req==10:
                    self.telemetry=dict(zip(('lat','lon','alt','ground','agl','speed','on_ground'),struct.unpack_from('<7d',b,40)));self.seen=time.monotonic()
            elif kind==16 and len(b)>=40+ACK.size: # CLIENT_DATA
                if struct.unpack_from('<I',b,12)[0]==2: self.ack=ACK.unpack_from(b,40);self.ack_seen=time.monotonic()
    def write(self,data):
        buf=C.create_string_buffer(data)
        self.call('SetClientData',self.h,1,1,0,0,len(data),C.cast(buf,H))
    def close(self):
        if self.h: self.call('Close',self.h);self.h=H()
