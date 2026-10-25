# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Периодический источник и его расширение конечным состоянием."""

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
import random
from collections.abc import Iterator, Sequence

from theory_inf.distributions import (
    Distribution, InputError, fields, object_map, references,
)


def read_json(path: str | Path) -> object:
    """Прочитать JSON, отвергая повторные ключи и поясняя ошибки синтаксиса."""
    def unique_keys(pairs: list[tuple[str, object]]) -> dict:
        """Собрать объект до потери повторных ключей стандартным JSON-декодером."""
        result = {}
        for key, value in pairs:
            if key in result:
                raise InputError(f"JSON: повторяющийся ключ {key!r}")
            result[key] = value
        return result

    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream, object_pairs_hook=unique_keys)
    except json.JSONDecodeError as exc:
        raise InputError(f"JSON: строка {exc.lineno}, столбец {exc.colno}: {exc.msg}") from exc
    except (RecursionError, ValueError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError("JSON: превышена допустимая глубина или длина числа") from exc


def schedule(value: object, switches: set[str], location: str) -> tuple[str, ...]:
    """Проверить непустой период из объявленных переключателей и вернуть кортеж."""
    if not isinstance(value, list) or not value:
        raise InputError(f"{location}: ожидается непустой список переключателей")
    if any(not isinstance(name, str) or name not in switches for name in value):
        raise InputError(f"{location}: неизвестный переключатель")
    return tuple(value)


@dataclass(frozen=True)
class Source:
    """Описание источника, общее для генерации и точного расчёта вероятностей.

    models: модель → распределение символов; switches: переключатель →
    распределение моделей; schedules: состояние → период переключателей.
    initial задаёт начальное состояние, transitions[состояние][символ] —
    распределение следующего состояния. emissions содержит уже смешанные
    вероятности символов для каждого переключателя. alphabet — общий алфавит,
    period — длина периода. Старый формат представлен одним состоянием default.
    """
    models: dict[str, Distribution]
    switches: dict[str, Distribution]
    schedules: dict[str, tuple[str, ...]]
    initial: Distribution
    transitions: dict[str, dict[str, Distribution]]
    emissions: dict[str, dict[str, Fraction]]
    alphabet: tuple[str, ...]
    period: int

    @classmethod
    def parse(cls, value: object) -> "Source":
        """Проверить описание и ссылки, построить состояния и эффективные распределения.

        Без state_machine добавляется одно постоянное состояние. Для каждого
        переключателя заранее считается P(a)=Σ_m P(m)·P(a|m).
        """
        data = object_map(value, "источник")
        fields(data, {"models", "switches", "source"}, {"state_machine"}, "источник")
        models = {
            name: Distribution.parse(item, f"models.{name}")
            for name, item in sorted(object_map(data["models"], "models").items())
        }
        switches = {
            name: Distribution.parse(item, f"switches.{name}")
            for name, item in sorted(object_map(data["switches"], "switches").items())
        }
        for name, switch in switches.items():
            references(switch, set(models), f"switches.{name}")
        base = schedule(data["source"], set(switches), "source")
        alphabet = tuple(sorted({a for model in models.values() for a in model.probabilities}))
        if "state_machine" not in data:
            initial = Distribution.parse({"default": "1"}, "initial")
            schedules = {"default": base}
            stay = Distribution.parse({"default": "1"}, "transition")
            transitions = {"default": {a: stay for a in alphabet}}
        else:
            machine = object_map(data["state_machine"], "state_machine")
            fields(machine, {"initial", "states"}, set(), "state_machine")
            states = object_map(machine["states"], "state_machine.states")
            initial = Distribution.parse(machine["initial"], "state_machine.initial")
            references(initial, set(states), "state_machine.initial")
            schedules, transitions = {}, {}
            for name, raw_state in sorted(states.items()):
                loc = f"state_machine.states.{name}"
                state = object_map(raw_state, loc)
                fields(state, {"transitions"}, {"source"}, loc)
                own = schedule(state.get("source", list(base)), set(switches), f"{loc}.source")
                if len(own) != len(base):
                    raise InputError(f"{loc}.source: длина должна равняться L={len(base)}")
                schedules[name] = own
                raw_transitions = object_map(state["transitions"], f"{loc}.transitions")
                if raw_transitions.keys() != set(alphabet):
                    raise InputError(f"{loc}.transitions: нужны ровно все символы алфавита")
                transitions[name] = {}
                for symbol, weights in sorted(raw_transitions.items()):
                    dist = Distribution.parse(weights, f"{loc}.transitions.{symbol}")
                    references(dist, set(states), f"{loc}.transitions.{symbol}")
                    transitions[name][symbol] = dist
        emissions = {
            name: {
                a: sum((weight * models[m].probabilities.get(a, Fraction(0))
                        for m, weight in switch.probabilities.items()), Fraction(0))
                for a in alphabet
            }
            for name, switch in switches.items()
        }
        return cls(models, switches, schedules, initial, transitions, emissions, alphabet, len(base))

    @classmethod
    def load(cls, path: str | Path) -> "Source":
        """Загрузить JSON-файл и разобрать его по правилам Source.parse."""
        return cls.parse(read_json(path))

    def generate(self, seed: int) -> Iterator[str]:
        """Бесконечно выдавать символы при фиксированном seed.

        На каждом такте: переключатель → модель → символ → новое состояние.
        Число выданных символов ограничивает вызывающий код, например CLI.
        """
        rng = random.Random(seed)
        state = self.initial.draw(rng)
        phase = 0
        while True:
            switch = self.switches[self.schedules[state][phase]]
            model = self.models[switch.draw(rng)]
            symbol = model.draw(rng)
            yield symbol
            state = self.transitions[state][symbol].draw(rng)
            phase = (phase + 1) % self.period

    def advance(
        self, masses: dict[str, Fraction], phase: int, symbol: str | None = None,
    ) -> dict[str, Fraction]:
        """Перенести массы состояний на один такт.

        Вклад перехода: масса состояния × P(символ | состояние, фаза)
        × P(следующее состояние | состояние, символ).
        symbol=None суммирует по всем символам, например при пропуске тактов.
        Массы не нормируются: их сумма после фиксации символов — вероятность
        уже выданного префикса, а не обязательно единица.
        """
        result: dict[str, Fraction] = {}
        for state, mass in masses.items():
            emissions = self.emissions[self.schedules[state][phase % self.period]]
            symbols = emissions if symbol is None else (symbol,)
            for a in symbols:
                emitted_mass = mass * emissions.get(a, Fraction(0))
                if not emitted_mass:
                    continue
                for next_state, weight in self.transitions[state][a].probabilities.items():
                    if weight:
                        result[next_state] = result.get(next_state, Fraction(0)) + emitted_mass * weight
        return result

    def block_probability(self, word: Sequence[str], offset: int = 0) -> Fraction:
        """Пропустить offset тактов, затем оставить только пути с данным словом."""
        if offset < 0:
            raise InputError("Смещение должно быть неотрицательным")
        masses = self.initial.probabilities.copy()
        for phase in range(offset):
            masses = self.advance(masses, phase)
        for phase, symbol in enumerate(word, offset):
            masses = self.advance(masses, phase, symbol)
        return sum(masses.values(), Fraction(0))

    def exact_probabilities(self, word: Sequence[str]) -> tuple[Fraction, Fraction]:
        """Вернуть P(блок с первого такта) и среднее P по смещениям 0,…,L−1."""
        probabilities = [self.block_probability(word, j) for j in range(self.period)]
        return probabilities[0], sum(probabilities, Fraction(0)) / self.period

# END GENERATED CODE: OpenAI Codex.
