"""Local diagnostic for FireOps bridge v1. Python 3.11+ x64, Windows only.
No server, no network protocol, no modification of SDK or simulator packages.
"""
import argparse
import ctypes
import math
import pathlib
import queue
import struct
import sys
import threading
import time
from protocol import pack_snapshot
from sim import Sim
from geoid import Geoid
from parameters import STYLES,new_id,values

GUID = 'C0F18F57-0F39-4EC1-8DED-E00C0597A908'

def world_offset(command):
    parts=command.split()
    if len(parts) not in (1,2) or parts[0]!='world':
        raise ValueError('Usa: world oppure world 50 (metri extra sul terreno +1 m).')
    value=0.0 if len(parts)==1 else float(parts[1])
    if not math.isfinite(value) or not -100<=value<=300:
        raise ValueError('Offset diagnostico ammesso: da -100 a +300 metri.')
    return value

def world_cell(telemetry, offset):
    return {'id':1,'lat':telemetry['lat'],'lon':telemetry['lon'],
            'alt':telemetry['ground']+1+offset,'hp':100.0}

def is_amd64(path):
    try:
        with path.open('rb') as f:
            if f.read(2) != b'MZ': return False
            f.seek(0x3c); offset = struct.unpack('<I', f.read(4))[0]
            f.seek(offset)
            return f.read(4) == b'PE\0\0' and struct.unpack('<H', f.read(2))[0] == 0x8664
    except (OSError, struct.error): return False

def find_dll(sdk):
    candidates = [p for p in sdk.rglob('SimConnect.dll') if is_amd64(p)]
    if not candidates:
        raise RuntimeError('DLL SimConnect.dll nativa x64 non trovata in '+str(sdk)+'. Specificare --dll PERCORSO.')
    candidates.sort(key=lambda p: (len(p.parts),str(p)))
    if len(candidates) > 1:
        print('Più DLL x64 trovate. Uso la prima; per sceglierne una usare --dll:')
        for p in candidates: print(' ',p)
    return candidates[0]

