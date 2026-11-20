import csv
import json
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coleccion import load, SCHEMAS
from construir import build
from publicar import files_to_publish

class DataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / 'coleccion'
        shutil.copytree(ROOT / 'colecciones/ejemplo', self.folder)

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, table, transform):
        with (self.folder / f'{table}.csv').open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        transform(rows)
        with (self.folder / f'{table}.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMAS[table])
            writer.writeheader(); writer.writerows(rows)

    def test_csv_multiline_quotes_and_unknown_price(self):
        note = 'Dulce, con "chocolate".\nSegunda impresión: mejor.'
        self.edit('valoraciones', lambda rows: rows[0].update(notas=note))
        self.edit('compras', lambda rows: rows[0].update(precio='', fecha='', tipo='muestra'))
        data = load(self.folder)
        self.assertEqual(data['valoraciones'][0]['notas'], note)
        self.assertEqual(data['compras'][0]['precio'], '')

    def test_invalid_relations_fail(self):
        self.edit('valoraciones', lambda rows: rows[0].update(compra_id='missing'))
        with self.assertRaisesRegex(ValueError, 'compra inexistente'):
            load(self.folder)

    def test_duplicate_ids_fail(self):
        self.edit('cafes', lambda rows: rows.append(rows[0].copy()))
        with self.assertRaisesRegex(ValueError, 'duplicado'):
            load(self.folder)

    def test_invalid_values_fail(self):
        for value in ['NaN', 'Infinity', '-1', '3,5', '6']:
            self.edit('valoraciones', lambda rows: rows[0].update(puntuacion=value))
            with self.assertRaises(ValueError):
                load(self.folder)

    def test_invalid_date_and_url_fail(self):
        self.edit('compras', lambda rows: rows[0].update(fecha='2026-02-30'))
        with self.assertRaisesRegex(ValueError, 'fecha'):
            load(self.folder)
        self.edit('compras', lambda rows: rows[0].update(fecha=''))
        self.edit('cafes', lambda rows: rows[0].update(url='javascript:alert(1)'))
        with self.assertRaisesRegex(ValueError, 'http'):
            load(self.folder)

    def test_build_only_public_files(self):
        output = build('ejemplo', Path(self.tmp.name) / 'public')
        self.assertEqual({p.name for p in output.iterdir()}, {'index.html','app.js','styles.css','datos.json','.nojekyll'})
        self.assertEqual(len(json.loads((output/'datos.json').read_text())['cafes']), 1)
        with self.assertRaisesRegex(ValueError, 'inseguro'):
            build('ejemplo', ROOT/'colecciones')

    def test_publishing_excludes_personal_sources(self):
        paths = [str(p.relative_to(ROOT)) for p in files_to_publish()]
        self.assertNotIn('preferencias.md', paths)
        self.assertNotIn('publicacion.local.json', paths)
        self.assertFalse(any(p.startswith(('fuentes/','archivo/','pedidos/')) for p in paths))

    @unittest.skipUnless((ROOT/'colecciones/deigote').exists(), 'Colección opcional')
    def test_migration_reconciles(self):
        data = load(ROOT/'colecciones/deigote')
        self.assertEqual([len(data[t]) for t in SCHEMAS], [7,9,5])
        for order, total in [('compra-inicial','39.25'),('2026-11-19','40.25')]:
            rows = [r for r in data['compras'] if r['pedido_id']==order]
            self.assertEqual(sum(Decimal(r['precio'])*int(r['cantidad']) for r in rows), Decimal(total))
        november = {r['id'] for r in data['compras'] if r['pedido_id']=='2026-11-19'}
        self.assertFalse(any(r['compra_id'] in november for r in data['valoraciones']))
        self.assertEqual(sum(c['id']=='etiopia-sidamo' for c in data['cafes']), 1)

if __name__ == '__main__':
    unittest.main()
