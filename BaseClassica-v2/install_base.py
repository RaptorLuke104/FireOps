"""Restore approved older artwork inside ONE v2 graph. No WASM or protocol edits."""
import pathlib,xml.etree.ElementTree as E,hashlib,json,datetime,argparse,sys,subprocess
B=pathlib.Path(__file__).resolve().parent
VFX=pathlib.Path('PackageSources/VisualEffectLibs/MyCompany/simple-fx');MAT=pathlib.Path('PackageSources/MaterialLibs/simplefx-materiallib')
GUID='{C0F18F57-0F39-4EC1-8DED-E00C0597A908}'
def sha(d):return hashlib.sha256(d).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve()
 if root not in p.parents:raise ValueError('Percorso non sicuro: '+str(rel))
 return p
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.fireops-tmp');q.write_bytes(d);q.replace(p)
def closed():
 if sys.platform=='win32':
  s=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,check=True).stdout.lower()
  if 'flightsimulator' in s:raise ValueError('Chiudi MSFS e il client prima di procedere.')
def plan(roots):
 root=roots['project'];client=roots['client']
 if not (root/'SimpleFX.xml').is_file():raise ValueError('SimpleFX.xml assente.')
 current=E.parse(root/VFX/'FireOps_Unified_v08.xml')
 if len(current.findall('.//VisualEffect.VisualEffect'))!=1 or current.find('.//VisualEffect.VisualEffect').get('InstanceId')!=GUID:raise ValueError('Serve la base con XML unico e bridge v2.')
 refs={pathlib.PureWindowsPath(n.get('File','')).stem for n in E.parse(root/VFX/'VisualEffectLibrary.vfxlib').findall('VisualEffect')}
 if 'FireOps_Unified_v08' not in refs or any(s.startswith('FireOps_R07_') for s in refs):raise ValueError('La libreria non e quella unificata. Nessun file modificato.')
 for name,g in [('FireOps_Flame_v02.material','{8E2A6B83-F2C6-4AB2-A03F-0AD954F8F53B}'),('FireOps_Smoke_Dense_v06.material','{4E3195CE-58E6-40EF-B2A1-EF5CABF825B1}')]:
  m=E.parse(root/MAT/name).getroot()
  if m.get('Guid')!=g:raise ValueError('Materiale base diverso: '+name)
  tex=pathlib.PureWindowsPath(m.find('TextureList/Texture').get('FileName')).as_posix()
  if not safe((root/MAT).resolve(),tex).is_file():raise ValueError('Texture base assente: '+tex)
 data=(B/'FireOps_Unified_v08.xml').read_bytes()
 if sha(data)!=json.loads((B/'manifest.json').read_text())['xml_sha256']:raise ValueError('XML del kit alterato.')
 changes={('project',(VFX/'FireOps_Unified_v08.xml').as_posix()):data}
 # Update only a misleading log label, never the client's protocol or behavior.
 c=client/'prova.py'
 if c.is_file():
  old=c.read_bytes();new=old.replace(b'massimo 256 particelle',b'base classica, capacita totale 832 particelle')
  if new!=old:changes[('client','prova.py')]=new
 return changes

def install(project,client,check=False):
 closed();roots={'project':project.resolve(),'client':client.resolve()};changes=plan(roots)
 for (k,r) in changes:print(k,r)
 if check:print('Verifica OK. Nessuna scrittura.');return
 backup=roots['project'].parent/('FireOps-backup-baseclassica-v2-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir();records=[]
 for (k,r),data in changes.items():
  p=safe(roots[k],r);old=p.read_bytes() if p.is_file() else None
  if old is not None:write(backup/'files'/k/r,old)
  records.append(dict(root=k,path=r,existed=old is not None,before=sha(old) if old is not None else None,after=sha(data)))
 (backup/'restore.json').write_text(json.dumps({'roots':{k:str(v) for k,v in roots.items()},'files':records},indent=2))
 try:
  for (k,r),data in changes.items():write(safe(roots[k],r),data)
 except Exception:
  for f in records:
   p=safe(roots[f['root']],f['path'])
   if f['existed']:write(p,(backup/'files'/f['root']/f['path']).read_bytes())
   else:p.unlink(missing_ok=True)
  raise
 report=f'Base classica installata nel singolo XML. Backup: {backup}\nBuild All SOLO su SimpleFX. Bridge v2, materiali e client funzionalmente invariati.\n'
 (B/'RISULTATO-INSTALLAZIONE.txt').write_text(report);print(report);return backup

def restore(project,client,backup):
 closed();roots={'project':project.resolve(),'client':client.resolve()};backup=backup.resolve()
 if backup.parent!=roots['project'].parent or not backup.name.startswith('FireOps-backup-baseclassica-v2-'):raise ValueError('Backup fuori posizione.')
 meta=json.loads((backup/'restore.json').read_text())
 if meta['roots']!={k:str(v) for k,v in roots.items()}:raise ValueError('Backup di altri percorsi.')
 for f in meta['files']:
  if sha(safe(roots[f['root']],f['path']).read_bytes())!=f['after']:raise ValueError('File modificato dopo installazione: '+f['path'])
  if f['existed'] and sha(safe((backup/'files'/f['root']).resolve(),f['path']).read_bytes())!=f['before']:raise ValueError('Backup danneggiato.')
 for f in meta['files']:
  p=safe(roots[f['root']],f['path'])
  if f['existed']:write(p,(backup/'files'/f['root']/f['path']).read_bytes())
  else:p.unlink()
 print('Sorgenti precedenti ripristinati. Build All su SimpleFX prima della prova.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',default=r'C:\FireOps\SimpleFX');p.add_argument('--client',default=r'C:\FireOps\Unico-v08\TestLocale');p.add_argument('--check',action='store_true');p.add_argument('--restore');a=p.parse_args()
 try:
  if a.restore:restore(pathlib.Path(a.project),pathlib.Path(a.client),pathlib.Path(a.restore))
  else:install(pathlib.Path(a.project),pathlib.Path(a.client),a.check)
 except Exception as e:print('STOP:',e);sys.exit(1)
