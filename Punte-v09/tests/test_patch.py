import unittest,pathlib,sys,xml.etree.ElementTree as E,json,hashlib,tempfile,shutil,re
from PIL import Image
B=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(B))
import install_tips as p
class Assets(unittest.TestCase):
 def test_atlas_has_moving_tips_fixed_base(self):
  im=Image.open(B/'payload'/p.MAT/'Textures/fireops_flame_tips_v09.png');self.assertEqual(im.size,(4096,256));self.assertEqual(im.mode,'RGBA')
  frames=[im.crop((i*256,0,(i+1)*256,256)) for i in range(16)]
  bottom=frames[0].crop((0,180,256,256)).tobytes()
  self.assertTrue(all(f.crop((0,180,256,256)).tobytes()==bottom for f in frames))
  self.assertEqual(len({f.crop((0,0,256,150)).tobytes() for f in frames}),16)
 def test_graph_and_limits(self):
  w=E.parse(B/'payload'/p.VFX/'FireOps_Unified_v08.xml').find('WorldBase.Flight');self.assertEqual(len(w.findall('VisualEffect.VisualEffect')),1);self.assertEqual(sum(int(n.text) for n in w.iter('Capacity')),256)
  self.assertEqual(w.find('VisualEffect.VisualEffect').get('InstanceId'),'{C0F18F57-0F39-4EC1-8DED-E00C0597A908}')
  self.assertEqual(len(list(w.iter('ParticleTextureIndex'))),3)
  for n in w.iter('ParticleTextureIndex'):self.assertIsNotNone(n.find('FloatIn'));self.assertEqual(len(n.findtext('FloatIn').split(',')),2)
  for n in w.findall('VisualEffect.Output')[:3]:self.assertEqual(n.findtext('UVMode'),'Atlas');self.assertTrue(n.findtext('AtlasSize').endswith(', 16, 1'))
  ids=[n.get('InstanceId') for n in w];ports={n.findtext('OutputValue') for n in w if n.find('OutputValue') is not None}
  self.assertEqual(len(ids),len(set(ids)))
  allowed=set(ids)|ports|{'{00000000-0000-0000-0000-000000000000}','{D87C44F0-AFC7-45C5-BC31-2ADE717E6B09}','{4E3195CE-58E6-40EF-B2A1-EF5CABF825B1}'}
  self.assertTrue(set(re.findall(r'\{[0-9A-F-]{36}\}',(B/'payload'/p.VFX/'FireOps_Unified_v08.xml').read_text()))<=allowed)
  for n in w.iter('xVariant'):self.assertEqual(len(n.text.split(',')),2)
 def test_flame_transport_is_zero(self):
  w=E.parse(B/'payload'/p.VFX/'FireOps_Unified_v08.xml').find('WorldBase.Flight')
  for tag in ['VisualEffect.BlockParticleInit','VisualEffect.BlockParticleUpdate']:
   for n in w.findall(tag)[:3]:self.assertEqual(list(map(float,n.findtext('ParticleVelocity/Float3In').split(',')[1:])),[0,0,0])
 def test_smoke_reachable_nodes_unchanged(self):
  old=E.parse(B/'tools/source/FireOps_Unified_v08.xml').find('WorldBase.Flight');new=E.parse(B/'payload'/p.VFX/'FireOps_Unified_v08.xml').find('WorldBase.Flight')
  def table(w):return {n.get('InstanceId'):n for n in w}|{n.findtext('OutputValue'):n for n in w if n.find('OutputValue') is not None}
  a=table(old);b=table(new);seen=set()
  def simple(n):return n.tag,tuple(n.attrib.items()),(n.text or '').strip(),tuple(simple(c) for c in n)
  def walk(n):
   key=n.get('InstanceId')
   if key in seen:return
   seen.add(key);self.assertEqual(simple(n),simple(b[key]))
   for g in re.findall(r'\{[0-9A-F-]{36}\}',E.tostring(n,encoding='unicode')):
    if g in a:walk(a[g])
  walk(old.findall('VisualEffect.Emitter')[3])
 def test_manifest_and_material(self):
  m=json.loads((B/'manifest.json').read_text());self.assertEqual(len(m),3)
  for r in m:self.assertEqual(hashlib.sha256((B/'payload'/r['path']).read_bytes()).hexdigest(),r['sha256'])
  mat=E.parse(B/'payload'/p.MAT/'FireOps_Flame_Tips_v09.material').getroot();self.assertEqual(mat.get('Guid'),'{D87C44F0-AFC7-45C5-BC31-2ADE717E6B09}');self.assertEqual(mat.find('Attributes/Emissive').get('Red'),'1')
class Installer(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)/'SimpleFX';shutil.copytree(B/'tests/fixture',self.root)
  (self.root/'SimpleFX.xml').write_text('<Project/>');shutil.copy2(B/'tools/source/FireOps_Unified_v08.xml',self.root/p.VFX/'FireOps_Unified_v08.xml')
  (self.root/p.VFX/'VisualEffectLibrary.vfxlib').write_text('<VisualEffectLibrary Version="1.0.0"><VisualEffect File="FireOps_Unified_v08"/></VisualEffectLibrary>')
 def tearDown(self):self.tmp.cleanup()
 def snapshot(self):return {f.relative_to(self.root).as_posix():f.read_bytes() for f in self.root.rglob('*') if f.is_file()}
 def test_check_readonly(self):
  before=self.snapshot();p.install(self.root,True);self.assertEqual(before,self.snapshot())
 def test_install_restore(self):
  before=self.snapshot();backup=p.install(self.root);after=self.snapshot();self.assertEqual(len([k for k in after if before.get(k)!=after[k]]),3)
  p.restore(self.root,backup);self.assertEqual(before,self.snapshot())
 def test_restore_protects_edits(self):
  backup=p.install(self.root);(self.root/p.VFX/'FireOps_Unified_v08.xml').write_text('user edit')
  with self.assertRaises(ValueError):p.restore(self.root,backup)
if __name__=='__main__':unittest.main()
