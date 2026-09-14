"""Generate minimal VFX source graphs. Requires real compiled MaterialLib GUIDs.
Validate/build in the MSFS 2024 editor; this is NOT an SPB compiler.
"""
import argparse, pathlib, uuid, json
import xml.etree.ElementTree as E
p=argparse.ArgumentParser();p.add_argument('--flame-material',required=True);p.add_argument('--smoke-material',required=True)
p.add_argument('--output',default='vfx-source');a=p.parse_args()
root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True)
zero='{00000000-0000-0000-0000-000000000000}'
ns=uuid.UUID('3f220439-62f6-479f-b981-5176bbec8f15')
def uid(n):return '{'+str(uuid.uuid5(ns,n)).upper()+'}'
def child(parent,tag,text):E.SubElement(parent,tag).text=str(text)
def graph(name,material,lifetime,size,speed,rate,color):
    ids={k:uid(name+'/'+k) for k in ('fx','emitter','init','update','output')}
    doc=E.Element('SimBase.Document',{'Type':'AceXML','version':'1,0'});child(doc,'Descr','AceXML Document');world=E.SubElement(doc,'WorldBase.Flight')
    def node(tag,key):return E.SubElement(world,'VisualEffect.'+tag,{'InstanceId':ids[key]})
    def link(parent,tag,key,kind):E.SubElement(E.SubElement(parent,tag),'ObjectReference',{'InstanceId':ids[key],'id':kind})
    def value(parent,tag,typ,values):child(E.SubElement(parent,tag),typ,zero+', '+values)
    fx=node('VisualEffect','fx');child(fx,'Name',name);link(fx,'EmitterList','emitter','Emitter')
    e=node('Emitter','emitter')
    for k,v in {'EmitInLocalSpace':'False','Capacity':512,'ParticleRate':zero+f', {rate}','ParticleRateType':'Time','TimeEmission':-1,'Delay':0,'MaxDistanceEmission':10000}.items():child(e,k,v)
    link(e,'ParticleInit','init','BlockParticleInit')
    init=node('BlockParticleInit','init');value(init,'ParticleLifetime','FloatIn',str(lifetime));value(init,'ParticleSize','FloatIn',str(size));value(init,'ParticleVelocity','Float3In',f'0, {speed}, 0')
    link(init,'ParticleUpdate','update','BlockParticleUpdate')
    update=node('BlockParticleUpdate','update');link(update,'ParticleOutput','output','Output')
    output=node('Output','output');child(output,'PrimitiveType','Quad');child(output,'QuadBillboardType','Spherical');child(output,'UVMode','Default')
    child(output,'Material','{'+str(uuid.UUID(material.strip('{}'))).upper()+'}');value(output,'ParticleColor','ColorIn',color)
    E.indent(doc);E.ElementTree(doc).write(root/(name+'.xml'),encoding='utf-8',xml_declaration=True)
    return ids['fx'].strip('{}')
guids={'flame_guid':graph('FireOps_Flame',a.flame_material,1.2,5,3,24,'1, 0.65, 0.15, 0.9'),
       'smoke_guid':graph('FireOps_Smoke',a.smoke_material,12,12,4,16,'0.22, 0.22, 0.22, 0.5')}
lib=E.Element('VisualEffectLibrary',{'Version':'1.0.0'})
for name in ('FireOps_Flame','FireOps_Smoke'):E.SubElement(lib,'VisualEffect',{'File':name+'.xml'})
E.indent(lib);E.ElementTree(lib).write(root/'FireOps.vfxlib',encoding='utf-8',xml_declaration=True)
(root/'guids.json').write_text(json.dumps(guids,indent=2));print(json.dumps(guids,indent=2))
