"""Lee y valida el único CSV de cada colección."""
import csv
import datetime as dt
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

FIELDS = ['cafe_id','nombre','tienda','url','tipo','fecha_compra','precio','gramos','fecha_valoracion','puntuacion','notas_web','notas_usuario','detalles']

def load(directory):
    directory = Path(directory)
    with (directory/'cafes.csv').open(encoding='utf-8-sig',newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise ValueError('Cabecera esperada: '+','.join(FIELDS))
        rows = list(reader)
    for i,r in enumerate(rows,2):
        def fail(message):
            raise ValueError(f'cafes.csv fila {i}: {message}')
        if None in r or any(v is None for v in r.values()): fail('número de columnas incorrecto')
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*',r['cafe_id']) or not r['nombre'].strip(): fail('falta café o ID válido')
        if r['tipo'] not in ('compra','muestra','cata'): fail('tipo debe ser compra, muestra o cata')
        if r['url']:
            u=urlparse(r['url'])
            if u.scheme not in ('http','https') or not u.netloc: fail('URL debe ser http(s)')
        for key in ('fecha_compra','fecha_valoracion'):
            if r[key]:
                try:
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',r[key]): raise ValueError()
                    dt.date.fromisoformat(r[key])
                except ValueError: fail('fecha inválida: '+key)
        for key in ('precio','gramos','puntuacion'):
            if r[key]:
                try: n=Decimal(r[key])
                except InvalidOperation: fail('número inválido: '+key)
                if not n.is_finite() or n<0: fail('número fuera de rango: '+key)
                if key=='puntuacion' and not 1<=n<=5: fail('puntuación debe estar entre 1 y 5')
                if key=='gramos' and n<=0: fail('gramos debe ser positivo')
        if r['puntuacion'] and not r['fecha_valoracion']: fail('falta fecha de valoración')
    config=json.loads((directory/'coleccion.json').read_text(encoding='utf-8'))
    if not isinstance(config.get('titulo'),str) or not config['titulo'].strip(): raise ValueError('Falta título')
    return {'registros':rows,'coleccion':{k:str(config.get(k,'')) for k in ('titulo','autor','descripcion')}}
