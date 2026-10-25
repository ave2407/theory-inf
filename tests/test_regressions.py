# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Регрессии из проверки: независимые эталоны источников, кодов и ZMH1."""

from copy import deepcopy
from fractions import Fraction as F
from itertools import islice, product
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from theory_inf.archive import compress, decompress
from theory_inf.distributions import InputError
from theory_inf.experiment import frequencies
from theory_inf.huffman import code_lengths
from theory_inf.iid import iid_distribution
from theory_inf.information import code_length, entropy
from theory_inf.source import Source
from theory_inf.uniform import analyze_uniform, asymptotic, optimal_error


def iid_input(weights):
    total = sum(weights)
    return {"models": {"own": {chr(65 + i): str(F(w, total))
                               for i, w in enumerate(weights)}},
            "switches": {"choose": {"own": "1"}}, "source": ["choose"]}


def command(*args, timeout=20):
    return subprocess.run([sys.executable, str(ROOT / "main.py"), *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def raw_word_law(raw, count):
    """Enumerate joint (state, output-prefix) paths using raw JSON weights."""
    machine = raw.get("state_machine")
    states = machine["states"] if machine else {"_": {}}
    initial = machine["initial"] if machine else {"_": "1"}
    paths = {(state, ()): F(weight) for state, weight in initial.items()}
    for position in range(count):
        following = {}
        for (state, prefix), mass in paths.items():
            info = states[state]
            period = info.get("source", raw["source"])
            switch = raw["switches"][period[position % len(period)]]
            for model, model_weight in switch.items():
                for symbol, symbol_weight in raw["models"][model].items():
                    transitions = info.get("transitions", {}).get(symbol, {state: "1"})
                    for target, transition_weight in transitions.items():
                        key = target, (*prefix, symbol)
                        weight = mass * F(model_weight) * F(symbol_weight) * F(transition_weight)
                        following[key] = following.get(key, F(0)) + weight
        paths = following
    law = {}
    for (_, word), mass in paths.items():
        law[word] = law.get(word, F(0)) + mass
    return law


def memory_input(depth):
    raw = {"models": {"biased0": {"0": "3/4", "1": "1/4"},
                      "biased1": {"0": "1/4", "1": "3/4"}},
           "switches": {"s0": {"biased0": "1"}, "s1": {"biased1": "1"}},
           "source": ["s0"]}
    names = ["".join(word) for word in product("01", repeat=depth)]
    raw["state_machine"] = {
        "initial": {name: str(F(1, len(names))) for name in names},
        "states": {name: {"source": ["s" + name[0]],
                          "transitions": {a: {name[1:] + a: "1"} for a in "01"}}
                   for name in names}}
    return raw


def make_archive(message, lengths):
    """Build ZMH from the documented format without project encoder helpers."""
    words = {}
    next_code = previous_length = 0
    for symbol, length in sorted(lengths.items(), key=lambda pair: (pair[1], pair[0])):
        next_code *= 2 ** (length - previous_length)
        words[symbol] = format(next_code, f"0{length}b") if length else ""
        next_code += 1
        previous_length = length
    bitstring = "".join(words[a] for a in message)
    padded = bitstring + "0" * (-len(bitstring) % 8)
    payload = bytes(int(padded[i:i + 8], 2) for i in range(0, len(padded), 8))
    meta = struct.pack(">4sQQHI", b"ZMH1", len(message), len(bitstring), len(lengths), zlib.crc32(message))
    model = bytes(value for pair in sorted(lengths.items()) for value in pair)
    return meta + struct.pack(">I", zlib.crc32(meta)) + model + payload


def decode_independently(blob):
    """Read canonical words as strings, independent of the project bit/tree code."""
    magic, size, bits, count, checksum = struct.unpack(">4sQQHI", blob[:26])
    assert magic == b"ZMH1"
    assert zlib.crc32(blob[:26]) == struct.unpack(">I", blob[26:30])[0]
    lengths = dict(zip(blob[30:30 + 2 * count:2], blob[31:30 + 2 * count:2]))
    assert len(blob) == 30 + 2 * count + (bits + 7) // 8
    if count == 0:
        result = b""
    elif count == 1:
        assert next(iter(lengths.values())) == 0 and bits == 0
        result = bytes(lengths) * size
    else:
        words = {}
        number = previous = 0
        for symbol, length in sorted(lengths.items(), key=lambda pair: (pair[1], pair[0])):
            number *= 2 ** (length - previous)
            words[format(number, f"0{length}b")] = symbol
            number += 1
            previous = length
        encoded = "".join(format(byte, "08b") for byte in blob[30 + 2 * count:])
        assert set(encoded[bits:]) <= {"0"}
        result = bytearray()
        prefix = ""
        for bit in encoded[:bits]:
            prefix += bit
            if prefix in words:
                result.append(words[prefix])
                prefix = ""
        assert not prefix
        result = bytes(result)
    assert len(result) == size and zlib.crc32(result) == checksum
    return result


class SourceRegressionTests(unittest.TestCase):
    def test_periodic_joint_law_from_raw_paths(self):
        raw = {"models": {"left": {"xy": "2/7", "я": "5/7"},
                          "right": {"xy": "4/5", "я": "1/5"}},
               "switches": {"mix": {"left": "1/3", "right": "2/3"},
                            "plain": {"left": "1"}},
               "source": ["mix", "plain", "plain"]}
        source = Source.parse(raw)
        for offset in range(4):
            for length in range(1, 4):
                law = raw_word_law(raw, offset + length)
                for word in product(("xy", "я"), repeat=length):
                    expected = sum(mass for whole, mass in law.items() if whole[offset:] == word)
                    self.assertEqual(source.block_probability(word, offset), expected)

    def test_stochastic_state_and_phase_joint_law(self):
        raw = {"models": {"a": {"0": "2/3", "1": "1/3"},
                          "b": {"0": "1/5", "1": "4/5"}},
               "switches": {"u": {"a": "1"}, "v": {"a": "1/4", "b": "3/4"}},
               "source": ["u", "v"],
               "state_machine": {"initial": {"cold": "2/7", "hot": "5/7"}, "states": {
                   "cold": {"transitions": {"0": {"cold": "1/3", "hot": "2/3"},
                                             "1": {"hot": "1"}}},
                   "hot": {"source": ["v", "u"], "transitions": {
                       "0": {"cold": "1"}, "1": {"cold": "3/8", "hot": "5/8"}}}}}}
        source = Source.parse(raw)
        for offset in range(3):
            for length in range(1, 4):
                law = raw_word_law(raw, offset + length)
                for word in product("01", repeat=length):
                    expected = sum(mass for whole, mass in law.items() if whole[offset:] == word)
                    self.assertEqual(source.block_probability(word, offset), expected)

    def test_memory_visible_only_after_four_symbols(self):
        source = Source.parse(memory_input(4))
        for word in product("01", repeat=4):
            self.assertEqual(source.block_probability(word), F(1, 16))
        self.assertEqual(source.block_probability("00000"), F(3, 64))
        with self.assertRaisesRegex(InputError, "память"):
            iid_distribution(source)

    def test_iid_even_with_output_dependent_hidden_transitions(self):
        raw = memory_input(2)
        raw["models"]["biased1"] = deepcopy(raw["models"]["biased0"])
        raw["state_machine"]["initial"] = {"00": "1"}
        self.assertEqual(iid_distribution(Source.parse(raw)), {"0": F(3, 4), "1": F(1, 4)})

    def test_multicharacter_symbol_overlaps(self):
        stream = ["ab", "я", "ab", "я", "ab", "я", "ab"]
        self.assertEqual(frequencies(stream, ["ab", "я", "ab"], [2, 3, 6, 7]),
                         {2: None, 3: F(1), 6: F(1, 2), 7: F(3, 5)})

    def test_long_block_exact_without_recursion(self):
        source = Source.parse(iid_input([2, 3]))
        self.assertEqual(source.block_probability(["A"] * 1200), F(2, 5) ** 1200)

    def test_seed_and_json_key_order(self):
        raw = memory_input(3)
        reordered = json.loads(json.dumps(raw, sort_keys=True))
        left = list(islice(Source.parse(raw).generate(637), 1200))
        right = list(islice(Source.parse(reordered).generate(637), 1200))
        self.assertEqual(left, right)
        self.assertNotEqual(left, list(islice(Source.parse(raw).generate(638), 1200)))

    def test_invalid_probabilities_and_references(self):
        malformed = []
        for value in ["-1/7", "1/0", "NaN", "0.9", 1, None, {}]:
            raw = iid_input([1])
            raw["models"]["own"]["A"] = value
            malformed.append(raw)
        raw = iid_input([1, 1]); raw["switches"]["choose"] = {"missing": "1"}; malformed.append(raw)
        raw = iid_input([1, 1]); raw["source"] = []; malformed.append(raw)
        for raw in malformed:
            with self.subTest(raw=raw), self.assertRaises(InputError):
                Source.parse(raw)


class UniformRegressionTests(unittest.TestCase):
    def test_random_optima_against_full_enumeration(self):
        rng = random.Random(84631)
        for _ in range(12):
            weights = [rng.randrange(1, 15) for _ in range(rng.randrange(2, 6))]
            total = sum(weights)
            p = {str(i): F(w, total) for i, w in enumerate(weights)}
            for n in range(1, 5):
                probabilities = sorted((math.prod(word) for word in product(p.values(), repeat=n)), reverse=True)
                for q in (2, 3, 7):
                    for length in range(3):
                        error, selected = optimal_error(p, n, q, length)
                        count = min(len(probabilities), q ** length)
                        self.assertEqual((error, selected), (1 - sum(probabilities[:count]), count))

    def test_code_lengths_via_integer_inequalities(self):
        p = {"A": F(2, 5), "B": F(3, 5)}
        for q in (2, 3, 5, 7):
            for rate in map(F, ("0", "1/3", "1", "13/10", "5/2")):
                for n in range(1, 51):
                    limit = 2 ** (n * rate.numerator)
                    expected = 0
                    while q ** ((expected + 1) * rate.denominator) <= limit:
                        expected += 1
                    self.assertEqual(code_length(n, rate, p, q), expected)

    def test_saved_code_has_unique_words_and_exact_error(self):
        p = {"A": F(3, 5), "B": F(3, 10), "C": F(1, 10)}
        report, code = analyze_uniform(p, F(4, 3), F(1, 10000), 3, 5)
        for row, spec in zip(report["table"], code["blocks"]):
            words = list(product(code["alphabet"], repeat=row["n"]))
            words.sort(key=lambda word: (-math.prod(p[a] for a in word),
                                         tuple(word.count(a) for a in code["alphabet"]), word))
            selected = words[:spec["selected_blocks"]]
            self.assertLessEqual(len(selected), code["q"] ** spec["length"])
            self.assertEqual(F(row["error"]["fraction"]), 1 - sum(math.prod(p[a] for a in w) for w in selected))

    def test_entropy_against_independent_logarithms(self):
        for weights in ([7, 5, 2], [1, 1, 1, 1, 1], [19, 1], [0, 3, 2]):
            p = {str(i): F(w, sum(weights)) for i, w in enumerate(weights)}
            expected = -sum(float(x) * math.log2(float(x)) for x in p.values() if x)
            self.assertAlmostEqual(float(entropy(p)), expected, places=12)

    def test_nonuniform_ternary_entropy_exact_rounding(self):
        # H=(4/3)log2(3), so n=3,q=3 gives EXACTLY four ternary digits.
        p = dict(zip("ABCDE", map(F, ("1/3", "1/3", "1/9", "1/9", "1/9"))))
        self.assertEqual(code_length(3, None, p, 3), 4)

    def test_cli_nonuniform_ternary_entropy(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "ternary.json"
            source.write_text(json.dumps(iid_input([3, 3, 1, 1, 1])))
            result = command("uniform", source, "--rate", "H", "--q", "3", "--n-max", "3",
                             "--code-output", Path(folder) / "code.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["table"][2]["length"], 4)

    def test_zero_rate_with_very_small_positive_entropy(self):
        rare = F(1, 10 ** 400)
        p = {"A": 1 - rare, "B": rare}
        report, _ = analyze_uniform(p, F(0), F(1, 10000), 5, 2)
        self.assertEqual(report["minimum_n"], 1)
        self.assertEqual(F(report["table"][0]["error"]["fraction"]), rare)
        self.assertFalse(report["asymptotic"]["eventually_below_epsilon"])

    def test_zero_error_requires_full_support_capacity(self):
        p = {"A": F(4, 5), "B": F(1, 5)}
        self.assertFalse(asymptotic(p, F(1), F(0), 3)["eventually_below_epsilon"])
        self.assertTrue(asymptotic(p, F(1), F(0), 2)["eventually_below_epsilon"])

    def test_full_cli_performance_five_symbols_fifty_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "five.json"
            source.write_text(json.dumps(iid_input([17, 9, 7, 5, 2])))
            start = time.perf_counter()
            result = command("uniform", source, "--rate", "13/10", "--q", "5", "--n-max", "50",
                             "--code-output", Path(folder) / "code.json", timeout=15)
            elapsed = time.perf_counter() - start
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)["table"]), 50)
            self.assertLessEqual(elapsed, 10)


class ArchiveRegressionTests(unittest.TestCase):
    def test_range_decoder_accepts_255_bit_codewords(self):
        # Полное «гребенчатое» дерево: по листу на уровнях 1..254 и два на 255.
        lengths = {a: min(a + 1, 255) for a in range(256)}
        message = bytes(range(256))
        with tempfile.TemporaryDirectory() as folder:
            packed = Path(folder) / "deep.zmh"
            packed.write_bytes(make_archive(message, lengths))
            output = Path(folder) / "restored.bin"
            decompress(packed, output)
            self.assertEqual(output.read_bytes(), message)

    def test_accepts_independently_built_container(self):
        message = b"ABACABCCABBA"
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "external.zmh"
            archive.write_bytes(make_archive(message, {65: 1, 66: 2, 67: 2}))
            restored = Path(folder) / "restored.bin"
            result = decompress(archive, restored)
            self.assertTrue(result["verified"])
            self.assertEqual(restored.read_bytes(), message)

    def test_compressor_output_decodes_independently(self):
        rng = random.Random(99401)
        messages = [b"", b"\xff", b"\x00" * 555, bytes(range(256)),
                    "е\u0308🙂\r\n\x00".encode() * 91]
        messages += [rng.randbytes(n) for n in (3, 31, 257, 4097, 65537)]
        with tempfile.TemporaryDirectory() as folder:
            for i, message in enumerate(messages):
                source = Path(folder) / f"input{i}.bin"; source.write_bytes(message)
                archive = Path(folder) / f"input{i}.zmh"
                stats = compress(source, archive)
                self.assertEqual(decode_independently(archive.read_bytes()), message)
                self.assertEqual(stats["archive_bytes"], archive.stat().st_size)
                self.assertEqual(stats["header_bytes"], 30 + 2 * len(set(message)))

    def test_huffman_optimal_cost_by_exhaustive_kraft_lengths(self):
        # Exhaust all complete binary prefix-code length vectors, m<=5.
        for weights in ([9, 3], [11, 4, 2], [17, 7, 5, 1], [13, 8, 5, 3, 2]):
            m = len(weights)
            best = min(sum(w * length for w, length in zip(weights, lengths))
                       for lengths in product(range(1, m), repeat=m)
                       if sum(F(1, 2 ** length) for length in lengths) == 1)
            actual = code_lengths(list(weights) + [0] * (256 - m))
            self.assertEqual(sum(weights[a] * length for a, length in actual.items()), best)

    def test_empty_and_single_symbol_external_containers(self):
        with tempfile.TemporaryDirectory() as folder:
            for i, message in enumerate((b"", b"q", b"q" * 1003)):
                archive = Path(folder) / f"external{i}.zmh"
                archive.write_bytes(make_archive(message, {113: 0} if message else {}))
                output = Path(folder) / f"out{i}"
                decompress(archive, output)
                self.assertEqual(output.read_bytes(), message)

    def test_padding_and_checksum_corruption_leave_no_file(self):
        valid = make_archive(b"ABACABA", {65: 1, 66: 2, 67: 2})
        cases = []
        padding = bytearray(valid); padding[-1] |= 1; cases.append(padding)
        payload = bytearray(valid); payload[-1] ^= 128; cases.append(payload)
        model = bytearray(valid); model[30] = model[32]; cases.append(model)
        cases.extend((valid + b"\x00", valid[:-1], valid[:33], b"not ZMH"))
        with tempfile.TemporaryDirectory() as folder:
            for i, blob in enumerate(cases):
                source = Path(folder) / f"bad{i}.zmh"; source.write_bytes(blob)
                output = Path(folder) / f"out{i}"
                with self.subTest(i=i), self.assertRaises(InputError):
                    decompress(source, output)
                self.assertFalse(output.exists())
            self.assertEqual(len(list(Path(folder).iterdir())), len(cases))

    def test_random_container_mutations_are_diagnostic(self):
        original = make_archive(b"ABACABA" * 11, {65: 1, 66: 2, 67: 2})
        rng = random.Random(739)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "mutated.zmh"
            for i in range(40):
                data = bytearray(original)
                index = rng.randrange(len(data)); data[index] ^= 1 << rng.randrange(8)
                source.write_bytes(data)
                output = Path(folder) / f"out{i}"
                with self.subTest(i=i), self.assertRaises(InputError):
                    decompress(source, output)
                self.assertFalse(output.exists())

    def test_existing_and_dangling_symlink_outputs_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.bin"; source.write_bytes(b"ABBA")
            output = Path(folder) / "output.zmh"; output.write_bytes(b"keep me")
            with self.assertRaises(InputError):
                compress(source, output)
            self.assertEqual(output.read_bytes(), b"keep me")
            output.unlink(); output.symlink_to(Path(folder) / "absent")
            with self.assertRaises(InputError):
                compress(source, output)
            self.assertTrue(output.is_symlink())
            self.assertFalse((Path(folder) / "absent").exists())

    def test_compression_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.bin"; source.write_bytes(bytes(range(253)) * 17)
            a, b = Path(folder) / "a.zmh", Path(folder) / "b.zmh"
            compress(source, a); compress(source, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())


class CliRegressionTests(unittest.TestCase):
    def test_analysis_cli_table_for_independent_periodic_input(self):
        raw = {"models": {"a": {"A": "1"}, "b": {"B": "1"}},
               "switches": {"a": {"a": "1"}, "b": {"b": "1"}},
               "source": ["a", "b", "a"]}
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "periodic.json"; source.write_text(json.dumps(raw))
            result = command("analyze", source, "--n", "101", "--word", "A", "A", "--seed", "73")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(F(data["exact_first"]["fraction"]), 0)
            self.assertEqual(F(data["exact_period_average"]["fraction"]), F(1, 3))
            self.assertEqual(F(data["frequency"]["fraction"]), F(33, 100))
            self.assertEqual([row["N"] for row in data["table"]], [100, 1000, 10000, 100000, 1000000])
            for row in data["table"]:
                n = row["N"]
                expected = F((n - 1) // 3, n - 1)
                self.assertEqual(F(row["frequency"]["fraction"]), expected)
                self.assertEqual(F(row["error_period_average"]["fraction"]), abs(expected - F(1, 3)))

    def test_archive_symlink_loop_is_diagnostic_not_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.bin"; source.write_bytes(b"ABBA")
            loop = Path(folder) / "loop"; loop.symlink_to(loop.name)
            result = command("compress", source, "--output", loop)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_symlink_loop_is_diagnostic_not_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.json"; source.write_text(json.dumps(iid_input([3, 2])))
            loop = Path(folder) / "loop"; loop.symlink_to(loop.name)
            result = command("generate", source, "--n", "1", "--output", loop)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_malformed_json_diagnostics(self):
        cases = ['{"models":', '{"models":{},"models":{}}', '[]', 'null',
                 '{"models":{"m":{"a":1}},"switches":{"s":{"m":"1"}},"source":["s"]}']
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.json"
            for payload in cases:
                source.write_text(payload)
                result = command("entropy", source)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)

    def test_hardlink_input_output_collision_preserves_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.json"; source.write_text(json.dumps(iid_input([3, 2])))
            output = Path(folder) / "alias.json"; output.hardlink_to(source)
            original = source.read_bytes()
            result = command("uniform", source, "--rate", "1", "--code-output", output)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_bytes(), original)

    def test_variant_matches_assignment_formulas(self):
        result = command("--variant")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         {"s": 2, "k": 3, "M": 4, "L": 5, "d": 3, "q": 5, "epsilon": "1/10000"})



if __name__ == "__main__":
    unittest.main()

# END GENERATED CODE: OpenAI Codex.
