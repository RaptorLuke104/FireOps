import unittest,pathlib,sys,json,hashlib,xml.etree.ElementTree as E,tempfile,shutil,re
B=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(B));import install_base as p
class Graph(unittest.TestCase):
 def test_single_classic_graph(self):
  w=E.parse(B/'FireOps_Unified_v08.xml').find('WorldBase.Flight')
  self.assertEqual(len(w.findall('VisualEffect.VisualEffect')),1);self.assertEqual(len(w.findall('VisualEffect.Emitter')),4)
  self.assertEqual([int(n.text) for n in w.iter('Capacity')],[64,64,64,640])
  self.assertEqual(w.find('VisualEffect.VisualEffect').get('InstanceId'),p.GUID)
  ports={n.findtext('OutputValue'):n for n in w if n.find('OutputValue') is not None}
  rates=[float(ports[n.findtext('ParticleRate').split(',')[0]].findtext('xVariant').split(',')[1]) for n in w.findall('VisualEffect.Emitter')]
  self.assertEqual(rates,[12,10,10,20]);self.assertFalse(list(w.iter('ParticleTextureIndex')))
  self.assertTrue(all(n.findtext('UVMode')=='Default' for n in w.findall('VisualEffect.Output')))
 def test_original_curves_and_lifetimes_retained(self):
  new=E.parse(B/'FireOps_Unified_v08.xml').find('WorldBase.Flight')
  old=[E.parse(B/'tools/source'/f'FireOps_{k}.xml').find('WorldBase.Flight') for k in ['Flame','Smoke']]
  self.assertCountEqual([n.text for w in old for n in w.iter('Curve')],[n.text for n in new.iter('Curve')])
  self.assertEqual({n.findtext('GraphParamName') for n in new.findall('VisualEffect.GraphParameter')},{'FireScale','SmokeWidth','SmokeRise','SmokeDensity','FireOn','SmokeOn'})
  refs={n.findtext('OutputValue'):n for n in new if n.find('OutputValue') is not None}
  life=[]
  for n in new.findall('VisualEffect.BlockParticleInit'):
   r=refs[n.findtext('ParticleLifetime/FloatIn').split(',')[0]];life.append(tuple(float(r.findtext(k).split(',')[1]) for k in ['MinRandValue','MaxRandValue']))
  self.assertEqual(life,[(1.2,2.0),(.85,1.5),(1.4,2.3),(18,28)])
 def test_links_and_scalar_variant_format(self):
  w=E.parse(B/'FireOps_Unified_v08.xml').find('WorldBase.Flight');ids=[n.get('InstanceId') for n in w];self.assertEqual(len(ids),len(set(ids)))
  ports={n.findtext('OutputValue') for n in w if n.find('OutputValue') is not None}
  allowed=set(ids)|ports|{'{00000000-0000-0000-0000-000000000000}','{8E2A6B83-F2C6-4AB2-A03F-0AD954F8F53B}','{4E3195CE-58E6-40EF-B2A1-EF5CABF825B1}'}
  self.assertTrue(set(re.findall(r'\{[0-9A-F-]{36}\}',(B/'FireOps_Unified_v08.xml').read_text()))<=allowed)
  for n in w.iter('xVariant'):self.assertEqual(len(n.text.split(',')),2)
  self.assertEqual(hashlib.sha256((B/'FireOps_Unified_v08.xml').read_bytes()).hexdigest(),json.loads((B/'manifest.json').read_text())['xml_sha256'])
class Installer(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.parent=pathlib.Path(self.tmp.name);self.root=self.parent/'SimpleFX';self.client=self.parent/'Unico-v08/TestLocale';self.client.mkdir(parents=True)
  shutil.copytree(B/'tests/fixture',self.root);(self.root/'SimpleFX.xml').write_text('<Project/>')
  (self.root/p.VFX/'VisualEffectLibrary.vfxlib').write_text('<VisualEffectLibrary Version="1.0.0"><VisualEffect File="FireOps_Unified_v08"/></VisualEffectLibrary>')
  (self.client/'prova.py').write_text('print("massimo 256 particelle")')
 def tearDown(self):self.tmp.cleanup()
 def snapshot(self):return {f.relative_to(self.parent).as_posix():f.read_bytes() for r in [self.root,self.client] for f in r.rglob('*') if f.is_file()}
 def test_check_no_writes(self):
  before=self.snapshot();p.install(self.root,self.client,True);self.assertEqual(before,self.snapshot())
 def test_install_restore_preserves_assets(self):
  before=self.snapshot();backup=p.install(self.root,self.client);after=self.snapshot()
  self.assertEqual({k for k in before if before[k]!=after[k]},{'SimpleFX/'+(p.VFX/'FireOps_Unified_v08.xml').as_posix(),'Unico-v08/TestLocale/prova.py'})
  p.restore(self.root,self.client,backup);self.assertEqual(before,self.snapshot())
 def test_restore_protects_edits(self):
  b=p.install(self.root,self.client);(self.root/p.VFX/'FireOps_Unified_v08.xml').write_text('user edit')
  with self.assertRaises(ValueError):p.restore(self.root,self.client,b)
if __name__=='__main__':unittest.main()
