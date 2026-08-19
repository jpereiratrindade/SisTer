from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def bash(script: str, check: bool = True):
    return subprocess.run(["bash", "-c", script], cwd=ROOT, text=True,
                          capture_output=True, check=check)

class DbDataDirContractTests(unittest.TestCase):
    def test_legacy_mode_is_default(self):
        r = bash('''
          unset SISTER_DB_DATA_DIR
          export SISTER_DB_PASSWORD=test-password
          source scripts/lib/sister_env.sh
          sister_load_env dev
          printf '%s|%s|%s\\n' "$(sister_db_storage_mode)" "$SISTER_DB_VOLUME" "${SISTER_DB_DATA_DIR:-}"
        ''')
        self.assertEqual("legacy-volume|sister_dev_pgdata|\n", r.stdout)

    def test_absolute_path_enables_bind_without_creating_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "postgres"
            r = bash(f'''
              export SISTER_DB_PASSWORD=test-password
              export SISTER_DB_DATA_DIR={d}
              source scripts/lib/sister_env.sh
              sister_load_env dev
              printf '%s|%s\\n' "$(sister_db_storage_mode)" "$SISTER_DB_DATA_DIR"
            ''')
            self.assertEqual(f"bind|{d}\n", r.stdout)
            self.assertFalse(d.exists())

    def test_relative_path_is_rejected(self):
        r = bash('''
          export SISTER_DB_PASSWORD=test-password
          export SISTER_DB_DATA_DIR=relative/postgres
          source scripts/lib/sister_env.sh
          sister_load_env dev
        ''', check=False)
        self.assertNotEqual(0, r.returncode)
        self.assertIn("must be an absolute path", r.stderr)

    def test_print_env_redacts_and_reports_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "postgres"
            r = bash(f'''
              source scripts/lib/sister_env.sh
              export SISTER_DATABASE_URL='postgresql://user:unique-secret@localhost/db'
              export SISTER_ENV=dev COMPOSE_PROJECT_NAME=x SISTER_DB_CONTAINER=x
              export SISTER_DB_PORT=1 SISTER_DB_VOLUME=x SISTER_APP_PORT=2
              export SISTER_BIND_HOST=127.0.0.1 SISTER_DB_DATA_DIR={d}
              sister_print_env
            ''')
            self.assertNotIn("unique-secret", r.stdout)
            self.assertIn("SISTER_DB_STORAGE=bind", r.stdout)
            self.assertIn(f"SISTER_DB_DATA_DIR={d}", r.stdout)
            self.assertIn("credentials redacted", r.stdout)

    def test_bind_mount_does_not_create_named_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp); d = td / "postgres"; log = td / "podman.log"
            r = bash(f'''
              export SISTER_DB_CONTAINER=sister-ops002b-test-db SISTER_DB_PORT=59999
              export SISTER_DB_VOLUME=legacy-volume SISTER_DB_PASSWORD=test-password
              export SISTER_DB_DATA_DIR={d} LOG={log}
              podman() {{
                printf '%s\\n' "$*" >> "$LOG"
                case "$1 $2" in
                  "container exists") return 1 ;;
                  "inspect --format") printf '%s\\n' healthy; return 0 ;;
                  *) return 0 ;;
                esac
              }}
              source scripts/lib/podman_db.sh
              sister_podman_up
            ''')
            self.assertEqual("", r.stderr)
            s = log.read_text()
            self.assertIn(f"-v {d}:/var/lib/postgresql/data:Z", s)
            self.assertNotIn("volume create legacy-volume", s)
            self.assertTrue(d.is_dir())

    def test_storage_mismatch_blocks_down(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp); expected = td/"expected"; other = td/"operational"; log=td/"podman.log"
            r = bash(f'''
              export SISTER_DB_CONTAINER=sister-dev-db SISTER_DB_DATA_DIR={expected} LOG={log}
              podman() {{
                printf '%s\\n' "$*" >> "$LOG"
                if [[ "$1 $2" == "container exists" ]]; then return 0; fi
                if [[ "$1" == "inspect" ]]; then printf '%s\\n' {other}; return 0; fi
                return 0
              }}
              source scripts/lib/podman_db.sh
              sister_podman_down
            ''', check=False)
            self.assertNotEqual(0, r.returncode)
            self.assertIn("storage identity mismatch", r.stderr)
            self.assertNotIn("stop sister-dev-db", log.read_text())

    def test_destroy_preserves_matching_bind_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp); d=td/"postgres"; d.mkdir(); sentinel=d/"keep-me"; sentinel.write_text("x"); log=td/"podman.log"
            r = bash(f'''
              export SISTER_DB_CONTAINER=sister-ops002b-test-db SISTER_DB_DATA_DIR={d} LOG={log}
              podman() {{
                printf '%s\\n' "$*" >> "$LOG"
                if [[ "$1 $2" == "container exists" ]]; then return 0; fi
                if [[ "$1" == "inspect" ]]; then printf '%s\\n' {d}; return 0; fi
                return 0
              }}
              source scripts/lib/podman_db.sh
              sister_podman_destroy
            ''')
            self.assertEqual(0, r.returncode)
            self.assertTrue(sentinel.exists())
            s=log.read_text()
            self.assertIn("rm -f sister-ops002b-test-db", s)
            self.assertNotIn("volume rm", s)

    def test_db_entrypoints_prioritize_bind_mode(self):
        for rel in ("scripts/db/up.sh", "scripts/db/down.sh", "scripts/db/destroy.sh"):
            t=(ROOT/rel).read_text()
            self.assertLess(t.index('if [[ -n "${SISTER_DB_DATA_DIR:-}" ]]'),
                            t.index('elif sister_compose_available; then'))

if __name__ == "__main__":
    unittest.main()
