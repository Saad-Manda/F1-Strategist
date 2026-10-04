"""Check every deterministic generator and site resource without modifying files."""
import subprocess
import sys
from paths import ROOT, SCRIPTS

CHECKS = (
    'build_course.py',
    'build_navigation.py',
    'build_catalog.py', 'build_foundation_pages.py', 'build_foundation_packs.py',
    'build_tabular_pages.py', 'build_tabular_packs.py', 'build_neural_readings.py',
    'build_neural_pages.py', 'build_neural_packs.py', 'build_multiagent_pages.py',
    'build_multiagent_packs.py', 'build_policy_pages.py', 'build_policy_packs.py',
    'build_reading_links.py', 'build_reading_sections.py', 'build_lab_downloads.py', 'validate_labs.py', 'audit_course.py',
)


def main():
    for name in CHECKS:
        result = subprocess.run([sys.executable, str(SCRIPTS / name)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            print(f'{name} failed:\n{result.stdout}{result.stderr}', file=sys.stderr)
            raise SystemExit(result.returncode)
        print(result.stdout.strip(), flush=True)
    print('All deterministic generators and resource checks passed. No training fixtures were regenerated.')


if __name__ == '__main__':
    main()
