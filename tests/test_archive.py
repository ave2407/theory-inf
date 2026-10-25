# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Архив ZMH1: контрольные коды, побайтовое восстановление и повреждения."""

from fractions import Fraction
import io
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

import theory_inf.archive as archive
from theory_inf.archive import (
    CHECKSUM, FIXED_HEADER_BYTES, MAGIC, METADATA, CorruptArchive,
    ForeignFormat, TruncatedArchive, compress, decompress,
)
from theory_inf.distributions import InputError
from theory_inf.huffman import BitWriter, canonical_codes, code_lengths

ROOT = Path(__file__).resolve().parents[1]


def container(size, bits, crc, pairs, payload=b""):
    metadata = METADATA.pack(MAGIC, size, bits, len(pairs), crc)
    model = bytes(value for pair in pairs for value in pair)
    return metadata + CHECKSUM.pack(zlib.crc32(metadata)) + model + payload


class HuffmanTests(unittest.TestCase):
    def test_leaf_queue_precedes_equal_weight_internal_node(self):
        # После слияния 1+1 оставшиеся листья 2,2 идут перед новым узлом 2.
        # Все четыре длины равны 2; правило minimum-symbol дало бы 3,3,2,1.
        self.assertEqual(code_lengths([1, 1, 2, 2] + [0] * 252),
                         {0: 2, 1: 2, 2: 2, 3: 2})

    def test_manual_tree_and_canonical_codes(self):
        frequencies = [0] * 256
        frequencies[65:68] = [4, 2, 1]
        self.assertEqual(code_lengths(frequencies), {65: 1, 66: 2, 67: 2})
        self.assertEqual(canonical_codes(code_lengths(frequencies)), {65: (0, 1), 66: (2, 2), 67: (3, 2)})

    def test_ties_and_all_bytes(self):
        self.assertEqual(set(code_lengths([1] * 256).values()), {8})
        codes = canonical_codes(code_lengths([1] * 256))
        self.assertEqual(codes, {a: (a, 8) for a in range(256)})

    def test_single_and_empty(self):
        self.assertEqual(code_lengths([0] * 256), {})
        frequencies = [0] * 256
        frequencies[255] = 100
        self.assertEqual(code_lengths(frequencies), {255: 0})
        self.assertEqual(canonical_codes({255: 0}), {255: (0, 0)})

    def test_invalid_code_lengths_and_frequencies(self):
        for lengths in [{0: 1}, {0: 1, 1: 1, 2: 1}, {0: 3, 1: 3},
                        {0: 0, 1: 1}, {0: 256}, {-1: 0}]:
            with self.subTest(lengths=lengths), self.assertRaises(InputError):
                canonical_codes(lengths)
        for frequencies in [[], [-1] * 256, [1.5] * 256]:
            with self.assertRaises(InputError):
                code_lengths(frequencies)

    def test_bit_order_padding_and_buffer(self):
        stream = io.BytesIO()
        writer = BitWriter(stream, buffer_size=1)
        for code, length in [(2, 2), (0, 1), (3, 2)]:
            writer.write(code, length)
        writer.finish()
        self.assertEqual(stream.getvalue(), b"\x98")  # 10 0 11 000
        self.assertEqual(writer.total_bits, 5)

    def test_deep_tree_without_recursion(self):
        values = [1, 1]
        for _ in range(254):
            values.append(values[-1] + values[-2])
        lengths = code_lengths(values)
        self.assertEqual(max(lengths.values()), 255)
        codes = canonical_codes(lengths)
        self.assertEqual(len(codes), 256)
        stream = io.BytesIO()
        writer = BitWriter(stream)
        for code, length in codes.values():
            writer.write(code, length)
        writer.finish()
        self.assertEqual(len(stream.getvalue()), (sum(lengths.values()) + 7) // 8)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source.bin"
        self.packed = self.root / "source.bin.zmh"
        self.restored = self.root / "restored.bin"

    def tearDown(self):
        self.temporary.cleanup()

    def roundtrip(self, data):
        self.source.write_bytes(data)
        compressed = compress(self.source, self.packed)
        restored = decompress(self.packed, self.restored)
        self.assertEqual(self.restored.read_bytes(), data)
        self.assertTrue(restored["verified"])
        self.assertEqual(compressed["archive_bytes"], self.packed.stat().st_size)
        self.assertEqual(compressed["original_bytes"], len(data))
        self.assertEqual(compressed["original_crc32"], restored["original_crc32"])
        return compressed

    def assert_rejected(self, data, kind):
        self.packed.write_bytes(data)
        with self.assertRaises(kind):
            decompress(self.packed, self.restored)
        self.assertFalse(self.restored.exists())
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_empty(self):
        stats = self.roundtrip(b"")
        self.assertEqual(stats["header_bytes"], 30)
        self.assertEqual(stats["payload_bits"], 0)
        self.assertIsNone(stats["compression_ratio"])

    def test_single_symbol(self):
        stats = self.roundtrip(b"\x00" * 200000)
        self.assertEqual(stats["archive_bytes"], 32)
        self.assertEqual(stats["average_code_length_bits"]["fraction"], "0")
        self.assertEqual(stats["entropy_bits_per_byte"], "0")

    def test_all_byte_values(self):
        stats = self.roundtrip(bytes(range(256)) * 17)
        self.assertEqual(stats["header_bytes"], 542)
        self.assertEqual(stats["average_code_length_bits"]["fraction"], "8")
        self.assertEqual(stats["entropy_bits_per_byte"], "8")
        self.assertGreater(stats["compression_ratio"], 1)

    def test_unicode_roundtrip(self):
        text = "Привет 🌍 😀 中文 café cafe\u0301 👩‍💻 👍🏽 🇷🇺\n"
        self.roundtrip(text.encode("utf-8") * 50)

    def test_manual_payload_and_statistics(self):
        stats = self.roundtrip(b"ABACABA")
        self.assertEqual(self.packed.read_bytes()[-2:], bytes.fromhex("4d00"))
        self.assertEqual(stats["payload_bits"], 10)
        self.assertEqual(stats["header_bytes"], 36)
        self.assertEqual(Fraction(stats["average_code_length_bits"]["fraction"]), Fraction(10, 7))

    def test_small_chunk_boundaries(self):
        data = random.Random(2).randbytes(100000)
        with patch.object(archive, "CHUNK_BYTES", 7):
            self.roundtrip(data)

    def test_random_sizes_and_reproducibility(self):
        rng = random.Random(2)
        for size in [1, 2, 3, 7, 8, 9, 255, 256, 257, 65535, 65536, 65537]:
            data = rng.randbytes(size)
            self.source.write_bytes(data)
            first = self.root / "first.zmh"
            second = self.root / "second.zmh"
            compress(self.source, first)
            compress(self.source, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            decompress(first, self.restored)
            self.assertEqual(self.restored.read_bytes(), data)
            for path in [first, second, self.restored]:
                path.unlink()

    def test_foreign_format(self):
        self.assert_rejected(b"not a zmh archive", ForeignFormat)

    def test_every_truncation_of_valid_archive(self):
        self.source.write_bytes(b"ABACABA")
        compress(self.source)
        original = self.packed.read_bytes()
        for size in range(len(original)):
            with self.subTest(size=size):
                self.assert_rejected(original[:size], TruncatedArchive)

    def test_every_single_bit_flip(self):
        self.source.write_bytes(b"ABACABA")
        compress(self.source)
        original = self.packed.read_bytes()
        for i in range(len(original)):
            for bit in range(8):
                mutated = bytearray(original)
                mutated[i] ^= 1 << bit
                with self.subTest(byte=i, bit=bit):
                    self.assert_rejected(mutated, (ForeignFormat, CorruptArchive))

    def test_trailing_bytes(self):
        self.source.write_bytes(b"ABACABA")
        compress(self.source)
        self.assert_rejected(self.packed.read_bytes() + b"\x00", CorruptArchive)

    def test_structurally_invalid_models(self):
        for pairs in [[(65, 1), (65, 2), (67, 2)], [(66, 2), (65, 1), (67, 2)],
                      [(65, 0), (66, 2), (67, 2)], [(65, 1), (66, 1), (67, 1)],
                      [(65, 3), (66, 3), (67, 3)]]:
            with self.subTest(pairs=pairs):
                self.assert_rejected(container(7, 10, 0, pairs, b"\x00\x00"), CorruptArchive)

    def test_bad_checksum_without_bad_metadata(self):
        self.assert_rejected(container(100, 0, 123, [(65, 0)]), CorruptArchive)

    def test_unused_symbol_in_model(self):
        original = b"AAAAABBBBB"
        stream = io.BytesIO()
        writer = BitWriter(stream)
        codes = canonical_codes({65: 1, 66: 2, 67: 2})
        for byte in original:
            writer.write(*codes[byte])
        writer.finish()
        data = container(len(original), 15, zlib.crc32(original),
                         [(65, 1), (66, 2), (67, 2)], stream.getvalue())
        self.assert_rejected(data, CorruptArchive)

    def test_inconsistent_metadata(self):
        for size, bits, pairs, payload in [(0, 1, [], b"\x00"), (10, 0, [], b""),
                                           (1, 1, [(65, 1)], b"\x00"),
                                           (1, 2, [(65, 1), (66, 1)], b"\x00")]:
            self.assert_rejected(container(size, bits, 0, pairs, payload), CorruptArchive)

    def test_no_overwrite_and_same_input_output(self):
        self.source.write_bytes(b"ABACABA")
        with self.assertRaises(InputError):
            compress(self.source, self.source)
        compress(self.source)
        self.restored.write_bytes(b"KEEP")
        with self.assertRaises(InputError):
            decompress(self.packed, self.restored)
        self.assertEqual(self.restored.read_bytes(), b"KEEP")
        with self.assertRaises(InputError):
            compress(self.source)

    def test_input_changes_between_passes(self):
        self.source.write_bytes(b"ABAB")
        scan = archive.scan

        def changing_scan(inp):
            result = scan(inp)
            self.source.write_bytes(b"BABA")
            return result

        with patch.object(archive, "scan", changing_scan), self.assertRaisesRegex(InputError, "изменился"):
            compress(self.source)
        self.assertFalse(self.packed.exists())
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_default_restore_name(self):
        self.source.write_bytes(b"ABACABA")
        compress(self.source)
        self.source.unlink()
        decompress(self.packed)
        self.assertEqual(self.source.read_bytes(), b"ABACABA")


class ArchiveCliTests(unittest.TestCase):
    def command(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "main.py"), *map(str, args)],
                              cwd=ROOT, capture_output=True, text=True, timeout=20)

    def test_both_modes_and_stats(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "unicode.txt"
            source.write_text("Привет 🌍 👩‍💻\n", encoding="utf-8")
            packed = source.with_name(source.name + ".zmh")
            restored = Path(folder) / "restored.txt"
            result = self.command("compress", source, "--stats")
            self.assertEqual(result.returncode, 0, result.stderr)
            stats = json.loads(result.stdout)
            self.assertEqual(stats["archive_bytes"], packed.stat().st_size)
            result = self.command("decompress", packed, "--output", restored, "--stats")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["verified"])
            self.assertEqual(restored.read_bytes(), source.read_bytes())
            again = self.command("decompress", packed, "--output", restored)
            self.assertEqual(again.returncode, 2)
            self.assertNotIn("Traceback", again.stderr)

    def test_distinct_diagnostics_and_no_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.zmh"
            output = Path(folder) / "out.bin"
            valid = container(0, 0, 0, [])
            corrupt = bytearray(valid)
            corrupt[5] ^= 1
            for content, message in [(b"OTHER", "Чужой формат"), (valid[:15], "Обрезанный архив"),
                                     (corrupt, "Повреждённый архив")]:
                source.write_bytes(content)
                result = self.command("decompress", source, "--output", output)
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

# END GENERATED CODE: OpenAI Codex.
