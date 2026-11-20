"""CSV es la fuente de verdad; JSON es únicamente una salida para el visor."""
import csv
import datetime as dt
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

SCHEMAS = {
    'cafes': ['id', 'nombre', 'tienda', 'web', 'url', 'origen', 'proceso', 'descripcion', 'notas'],
    'compras': ['id', 'cafe_id', 'pedido_id', 'fecha', 'fecha_registro', 'tipo', 'precio', 'moneda', 'cantidad', 'gramos', 'molienda', 'tueste', 'version', 'notas', 'version_id'],
    'valoraciones': ['id', 'cafe_id', 'compra_id', 'fecha', 'fecha_consumo', 'puntuacion', 'version', 'notas', 'version_id'],
    'versiones': ['id', 'cafe_id', 'fecha', 'fuente', 'url', 'notas_cata', 'proceso', 'variedades', 'region', 'productor', 'altitud', 'sca', 'descripcion', 'notas'],
}

def fail(context, message):
    raise ValueError(f'{context}: {message}')

def date(value, context):
    if value:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            fail(context, 'fecha debe ser AAAA-MM-DD o vacía')
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            fail(context, 'fecha inexistente')

def number(value, context, minimum=Decimal('0'), maximum=None, integer=False):
    if value == '':
        return
    try:
        n = Decimal(value)
    except InvalidOperation:
        fail(context, 'número inválido; usa punto decimal')
    if not n.is_finite() or n < minimum or (maximum is not None and n > maximum):
        fail(context, 'número fuera de rango')
    if integer and n != n.to_integral_value():
        fail(context, 'debe ser entero')

def load(directory):
    directory = Path(directory)
    data = {}
    for table, fields in SCHEMAS.items():
        with (directory / f'{table}.csv').open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != fields:
                fail(table, f'cabecera esperada: {",".join(fields)}')
            rows = list(reader)
        ids = set()
        for rowno, row in enumerate(rows, 2):
            context = f'{table}.csv fila {rowno}'
            if None in row or any(v is None for v in row.values()):
                fail(context, 'número de columnas incorrecto')
            if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', row['id']):
                fail(context, 'id vacío o inválido')
            if row['id'] in ids:
                fail(context, f'id duplicado {row["id"]}')
            ids.add(row['id'])
            for field in ('fecha', 'fecha_registro', 'fecha_consumo'):
                if field in row:
                    date(row[field], f'{context} {field}')
            for field in ('web', 'url'):
                if row.get(field):
                    parsed = urlparse(row[field])
                    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                        fail(context, f'{field} debe ser URL http(s)')
            if table == 'cafes' and not row['nombre'].strip():
                fail(context, 'falta nombre')
            if table == 'compras':
                if row['tipo'] not in ('compra', 'muestra'):
                    fail(context, 'tipo debe ser compra o muestra')
                if not row['cantidad']:
                    fail(context, 'falta cantidad')
                number(row['precio'], context)
                number(row['cantidad'], context, Decimal('1'), integer=True)
                number(row['gramos'], context, Decimal('0.001'))
                if row['precio'] and not re.fullmatch(r'[A-Z]{3}', row['moneda']):
                    fail(context, 'precio requiere moneda ISO de tres letras')
            if table == 'valoraciones':
                if not row['puntuacion'] or not row['fecha']:
                    fail(context, 'valoración requiere puntuación y fecha de registro')
                number(row['puntuacion'], context, Decimal('1'), Decimal('5'))
        data[table] = rows
    cafes = {r['id'] for r in data['cafes']}
    compras = {r['id']: r for r in data['compras']}
    versiones = {r['id']: r for r in data['versiones']}
    for table in ('compras', 'valoraciones', 'versiones'):
        for row in data[table]:
            if row['cafe_id'] not in cafes:
                fail(row['id'], 'cafe_id inexistente')
    for row in data['versiones']:
        if not row['fecha'] or not row['fuente'].strip():
            fail(row['id'], 'versión requiere fecha de consulta/registro y fuente')
        number(row['sca'], row['id'], Decimal('0'), Decimal('100'))
    for table in ('compras', 'valoraciones'):
        for row in data[table]:
            if row['version_id']:
                version = versiones.get(row['version_id'])
                if not version or version['cafe_id'] != row['cafe_id']:
                    fail(row['id'], 'versión inexistente o de otro café')
    for row in data['valoraciones']:
        if row['compra_id']:
            compra = compras.get(row['compra_id'])
            if not compra or compra['cafe_id'] != row['cafe_id']:
                fail(row['id'], 'compra inexistente o de otro café')
    config = json.loads((directory / 'coleccion.json').read_text(encoding='utf-8'))
    if not isinstance(config.get('titulo'), str) or not config['titulo'].strip():
        fail('coleccion.json', 'falta titulo')
    # Solo estos metadatos se publican; nunca preferencias o archivos arbitrarios.
    data['coleccion'] = {k: config.get(k, '') for k in ('titulo', 'autor', 'descripcion')}
    return data
