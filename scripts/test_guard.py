import tempfile
import os
import subprocess
import unittest
from pathlib import Path
from public_surface_guard import check, EXPECTED

class AllowlistGuardTests(unittest.TestCase):
    def make_fixture(self, root):
        for rel in EXPECTED:
            f = root / rel
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_text('synthetic fixture',encoding='utf-8')

    def test_known_safe_files_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_fixture(root)
            self.assertEqual(check(root), [])

    def test_unreviewed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_fixture(root)
            (root / 'private-production.json').write_text('production',encoding='utf-8')
            self.assertTrue(any('Unreviewed file' in error for error in check(root)))

    def test_private_key_pattern_blocked_without_logging_value(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_fixture(root)
            (root / 'README.md').write_text('-----BEGIN ' + 'PRIVATE KEY-----' + '\nSYNTHETIC',encoding='utf-8')
            errors = check(root)
            self.assertTrue(any('private-key' in error for error in errors))
            self.assertTrue(all('PRIVATE KEY-----' not in error for error in errors))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_fixture(root)
            (root / 'unexpected').symlink_to(root / 'README.md')
            self.assertTrue(any('symlink' in error for error in check(root)))

    def test_generated_python_cache_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_fixture(root)
            cache = root / 'scripts' / '__pycache__'
            cache.mkdir()
            (cache / 'public_surface_guard.cpython-313.pyc').write_bytes(b'synthetic bytecode')
            errors = check(root)
            self.assertTrue(any('__pycache__' in error for error in errors))

    def test_upstream_dependencies_are_immutable_and_no_apt_client_install(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/public-safe-ci.yml').read_text()
        flutter = (root / 'scripts/mobile-smoke.sh').read_text()
        mysql = (root / 'scripts/mysql-smoke.sh').read_text()
        self.assertIn('mariadb:11.4.13@sha256:9c8b5172fa219e01913060f26c5498029999657fb9b7e7bbd0ca9e87f51020e2', workflow)
        self.assertNotIn('image: mariadb:11.4\n', workflow)
        self.assertNotIn('apt-get', workflow)
        self.assertIn('CI_DB_CONTAINER_ID: ${{ job.services.db.id }}', workflow)
        self.assertIn('b8962555571d8c170cff8e76023ea7bf60e5ec4b', flutter)
        self.assertIn('git -C "$flutter_dir" rev-parse HEAD', flutter)
        self.assertNotIn('git clone --depth 1 --branch', flutter)
        self.assertIn('docker inspect --format', mysql)
        self.assertIn('docker exec -i', mysql)
        self.assertIn('git -C "$flutter_dir" fetch --no-tags --depth 1 origin refs/tags/3.35.0', flutter)
        self.assertIn('actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444', workflow)
        self.assertIn('actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd', workflow)
        self.assertNotIn('ubuntu-24.04', workflow)
        self.assertEqual(workflow.count('runs-on: ubuntu-22.04'), 7)
        self.assertEqual(workflow.count('persist-credentials: false'), 7)
        self.assertEqual(workflow.count('fetch-depth: 1'), 7)
        self.assertIn("node-version: '22.16.0'", workflow)
        self.assertIn('EXPECTED_PUBLIC_REPO: sudheeerrr/bulkgram-ci-public', workflow)
        self.assertIn('GITHUB_EVENT_NAME', workflow)
        self.assertIn('RUNNER_ENVIRONMENT', workflow)

    def test_browser_maintains_sandbox_and_isolated_profile(self):
        root = Path(__file__).resolve().parents[1]
        browser = (root / 'scripts/browser-smoke.sh').read_text()
        self.assertIn('--user-data-dir="$profile"', browser)
        self.assertIn('--disable-background-networking', browser)
        self.assertIn("trap 'rm -rf -- \"$profile\"' EXIT", browser)
        self.assertNotIn('--no-sandbox', browser)

    def _mysql_script(self, env_changes, docker_output=None):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            fake_bin = Path(d) / 'bin'
            fake_bin.mkdir()
            if docker_output is not None:
                docker = fake_bin / 'docker'
                docker.write_text('#!/bin/sh\nif [ "$1" = inspect ]; then printf "%s\n" "$CI_FAKE_IMAGE"; fi\n', encoding='utf-8')
                docker.chmod(0o700)
            env = dict(os.environ)
            env.update({
                'CI_DB_HOST': '127.0.0.1',
                'CI_DB_NAME': 'public_ci_synthetic',
                'CI_DB_USER': 'publicci',
                'CI_DB_PASSWORD': 'synthetic-test-only',
                'GITHUB_ACTIONS': 'true',
                'CI_DB_CONTAINER_ID': 'a' * 64,
                'CI_FAKE_IMAGE': docker_output or '',
                'PATH': str(fake_bin) + os.pathsep + env.get('PATH', ''),
            })
            env.update(env_changes)
            return subprocess.run(
                ['bash', str(root / 'scripts/mysql-smoke.sh')],
                env=env, capture_output=True, text=True, timeout=10,
            )

    def test_mysql_rejects_nonlocal_database_before_service_access(self):
        result = self._mysql_script({'CI_DB_HOST': 'db.example.invalid'})
        self.assertEqual(result.returncode, 11)
        self.assertIn('non-loopback', result.stderr)

    def test_mysql_rejects_unexpected_service_container_image(self):
        result = self._mysql_script({}, 'mariadb:latest')
        self.assertEqual(result.returncode, 15)
        self.assertIn('Unexpected database service image', result.stderr)

    def test_mysql_rejects_missing_service_container_identity(self):
        result = self._mysql_script({'CI_DB_CONTAINER_ID': 'not-a-container-id'}, 'mariadb:latest')
        self.assertEqual(result.returncode, 15)
        self.assertIn('Invalid service container ID', result.stderr)

    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_fixture(root)
            (root / 'README.md').unlink()
            self.assertTrue(any('Missing required' in error for error in check(root)))

if __name__ == '__main__':
    unittest.main()
