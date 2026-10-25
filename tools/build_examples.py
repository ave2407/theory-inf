"""Воспроизводимо подготовить собственные входы задачи 1.1, s=2."""

from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from theory_inf.variant import VARIANT


def examples() -> dict[str, dict]:
    """Вернуть пять описаний источников s=2: iid, периодический, марковский,
    стационарный неэргодический и детерминированный. Файлы здесь не записываются.
    """
    if VARIANT.s != 2:
        raise ValueError("Примеры построены для s=2; при смене варианта их нужно пересмотреть")
    symbols = ("A", "B", "C")
    models = {
        "A_only": {"A": "1", "B": "0", "C": "0"},
        "B_only": {"A": "0", "B": "1", "C": "0"},
        "C_only": {"A": "0", "B": "0", "C": "1"},
        "uniform": {a: "1/3" for a in symbols},
    }
    switches = {}
    for i, symbol in enumerate(symbols):
        switches[symbol] = {
            f"{symbols[i]}_only": "1/2",
            f"{symbols[(i + 1) % 3]}_only": "1/4",
            f"{symbols[(i + 2) % 3]}_only": "1/8",
            "uniform": "1/8",
        }
    iid = {"models": models, "switches": switches, "source": ["A"] * VARIANT.period}
    periodic = deepcopy(iid)
    periodic["source"] = ["A", "B", "C", "A", "B"]
    markov = deepcopy(iid)
    states = {}
    histories = ["".join(parts) for parts in product(symbols, repeat=VARIANT.depth)]
    for context in histories:
        states[context] = {
            "source": [context[0]] * VARIANT.period,
            "transitions": {a: {context[1:] + a: "1"} for a in symbols},
        }
    markov["state_machine"] = {
        "initial": {context: f"1/{len(histories)}" for context in histories},
        "states": states,
    }
    mixture = deepcopy(iid)
    mixture["state_machine"] = {
        "initial": {"regime_A": "1/2", "regime_B": "1/2"},
        "states": {
            name: {
                "source": [switch] * VARIANT.period,
                "transitions": {a: {name: "1"} for a in symbols},
            }
            for name, switch in [("regime_A", "A"), ("regime_B", "B")]
        },
    }
    deterministic = deepcopy(iid)
    deterministic["switches"] = {"always_A": {"A_only": "1"}}
    deterministic["source"] = ["always_A"] * VARIANT.period
    return {"iid": iid, "periodic": periodic, "markov": markov,
            "nonergodic": mixture, "deterministic": deterministic}


def write(path: Path, value: object) -> None:
    """Перезаписать UTF-8 JSON-файл с одинаковым форматированием всех примеров."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    folder = ROOT / "examples" / "task_1_1"
    folder.mkdir(parents=True, exist_ok=True)
    data = examples()
    for name, value in data.items():
        write(folder / f"{name}.json", value)
    write(folder / "word.json", ["A", "B"])
    invalid = folder / "invalid"
    invalid.mkdir(exist_ok=True)
    for name in ["negative", "unnormalized", "unknown_model", "unknown_switch", "empty_source"]:
        value = deepcopy(data["iid"])
        if name == "negative":
            value["models"]["A_only"] = {"A": "-1", "B": "2"}
        elif name == "unnormalized":
            value["models"]["A_only"] = {"A": "0.9"}
        elif name == "unknown_model":
            value["switches"]["A"] = {"missing": "1"}
        elif name == "unknown_switch":
            value["source"][0] = "missing"
        else:
            value["source"] = []
        write(invalid / f"{name}.json", value)
    (invalid / "broken.json").write_text('{"models":', encoding="utf-8")
