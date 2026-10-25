# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Проверки настоящего CLI, файлов, диагностик и остановки бесконечного потока."""

import json
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "task_1_1"


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / "main.py"), *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=20)


class CliTests(unittest.TestCase):
    def test_launch_script_outside_repository(self):
        result = subprocess.run(["sh", str(ROOT / "run.sh"), "--variant"],
                                cwd=tempfile.gettempdir(), capture_output=True,
                                text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["s"], 2)

    def test_variant(self):
        result = run("--variant")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["s"], 2)

    def test_finite_generation_for_all_examples(self):
        for name in ["iid", "periodic", "markov", "nonergodic", "deterministic"]:
            args = ("generate", EXAMPLES / f"{name}.json", "--n", 30, "--seed", 2)
            first, second = run(*args), run(*args)
            with self.subTest(name=name):
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertEqual(first.stdout, second.stdout)
                self.assertEqual(len(first.stdout.splitlines()), 30)
                self.assertTrue(all(json.loads(line) in "ABC" for line in first.stdout.splitlines()))

    def test_output_and_word_files(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.json"
            result = run("analyze", EXAMPLES / "periodic.json", "--n", 100,
                         "--word-file", EXAMPLES / "word.json", "--seed", 2,
                         "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            data = json.loads(output.read_text())
            self.assertEqual(data["exact_first"]["fraction"], "169/576")
            self.assertEqual(data["exact_period_average"]["fraction"], "431/2880")
            self.assertEqual(len(data["table"]), 5)

    def test_protect_input_from_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.json"
            original = (EXAMPLES / "iid.json").read_bytes()
            source.write_bytes(original)
            result = run("generate", source, "--n", 1, "--output", source)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_bytes(), original)

    def test_invalid_files(self):
        for source in sorted((EXAMPLES / "invalid").glob("*.json")):
            for mode_args in [("generate", "--n", "1"), ("analyze", "--n", "100", "--word", "A")]:
                mode, *args = mode_args
                result = run(mode, source, *args)
                with self.subTest(file=source.name, mode=mode):
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("Ошибка:", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_bad_cli_arguments(self):
        for args in [(), ("generate", "missing.json", "--n", "1"),
                     ("generate", EXAMPLES / "iid.json", "--n", "abc"),
                     ("analyze", EXAMPLES / "iid.json", "--n", "0", "--word", "A"),
                     ("analyze", EXAMPLES / "iid.json", "--n", "1", "--word", "A", "B")]:
            result = run(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)

    def test_malformed_json_and_word_types(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "bad.json"
            for payload in [b'{}', b'[]', b'{"models":{},"models":{}}', b'\xff',
                            b'[' * 1500 + b']' * 1500]:
                bad.write_bytes(payload)
                result = run("generate", bad, "--n", 1)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
            for word in [[], [1], "AB", [""]]:
                bad.write_text(json.dumps(word))
                result = run("analyze", EXAMPLES / "iid.json", "--n", 100, "--word-file", bad)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    @unittest.skipIf(sys.platform == "win32", "Проверка SIGINT через POSIX pipe")
    def test_unbounded_generation_is_interruptible(self):
        for length in ["None", "0", "-3"]:
            process = subprocess.Popen(
                [sys.executable, str(ROOT / "main.py"), "generate",
                 str(EXAMPLES / "iid.json"), "--n", length, "--seed", "2"],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                ready, _, _ = select.select([process.stdout], [], [], 5)
                self.assertTrue(ready, "Нет первого символа потока")
                self.assertIn(json.loads(process.stdout.readline()), "ABC")
                process.send_signal(signal.SIGINT)
                _, error = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 130, error)
                self.assertIn("Ctrl+C", error)
                self.assertNotIn("Traceback", error)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()


if __name__ == "__main__":
    unittest.main()

# END GENERATED CODE: OpenAI Codex.
