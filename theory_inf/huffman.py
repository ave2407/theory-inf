"""Длины и канонические коды Хаффмана для байтового алфавита."""

# Adapted from Project Nayuki, Reference Huffman coding.
# Copyright (c) Project Nayuki. MIT License: SOURCES.md.
# Изменения относительно исходника перечислены в SOURCES.md.

import heapq
from typing import BinaryIO

from theory_inf.distributions import InputError


def code_lengths(frequencies: list[int]) -> dict[int, int]:
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
        left = heapq.heappop(queue)
        right = heapq.heappop(queue)
        heapq.heappush(queue, (left[0] + right[0], min(left[1], right[1]), (left[2], right[2])))
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
    """Байт → (целочисленное кодовое слово, число его битов)."""
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
    """MSB-first, нулевое дополнение справа, буферизованный вывод."""

    def __init__(self, stream: BinaryIO, buffer_size: int = 65536):
        self.stream = stream
        self.buffer_size = buffer_size
        self.buffer = bytearray()
        self.pending = 0
        self.pending_bits = 0
        self.total_bits = 0

    def write(self, code: int, length: int) -> None:
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
        if self.pending_bits:
            self.buffer.append(self.pending << (8 - self.pending_bits))
        self.stream.write(self.buffer)
        self.buffer.clear()
        self.pending = self.pending_bits = 0
