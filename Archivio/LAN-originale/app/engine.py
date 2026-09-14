import math, time

def distance(a,b):
    p,q=math.radians(a['lat']),math.radians(b['lat'])
    dp=q-p; dl=math.radians(b['lon']-a['lon'])
    h=math.sin(dp/2)**2+math.cos(p)*math.cos(q)*math.sin(dl/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(h)))

class Mission:
    def __init__(self):
        self.fires=[]; self.players={}; self.revision=0; self.number=0
        self.phase='ATTESA'; self.messages=[]; self.mid=0
        self.say('Dispatcher pronto. Host: here per creare un incendio sotto la posizione attuale.')
    def say(self,text):
        self.mid+=1; self.messages.append({'id':self.mid,'text':text})
        self.messages=self.messages[-30:]
    def join(self,pid,name):
        self.players[pid]={'name':name,'water':2000,'last_drop':0,'telemetry':None,'seen':0}
        self.say(name+' collegato. Serbatoio virtuale: 2000 L.')
    def telemetry(self,pid,t):
        keys=('lat','lon','alt','ground','agl','speed','on_ground')
        if not isinstance(t,dict) or any(type(t.get(k)) not in (float,int) or not math.isfinite(t[k]) for k in keys):
            raise ValueError('Telemetria non valida')
        if not -90<=t['lat']<=90 or not -180<=t['lon']<=180 or not -1000<=t['alt']<=50000 or not 0<=t['speed']<=1500:
            raise ValueError('Telemetria fuori intervallo')
        p=self.players[pid]; p['telemetry']=t; p['seen']=time.monotonic()
    def fresh(self,pid):
        p=self.players[pid]
        if p['telemetry'] is None or time.monotonic()-p['seen']>3: raise ValueError('Telemetria assente o vecchia: carica un volo e attendi.')
        return p,p['telemetry']
    def create(self,pid):
        p,t=self.fresh(pid)
        if not t['on_ground'] or t['speed']>2: raise ValueError('Per here fermati a terra: serve una quota terreno locale affidabile.')
        self.number+=1; self.revision+=1; self.phase='ATTIVA'
        self.fires=[{'id':self.number,'lat':t['lat'],'lon':t['lon'],'alt':t['ground']+1,'hp':100.0}]
        self.say(f"Missione {self.number}: incendio {t['lat']:.6f}, {t['lon']:.6f}. Decolla, poi sgancia entro 100 m AGL e 80 m dal bersaglio. Quattro centri per estinguere.")
    def drop(self,pid):
        p,t=self.fresh(pid); now=time.monotonic()
        if self.phase!='ATTIVA': raise ValueError('Nessuna missione attiva')
        if t['on_ground'] or not 5<=t['agl']<=100 or t['speed']>100: raise ValueError('Sgancio rifiutato: richiesti volo, AGL 5–100 m, velocita <=100 m/s.')
        if now-p['last_drop']<2: raise ValueError('Attendi 2 secondi tra gli sganci')
        if p['water']<500: raise ValueError('Serbatoio vuoto: atterra e usa refill')
        p['last_drop']=now; p['water']-=500
        hits=[f for f in self.fires if f['hp']>0 and distance(t,f)<=80]
        for f in hits: f['hp']=max(0,f['hp']-25)
        self.revision+=1
        self.say(p['name']+f": sgancio 500 L, bersagli colpiti {len(hits)}. Acqua residua {p['water']} L.")
        if all(f['hp']==0 for f in self.fires):
            self.phase='COMPLETATA'; self.say('Dispatcher: incendio estinto. Missione completata, rientrare alla base. Host: here per una nuova missione.')
    def refill(self,pid):
        p,t=self.fresh(pid)
        if not t['on_ground'] or t['speed']>2: raise ValueError('Rifornimento consentito solo fermi a terra')
        p['water']=2000; self.say(p['name']+': rifornimento virtuale completato.')
    def cancel(self):
        self.fires=[]; self.phase='ANNULLATA'; self.revision+=1; self.say('Dispatcher: missione annullata.')
    def snapshot(self):
        return {'type':'state','mission':self.number,'revision':self.revision,'phase':self.phase,'fires':self.fires,
                'players':{k:{'name':p['name'],'water':p['water']} for k,p in self.players.items()},'messages':self.messages}
