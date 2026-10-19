#!/usr/bin/env python3
"""Build an isolated P3 suite and immutable action snapshot; never run SpaceClaim."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
from collections.abc import Mapping

from build_atomic_scripts import ACTIONS
from package_scscript import package_scscript


SUITES = ('forward', 'delta', 'advanced', 'import')
DEFAULT_IMPORT_BBOX_TOLERANCE_MM = 0.001
DEFAULT_IMPORT_VOLUME_TOLERANCE_MM3 = 0.001


def _config_value(config, name, *aliases):
    """Read a configuration key while accepting the public injected names."""

    for key in (name,) + aliases:
        if key in config:
            return config[key]
    return None


def _finite_number(value, name):
    if isinstance(value, bool):
        raise ValueError('%s must be numeric, not boolean' % name)
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('%s must be numeric' % name) from exc
    if not math.isfinite(value):
        raise ValueError('%s must be finite' % name)
    return value


def _normalise_body_signatures(config):
    signatures = _config_value(
        config,
        'expected_body_signatures',
        'expected_signatures',
        'IMPORT_EXPECTED_BODY_SIGNATURES',
        'IMPORT_EXPECTED_SIGNATURES',
    )
    if signatures is None:
        expected_bbox = _config_value(
            config,
            'expected_bbox_mm',
            'bbox_mm',
            'IMPORT_EXPECTED_BBOX_MM',
        )
        expected_volume = _config_value(
            config,
            'expected_volume_mm3',
            'volume_mm3',
            'IMPORT_EXPECTED_VOLUME_MM3',
        )
        if expected_bbox is not None and expected_volume is not None:
            signatures = [{'bbox_mm': expected_bbox, 'volume_mm3': expected_volume}]
    if not isinstance(signatures, (list, tuple)) or not signatures:
        raise ValueError(
            'import_config must provide non-empty expected_body_signatures'
        )

    normalised = []
    for index, signature in enumerate(signatures):
        if not isinstance(signature, Mapping):
            raise ValueError('expected body signature %d must be an object' % index)
        if 'bbox_mm' not in signature or 'volume_mm3' not in signature:
            raise ValueError(
                'expected body signature %d requires bbox_mm and volume_mm3' % index
            )
        bbox = signature['bbox_mm']
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 6:
            raise ValueError(
                'expected body signature %d bbox_mm requires six coordinates' % index
            )
        normalised_bbox = [
            _finite_number(value, 'expected body signature %d bbox_mm' % index)
            for value in bbox
        ]
        volume = _finite_number(
            signature['volume_mm3'],
            'expected body signature %d volume_mm3' % index,
        )
        if volume <= 0:
            raise ValueError(
                'expected body signature %d volume_mm3 must be positive' % index
            )
        normalised.append({'bbox_mm': normalised_bbox, 'volume_mm3': volume})
    return normalised


def _normalise_import_config(import_config):
    """Validate and canonicalise caller-owned native-import configuration.

    The builder deliberately does not know any fixture path or digest.  The
    caller supplies both, and the source is checked once at build time so the
    generated run cannot silently carry a stale digest.
    """

    if not isinstance(import_config, Mapping):
        raise TypeError('import_config must be a mapping for the import suite')

    source_value = _config_value(
        import_config,
        'source',
        'source_path',
        'import_source',
        'import_source_path',
        'IMPORT_SOURCE',
    )
    if source_value is None or not str(source_value).strip():
        raise ValueError('import_config must provide source')
    source = Path(source_value).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError('import source does not exist: %s' % source)

    digest_value = _config_value(
        import_config,
        'sha256',
        'source_sha256',
        'import_sha256',
        'IMPORT_SHA256',
    )
    if digest_value is None:
        raise ValueError('import_config must provide sha256')
    digest = str(digest_value).strip().lower()
    if len(digest) != 64 or any(character not in '0123456789abcdef' for character in digest):
        raise ValueError('import_config sha256 must be a 64-character hexadecimal digest')
    actual_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_digest != digest:
        raise ValueError(
            'import source sha256 mismatch: expected %s, found %s'
            % (digest, actual_digest)
        )

    bbox_tolerance_value = _config_value(
        import_config,
        'bbox_tolerance_mm',
        'import_bbox_tolerance_mm',
        'IMPORT_BBOX_TOLERANCE_MM',
    )
    volume_tolerance_value = _config_value(
        import_config,
        'volume_tolerance_mm3',
        'import_volume_tolerance_mm3',
        'IMPORT_VOLUME_TOLERANCE_MM3',
    )
    bbox_tolerance = _finite_number(
        bbox_tolerance_value
        if bbox_tolerance_value is not None
        else DEFAULT_IMPORT_BBOX_TOLERANCE_MM,
        'bbox_tolerance_mm',
    )
    volume_tolerance = _finite_number(
        volume_tolerance_value
        if volume_tolerance_value is not None
        else DEFAULT_IMPORT_VOLUME_TOLERANCE_MM3,
        'volume_tolerance_mm3',
    )
    if bbox_tolerance < 0 or volume_tolerance < 0:
        raise ValueError('import tolerances must be nonnegative')

    return {
        'source': str(source),
        'sha256': digest,
        'expected_body_signatures': _normalise_body_signatures(import_config),
        'bbox_tolerance_mm': bbox_tolerance,
        'volume_tolerance_mm3': volume_tolerance,
    }


def _import_prefix(import_config):
    """Render only caller-supplied import values into the generated source."""

    return (
        'IMPORT_SOURCE = %r\n'
        'IMPORT_SHA256 = %r\n'
        'IMPORT_EXPECTED_BODY_SIGNATURES = %r\n'
        'IMPORT_BBOX_TOLERANCE_MM = %r\n'
        'IMPORT_VOLUME_TOLERANCE_MM3 = %r\n'
        % (
            import_config['source'],
            import_config['sha256'],
            import_config['expected_body_signatures'],
            import_config['bbox_tolerance_mm'],
            import_config['volume_tolerance_mm3'],
        )
    )


def build(output, suite='forward', import_config=None):
    if suite not in SUITES:
        raise ValueError('Unknown suite')
    if suite == 'import':
        import_config = _normalise_import_config(import_config)
    elif import_config is not None:
        raise ValueError('import_config is only valid for the import suite')

    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output / 'actions'
    snapshot.mkdir()
    for path in sorted(ACTIONS.glob('ma-*.scscript')):
        shutil.copy2(path, snapshot / path.name)
        shutil.copy2(path.with_suffix('.py'), snapshot / path.with_suffix('.py').name)
    harness = Path(__file__).resolve().parents[1] / (
        'assets/evaluations/p3-actions/' + suite + '-test.py'
    )
    prefix = (
        '# Python Script, API Version = V21\n'
        'ACTION_DIR = %r\n'
        'REPORT = %r\n'
        % (str(snapshot), str(output / 'report.json'))
    )
    if suite == 'import':
        prefix += _import_prefix(import_config)
    prefix += (
        'import os\n'
        'if os.path.exists(REPORT):\n'
        '    raise IOError("Run report already exists; build a fresh run directory")\n'
    )
    source = output / 'forward.py'
    source.write_text(prefix + harness.read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
    target = output / 'forward.scscript'
    package_scscript(source, target)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='New run-owned directory; existing directories are refused')
    parser.add_argument('--suite', choices=SUITES, default='forward')
    parser.add_argument(
        '--import-config',
        type=Path,
        help='JSON object with source, sha256, expected_body_signatures, and tolerances',
    )
    args = parser.parse_args()
    config = None
    if args.import_config is not None:
        try:
            config = json.loads(args.import_config.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            parser.error('could not read --import-config: %s' % exc)
    if args.suite == 'import' and config is None:
        parser.error('--import-config is required when --suite=import')
    if args.suite != 'import' and config is not None:
        parser.error('--import-config requires --suite=import')
    print(build(args.output, args.suite, import_config=config))
