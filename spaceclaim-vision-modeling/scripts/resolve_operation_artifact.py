"""Resolve repository-relative metadata in either a checkout or a Skill install.

Resolution reads no CAD and performs no execution, status promotion, or evidence
verification. Repository-only test/provenance files require an explicit checkout.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path,PurePosixPath
import re

PACKAGE_NAME='spaceclaim-vision-modeling'

def resolve_artifact(reference,*,package_root=None,repository_root=None):
    if not isinstance(reference,str) or not reference.strip():
        raise ValueError('Expected repository-relative artifact path')
    name=reference.replace('\\','/')
    if name.startswith('/') or re.match(r'^[A-Za-z]:',name) or '..' in PurePosixPath(name).parts:
        raise ValueError('Absolute paths and parent traversal are not metadata references')
    package=Path(package_root or Path(__file__).resolve().parents[1]).resolve()
    parts=PurePosixPath(name).parts
    if parts and parts[0]==PACKAGE_NAME:
        root=package
        relative=Path(*parts[1:])
        scope='installed_package'
    else:
        if repository_root is None:
            return dict(status='unavailable',scope='repository_only',path=None,
                reason='Full checkout required for this test/provenance reference; not a runtime dependency.')
        root=Path(repository_root).resolve()
        if (root/PACKAGE_NAME).resolve()!=package:
            raise ValueError('Explicit checkout must contain this same Skill package')
        relative=Path(*parts)
        scope='repository'
    target=(root/relative).resolve()
    if not target.is_relative_to(root): raise ValueError('Resolved artifact escapes its declared root')
    if not target.is_file():
        return dict(status='unavailable',scope=scope,path=None,reason='Referenced file is absent; do not infer support.')
    return dict(status='resolved',scope=scope,path=str(target))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference')
    parser.add_argument('--package-root',type=Path)
    parser.add_argument('--repository-root',type=Path)
    args=parser.parse_args()
    try: result=resolve_artifact(args.reference,package_root=args.package_root,repository_root=args.repository_root)
    except (OSError,ValueError) as exc: result=dict(status='rejected',path=None,reason=str(exc))
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='resolved' else 1

if __name__=='__main__': raise SystemExit(main())
