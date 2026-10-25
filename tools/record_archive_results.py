# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""CLI-измерения задачи 1.3, read-back и примеры диагностик повреждений."""

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INPUTS = Path("examples/task_1_3")
OUTPUTS = Path("results/task_1_3")
MARKER = "# Результаты задачи 1.3"
NAMES = ("russian.txt", "english.txt", "image.png", "repeated.bin", "empty.bin", "unicode.txt", "all_bytes.bin",
         "attention_is_all_you_need.pdf", "konstituciya_rossiyskoy_federacii.pdf")


def execute(arguments, expected=0):
    """Запустить CLI архиватора и проверить код завершения, включая ожидаемые ошибки."""
    result = subprocess.run([sys.executable, "main.py", *map(str, arguments)], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    if result.returncode != expected:
        raise RuntimeError(f"{arguments}: код {result.returncode}; {result.stderr}")
    return result


def main():
    """Пересоздать архивы корпуса, проверить восстановление и записать статистику.

    Для каждого входа сравниваются байты, SHA-256 и результат проверки CRC32.
    Затем сохраняются примеры повреждений и обновляется раздел 1.3 RESULTS.md.
    """
    (ROOT / OUTPUTS).mkdir(parents=True, exist_ok=True)
    lines = [MARKER, "", f"Python {platform.python_version()}. Воспроизведение: `python3 tools/record_archive_results.py`.", "",
             "PNG синтетический, создан tools/build_archive_examples.py с seed=2. Контрольные тексты собственные, UTF-8.",
             "Реальные документы и происхождение: `examples/task_1_3/real_sources.json`.", "",
             "Проверка восстановления выполнена побайтовым сравнением и SHA-256.", ""]
    summary = ["| Файл | Исходных байтов | H, бит/байт | Средняя длина, бит | Заголовок | Данные | Архив | Архив / исходник |",
               "|---|---:|---:|---:|---:|---:|---:|---:|"]
    manifest = []
    with tempfile.TemporaryDirectory() as temporary:
        for name in NAMES:
            source = INPUTS / name
            packed = OUTPUTS / (name + ".zmh")
            # Удаляются только результаты этого скрипта; CLI всегда запрещает перезапись.
            (ROOT / packed).unlink(missing_ok=True)
            arguments = ["compress", str(source), "--output", str(packed), "--stats"]
            result = execute(arguments)
            stats = json.loads(result.stdout)
            (ROOT / OUTPUTS / (name + ".stats.json")).write_text(result.stdout, encoding="utf-8")
            restored = Path(temporary) / name
            read_back = execute(["decompress", str(packed), "--output", str(restored), "--stats"])
            verification = json.loads(read_back.stdout)
            original_bytes = (ROOT / source).read_bytes()
            restored_bytes = restored.read_bytes()
            if original_bytes != restored_bytes or not verification["verified"]:
                raise AssertionError(f"Восстановление не совпало: {name}")
            digest = hashlib.sha256(original_bytes).hexdigest()
            manifest.append({"input": str(source), "archive": str(packed),
                             "sha256_original": digest,
                             "sha256_restored": hashlib.sha256(restored_bytes).hexdigest(),
                             "byte_equal": True, "crc_verified": True})
            ratio = "—" if stats["compression_ratio"] is None else f"{stats['compression_ratio']:.6f}"
            summary.append(f"| {name} | {stats['original_bytes']} | {float(stats['entropy_bits_per_byte']):.6f} | "
                           f"{stats['average_code_length_bits']['decimal']:.6f} | {stats['header_bytes']} | "
                           f"{stats['data_bytes']} | {stats['archive_bytes']} | {ratio} |")
            lines += [f"## {name}", "", f"`python3 main.py {' '.join(arguments)}`", "",
                      "```json", result.stdout.rstrip(), "```", "",
                      f"Восстановление: CRC32 пройдена; байты совпали; SHA-256 `{digest}`.", ""]
    (ROOT / OUTPUTS / "verification.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    invalid = ROOT / INPUTS / "invalid"
    invalid.mkdir(exist_ok=True)
    valid = (ROOT / OUTPUTS / "english.txt.zmh").read_bytes()
    cases = {"foreign.zmh": b"This is not a ZMH file.", "truncated.zmh": valid[:-1]}
    corrupted = bytearray(valid)
    corrupted[-1] ^= 0x80
    cases["corrupted.zmh"] = bytes(corrupted)
    lines += ["## Диагностика", ""]
    for name, payload in cases.items():
        path = invalid / name
        path.write_bytes(payload)
        output = ROOT / OUTPUTS / (name + ".unexpected-output")
        result = execute(["decompress", str(path.relative_to(ROOT)), "--output", str(output)], expected=2)
        if output.exists():
            raise AssertionError("После неуспешной проверки появился конечный файл")
        lines += [f"- `{name}`: код 2, {result.stderr.strip()}"]
    lines += ["", "## Сводная таблица", "", *summary]
    results = ROOT / "RESULTS.md"
    before = results.read_text(encoding="utf-8").split(MARKER, 1)[0].rstrip()
    results.write_text(before + "\n\n" + "\n".join(lines).rstrip() + "\n", encoding="utf-8")
    (ROOT / OUTPUTS / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main()

# END GENERATED CODE: OpenAI Codex.
