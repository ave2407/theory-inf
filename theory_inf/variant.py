"""Параметры из раздела «Параметры варианта» условия ДЗ №1."""

from dataclasses import dataclass
from fractions import Fraction

STUDENT_NUMBER = 2


@dataclass(frozen=True)
class Variant:
    """Параметры варианта: k — алфавит, models — M, period — L, depth — d.

    s — номер студента, q — алфавит кодера, epsilon — допустимая ошибка.
    Объект VARIANT используется в CLI и подготовке собственных примеров.
    """
    s: int
    k: int
    models: int
    period: int
    depth: int
    q: int
    epsilon: Fraction

    @classmethod
    def from_student(cls, s: int) -> "Variant":
        """Вычислить все параметры по положительному номеру s из формул условия."""
        if type(s) is not int or s < 1:
            raise ValueError("Номер студента должен быть положительным целым числом")
        residue = s % 3
        return cls(
            s=s,
            k=5 - residue,
            models=2 + residue,
            period=3 + s % 5,
            depth=1 + residue,
            q=(2, 3, 5, 7)[s % 4],
            epsilon=Fraction(1, 10 ** (2 + residue)),
        )

    def as_dict(self) -> dict:
        """Подготовить вывод --variant с обозначениями M, L, d и точной строкой ε."""
        return {
            "s": self.s, "k": self.k, "M": self.models, "L": self.period,
            "d": self.depth, "q": self.q, "epsilon": str(self.epsilon),
        }


VARIANT = Variant.from_student(STUDENT_NUMBER)
