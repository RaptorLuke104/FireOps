"""Install only flame atlas/material and the existing combined graph. Stdlib only."""
import pathlib,xml.etree.ElementTree as E,json,hashlib,datetime,argparse,sys,subprocess
B=pathlib.Path(__file__).resolve().parent;VFX=pathlib.Path('PackageSources/VisualEffectLibs/MyCompany/simple-fx');MAT=pathlib.Path('PackageSources/MaterialLibs/simplefx-materiallib')
def sha(d):return hashlib.sha256(d).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve()
 if root.resolve() not in p.parents:raise ValueError('Percorso non sicuro: '+str(rel))
 return p
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.fireops-tmp');t.write_bytes(d);t.replace(p)
def closed():
 if sys.platform=='win32':
  s=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,check=True).stdout.lower()
  if 'flightsimulator' in s:raise ValueError('Chiudi MSFS prima di installare/ripristinare la patch texture.')
def plan(root):
 if not (root/'SimpleFX.xml').is_file():raise ValueError('SimpleFX.xml non trovato.')
 tree=E.parse(root/VFX/'FireOps_Unified_v08.xml')
 if tree.find('.//VisualEffect.VisualEffect').get('InstanceId')!='{C0F18F57-0F39-4EC1-8DED-E00C0597A908}':raise ValueError('Serve Unico-v08 funzionante.')
 inits=tree.findall('.//VisualEffect.BlockParticleInit')
 for init in inits[:3]:
  if list(map(float,init.findtext('ParticleVelocity/Float3In').split(',')[1:]))!=[0,0,0]:raise ValueError('Installa prima la correzione della fiamma che non si stacca.')
 lib=E.parse(root/VFX/'VisualEffectLibrary.vfxlib')
 if 'FireOps_Unified_v08' not in {pathlib.PureWindowsPath(n.get('File','')).stem for n in lib.findall('VisualEffect')}:raise ValueError('Riferimento al grafo unico assente dalla libreria.')
 for name,guid in [('FireOps_Flame_v02.material','{8E2A6B83-F2C6-4AB2-A03F-0AD954F8F53B}'),('FireOps_Smoke_Dense_v06.material','{4E3195CE-58E6-40EF-B2A1-EF5CABF825B1}')]:
  if E.parse(root/MAT/name).getroot().get('Guid')!=guid:raise ValueError('Materiale base diverso: '+name)
 changes={}
 for rec in json.loads((B/'manifest.json').read_text()):
  data=safe(B/'payload',rec['path']).read_bytes()
  if sha(data)!=rec['sha256']:raise ValueError('Kit alterato: '+rec['path'])
  safe(root,rec['path']);changes[rec['path']]=data
 return changes

def install(root,check=False):
 closed();root=root.resolve();changes=plan(root)
 if check:print('Verifica OK: 3 file, nessuna scrittura.');return
 backup=root.parent/('FireOps-backup-punte-v09-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir();records=[]
 for rel,data in changes.items():
  p=safe(root,rel);old=p.read_bytes() if p.is_file() else None
  if old is not None:write(backup/'files'/rel,old)
  records.append(dict(path=rel,existed=old is not None,before=sha(old) if old is not None else None,after=sha(data)))
 (backup/'restore.json').write_text(json.dumps({'root':str(root),'files':records},indent=2))
 try:
  for rel,data in changes.items():write(safe(root,rel),data)
 except Exception:
  for r in records:
   if r['existed']:write(safe(root,r['path']),(backup/'files'/r['path']).read_bytes())
   else:safe(root,r['path']).unlink(missing_ok=True)
  raise
 report=f'Backup: {backup}\nTre file installati. Ora Build All solo su SimpleFX, poi Load nel nuovo materiale FireOps_Flame_Tips_v09.\nWASM e client Unico-v08 invariati.\n'
 (B/'RISULTATO-INSTALLAZIONE.txt').write_text(report);print(report);return backup

def restore(root,backup):
 closed();root=root.resolve();backup=backup.resolve()
 if backup.parent!=root.parent or not backup.name.startswith('FireOps-backup-punte-v09-'):raise ValueError('Backup fuori posizione.')
 r=json.loads((backup/'restore.json').read_text())
 if r['root']!=str(root):raise ValueError('Backup appartenente ad altro progetto.')
 for f in r['files']:
  if sha(safe(root,f['path']).read_bytes())!=f['after']:raise ValueError('File modificato dopo installazione: '+f['path'])
  if f['existed'] and sha(safe(backup/'files',f['path']).read_bytes())!=f['before']:raise ValueError('Backup danneggiato.')
 for f in r['files']:
  if f['existed']:write(safe(root,f['path']),(backup/'files'/f['path']).read_bytes())
  else:safe(root,f['path']).unlink()
 print('Ripristino sorgenti completato. Build All su SimpleFX prima della prossima prova.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',default=r'C:\FireOps\SimpleFX');p.add_argument('--check',action='store_true');p.add_argument('--restore');a=p.parse_args()
 try:
  if a.restore:restore(pathlib.Path(a.project),pathlib.Path(a.restore))
  else:install(pathlib.Path(a.project),a.check)
 except Exception as e:print('STOP:',e);sys.exit(1)
