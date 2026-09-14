"""One effect with four emitters; fixed capacities and spawn-time graph parameters."""
from pathlib import Path
import xml.etree.ElementTree as E
import uuid,re,json,hashlib
B=Path(__file__).resolve().parents[1];ZERO='{00000000-0000-0000-0000-000000000000}'
GUID='{C0F18F57-0F39-4EC1-8DED-E00C0597A908}';NS=uuid.UUID('2ab14a81-27b1-4292-8daf-039b4cc70273')
def uid(s):return '{'+str(uuid.uuid5(NS,s)).upper()+'}'
t=E.parse(B/'tools/source/FireOps_Flame.xml');w=t.find('WorldBase.Flight');root=w.find('VisualEffect.VisualEffect')
sm=E.parse(B/'tools/source/FireOps_Smoke.xml').find('WorldBase.Flight')
for r in sm.find('VisualEffect.VisualEffect/EmitterList'):root.find('EmitterList').append(r)
for n in list(sm):
 if n.tag!='VisualEffect.VisualEffect':w.append(n)
def text(n,path,s):
 e=n.find(path)
 if e is None:e=E.SubElement(n,path)
 e.text=s
 return e
def node(kind,label):return E.SubElement(w,'VisualEffect.'+kind,InstanceId=uid(label))
params={}
for name in ['FireScale','SmokeWidth','SmokeRise','SmokeDensity','FireOn','SmokeOn']:
 n=node('GraphParameter',name);out=uid(name+'/output');text(n,'OutputValue',out);text(n,'GraphParamName',name);text(n,'GraphParamDefaultValue',ZERO+', 1');params[name]=out
counter=0
def wrap(e,param):
 global counter
 counter+=1;n=node('SetScale','scale/'+str(counter));out=uid('scale/'+str(counter)+'/output')
 original=[s.strip() for s in e.text.split(',')]
 # Variant fields serialize one reference + one scalar fallback, NOT a raw
 # Float3In tuple. Put constant vectors in a typed Vector3 node instead.
 variant=e.text
 if len(original)==4:
  if original[0]==ZERO:
   vec=node('Vector3','constant-vector/'+str(counter));vecout=uid('constant-vector/'+str(counter)+'/output')
   text(vec,'OutputValue',vecout)
   for component,value in zip(['x','y','z'],original[1:]):text(vec,component,ZERO+', '+value)
   variant=vecout+', 0'
  else:variant=original[0]+', 0'
 text(n,'OutputValue',out);text(n,'xVariant',variant);text(n,'FXScale',params[param]+', 1');e.text=out+', '+', '.join(['0']*max(1,len(original)-1))
lookup={n.get('InstanceId'):n for n in w};ports={n.findtext('OutputValue'):n for n in w if n.find('OutputValue') is not None}
def source(s):return ports[s.split(',')[0]]
for i,em in enumerate(w.findall('VisualEffect.Emitter')):
 init=lookup[em.find('ParticleInit/ObjectReference').get('InstanceId')];up=lookup[init.find('ParticleUpdate/ObjectReference').get('InstanceId')]
 out=lookup[up.find('ParticleOutput/ObjectReference').get('InstanceId')]
 fire=i<3;wrap(em.find('ParticleRate'),'FireOn' if fire else 'SmokeOn')
 if not fire:
  color=source(out.findtext('ParticleColor/ColorIn'));wrap(color.find('w'),'SmokeDensity')
 for path in ['ParticleSize/FloatIn']:wrap(init.find(path),'FireScale' if fire else 'SmokeWidth');wrap(up.find(path),'FireScale' if fire else 'SmokeWidth')
 if fire:wrap(init.find('ParticlePosition/Float3In'),'FireScale')
 wrap(init.find('ParticleVelocity/Float3In'),'FireScale' if fire else 'SmokeRise')
 # Link Update to the SAME parameterized velocity instead of creating another wrapper.
 up.find('ParticleVelocity/Float3In').text=init.findtext('ParticleVelocity/Float3In')
root.find('Name').text='FireOps_Unified_Classico_v2'
# Prune unused source nodes, not just join the files.
lookup={n.get('InstanceId'):n for n in w}
for n in w:
 if n.find('OutputValue') is not None:lookup[n.findtext('OutputValue')]=n
seen=set()
def visit(n):
 if n.get('InstanceId') in seen:return
 seen.add(n.get('InstanceId'))
 for g in re.findall(r'\{[0-9A-F-]{36}\}',E.tostring(n,encoding='unicode')):
  if g in lookup:visit(lookup[g])
visit(root)
for n in list(w):
 if n.get('InstanceId') not in seen:w.remove(n)
keep={ZERO,'{8E2A6B83-F2C6-4AB2-A03F-0AD954F8F53B}','{4E3195CE-58E6-40EF-B2A1-EF5CABF825B1}'}
raw=E.tostring(t.getroot(),encoding='unicode')
t=E.ElementTree(E.fromstring(re.sub(r'\{[0-9A-F-]{36}\}',lambda m:m[0] if m[0] in keep else uid('unified/'+m[0]),raw)))
t.find('.//VisualEffect.VisualEffect').set('InstanceId',GUID)
p=B/'FireOps_Unified_v08.xml';E.indent(t,space='    ');t.write(p,encoding='utf-8',xml_declaration=True)
print('One effect,',len(t.findall('.//VisualEffect.Emitter')),'emitters;',sum(int(n.text) for n in t.iter('Capacity')),'total capacity;',len(t.find('WorldBase.Flight')),'nodes')
