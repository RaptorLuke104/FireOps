"""Animated flame tips, stationary lower texture. Pillow/numpy for authoring only."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import xml.etree.ElementTree as E
import uuid,json,hashlib,re
B=Path(__file__).resolve().parents[1];MAT=Path('PackageSources/MaterialLibs/simplefx-materiallib');VFX=Path('PackageSources/VisualEffectLibs/MyCompany/simple-fx/FireOps_Unified_v08.xml')
ZERO='{00000000-0000-0000-0000-000000000000}';FM='{D87C44F0-AFC7-45C5-BC31-2ADE717E6B09}'
NS=uuid.UUID('b9430db3-ef39-485a-8c99-7b744204e4ae')
def uid(s):return '{'+str(uuid.uuid5(NS,s)).upper()+'}'
def save(t,p):p.parent.mkdir(parents=True,exist_ok=True);E.indent(t,space='    ');t.write(p,encoding='utf-8',xml_declaration=True)
source=Image.open(B/'tools/source/fireops_flame_v02.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
a=np.asarray(source,dtype=np.float32)/255.;prem=a.copy();prem[:,:,:3]*=prem[:,:,3:4]
y,x=np.mgrid[0:256,0:256].astype(np.float32);height=(255-y)/255;weight=np.clip((height-.30)/.70,0,1)**1.8
frames=[]
for i in range(16):
 phase=2*np.pi*i/16
 dx=weight*(12*np.sin(phase+x*.017)+5*np.sin(2*phase+x*.041))
 dy=weight*(5*np.sin(phase+x*.031)+2*np.sin(2*phase-x*.012))
 sx=x-dx;sy=y+dy;xx=np.floor(sx).astype(int);yy=np.floor(sy).astype(int);fx=(sx-xx)[:,:,None];fy=(sy-yy)[:,:,None]
 def sample(ix,iy):return prem[np.clip(iy,0,255),np.clip(ix,0,255)]*((ix>=0)&(ix<256)&(iy>=0)&(iy<256))[:,:,None]
 v=sample(xx,yy)*(1-fx)*(1-fy)+sample(xx+1,yy)*fx*(1-fy)+sample(xx,yy+1)*(1-fx)*fy+sample(xx+1,yy+1)*fx*fy
 rgb=np.divide(v[:,:,:3],v[:,:,3:4],out=np.zeros_like(v[:,:,:3]),where=v[:,:,3:4]>1e-6)
 rgb[v[:,:,3]<=1e-6]=[1.,.20,.02] # Warm transparent edges avoid dark filtering fringes.
 rgba=(np.clip(np.concatenate([rgb,v[:,:,3:4]],axis=2),0,1)*255).round().astype(np.uint8)
 frames.append(Image.fromarray(rgba))
atlas=Image.new('RGBA',(4096,256))
for i,f in enumerate(frames):atlas.paste(f,(i*256,0))
p=B/'payload'/MAT/'Textures/fireops_flame_tips_v09.png';p.parent.mkdir(parents=True,exist_ok=True);atlas.save(p)
# Preview of the texture animation ONLY, not of MSFS or its material shader.
preview=[]
for f in frames:
 im=Image.new('RGB',(320,310),(27,31,36));im.paste(f,(32,24),f);ImageDraw.Draw(im).text((10,287),'Texture preview - NOT an MSFS render',fill=(220,220,220));preview.append(im)
preview[0].save(B/'Anteprima-punte.gif',save_all=True,append_images=preview[1:],duration=110,loop=0)
m=E.parse(B/'tools/source/FireOps_Flame_v02.material');r=m.getroot();r.set('Name','FireOps_Flame_Tips_v09');r.set('Guid',FM);r.find('TextureList/Texture').set('FileName','Textures\\fireops_flame_tips_v09.png');save(m,B/'payload'/MAT/'FireOps_Flame_Tips_v09.material')
t=E.parse(B/'tools/source/FireOps_Unified_v08.xml');w=t.find('WorldBase.Flight');w.find('VisualEffect.VisualEffect/Name').text='FireOps_Unified_v09'
nodes={n.get('InstanceId'):n for n in w};ports={n.findtext('OutputValue'):n for n in w if n.find('OutputValue') is not None}
def node(kind,label,props):
 n=E.SubElement(w,'VisualEffect.'+kind,InstanceId=uid(label));out=uid(label+'/output');E.SubElement(n,'OutputValue').text=out
 for k,v in props.items():E.SubElement(n,k).text=v
 return out
for i,em in enumerate(w.findall('VisualEffect.Emitter')[:3]):
 init=nodes[em.find('ParticleInit/ObjectReference').get('InstanceId')];up=nodes[init.find('ParticleUpdate/ObjectReference').get('InstanceId')];out=nodes[up.find('ParticleOutput/ObjectReference').get('InstanceId')]
 color=ports[out.findtext('ParticleColor/ColorIn').split(',')[0]];fade=ports[color.findtext('w').split(',')[0]]
 life=ports[init.findtext('ParticleLifetime/FloatIn').split(',')[0]]
 # Three seamless cycles over each particle's lifetime (~7.5-12.6 frames/s).
 play=node('GetBezierCurve',f'frames/{i}',{'FXTime':fade.findtext('FXTime'),'Curve':'0,0,NAN,NAN,1,48,NAN,NAN'})
 phase=node('RandomValue',f'phase/{i}',{'MinRandValue':ZERO+', 0','MaxRandValue':ZERO+', 15','RandSeed':ZERO+', '+str(9001+i*97),'RandIndex':life.findtext('RandIndex')})
 index=node('AddOperation',f'index/{i}',{'xVariant':play+', 0','yVariant':phase+', 0'})
 tex=E.SubElement(up,'ParticleTextureIndex');E.SubElement(tex,'FloatIn').text=index+', 0'
 # Texture does the motion: remove whole-sprite width breathing.
 up.find('ParticleScale/Float3In').text=ZERO+', 0.8, 1.45, 1'
 out.find('Material').text=FM;out.find('UVMode').text='Atlas'
 atlasnode=out.find('AtlasSize')
 if atlasnode is None:atlasnode=E.SubElement(out,'AtlasSize')
 atlasnode.text=ZERO+', 16, 1'
# Drop width-only nodes that are now unused; don't leave dead work in the graph.
lookup={n.get('InstanceId'):n for n in w}
for n in w:
 if n.find('OutputValue') is not None:lookup[n.findtext('OutputValue')]=n
seen=set()
def visit(n):
 if n.get('InstanceId') in seen:return
 seen.add(n.get('InstanceId'))
 for g in re.findall(r'\{[0-9A-F-]{36}\}',E.tostring(n,encoding='unicode')):
  if g in lookup:visit(lookup[g])
visit(w.find('VisualEffect.VisualEffect'))
for n in list(w):
 if n.get('InstanceId') not in seen:w.remove(n)
save(t,B/'payload'/VFX)
files=[{'path':p.relative_to(B/'payload').as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((B/'payload').rglob('*')) if p.is_file()]
(B/'manifest.json').write_text(json.dumps(files,indent=2)+'\n')
# Offline guarantees: lower 30% remains identical across frames, tips actually move.
arr=[np.asarray(f) for f in frames]
assert all(np.array_equal(v[180:],arr[0][180:]) for v in arr)
assert any(not np.array_equal(v[:150],arr[0][:150]) for v in arr[1:])
print('Generated 16-frame horizontal atlas, dedicated material and one combined effect. Lower texture fixed; tips animated. SDK validation pending.')
