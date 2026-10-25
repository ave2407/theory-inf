"""Длины и канонические коды Хаффмана для байтового алфавита."""

import heapq
from typing import BinaryIO

from theory_inf.distributions import InputError


def code_lengths(frequencies: list[int]) -> dict[int, int]:
    """По 256 частотам байтов вернуть длины слов только для встречающихся символов.

    Два самых лёгких поддерева сливаются, глубина листа становится длиной слова.
    Для пустого входа результат пуст; единственному символу назначается длина 0.
    """
    if len(frequencies) != 256 or any(type(n) is not int or n < 0 for n in frequencies):
        raise InputError("Нужны 256 неотрицательных целых частот байтов")
    queue = [(freq, symbol, symbol) for symbol, freq in enumerate(frequencies) if freq]
    heapq.heapify(queue)
    if not queue:
        return {}
    if len(queue) == 1:
        return {queue[0][1]: 0}
    # Минимальный символ поддерева разрешает равенство весов детерминированно.
    while len(queue) > 1:
        left_weight, left_min_symbol, left_tree = heapq.heappop(queue)
        right_weight, right_min_symbol, right_tree = heapq.heappop(queue)
        combined_weight = left_weight + right_weight
        min_symbol = min(left_min_symbol, right_min_symbol)
        heapq.heappush(queue, (combined_weight, min_symbol, (left_tree, right_tree)))
    lengths = {}
    stack = [(queue[0][2], 0)]
    while stack:
        node, depth = stack.pop()
        if isinstance(node, int):
            lengths[node] = depth
        else:
            stack.append((node[1], depth + 1))
            stack.append((node[0], depth + 1))
    return lengths


def canonical_codes(lengths: dict[int, int]) -> dict[int, tuple[int, int]]:
    """Байт → (слово как целое число, длина в битах).

    Для длин A:1, B:2, C:2 получатся A:0, B:10, C:11.
    При переходе к большей длине приписываем нули справа;
    следующее слово той же длины получаем прибавлением единицы.
    """
    if any(type(a) is not int or not 0 <= a <= 255 or
           type(n) is not int or not 0 <= n <= 255 for a, n in lengths.items()):
        raise InputError("Некорректный символ или длина кода")
    if not lengths:
        return {}
    if len(lengths) == 1:
        symbol, length = next(iter(lengths.items()))
        if length != 0:
            raise InputError("Единственный символ должен иметь код длины 0")
        return {symbol: (0, 0)}
    if 0 in lengths.values():
        raise InputError("Нулевая длина разрешена только для единственного символа")
    # Канонические слова определены длинами и порядком символов.
    result = {}
    code = previous_length = 0
    for length, symbol in sorted((length, symbol) for symbol, length in lengths.items()):
        code <<= length - previous_length
        if code >= 1 << length:
            raise InputError("Переполненное кодовое дерево")
        result[symbol] = (code, length)
        code += 1
        previous_length = length
    if code != 1 << previous_length:
        raise InputError("Неполное кодовое дерево")
    return result


def decoding_tree(codes: dict[int, tuple[int, int]]) -> dict:
    """Построить дерево из проверенных кодов: ключи 0/1 — ветви, целые листья — байты.

    Пустое кодовое слово не поддерживается: один символ восстанавливается
    отдельно по размеру исходного файла из заголовка.
    """
    tree = {}
    for symbol, (code, length) in codes.items():
        if not length:
            raise InputError("Пустое слово декодируется отдельно по исходной длине")
        node = tree
        for shift in range(length - 1, 0, -1):
            node = node.setdefault((code >> shift) & 1, {})
        node[code & 1] = symbol
    return tree


class BitWriter:
    """Записывать кодовые слова произвольной длины в бинарный поток, MSB-first.

    buffer хранит готовые байты, pending/pending_bits — неполный хвост,
    total_bits считает полезные биты без заполнения. После всех write
    вызывается finish; переданный поток остаётся открытым.
    """

    def __init__(self, stream: BinaryIO, buffer_size: int = 65536):
        self.stream = stream
        self.buffer_size = buffer_size
        self.buffer = bytearray()
        self.pending = 0
        self.pending_bits = 0
        self.total_bits = 0

    def write(self, code: int, length: int) -> None:
        """Приписать length битов проверенного слова code; готовые байты буферизовать."""
        # pending хранит ещё не выведенный хвост, pending_bits — его длину.
        self.pending = (self.pending << length) | code
        self.pending_bits += length
        self.total_bits += length
        while self.pending_bits >= 8:
            self.pending_bits -= 8
            self.buffer.append(self.pending >> self.pending_bits)
            self.pending &= (1 << self.pending_bits) - 1
        if len(self.buffer) >= self.buffer_size:
            self.stream.write(self.buffer)
            self.buffer.clear()

    def finish(self) -> None:
        """Дополнить неполный байт нулями справа и записать оставшийся буфер."""
        if self.pending_bits:
            self.buffer.append(self.pending << (8 - self.pending_bits))
        self.stream.write(self.buffer)
        self.buffer.clear()
        self.pending = self.pending_bits = 0
