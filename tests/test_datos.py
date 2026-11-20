import csv,json,sys,tempfile,shutil,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from coleccion import load,FIELDS
from construir import build
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)/'data';shutil.copytree(ROOT/'colecciones/ejemplo',self.folder)
 def tearDown(self):self.tmp.cleanup()
 def save(self,rows):
  with (self.folder/'cafes.csv').open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 def test_quotes_and_empty(self):
  rows=load(self.folder)['registros'];rows[0].update(notas_usuario='Dulce, "rico"\nOtra impresión',precio='',fecha_compra='');self.save(rows);self.assertEqual(load(self.folder)['registros'],rows)
  self.save([]);self.assertEqual(load(self.folder)['registros'],[])
 def test_invalid_data(self):
  original=load(self.folder)['registros'][0]
  for change in [dict(precio='NaN'),dict(puntuacion='6'),dict(url='javascript:alert(1)'),dict(fecha_compra='2026-02-30'),dict(tipo='nuevo')]:
   self.save([dict(original,**change)])
   with self.assertRaises(ValueError):load(self.folder)
 def test_repeated_coffee_allowed(self):
  rows=load(self.folder)['registros'];self.save(rows+rows);self.assertEqual(len(load(self.folder)['registros']),2)
 def test_build(self):
  p=build('ejemplo',Path(self.tmp.name)/'site');self.assertEqual(set(x.name for x in p.iterdir()),{'index.html','app.js','styles.css','datos.json','.nojekyll'})
  with self.assertRaises(ValueError):build('ejemplo',ROOT/'colecciones')
 def test_migration(self):
  rows=load(ROOT/'colecciones/deigote')['registros'];self.assertEqual(len(rows),11);self.assertEqual(len({r['cafe_id'] for r in rows}),7)
  self.assertEqual(sum(r['tipo']!='cata' for r in rows),9);self.assertEqual(sum(bool(r['puntuacion']) for r in rows),5)
  self.assertEqual(sum(float(r['precio']) for r in rows if r['fecha_compra']=='2026-11-19'),40.25)
  self.assertTrue(all(not r['puntuacion'] for r in rows if r['fecha_compra']=='2026-11-19'))
  self.assertTrue(any('vino ligero' in r['notas_web'] for r in rows));self.assertTrue(any('arándano' in r['notas_web'] for r in rows))
if __name__=='__main__':unittest.main()
