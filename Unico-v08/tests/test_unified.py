import unittest,pathlib,sys,xml.etree.ElementTree as E,re,tempfile,shutil,json,hashlib,subprocess,math,struct
B=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(B),str(B/'TestLocale')]
import install_unified as ins
from parameters import new_id,values
from protocol import pack_snapshot
class Graph(unittest.TestCase):
 def test_single_and_bounds(self):
  t=E.parse(B/'FireOps_Unified_v08.xml');self.assertEqual(len(t.findall('.//VisualEffect.VisualEffect')),1)
  self.assertEqual(len(t.findall('.//VisualEffect.Emitter')),4);self.assertEqual(sum(int(n.text) for n in t.iter('Capacity')),256)
  self.assertEqual({n.findtext('GraphParamName') for n in t.iter('VisualEffect.GraphParameter')},{'FireScale','SmokeWidth','SmokeRise','SmokeDensity','FireOn','SmokeOn'})
 def test_links(self):
  t=E.parse(B/'FireOps_Unified_v08.xml');w=t.find('WorldBase.Flight');ids=[n.get('InstanceId') for n in w]
  ports={n.findtext('OutputValue') for n in w if n.find('OutputValue') is not None}
  self.assertEqual(len(ids),len(set(ids)));allowed=set(ids)|ports|{'{00000000-0000-0000-0000-000000000000}','{8E2A6B83-F2C6-4AB2-A03F-0AD954F8F53B}','{4E3195CE-58E6-40EF-B2A1-EF5CABF825B1}'}
  self.assertTrue(set(re.findall(r'\{[0-9A-F-]{36}\}',(B/'FireOps_Unified_v08.xml').read_text()))<=allowed)
 def test_generation_and_protocol(self):
  old=0
  for style in ['auto','tiny','small','medium','large','huge','base']:
   for profile in ['fire','smoke','both']:
    n=new_id(profile,style,old);self.assertNotEqual(n,old);old=n;v=values(n)
    self.assertTrue(.25<=v['FireScale']<=1.8);self.assertTrue(.55<=v['SmokeWidth']<=1.3)
    self.assertEqual(v['FireOn'],int(profile!='smoke'));self.assertEqual(v['SmokeOn'],int(profile!='fire'))
    self.assertEqual(v,values(n))
    packet=pack_snapshot({'fires':[{'id':n,'lat':46,'lon':11,'alt':234,'hp':100}]},'C0F18F57-0F39-4EC1-8DED-E00C0597A908','',1)
    self.assertEqual(len(packet),1120);self.assertEqual(struct.unpack_from('<I',packet)[0],2)
 def test_cpp_python_agree(self):
  with tempfile.TemporaryDirectory() as d:
   exe=str(pathlib.Path(d)/'params')
   subprocess.run(['g++','-std=c++17',str(B/'tests/params_test.cpp'),'-o',exe],check=True)
   for line in subprocess.check_output([exe],text=True).splitlines():
    tokens=line.split();v=values(int(tokens[0]));actual=list(map(float,tokens[1:]))
    for a,b in zip(actual,v.values()):self.assertAlmostEqual(a,b,places=5)
 def test_bridge_guards_and_sdk_signature(self):
  s=(B/'Bridge/Module.cpp').read_text();self.assertIn('next.count>1',s);self.assertIn('next.version!=2',s);self.assertIn('next.test!=0',s)
  self.assertIn('-1,parameters,6)',s);self.assertIn('FireOps.Snapshot.v2',s);self.assertIn('RPNExpression',s)
class Installer(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.parent=pathlib.Path(self.tmp.name);self.root=self.parent/'SimpleFX';self.code=self.parent/'StandaloneModule/Sources/Code';self.code.mkdir(parents=True)
  shutil.copytree(B/'tests/fixture',self.root);(self.root/'SimpleFX.xml').write_text('<Project/>')
  for f in ['Module.cpp','Module.h','VfxSdk.h','protocol.h']:(self.code/f).write_text('original '+f)
  lib=E.parse(self.root/ins.VFX/'VisualEffectLibrary.vfxlib')
  for k in ['Flame','Smoke']:
   for c in ['tiny','small','medium','large','huge']:
    for j in range(1,7):
     stem=f'FireOps_R07_{k}_{c}_{j:02}';(self.root/ins.VFX/(stem+'.xml')).write_text('old '+stem);E.SubElement(lib.getroot(),'VisualEffect',File=stem)
  lib.write(self.root/ins.VFX/'VisualEffectLibrary.vfxlib')
  (self.root/ins.VFX/'FireOps_Flame.edition.xml').write_text('old sidecar')
 def tearDown(self):self.tmp.cleanup()
 def snapshot(self):return {p.relative_to(self.parent).as_posix():p.read_bytes() for r in [self.root,self.code] for p in r.rglob('*') if p.is_file()}
 def test_check_readonly(self):
  before=self.snapshot();ins.install(self.root,self.code,True);self.assertEqual(before,self.snapshot())
 def test_cleanup_and_restore(self):
  before=self.snapshot();backup=ins.install(self.root,self.code)
  self.assertEqual(len(list((self.root/ins.VFX).glob('FireOps*.xml'))),1)
  refs=[n.get('File') for n in E.parse(self.root/ins.VFX/'VisualEffectLibrary.vfxlib').findall('VisualEffect')]
  self.assertEqual(refs,['EngineSmoke','FireOps_Unified_v08'])
  self.assertEqual((self.root/ins.MAT/'FireOps_Flame_v02.material').read_bytes(),before['SimpleFX/'+(ins.MAT/'FireOps_Flame_v02.material').as_posix()])
  ins.restore(self.root,self.code,backup);self.assertEqual(before,self.snapshot())
 def test_restore_refuses_edits(self):
  b=ins.install(self.root,self.code);(self.code/'Module.cpp').write_text('my work')
  with self.assertRaises(ValueError):ins.restore(self.root,self.code,b)
 def test_missing_material_no_writes(self):
  (self.root/ins.MAT/'FireOps_Smoke_Dense_v06.material').unlink();before=self.snapshot()
  with self.assertRaises(FileNotFoundError):ins.install(self.root,self.code)
  self.assertEqual(before,self.snapshot())
if __name__=='__main__':unittest.main()
