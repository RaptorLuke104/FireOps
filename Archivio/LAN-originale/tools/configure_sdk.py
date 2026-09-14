"""Find the SDK VFX header rather than assuming a header name across SDK builds."""
import argparse,pathlib
p=argparse.ArgumentParser();p.add_argument('sdk');a=p.parse_args();sdk=pathlib.Path(a.sdk)
base=sdk/'WASM'/'include'
if not base.is_dir():raise SystemExit(f'Include WASM non trovati: {base}')
found=[]
for h in base.rglob('*.h'):
    if 'fsVfxSpawnInWorld' in h.read_text(encoding='utf-8',errors='ignore'):found.append(h)
if len(found)!=1:raise SystemExit('Trovati header VFX: '+str(found)+'. Selezionare manualmente quello che dichiara la funzione in wasm/VfxSdk.h')
out=pathlib.Path(__file__).resolve().parents[1]/'wasm'/'VfxSdk.h'
out.write_text('#pragma once\n#include <'+found[0].relative_to(base).as_posix()+'>\n')
print('Configurato',out,':',found[0])
print('DLL native disponibili:')
for f in sdk.rglob('SimConnect.dll'):print(f)
