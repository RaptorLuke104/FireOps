"""Packages a compiled Standalone WASM. Does NOT compile VFX or create a fake binary."""
import argparse,pathlib,json,shutil,datetime
p=argparse.ArgumentParser();p.add_argument('wasm');p.add_argument('--output',default='packages/fireops-bridge');a=p.parse_args()
src=pathlib.Path(a.wasm)
if src.read_bytes()[:4]!=b'\0asm': raise SystemExit('Non e un modulo WebAssembly valido')
root=pathlib.Path(a.output); (root/'modules').mkdir(parents=True,exist_ok=True)
shutil.copy2(src,root/'modules'/'FireOps.wasm')
(root/'manifest.json').write_text(json.dumps({'dependencies':[],'content_type':'MISC','title':'FireOps LAN Bridge','manufacturer':'','creator':'FireOps','package_version':'0.1.0','minimum_game_version':'1.0.0','release_notes':{'neutral':{'LastUpdate':'','OlderHistory':''}}},indent=2))
entries=[]
for f in sorted(root.rglob('*')):
    if f.is_file() and f.name not in ('layout.json','manifest.json'):
        entries.append({'path':f.relative_to(root).as_posix(),'size':f.stat().st_size,'date':int((f.stat().st_mtime+11644473600)*10000000)})
(root/'layout.json').write_text(json.dumps({'content':entries},indent=2))
print('Pacchetto creato:',root.resolve(),'- verificare caricamento nella build MSFS installata.')
