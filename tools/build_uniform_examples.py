"""Входы задачи 1.2 на варианте s=2 и отдельный контроль производительности."""

from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_examples import examples, write


def main():
    directory = ROOT / "examples/task_1_2"
    directory.mkdir(parents=True, exist_ok=True)
    iid = examples()["iid"]
    write(directory / "iid.json", iid)
    uniform = deepcopy(iid)
    uniform["switches"]["A"] = {"uniform": "1"}
    write(directory / "uniform.json", uniform)
    dyadic = deepcopy(iid)
    dyadic["switches"]["A"] = {"A_only": "1/2", "B_only": "1/4", "C_only": "1/4"}
    write(directory / "dyadic.json", dyadic)
    skewed = deepcopy(iid)
    skewed["switches"]["A"] = {"A_only": "99999/100000", "B_only": "1/200000", "C_only": "1/200000"}
    write(directory / "skewed.json", skewed)
    write(directory / "deterministic.json", examples()["deterministic"])
    hidden = deepcopy(examples()["nonergodic"])
    machine = hidden["state_machine"]
    for state in machine["states"].values():
        state["transitions"] = {a: machine["initial"] for a in "ABC"}
    write(directory / "iid_hidden.json", hidden)
    fixtures = ROOT / "tests/fixtures"
    fixtures.mkdir(exist_ok=True)
    write(fixtures / "uniform_k5.json", {
        "models": {"five_symbols": dict(zip("ABCDE", ["31/100", "27/100", "19/100", "14/100", "9/100"]))},
        "switches": {"only": {"five_symbols": "1"}}, "source": ["only"],
    })


if __name__ == "__main__":
    main()
