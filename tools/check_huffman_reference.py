"""Сравнить адаптацию с оригинальным huffmancoding.py Nayuki, полученным отдельно."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from theory_inf.huffman import canonical_codes, code_lengths


def main():
    """Загрузить переданный исходник Nayuki и сверить длины и слова на 52 наборах частот.

    Пустая модель и один символ исключены из сравнения как намеренные отличия.
    SHA-256 исходника и итог записываются в reference_validation.json.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--seed", type=int, default=2)
    args = parser.parse_args()
    specification = importlib.util.spec_from_file_location("reference_huffman", args.reference)
    reference = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(reference)
    rng = random.Random(args.seed)
    cases = [[1] * 256, [4, 2, 1] + [0] * 253]
    cases.extend([[rng.randrange(100) for _ in range(256)] for _ in range(50)])
    for frequencies in cases:
        tree = reference.FrequencyTable(frequencies).build_code_tree()
        canonical = reference.CanonicalCode(tree=tree, symbollimit=256)
        lengths = {a: n for a, n in enumerate(canonical.codelengths) if n}
        if lengths != code_lengths(frequencies):
            raise AssertionError("Длины отличаются от исходной реализации")
        upstream_tree = canonical.to_code_tree()
        for symbol, (code, length) in canonical_codes(lengths).items():
            original = upstream_tree.get_code(symbol)
            if len(original) != length or int("".join(map(str, original)), 2) != code:
                raise AssertionError("Канонические слова отличаются от исходной реализации")
    output = {
        "reference_url": "https://github.com/nayuki/Reference-Huffman-coding/blob/master/python/huffmancoding.py",
        "reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
        "seed": args.seed, "cases": len(cases), "all_equal": True,
        "scope": "Длины и канонические слова при минимум двух символах; вырожденные случаи изменены намеренно",
    }
    target = ROOT / "results/task_1_3/reference_validation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
