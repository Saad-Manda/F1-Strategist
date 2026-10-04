"""Create reproducible lesson archives from reviewed source packs (authoring only)."""
import argparse
from io import BytesIO
from pathlib import Path
import zipfile
from build_catalog import load_registry

from paths import ROOT, LABS
PACKS = LABS / 'downloads'
FILES = ('README.md', 'starter.py', 'broken.py', 'solution.py', 'exercise_common.py',
         'checks.py', 'requirements.txt', 'fixtures.json')


def archive_bytes(lab_id):
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        names = FILES + (('compare.py',) if (PACKS / lab_id / 'compare.py').is_file() else ())
        for name in names:
            path = PACKS / lab_id / name
            info = zipfile.ZipInfo(f'{lab_id}/{name}', date_time=(2026, 10, 3, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    lab_ids = [lab['id'] for lab in load_registry()['labs'] if lab['status'] == 'ready']
    for lab_id in lab_ids:
        expected = archive_bytes(lab_id)
        path = PACKS / f'{lab_id}.zip'
        if args.write:
            path.write_bytes(expected)
        elif not path.exists() or path.read_bytes() != expected:
            raise SystemExit(f'{lab_id} archive is stale. Run build_lab_downloads.py --write.')
    print(f'{len(lab_ids)} archives ' + ('generated.' if args.write else 'are current.'))


if __name__ == '__main__':
    main()
