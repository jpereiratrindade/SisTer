from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DevPreviewRuntimeContractTests(unittest.TestCase):
    def test_entrypoint_declares_complete_preview_identity(self):
        source = (ROOT / "scripts/runtime.sh").read_text(encoding="utf-8")
        for marker in (
            "SISTER_RUNTIME_MODE",
            "SISTER_RUNTIME_INSTANCE_ID",
            "SISTER_RUNTIME_STATE_DIR",
            "SISTER_RUNTIME_RUN_DIR",
            "SISTER_RUNTIME_DATA_DIR",
        ):
            self.assertIn(marker, source)

    def test_preview_resources_are_derived_from_ephemeral_identity(self):
        with tempfile.TemporaryDirectory(prefix="sister-preview-contract-") as tmp:
            state = Path(tmp) / "state"
            data = state / "data"
            script = f'''
              source scripts/lib/sister_env.sh
              export SISTER_DB_PASSWORD=test-password
              export SISTER_RUNTIME_MODE=dev-preview
              export SISTER_RUNTIME_INSTANCE_ID=sister-contract-123
              export SISTER_RUNTIME_STATE_DIR={state}
              export SISTER_RUNTIME_RUN_DIR={Path(tmp) / "run"}
              export SISTER_RUNTIME_DATA_DIR={data}
              export SISTER_PREVIEW_DB_PORT=49123
              sister_load_env dev
              printf '%s|%s|%s|%s|%s\n' \
                "$COMPOSE_PROJECT_NAME" "$SISTER_DB_CONTAINER" \
                "$SISTER_DB_PORT" "$SISTER_DB_DATA_DIR" "$SISTER_DATABASE_URL"
            '''
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            fields = result.stdout.strip().split("|")
            self.assertEqual("sister-preview-sister-contract-123", fields[0])
            self.assertEqual("sister-preview-sister-contract-123-db", fields[1])
            self.assertEqual("49123", fields[2])
            self.assertEqual(str(data / "postgresql"), fields[3])
            self.assertIn("localhost:49123/sister", fields[4])
            self.assertNotIn("sister-dev-db", result.stdout)
            self.assertNotIn("sister_dev_pgdata", result.stdout)

    def test_preview_rejects_data_directory_outside_state(self):
        with tempfile.TemporaryDirectory(prefix="sister-preview-contract-") as tmp:
            env = dict(os.environ)
            env.update(
                {
                    "SISTER_COMPONENT_CONFIG_FILE": "/dev/null",
                    "SISTER_RUNTIME_MODE": "dev-preview",
                    "SISTER_RUNTIME_INSTANCE_ID": "sister-contract-escape",
                    "SISTER_RUNTIME_STATE_DIR": str(Path(tmp) / "state"),
                    "SISTER_RUNTIME_RUN_DIR": str(Path(tmp) / "run"),
                    "SISTER_RUNTIME_DATA_DIR": str(Path(tmp) / "outside"),
                    "SISTER_RUNTIME_CLEANUP_SCOPE": "preview-only",
                }
            )
            result = subprocess.run(
                [str(ROOT / "scripts/runtime.sh"), "status"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("deve pertencer ao state dir", result.stderr)

    def test_sisterd_process_receives_preview_identity(self):
        source = (ROOT / "scripts/app/serve.sh").read_text(encoding="utf-8")
        for marker in (
            "SISTER_RUNTIME_MODE",
            "SISTER_RUNTIME_INSTANCE_ID",
            "SISTER_RUNTIME_STATE_DIR",
            "SISTER_RUNTIME_RUN_DIR",
            "SISTER_RUNTIME_DATA_DIR",
        ):
            self.assertIn(f'{marker}="', source)


if __name__ == "__main__":
    unittest.main()
