"""Exercise an isolated project copy with no main-project files or plan directory."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def test_isolated_copy_generates_checks_and_packages_without_parent_project(tmp_path):
    target = tmp_path / 'standalone'
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', '.venv', 'venv', 'node_modules', 'dist'))
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    # Deliberately invoke from outside the project so cwd-based resolution fails.
    def run(*args, timeout=600):
        result = subprocess.run(args, cwd=tmp_path, env=env, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        assert result.returncode == 0, result.stdout + result.stderr
        return result
    assert not (target.parent / '.antigravity').exists()
    assert not (target.parent / 'src').exists()
    # Complete generator/test/archive suites need more time than one check on Windows.
    run(sys.executable, str(target / 'scripts/check_project.py'))
    run(sys.executable, '-m', 'pytest', str(target / 'tests/test_curriculum.py'),
        str(target / 'tests/test_course_v2.py'), str(target / 'tests/test_p1_loop.py'),
        str(target / 'tests/test_course_pages.py'),
        str(target / 'tests/test_course_navigation.py'),
        '-p', 'no:cacheprovider', '-q')
    # Avoid depending on a shell's wildcard expansion (PowerShell and POSIX differ).
    run(shutil.which('node') or 'node', '--test', *map(str, sorted((target / 'tests').glob('*.mjs'))))
    run(sys.executable, str(target / 'scripts/build_static_delivery.py'), '--write')
    archive = target / 'dist/rl-prerequisites-static.zip'
    assert archive.is_file()
    with zipfile.ZipFile(archive) as z:
        assert 'index.html' in z.namelist()
        assert len([n for n in z.namelist() if n.endswith('.zip')]) == 25
        assert not any(n.startswith(('scripts/', 'tests/', 'docs/')) for n in z.namelist())
        assert not any('AUTHOR_SPECIFICATIONS' in n or 'CONTENT_REVIEW' in n for n in z.namelist())
    # Recheck reproducibility without write mode from another cwd.
    run(sys.executable, str(target / 'scripts/build_static_delivery.py'))
