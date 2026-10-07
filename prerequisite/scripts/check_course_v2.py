"""Check v2 metadata/migration inputs; --publish also requires every authored body."""
import argparse
import json
from course_v2 import load_course_v2, validate_course_v2, reading_context
from migration_v2 import load_migration_inputs, validate_migration_contracts
from paths import ROOT, SITE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--write', action='store_true', help='Regenerate the offline navigation manifest only')
    args = parser.parse_args()
    course = load_course_v2()
    labs = json.loads((SITE / 'labs/assets/lab-registry.json').read_text(encoding='utf-8'))
    errors = validate_course_v2(course, labs, allow_planned=not args.publish)
    if errors:
        raise SystemExit('\n'.join(errors))
    snapshot, mapping, relocations = load_migration_inputs()
    errors = validate_migration_contracts(course, labs, snapshot, mapping, relocations)
    if errors:
        raise SystemExit('\n'.join(errors))
    manifest = {r['route']: reading_context(course, r['id']) for r in course['readings']}
    path = ROOT / 'content/navigation-v2.json'
    source = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    if args.write:
        path.write_text(source, encoding='utf-8')
    elif not path.is_file() or path.read_text(encoding='utf-8') != source:
        raise SystemExit('Offline v2 navigation manifest is stale; use --write.')
    print(f'V2 {"publishable sources" if args.publish else "metadata"} and canonical navigation verified.')


if __name__ == '__main__':
    main()
