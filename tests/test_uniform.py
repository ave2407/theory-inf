"""Сравнение метода типов с полным перебором и проверки законов источников."""

from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import product
import json
from math import prod
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from theory_inf.distributions import InputError, fraction_text
from theory_inf.source import Source
from theory_inf.iid import iid_distribution
from theory_inf.information import code_length, entropy, log_ratio
from theory_inf.uniform import analyze_uniform, asymptotic, block_types, optimal_error
from tools.build_examples import examples

ROOT = Path(__file__).resolve().parents[1]


class UniformTests(unittest.TestCase):
    def test_entropy_hand_calculation(self):
        self.assertEqual(entropy({"A": F(1, 2), "B": F(1, 4), "C": F(1, 4)}), Decimal("1.5"))
        self.assertEqual(entropy({"A": F(1), "B": F(0)}), 0)

    def test_entropy_when_one_probability_is_close_to_one(self):
        rare = F(1, 10 ** 100)
        p = {"A": 1 - rare, "B": rare}
        with localcontext() as context:
            context.prec = 80
            self.assertEqual(entropy(p, 80), +entropy(p, 160))
        self.assertTrue(Decimal("3.336e-98") < entropy(p) < Decimal("3.337e-98"))

    def test_saved_code_reconstructs_optimal_small_codebooks(self):
        p = {"A": F(1, 2), "B": F(1, 4), "C": F(1, 4)}
        result, description = analyze_uniform(p, F(1), F(1, 100), 3, 4)
        alphabet = description["alphabet"]
        for row, spec in zip(result["table"], description["blocks"]):
            words = list(product(alphabet, repeat=spec["n"]))
            # Независимое восстановление по спецификации, без block_types.
            words.sort(key=lambda word: (-prod(p[a] for a in word),
                                        tuple(word.count(a) for a in alphabet), word))
            codebook = {}
            for rank, word in enumerate(words[:spec["selected_blocks"]]):
                digits = [0] * spec["length"]
                remaining = rank
                for i in range(len(digits) - 1, -1, -1):
                    remaining, digits[i] = divmod(remaining, description["q"])
                self.assertEqual(remaining, 0)
                self.assertNotIn(tuple(digits), codebook)
                codebook[tuple(digits)] = word
                decoded_rank = 0
                for digit in digits:
                    decoded_rank = decoded_rank * description["q"] + digit
                self.assertEqual(words[decoded_rank], word)
            covered = sum(prod(p[a] for a in word) for word in codebook.values())
            self.assertEqual(1 - covered, F(row["error"]["fraction"]))

    def test_iid_and_degenerate_inputs(self):
        data = examples()
        self.assertEqual(iid_distribution(Source.parse(data["iid"]))["A"], F(13, 24))
        self.assertEqual(iid_distribution(Source.parse(data["deterministic"]))["A"], 1)

    def test_rejects_periodic_and_dependent_laws(self):
        for name, message in [("periodic", "нестационарен"), ("markov", "имеет память"),
                              ("nonergodic", "имеет память")]:
            with self.subTest(name=name), self.assertRaisesRegex(InputError, message):
                iid_distribution(Source.parse(examples()[name]))

    def test_hidden_states_do_not_imply_memory(self):
        raw = deepcopy(examples()["nonergodic"])
        # После каждого символа режим выбирается заново из того же initial.
        machine = raw["state_machine"]
        for state in machine["states"].values():
            state["transitions"] = {a: machine["initial"] for a in "ABC"}
        self.assertEqual(iid_distribution(Source.parse(raw)),
                         {"A": F(17, 48), "B": F(5, 12), "C": F(11, 48)})

    def test_unreachable_states_are_irrelevant(self):
        raw = deepcopy(examples()["nonergodic"])
        raw["state_machine"]["initial"] = {"regime_A": "1"}
        self.assertEqual(iid_distribution(Source.parse(raw))["A"], F(13, 24))

    def test_equal_effective_distributions_with_different_switch_names(self):
        raw = deepcopy(examples()["periodic"])
        raw["switches"]["B"] = raw["switches"]["A"]
        raw["switches"]["C"] = raw["switches"]["A"]
        self.assertEqual(iid_distribution(Source.parse(raw))["A"], F(13, 24))

    def test_types_against_exhaustive_enumeration(self):
        distributions = [
            {"A": F(1, 2), "B": F(1, 4), "C": F(1, 4)},
            {"A": F(13, 24), "B": F(7, 24), "C": F(1, 6)},
            {"A": F(1, 3), "B": F(1, 3), "C": F(1, 3)},
            dict(zip("ABCDE", map(F, ["31/100", "27/100", "19/100", "14/100", "9/100"]))),
            {"A": F(0), "B": F(1)},
        ]
        for p in distributions:
            positive = [value for value in p.values() if value]
            for n in range(1, 6):
                ordered = sorted((prod(block) for block in product(positive, repeat=n)), reverse=True)
                for q in [2, 3, 5]:
                    for length in range(4):
                        with self.subTest(p=p, n=n, q=q, length=length):
                            error, selected = optimal_error(p, n, q, length)
                            self.assertEqual(selected, min(q ** length, len(ordered)))
                            self.assertEqual(error, 1 - sum(ordered[:q ** length]))

    def test_partial_type_and_zero_length(self):
        p = {"0": F(3, 4), "1": F(1, 4)}
        # Для n=3 выбираем 000 и только один из трёх блоков с одной единицей.
        self.assertEqual(optimal_error(p, 3, 2, 1), (F(7, 16), 2))
        self.assertEqual(optimal_error(p, 3, 5, 0), (F(37, 64), 1))

    def test_types_have_correct_total_cardinality(self):
        items = block_types((3, 2, 1), 5)
        self.assertEqual(len(items), 21)
        self.assertEqual(sum(size for _, _, size in items), 3 ** 5)
        self.assertEqual(sum(weight * size for weight, _, size in items), 6 ** 5)
        self.assertEqual(items, sorted(items, key=lambda item: (-item[0], item[1])))

    def test_lengths_and_rounding_boundaries(self):
        p = {"A": F(1, 2), "B": F(1, 4), "C": F(1, 4)}
        for n in range(1, 51):
            self.assertEqual(code_length(n, F(3, 2), p, 2), (3 * n) // 2)
            self.assertEqual(code_length(n, None, p, 4), (3 * n) // 4)
            self.assertEqual(code_length(n, F(0), p, 5), 0)
        self.assertEqual(code_length(1, F("2.32192809488736234787031942948939017586483139302458061205475"), p, 5), 0)
        self.assertEqual(code_length(1, F("2.32192809488736234787031942948939017586483139302458061205476"), p, 5), 1)

    def test_log_ratio(self):
        for m, q, answer in [(1, 5, F(0)), (4, 8, F(2, 3)), (9, 3, F(2)),
                             (3, 9, F(1, 2)), (12, 144, F(1, 2)), (3, 5, None), (6, 12, None)]:
            self.assertEqual(log_ratio(m, q), answer)

    def test_small_n_can_succeed_below_entropy(self):
        p = {"A": F(99, 100), "B": F(1, 100)}
        result, _ = analyze_uniform(p, F(0), F(1, 50), 5, 4)
        self.assertEqual(result["minimum_n"], 1)
        self.assertFalse(result["asymptotic"]["eventually_below_epsilon"])
        self.assertFalse(result["table"][-1]["meets_epsilon"])

    def test_entropy_rate_nonuniform_boundary(self):
        p = {"A": F(1, 2), "B": F(1, 4), "C": F(1, 4)}
        for rate in [None, F(3, 2)]:
            self.assertFalse(asymptotic(p, rate, F(1, 10000), 5)["eventually_below_epsilon"])
            self.assertTrue(asymptotic(p, rate, F(1, 2), 5)["eventually_below_epsilon"])

    def test_entropy_rate_uniform_boundary(self):
        p4 = {str(i): F(1, 4) for i in range(4)}
        self.assertTrue(asymptotic(p4, None, F(3, 4), 8)["eventually_below_epsilon"])
        self.assertFalse(asymptotic(p4, None, F(74, 100), 8)["eventually_below_epsilon"])
        for n in range(1, 20):
            self.assertEqual(code_length(n, None, p4, 8), 2 * n // 3)
        p3 = {str(i): F(1, 3) for i in range(3)}
        self.assertTrue(asymptotic(p3, None, F(4, 5), 5)["eventually_below_epsilon"])
        self.assertFalse(asymptotic(p3, None, F(79, 100), 5)["eventually_below_epsilon"])

    def test_zero_and_one_epsilon(self):
        p = {"A": F(1, 2), "B": F(1, 4), "C": F(1, 4)}
        self.assertFalse(asymptotic(p, F(3, 2), F(0), 2)["eventually_below_epsilon"])
        self.assertTrue(asymptotic(p, F(2), F(0), 5)["eventually_below_epsilon"])
        self.assertTrue(asymptotic(p, F(0), F(1), 5)["eventually_below_epsilon"])

    def test_variant_hand_calculation_and_description(self):
        p = iid_distribution(Source.parse(examples()["iid"]))
        result, code = analyze_uniform(p, F(2), F(1, 10000), 5, 4)
        self.assertEqual([r["error"]["fraction"] for r in result["table"]],
                         ["11/24", "121/576", "11/864", "0"])
        self.assertEqual(result["minimum_n"], 4)
        self.assertEqual(code["blocks"][3], {"n": 4, "length": 3, "selected_blocks": 81})
        self.assertEqual(code["format"], "uniform-types-v1")

    def test_invalid_parameters(self):
        p = {"A": F(1, 2), "B": F(1, 2)}
        for r, e, q, n in [(F(-1), F(1, 10), 5, 5), (F(1), F(2), 5, 5),
                            (F(1), F(-1), 5, 5), (F(1), F(1, 10), 1, 5), (F(1), F(1, 10), 5, 0)]:
            with self.assertRaises(InputError):
                analyze_uniform(p, r, e, q, n)


class UniformCliTests(unittest.TestCase):
    def command(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "main.py"), *map(str, args)],
                              cwd=ROOT, capture_output=True, text=True, timeout=20)

    def test_entropy(self):
        result = self.command("entropy", ROOT / "examples/task_1_1/iid.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["memoryless"])

    def test_exact_fraction_longer_than_python_integer_string_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.json"
            rare = F(1, 10 ** 100)
            source.write_text(json.dumps({
                "models": {"m": {"A": fraction_text(1 - rare), "B": fraction_text(rare)}},
                "switches": {"s": {"m": "1"}}, "source": ["s"],
            }))
            result = self.command("uniform", source, "--rate", "0", "--n-max", "44",
                                  "--code-output", Path(folder) / "code.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            exact = json.loads(result.stdout)["table"][-1]["error"]["fraction"]
            self.assertGreater(len(exact), 4300)
            self.assertEqual(exact, fraction_text(1 - (1 - rare) ** 44))

    def test_unserializable_integer_is_diagnostic(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "code.json"
            rate = "9" * 4300
            result = self.command("uniform", ROOT / "examples/task_1_2/dyadic.json", "--rate", rate,
                                  "--q", "2", "--n-max", "2", "--code-output", output)
            self.assertEqual(result.returncode, 2, result.stderr[-500:])
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_reproducible_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            code = Path(folder) / "code.json"
            output = Path(folder) / "result.json"
            args = ("uniform", ROOT / "examples/task_1_1/iid.json", "--rate", "2", "--n-max", "4",
                    "--code-output", code, "--output", output)
            first = self.command(*args)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = code.read_bytes(), output.read_bytes()
            second = self.command(*args)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(original, (code.read_bytes(), output.read_bytes()))
            self.assertEqual(json.loads(output.read_text())["minimum_n"], 4)

    def test_invalid_parameters_and_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            for extra in [("--q", "1"), ("--rate", "-1"), ("--epsilon", "2"),
                          ("--n-max", "0"), ("--rate", "NaN")]:
                result = self.command("uniform", ROOT / "examples/task_1_1/iid.json", "--rate", "2",
                                      "--code-output", Path(folder) / "code.json", *extra)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
            for name in ["periodic", "markov", "nonergodic"]:
                result = self.command("entropy", ROOT / f"examples/task_1_1/{name}.json")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
            for name in ["broken", "negative", "unknown_model", "empty_source"]:
                source = ROOT / f"examples/task_1_1/invalid/{name}.json"
                for mode in ["entropy", "uniform"]:
                    arguments = [] if mode == "entropy" else [
                        "--rate", "2", "--code-output", Path(folder) / "code.json"]
                    result = self.command(mode, source, *arguments)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_output_collision(self):
        with tempfile.TemporaryDirectory() as folder:
            source = ROOT / "examples/task_1_1/iid.json"
            original = source.read_bytes()
            result = self.command("uniform", source, "--rate", "2", "--code-output", source)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_bytes(), original)
            output = Path(folder) / "same.json"
            result = self.command("uniform", source, "--rate", "2", "--code-output", output, "--output", output)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