def run(args):
    if sys.platform != 'win32': raise RuntimeError('Questo test va eseguito sul PC Windows con MSFS.')
    if ctypes.sizeof(ctypes.c_void_p) != 8: raise RuntimeError('Serve Python 64 bit, non Python 32 bit.')
    dll = pathlib.Path(args.dll) if args.dll else find_dll(pathlib.Path(args.sdk))
    if not is_amd64(dll): raise RuntimeError('Il file DLL non è un eseguibile PE x64 valido: '+str(dll))
    print('DLL:',dll,flush=True)
    geoid = Geoid()
    print('Griglia EGM96 verificata. world auto usa terreno + 1 m + N(lat,lon).',flush=True)
    sim = Sim(dll)
    commands = queue.Queue()
    def read_input():
        while True:
            try: line=input()
            except EOFError:
                commands.put('quit'); return
            commands.put(line.strip().lower())
    threading.Thread(target=read_input,daemon=True).start()
    print('FireOps UNICO v08 - bridge v2, un solo effetto, base classica, capacita totale 832 particelle',flush=True)
    print('Connessione SimConnect aperta. Attendo ACK dal WASM...',flush=True)
    print('Comandi: world auto | world [metri extra] | effects fire/smoke/both | size auto/tiny/small/medium/large/huge/base | clear | status | quit',flush=True)
    print('NON eseguire contemporaneamente il client FireOps principale.',flush=True)
    flame_guid=GUID; smoke_guid=''; profile='both'; style='auto'; generation_id=0
    state={'fires':[]}; test=False; seq=0; sent=0; reported=0; started=time.monotonic(); last_heartbeat=None
    try:
        while True:
            sim.poll(); now=time.monotonic()
            while not commands.empty():
                cmd=commands.get()
                if cmd=='quit': return
                is_world=cmd=='world' or cmd.startswith('world ')
                if cmd=='test on' or is_world:
                    if not sim.ack or now-sim.ack_seen>4:
                        print('Bridge non pronto: serve ACK recente. Nessun effetto richiesto.',flush=True); continue
                    if not sim.telemetry or now-sim.seen>3:
                        print('Telemetria assente/vecchia: carica un volo e attendi.',flush=True); continue
                if cmd=='test on':
                    print('Test attached disabilitato per sicurezza: usa world auto.',flush=True)
                elif cmd=='test off':
                    test=False
                    print('Test sul velivolo disattivato.',flush=True)
                elif is_world:
                    try:
                        offset=geoid.undulation(sim.telemetry['lat'],sim.telemetry['lon']) if cmd=='world auto' else world_offset(cmd)
                    except ValueError as e:
                        print('Comando rifiutato:',e,flush=True);continue
                    t=sim.telemetry
                    if not all(math.isfinite(v) for v in t.values()) or not t['on_ground'] or t['speed']>2:
                        print('Per world devi essere fermo a terra (<2 m/s).',flush=True);continue
                    test=False
                    generation_id=new_id(profile,style,generation_id)
                    cell=world_cell(t,offset);cell['id']=generation_id
                    state={'fires':[cell]}
                    print('GENERAZIONE:',generation_id,'classe:',style,'parametri:',values(generation_id),flush=True)
                    if cmd=='world auto':
                        print(f'EGM96: H_terreno={t["ground"]:.3f} m; N={offset:+.3f} m; quota API={t["ground"]+1+offset:.3f} m. Modalita legacy ellissoidale DA VALIDARE.',flush=True)
                    else:
                        print(f'QUOTA MANUALE: terreno={t["ground"]:.2f} m + 1 m + extra={offset:.2f} m; non e una correzione globale.',flush=True)
                    print('Richiesto effetto fisso al mondo:',state['fires'][0],flush=True)
                elif cmd.startswith('effects '):
                    selected=cmd.split()[1:]
                    profiles={'fire':(GUID,''),'smoke':(GUID,''),'both':(GUID,'')}
                    if len(selected)!=1 or selected[0] not in profiles:
                        print('Usa effects fire / effects smoke / effects both',flush=True);continue
                    profile=selected[0];flame_guid,smoke_guid=profiles[profile]
                    state={'fires':[]};test=False
                    print('GUID richiesti:',flame_guid,smoke_guid,flush=True)
                    print('Profilo:',profile,'- effetti precedenti rimossi. Richiedi world auto (sperimentale) oppure world 50.',flush=True)
                elif cmd.startswith('size '):
                    args=cmd.split()[1:]
                    if len(args)==1 and args[0] in STYLES:
                        style=args[0];print('Dimensione per la prossima generazione:',style,flush=True)
                    else:print('Usa size auto/tiny/small/medium/large/huge/base',flush=True)
                elif cmd=='clear':
                    state={'fires':[]};test=False
                    print('Richiesta rimozione di tutti gli effetti del bridge.',flush=True)
                elif cmd=='status':
                    print('GENERAZIONE:',generation_id,'parametri:',values(generation_id) if generation_id else None,flush=True)
                    print('PROFILO:',profile,'flame_guid=',flame_guid,'smoke_guid=',smoke_guid,flush=True)
                    print('TELEMETRIA:',sim.telemetry,flush=True)
                    print('VFX RICHIESTO:',state,'test_aereo=',test,flush=True)
                    print('ACK (versione, sequenza, heartbeat, live, failed, eccezione):',sim.ack,flush=True)
                elif cmd:
                    print('Comandi: world auto | world [metri extra] | effects fire/smoke/both | size auto/tiny/small/medium/large/huge/base | clear | status | quit',flush=True)
            if now-sent>=0.5:
                sent=now
                if sim.ack and sim.ack[0] == 2 and now-sim.ack_seen < 4:
                    seq=(seq+1)&0xffffffff
                    fresh=sim.telemetry is not None and now-sim.seen<3
                    sim.write(pack_snapshot(state if fresh else {'fires':[]},flame_guid,smoke_guid,seq,test and fresh))
            if now-reported>=3:
                reported=now
                if sim.ack and now-sim.ack_seen<4:
                    v,s,h,live,failed,exc=sim.ack
                    advancing=last_heartbeat is not None and h!=last_heartbeat
                    print(f'ACK v={v} seq={s} heartbeat={h} live={live} failed={failed} exception={exc}'
                          + (' [heartbeat avanza]' if advancing else ''),flush=True)
                    last_heartbeat=h
                else:
                    print('ACK v2 ASSENTE: serve il nuovo Module.cpp compilato e caricato. Non avviare il vecchio client v07.',flush=True)
                if now-started>10 and not sim.telemetry:
                    print('Nessuna telemetria ricevuta: verifica che il volo sia caricato.',flush=True)
            time.sleep(0.02)
    finally:
        if sim.ack:
            try:
                sim.write(pack_snapshot({'fires':[]},flame_guid,smoke_guid,(seq+1)&0xffffffff))
                # Brief cleanup grace; the bridge also has its own stale-snapshot timeout.
                for _ in range(15):
                    sim.poll();time.sleep(0.1)
            except Exception: pass
        sim.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk',default=r'C:\MSFS 2024 SDK')
    p.add_argument('--dll',default='')
    a=p.parse_args()
    try: run(a)
    except KeyboardInterrupt: print('Test interrotto.')
    except Exception as e:
        print('STOP:',e,flush=True)
        raise SystemExit(1)
