#!/usr/bin/env python3
"""Valida, copia a un clon fuera de Dropbox y, con --push, publica los cambios."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from construir import ROOT, build

FIXED = ['AGENTS.md', 'README.md', 'preferencias.example.md', '.gitignore', 'publicacion.example.json']
TREES = {'scripts': ('.py',), 'web': ('.html', '.js', '.css'), 'tests': ('.py', '.js'), 'colecciones': ('.csv', '.json', '.md')}

def run(*args, cwd=None, capture=False):
    if args[0] == 'git':
        args = ('git', '-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential', *args[1:])
    result = subprocess.run(args, cwd=cwd, text=True, check=True, capture_output=capture)
    return result.stdout.strip() if capture else ''

def files_to_publish():
    paths = [ROOT / name for name in FIXED]
    for folder, suffixes in TREES.items():
        for p in (ROOT / folder).rglob('*'):
            if p.is_file() and p.suffix in suffixes and '__pycache__' not in p.parts:
                if p.is_symlink():
                    raise ValueError(f'No se publican enlaces simbólicos: {p}')
                paths.append(p)
    return sorted(paths)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--push', action='store_true', help='Crear commit y subir a origin/main (sin force push)')
    parser.add_argument('--mensaje', default='Actualizar colección de cafés')
    parser.add_argument('--config', type=Path, default=ROOT / 'publicacion.local.json')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    repo, collection = config['repositorio'], config['coleccion']
    import re
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('repositorio debe ser propietario/nombre')
    clone = Path(config['clon']).expanduser().resolve()
    if clone == ROOT or clone in ROOT.parents or ROOT in clone.parents:
        raise ValueError('El clon debe estar fuera de la carpeta de trabajo')
    build(collection)
    for p in sorted((ROOT / 'colecciones').iterdir()):
        if p.is_dir():
            from coleccion import load
            load(p)
    paths = files_to_publish()
    print('Repositorio:', repo, '\nClon:', clone, '\nColección web:', collection)
    print('Se publican código, documentación y CSV de colecciones. Se excluyen preferencias, fuentes, pedidos y archivo histórico.')
    if not (clone / '.git').exists():
        if clone.exists() and any(clone.iterdir()):
            raise ValueError('El destino del clon no está vacío')
        clone.parent.mkdir(parents=True, exist_ok=True)
        run('git', 'clone', f'https://github.com/{repo}.git', str(clone))
    origin = run('git', 'remote', 'get-url', 'origin', cwd=clone, capture=True)
    expected = {f'https://github.com/{repo}', f'https://github.com/{repo}.git', f'git@github.com:{repo}.git'}
    if origin not in expected:
        raise ValueError(f'origin no corresponde a {repo}')
    if run('git', 'status', '--porcelain', cwd=clone, capture=True):
        raise ValueError('El clon contiene cambios locales. Revísalos antes de sincronizar; no se sobrescriben.')
    has_head = subprocess.run(['git','rev-parse','--verify','HEAD'], cwd=clone, capture_output=True).returncode == 0
    if not has_head:
        run('git', 'symbolic-ref', 'HEAD', 'refs/heads/main', cwd=clone)
    branch = run('git', 'symbolic-ref', '--short', 'HEAD', cwd=clone, capture=True)
    if branch != 'main':
        raise ValueError('El clon debe estar en la rama main')
    # Los repos vacíos no tienen aún HEAD. No se reescribe historia remota.
    if has_head:
        before = run('git', 'rev-parse', 'HEAD', cwd=clone, capture=True)
        run('git', 'pull', '--ff-only', 'origin', 'main', cwd=clone)
        after = run('git', 'rev-parse', 'HEAD', cwd=clone, capture=True)
        if before != after:
            raise ValueError('Se han recibido cambios remotos. Revisa e intégralos en la carpeta de trabajo antes de publicar.')
    managed = [str(p.relative_to(ROOT)) for p in paths]
    site = [p for p in (ROOT / 'dist').iterdir() if p.name in ('index.html', 'app.js', 'styles.css', 'datos.json', '.nojekyll')]
    managed += ['docs/' + p.name for p in site]
    manifest = clone / '.cafe-publicacion.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else []
    for rel in previous:
        target = (clone / rel).resolve()
        if clone not in target.parents or '.git' in Path(rel).parts:
            raise ValueError('Manifest de publicación inválido')
        if rel not in managed and target.is_file():
            target.unlink()
    for source in paths:
        target = clone / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for source in site:
        target = clone / 'docs' / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    manifest.write_text(json.dumps(managed, indent=2) + '\n')
    changes = run('git','status','--short',cwd=clone,capture=True)
    print(changes or 'Sin cambios de contenido.')
    if not args.push:
        print('Copia preparada, sin commit ni push. Revisa el clon; confirma o descarta allí los cambios antes de volver a ejecutar el script.')
        return
    if changes:
        run('git','add','--',*sorted(set(managed + previous + ['.cafe-publicacion.json'])),cwd=clone)
        run('git','commit','-m',args.mensaje,cwd=clone)
    # También reintenta un push fallido de una ejecución anterior, aunque no haya cambios nuevos.
    run('git','push','-u','origin','main',cwd=clone)
    print(f'Push completado. GitHub Pages publicará https://{repo.split("/")[0]}.github.io/{repo.split("/")[1]}/')

if __name__ == '__main__':
    main()
