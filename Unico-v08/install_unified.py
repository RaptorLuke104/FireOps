"""Offline replacement. Run with MSFS and Visual Studio closed. Standard library only."""
import pathlib,xml.etree.ElementTree as E,datetime,json,hashlib,argparse,sys,subprocess
B=pathlib.Path(__file__).resolve().parent;VFX=pathlib.Path('PackageSources/VisualEffectLibs/MyCompany/simple-fx');MAT=pathlib.Path('PackageSources/MaterialLibs/simplefx-materiallib')
def sha(d):return hashlib.sha256(d).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve()
 if root not in p.parents:raise ValueError('Percorso non sicuro: '+str(rel))
 return p
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.fireops-tmp');tmp.write_bytes(d);tmp.replace(p)
def ensure_closed():
 if sys.platform=='win32':
  r=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,check=True)
  names=[line.split(',')[0].strip('"').lower() for line in r.stdout.splitlines()]
  if any('flightsimulator' in n or n=='devenv.exe' for n in names):raise ValueError('Chiudi MSFS e Visual Studio prima di installare/ripristinare.')
def plan(project,code):
 if not (project/'SimpleFX.xml').is_file():raise ValueError('SimpleFX.xml non trovato.')
 for f in ['Module.cpp','Module.h','VfxSdk.h','protocol.h']:
  if not (code/f).is_file():raise ValueError('Bridge esistente non trovato: '+str(code/f))
 for f,g in [('FireOps_Flame_v02.material','{8E2A6B83-F2C6-4AB2-A03F-0AD954F8F53B}'),('FireOps_Smoke_Dense_v06.material','{4E3195CE-58E6-40EF-B2A1-EF5CABF825B1}')]:
  m=E.parse(project/MAT/f).getroot()
  if m.get('Guid')!=g:raise ValueError('Materiale richiesto diverso: '+f)
  tex=pathlib.PureWindowsPath(m.find('TextureList/Texture').get('FileName')).as_posix()
  if not safe(project/MAT,tex).is_file():raise ValueError('Texture assente: '+tex)
 manifest=json.loads((B/'manifest.json').read_text())
 for rel,digest in manifest.items():
  if sha((B/rel).read_bytes())!=digest:raise ValueError('Kit alterato/incompleto: '+rel)
 changes={('project',(VFX/'FireOps_Unified_v08.xml').as_posix()):(B/'FireOps_Unified_v08.xml').read_bytes()}
 old={'FireOps_Flame','FireOps_Smoke'}|{f'FireOps_R07_{k}_{c}_{j:02}' for k in ['Flame','Smoke'] for c in ['tiny','small','medium','large','huge'] for j in range(1,7)}
 oldlow={n.lower() for n in old}
 # Archive old graphs and known editor sidecars, not just their library references.
 for f in (project/VFX).iterdir():
  if f.is_file() and any(f.name.lower() in {n+'.xml',n+'.edition.xml',n+'.xml.edition.xml',n+'.spb'} for n in oldlow):changes[('project',f.relative_to(project).as_posix())]=None
 libpath=VFX/'VisualEffectLibrary.vfxlib';lib=E.parse(project/libpath)
 for e in list(lib.getroot()):
  if e.tag=='VisualEffect' and pathlib.PureWindowsPath(e.get('File','')).stem.lower() in oldlow:lib.getroot().remove(e)
 if not any(pathlib.PureWindowsPath(e.get('File','')).stem=='FireOps_Unified_v08' for e in lib.findall('VisualEffect')):E.SubElement(lib.getroot(),'VisualEffect',File='FireOps_Unified_v08')
 E.indent(lib,space='    ');changes[('project',libpath.as_posix())]=E.tostring(lib.getroot(),encoding='utf-8',xml_declaration=True)
 for f in ['Module.cpp','UnifiedParams.h','protocol.h']:changes[('code',f)]=(B/'Bridge'/f).read_bytes()
 return changes

def install(project,code,check=False):
 ensure_closed();roots={'project':project.resolve(),'code':code.resolve()};changes=plan(roots['project'],roots['code'])
 print('File da scrivere:',sum(d is not None for d in changes.values()),'File vecchi da archiviare:',sum(d is None for d in changes.values()))
 if check:print('Verifica OK, nessuna modifica.');return
 backup=roots['project'].parent/('FireOps-backup-unico-v08-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir()
 records=[]
 for (which,rel),data in changes.items():
  dest=safe(roots[which],rel);old=dest.read_bytes() if dest.is_file() else None
  if old is not None:write(backup/'files'/which/rel,old)
  records.append(dict(root=which,path=rel,existed=old is not None,before_sha=sha(old) if old is not None else None,after_sha=sha(data) if data is not None else None))
 (backup/'restore.json').write_text(json.dumps({'roots':{k:str(v) for k,v in roots.items()},'files':records},indent=2))
 try:
  for (which,rel),data in changes.items():
   dest=safe(roots[which],rel)
   if data is None:dest.unlink(missing_ok=True)
   else:write(dest,data)
 except Exception:
  for rec in records:
   dest=safe(roots[rec['root']],rec['path'])
   if rec['existed']:write(dest,(backup/'files'/rec['root']/rec['path']).read_bytes())
   else:dest.unlink(missing_ok=True)
  raise
 report=f'Backup: {backup}\nProgetto: {project}\nCodice bridge: {code}\nInstallati solo sorgenti. Ricompilare il bridge in Visual Studio, poi i pacchetti in MSFS. NON aprire la vecchia libreria prima della nuova build.\n'
 (B/'RISULTATO-INSTALLAZIONE.txt').write_text(report);print(report)
 return backup

def restore(project,code,backup):
 ensure_closed();roots={'project':project.resolve(),'code':code.resolve()};backup=backup.resolve()
 if backup.parent!=project.resolve().parent or not backup.name.startswith('FireOps-backup-unico-v08-'):raise ValueError('Backup fuori posizione.')
 r=json.loads((backup/'restore.json').read_text())
 if {k:str(v) for k,v in roots.items()}!=r['roots']:raise ValueError('Backup di altri progetti.')
 for rec in r['files']:
  dest=safe(roots[rec['root']],rec['path'])
  actual=sha(dest.read_bytes()) if dest.is_file() else None
  if actual!=rec['after_sha']:raise ValueError('File modificato dopo installazione: '+str(dest))
  if rec['existed'] and sha(safe((backup/'files'/rec['root']).resolve(),rec['path']).read_bytes())!=rec['before_sha']:raise ValueError('Backup danneggiato.')
 for rec in r['files']:
  dest=safe(roots[rec['root']],rec['path'])
  if rec['existed']:write(dest,(backup/'files'/rec['root']/rec['path']).read_bytes())
  else:dest.unlink(missing_ok=True)
 print('Sorgenti ripristinati. Serve ricompilare bridge/pacchetti. ATTENZIONE: il ripristino puo riportare i 60 grafi v07 che precedevano il crash.')
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--project',default=r'C:\FireOps\SimpleFX');a.add_argument('--code',default=r'C:\FireOps\StandaloneModule\Sources\Code');a.add_argument('--check',action='store_true');a.add_argument('--restore')
 args=a.parse_args()
 try:
  if args.restore:restore(pathlib.Path(args.project),pathlib.Path(args.code),pathlib.Path(args.restore))
  else:install(pathlib.Path(args.project),pathlib.Path(args.code),args.check)
 except Exception as e:print('STOP:',e);sys.exit(1)
