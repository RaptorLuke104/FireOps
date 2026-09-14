import argparse, asyncio, json, pathlib, threading, queue, time, uuid
from protocol import pack_snapshot
from sim import Sim

async def run(cfg):
    for key in ('flame_guid','smoke_guid'):
        if cfg.get(key): uuid.UUID(cfg[key])
    if not cfg.get('flame_guid'): raise ValueError('Configura flame_guid: non viene fornito un GUID inventato.')
    dll=pathlib.Path(cfg['simconnect_dll']).resolve()
    if not dll.is_file(): raise ValueError('SimConnect.dll non trovata: correggi simconnect_dll')
    sim=Sim(dll); state={'fires':[]}; seq=0; test=False; last_message=0; last_state=0
    commands=queue.Queue(); stop=asyncio.Event()
    def console():
        print('Comandi: here | drop | refill | cancel | test on | test off | status | quit',flush=True)
        while True:
            try: commands.put(input().strip().lower())
            except EOFError: return
    threading.Thread(target=console,daemon=True).start()
    writer=None
    try:
        reader,writer=await asyncio.open_connection(cfg['host'],cfg.get('port',8765),limit=65536)
        async def send(obj):
            writer.write((json.dumps(obj,allow_nan=False)+'\n').encode()); await asyncio.wait_for(writer.drain(),3)
        await send({'type':'hello','name':cfg['name'],'token':cfg['token'],'admin':cfg.get('admin','')})
        async def receive():
            nonlocal state,last_message,last_state
            while True:
                line=await asyncio.wait_for(reader.readline(),8)
                if not line: raise ConnectionError('Server disconnesso o chiave errata')
                msg=json.loads(line)
                if msg['type']=='welcome': print('Connesso. Dispatcher host:',msg['admin'],flush=True)
                elif msg['type']=='error': print('ERRORE:',msg['text'],flush=True)
                elif msg['type']=='state':
                    state=msg;last_state=time.monotonic()
                    for m in msg['messages']:
                        if m['id']>last_message: print('[RADIO]',m['text'],flush=True);last_message=m['id']
        async def pump():
            nonlocal seq,test
            sent=0; diagnostic=0
            while not stop.is_set():
                sim.poll();now=time.monotonic()
                while not commands.empty():
                    cmd=commands.get()
                    if cmd=='quit': stop.set();return
                    elif cmd=='test on': test=True
                    elif cmd=='test off': test=False
                    elif cmd=='status': print('TELEMETRIA:',sim.telemetry,'ACK:',sim.ack,'MISSIONE:',state,flush=True)
                    elif cmd in ('here','drop','refill','cancel'): await send({'type':'command','command':cmd})
                    elif cmd: print('Comando sconosciuto',flush=True)
                if now-sent>=0.5:
                    sent=now;seq=(seq+1)&0xffffffff
                    if sim.telemetry and now-sim.seen<2.5: await send({'type':'telemetry','data':sim.telemetry})
                    # No ACK means bridge not ready: prevent endless SetClientData errors.
                    if sim.ack and now-sim.ack_seen<4:
                        visible=state if now-last_state<4 and now-sim.seen<3 else {'fires':[]}
                        sim.write(pack_snapshot(visible,cfg['flame_guid'],cfg.get('smoke_guid',''),seq,test,cfg.get('altitude_bias_m',0)))
                if now-diagnostic>5:
                    diagnostic=now
                    if not sim.ack or now-sim.ack_seen>4: print('BRIDGE NON PRONTO: controlla pacchetto WASM; poi riavvia client.',flush=True)
                    else: print('BRIDGE version/seq/heartbeat/live/failed/exception:',sim.ack,flush=True)
                await asyncio.sleep(0.02)
        tasks=[asyncio.create_task(receive()),asyncio.create_task(pump())]
        done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()
        await asyncio.gather(*pending,return_exceptions=True)
        for task in done: task.result()
    finally:
        try: sim.write(pack_snapshot({'fires':[]},cfg['flame_guid'],'',0))
        except Exception: pass
        sim.close()
        if writer: writer.close();await writer.wait_closed()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default='client.json');a=p.parse_args()
    try: asyncio.run(run(json.loads(pathlib.Path(a.config).read_text(encoding='utf-8-sig'))))
    except KeyboardInterrupt: pass
    except Exception as e: print('STOP:',e);raise SystemExit(1)
