# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Контрольные вероятности не вычисляются повторением алгоритма реализации."""

from copy import deepcopy
from fractions import Fraction as F
from itertools import islice, product
import unittest

from theory_inf.distributions import Distribution, InputError
from theory_inf.experiment import frequencies
from theory_inf.source import Source
from theory_inf.variant import VARIANT, Variant
from tools.build_examples import examples


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.inputs = examples()

    def load(self, name):
        return Source.parse(self.inputs[name])

    def test_variant(self):
        self.assertEqual(VARIANT.as_dict(), {
            "s": 2, "k": 3, "M": 4, "L": 5, "d": 3, "q": 5, "epsilon": "1/10000",
        })
        for s in range(1, 16):
            v = Variant.from_student(s)
            self.assertEqual(v.q, (2, 3, 5, 7)[s % 4])
            self.assertEqual(v.epsilon, F(1, 10 ** (2 + s % 3)))

    def test_examples_match_variant(self):
        for name in self.inputs:
            with self.subTest(name=name):
                source = self.load(name)
                self.assertEqual(len(source.alphabet), VARIANT.k)
                self.assertEqual(len(source.models), VARIANT.models)
                self.assertEqual(source.period, VARIANT.period)

    def test_iid_hand_calculation(self):
        self.assertEqual(self.load("iid").exact_probabilities(["A", "B"]), (F(91, 576), F(91, 576)))

    def test_periodic_hand_calculation(self):
        # AB: 13*13, 4*4, 7*7, 13*13, 4*7; знаменатель 24².
        self.assertEqual(self.load("periodic").exact_probabilities(["A", "B"]), (F(169, 576), F(431, 2880)))

    def test_nonergodic_joint_is_not_product_of_marginals(self):
        source = self.load("nonergodic")
        self.assertEqual(source.block_probability(["A"]), F(17, 48))
        self.assertEqual(source.block_probability(["A", "A"]), F(185, 1152))
        self.assertNotEqual(source.block_probability(["A", "A"]), F(17, 48) ** 2)
        self.assertEqual(source.exact_probabilities(["A", "A"]), (F(185, 1152), F(185, 1152)))

    def test_markov_memory_is_exactly_three(self):
        source = self.load("markov")
        # Uniform initial history; first three emissions have iid uniform law.
        self.assertEqual(source.block_probability(["A", "B", "C"]), F(1, 27))
        # The fourth symbol depends on the first: P(A|AAA)=13/24.
        p_aaa = source.block_probability(["A"] * 3)
        self.assertEqual(source.block_probability(["A"] * 4) / p_aaa, F(13, 24))
        p_baa = source.block_probability(["B", "A", "A"])
        self.assertEqual(source.block_probability(["B", "A", "A", "A"]) / p_baa, F(1, 6))

    def test_markov_stationary_state_distribution(self):
        source = self.load("markov")
        masses = source.initial.probabilities
        for phase in range(source.period):
            self.assertEqual(source.advance(masses, phase), masses)

    def test_block_law_normalized(self):
        for name in self.inputs:
            source = self.load(name)
            for offset in [0, 2, 5]:
                with self.subTest(name=name, offset=offset):
                    total = sum(source.block_probability(word, offset)
                                for word in product(source.alphabet, repeat=2))
                    self.assertEqual(total, 1)

    def test_state_distribution_is_advanced_before_offset_block(self):
        raw = deepcopy(self.inputs["deterministic"])
        raw["switches"]["always_B"] = {"B_only": "1"}
        raw["state_machine"] = {
            "initial": {"start": "1"},
            "states": {
                "start": {"transitions": {a: {"end": "1"} for a in "ABC"}},
                "end": {"source": ["always_B"] * 5,
                        "transitions": {a: {"end": "1"} for a in "ABC"}},
            },
        }
        source = Source.parse(raw)
        self.assertEqual(source.exact_probabilities(["B"]), (F(0), F(4, 5)))

    def test_original_assignment_example(self):
        raw = {"models": {"m1": {"0": "1/3", "1": "2/3"},
                          "m2": {"0": "2/3", "1": "1/3"}},
               "switches": {"s1": {"m1": "1/2", "m2": "1/2"},
                            "s2": {"m1": "0.3", "m2": "0.7"},
                            "s3": {"m1": "0.4", "m2": "0.6"}},
               "source": ["s1", "s2", "s3", "s2"]}
        source = Source.parse(raw)
        self.assertEqual(source.block_probability(["0", "1"]), F(13, 60))
        self.assertEqual(source.block_probability(["0"], 5), F(17, 30))

    def test_rational_draw_uses_integer_tickets(self):
        class Tickets:
            def __init__(self, ticket):
                self.ticket = ticket

            def randrange(self, total):
                self.total = total
                return self.ticket
        dist = Distribution.parse({"A": "1/3", "B": "2/3", "C": "0"}, "test")
        self.assertEqual([dist.draw(Tickets(i)) for i in range(3)], ["A", "B", "B"])
        self.assertEqual(Distribution.parse({"A": "0.1", "B": "0.9"}, "test").probabilities["A"], F(1, 10))

    def test_same_seed_and_json_key_order(self):
        for name in self.inputs:
            source = self.load(name)
            raw = self.inputs[name]
            reordered = Source.parse(dict(reversed(list(raw.items()))))
            first = list(islice(source.generate(17), 200))
            self.assertEqual(first, list(islice(source.generate(17), 200)))
            self.assertEqual(first, list(islice(reordered.generate(17), 200)))

    def test_unknown_symbol_has_zero_probability(self):
        self.assertEqual(self.load("iid").block_probability(["not in alphabet"]), 0)

    def test_overlapping_matches(self):
        self.assertEqual(frequencies(iter("AAAAA"), "AAA", [2, 3, 5]), {2: None, 3: F(1), 5: F(1)})
        self.assertEqual(frequencies(iter("ABABABA"), "ABA", [7]), {7: F(3, 5)})

    def test_long_word_and_incomplete_stream(self):
        with self.assertRaises(InputError):
            frequencies(iter("A"), "AA", [2])
        with self.assertRaises(InputError):
            frequencies(iter("A"), [], [1])

    def test_invalid_distributions(self):
        for raw in [{}, [], {"A": 1}, {"A": "1/0"}, {"A": "NaN"},
                    {"A": "-1", "B": "2"}, {"A": "0.9"}, {"A": "0"}]:
            with self.subTest(raw=raw), self.assertRaises(InputError):
                Distribution.parse(raw, "test")

    def test_invalid_sources(self):
        mutations = [
            lambda d: d.update(source=[]),
            lambda d: d.update(source=["missing"]),
            lambda d: d["switches"].update(A={"missing": "1"}),
            lambda d: d.update(soruce=["A"]),
            lambda d: d.update(models=[]),
        ]
        for mutate in mutations:
            raw = deepcopy(self.inputs["iid"])
            mutate(raw)
            with self.assertRaises(InputError):
                Source.parse(raw)

    def test_invalid_state_machines(self):
        for change in ["missing_state", "wrong_length", "missing_symbol", "bad_transition"]:
            raw = deepcopy(self.inputs["nonergodic"])
            machine = raw["state_machine"]
            state = machine["states"]["regime_A"]
            if change == "missing_state":
                machine["initial"] = {"missing": "1"}
            elif change == "wrong_length":
                state["source"] = ["A"]
            elif change == "missing_symbol":
                del state["transitions"]["C"]
            else:
                state["transitions"]["A"] = {"missing": "1"}
            with self.subTest(change=change), self.assertRaises(InputError):
                Source.parse(raw)


if __name__ == "__main__":
    unittest.main()

# END GENERATED CODE: OpenAI Codex.
