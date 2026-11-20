#!/usr/bin/env python3
"""Valida una colección y genera exclusivamente los archivos públicos del visor."""
import argparse
import json
import shutil
from pathlib import Path
from coleccion import load

ROOT = Path(__file__).resolve().parents[1]

def build(collection='deigote', output=None):
    if not collection or Path(collection).name != collection or collection in ('.', '..'):
        raise ValueError('Nombre de colección inválido')
    source = ROOT / 'colecciones' / collection
    data = load(source)
    output = Path(output) if output else ROOT / 'dist'
    output = output.resolve()
    # Prohibir destinos que sobrescriban los CSV o el código.
    if output == ROOT or output in ROOT.parents or any(output == ROOT / p or ROOT / p in output.parents for p in ('colecciones', 'web', 'scripts', 'tests', '.git')):
        raise ValueError('Destino de salida inseguro')
    output.mkdir(parents=True, exist_ok=True)
    for name in ('index.html', 'app.js', 'styles.css'):
        shutil.copyfile(ROOT / 'web' / name, output / name)
    (output / 'datos.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (output / '.nojekyll').touch()
    print(f'Web generada: {output} ({len(data["registros"])} registros)')
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coleccion', default='deigote')
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    build(args.coleccion, args.salida)
