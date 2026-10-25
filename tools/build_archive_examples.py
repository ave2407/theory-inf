# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Собственные бинарные входы архиватора, включая синтетический PNG и Unicode."""

import argparse
from pathlib import Path
import random
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]


def png_chunk(kind: bytes, data: bytes) -> bytes:
    """Собрать PNG-блок: длина данных, четырёхбайтовый тип, данные и CRC32."""
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def main():
    """Записать семь контрольных файлов, включая PNG с seed; реальные PDF не менять."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2)
    args = parser.parse_args()
    directory = ROOT / "examples/task_1_3"
    directory.mkdir(parents=True, exist_ok=True)
    russian = (
        "Теория информации изучает способы представления и передачи сообщений. "
        "Частым символам можно назначить короткие кодовые слова, редким — длинные. "
        "После распаковки каждый байт должен совпасть с исходным.\n"
    )
    english = (
        "Information theory studies how messages are represented and transmitted. "
        "Frequent symbols can receive short codewords, while rare symbols use longer ones. "
        "Decompression must reproduce every original byte.\n"
    )
    unicode = "Привет 🌍 😀 中文 café cafe\u0301 👩‍💻 👍🏽 🇷🇺 Ελληνικά العربية\n"
    (directory / "russian.txt").write_text(russian * 40, encoding="utf-8")
    (directory / "english.txt").write_text(english * 40, encoding="utf-8")
    (directory / "unicode.txt").write_text(unicode * 40, encoding="utf-8")
    (directory / "repeated.bin").write_bytes(b"A" * 4096)
    (directory / "empty.bin").write_bytes(b"")
    (directory / "all_bytes.bin").write_bytes(bytes(range(256)) * 8)
    width = height = 128
    rng = random.Random(args.seed)
    pixels = b"".join(b"\x00" + rng.randbytes(width * 3) for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    # zlib сжимает только тестовое изображение; архиватор использует свой Хаффман.
    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) +
           png_chunk(b"IDAT", zlib.compress(pixels, level=9)) + png_chunk(b"IEND", b""))
    (directory / "image.png").write_bytes(png)


if __name__ == "__main__":
    main()

# END GENERATED CODE: OpenAI Codex.
