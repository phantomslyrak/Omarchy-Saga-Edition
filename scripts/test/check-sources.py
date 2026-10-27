#!/usr/bin/env python3
"""Read-only checks of repository sources and staged content; no installed scripts run."""
from pathlib import Path
import ast, hashlib, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]

def run(*args):
    subprocess.run(args,cwd=ROOT,check=True)

def files():
    out=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT)
    return sorted(set(p.decode() for p in out.split(b'\0') if p))
paths=files();errors=[]
for rel in paths:
    p=ROOT/rel
    if p.is_symlink():errors.append(f'symlink requires explicit review: {rel}');continue
    data=p.read_bytes()
    if p.stat().st_size>1024*1024:errors.append(f'large file: {rel}')
    try:s=data.decode('utf-8')
    except UnicodeDecodeError:errors.append(f'non-text file: {rel}');continue
    if '\0' in s:errors.append(f'binary content: {rel}')
    if re.search(r'\.(efi|uki|img|initrd|ttf|otf|png|jpg|webp|pyc|so|o|a)$',rel,re.I):errors.append(f'excluded artifact: {rel}')
    patterns=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'\bAKIA[0-9A-Z]{16}\b',r'\bgh[pousr]_[A-Za-z0-9]{30,}\b',r'\bgithub_pat_[A-Za-z0-9_]{40,}\b',r'\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b',r'(?i)(?:password|api_key|access_token|secret_key)\s*[:=]\s*[\'\"][^\'\"\s]{12,}[\'\"]']
    if rel!=str(Path(__file__).relative_to(ROOT)):
        for pattern in patterns:
            if re.search(pattern,s):errors.append(f'possible secret (inspect privately): {rel}');break
    if p.suffix=='.json' or p.name.endswith('.json.in'):json.loads(s)
    is_python=p.suffix=='.py' or p.name.endswith('.py.in') or (s.startswith('#!') and 'python' in s.splitlines()[0])
    if is_python:ast.parse(s,filename=rel)
    elif p.suffix=='.sh' or p.name.endswith('.sh.in') or s.startswith('#!/bin/sh') or s.startswith('#!/usr/bin/env bash') or s.startswith('#!/bin/bash'):
        run('bash','-n',str(p))
for record in json.loads((ROOT/'docs/development/provenance.json').read_text()):
    p=ROOT/record['path']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:errors.append(f'copy integrity: {record["path"]}')
# QML references deliberately keep the installed design/plugin relative layout.
for p in (ROOT/'components/sagalock/lock-designs').rglob('*.qml'):
    for ref in re.findall(r'(?:import\s+|Qt.resolvedUrl\()[\'"]([^\'"]+)[\'"]',p.read_text()):
        if 'plugins/io.github.sirjul1337.lock-explorer/designs' in ref:continue
        if not (p.parent/ref).exists():errors.append(f'broken local QML reference: {p.relative_to(ROOT)} → {ref}')
for p in ROOT.rglob('*.md'):
    if any(x in p.parts for x in ['.git','.local']):continue
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http:','https:','#','mailto:')):continue
        if not (p.parent/target.split('#')[0]).exists():errors.append(f'broken documentation link: {p.relative_to(ROOT)} → {target}')
# Audit actual Git index bytes too, in case staged content differs from working tree.
for rel in subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0'):
    if not rel:continue
    data=subprocess.check_output(['git','show',':'+rel.decode()],cwd=ROOT)
    if data!=(ROOT/rel.decode()).read_bytes():errors.append('index differs from reviewed working tree: '+rel.decode())
if errors:
    print('\n'.join(errors),file=sys.stderr);raise SystemExit(1)
print(f'PASS: {len(paths)} files; source hashes, Python/shell syntax, local QML/docs links, text/artifact and secret-pattern checks')
print('Limits: pattern matching cannot prove absence of every possible secret; external assets and Explorer imports are intentionally absent.')
