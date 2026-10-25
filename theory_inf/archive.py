"""Двухпроходный архиватор ZMH1 с проверкой целостности и потоковым I/O."""

from collections import Counter
from contextlib import contextmanager
from fractions import Fraction
import os
from pathlib import Path
import struct
import tempfile
from typing import BinaryIO
import zlib

from theory_inf.distributions import InputError
from theory_inf.experiment import fraction_record
from theory_inf.huffman import BitWriter, canonical_codes, code_lengths, decoding_tree
from theory_inf.information import entropy

MAGIC = b"ZMH1"
METADATA = struct.Struct(">4sQQHI")  # magic, исходных байтов, полезных битов, символов, CRC32
CHECKSUM = struct.Struct(">I")
FIXED_HEADER_BYTES = METADATA.size + CHECKSUM.size  # 30
CHUNK_BYTES = 65536
UINT64_MAX = (1 << 64) - 1


class ForeignFormat(InputError):
    """Сигнатура не принадлежит поддерживаемому формату."""


class TruncatedArchive(InputError):
    """Не хватает заявленной части архива."""


class CorruptArchive(InputError):
    """Структура или контрольная сумма не прошла проверку."""


@contextmanager
def atomic_output(path: Path, source: Path):
    """Выдать временный бинарный поток, опубликовать результат только при успехе.

    Запрещает совпадение с исходником и перезапись существующего пути.
    При исключении временный файл удаляется; hard link в конце защищает
    также от появления чужого файла по выходному пути за время операции.
    """
    if path.resolve() == source.resolve() or (
        path.exists() and source.exists() and path.samefile(source)
    ):
        raise InputError("Выходной файл не должен совпадать с входным")
    if os.path.lexists(path):
        raise InputError(f"Выходной файл уже существует: {path}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                         prefix="." + path.name + ".", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            yield stream
        # link создаёт результат атомарно и не затирает файл, появившийся за время работы.
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def statistics(frequencies: list[int], lengths: dict[int, int], bits: int, crc: int) -> dict:
    """Собрать H на байт, среднюю длину, размеры контейнера и коэффициент сжатия.

    bits — полезные биты без заполнения; коэффициент включает заголовок.
    Для пустого входа H и средняя длина равны 0, коэффициент — None.
    """
    size = sum(frequencies)
    header = FIXED_HEADER_BYTES + 2 * len(lengths)
    data = (bits + 7) // 8
    distribution = {str(a): Fraction(n, size) for a, n in enumerate(frequencies) if n}
    return {
        "original_bytes": size,
        "model_symbols": len(lengths),
        "entropy_bits_per_byte": str(entropy(distribution)) if size else "0",
        "average_code_length_bits": fraction_record(Fraction(bits, size) if size else Fraction(0)),
        "header_bytes": header,
        "data_bytes": data,
        "payload_bits": bits,
        "archive_bytes": header + data,
        "compression_ratio": (header + data) / size if size else None,
        "ratio_definition": "archive_bytes/original_bytes",
        "original_crc32": f"{crc:08x}",
    }


def scan(stream: BinaryIO) -> tuple[list[int], int, int]:
    """Прочитать поток от текущей позиции до конца: 256 частот, размер и CRC32."""
    counts = Counter()
    checksum = size = 0
    while chunk := stream.read(CHUNK_BYTES):
        counts.update(chunk)
        checksum = zlib.crc32(chunk, checksum)
        size += len(chunk)
    return [counts[a] for a in range(256)], size, checksum


def compress(source: str | Path, output: str | Path | None = None) -> dict:
    """Сжать файл в два прохода и вернуть путь со статистикой.

    Первый проход даёт частоты и модель, второй записывает кодовые слова.
    Совпадение частот и CRC32 проверяет, что исходник не изменился между
    проходами. По умолчанию к имени добавляется .zmh; перезапись запрещена.
    """
    source = Path(source)
    output = Path(output) if output is not None else source.with_name(source.name + ".zmh")
    with source.open("rb") as inp:
        frequencies, size, checksum = scan(inp)
        lengths = code_lengths(frequencies)
        codes = canonical_codes(lengths)
        bits = sum(frequencies[a] * length for a, length in lengths.items())
        if size > UINT64_MAX or bits > UINT64_MAX:
            raise InputError("Размер не помещается в 64-битные поля ZMH1")
        metadata = METADATA.pack(MAGIC, size, bits, len(lengths), checksum)
        model = bytes(value for pair in sorted(lengths.items()) for value in pair)
        with atomic_output(output, source) as out:
            out.write(metadata)
            out.write(CHECKSUM.pack(zlib.crc32(metadata)))
            out.write(model)
            inp.seek(0)
            writer = BitWriter(out)
            second_counts = Counter()
            second_checksum = 0
            while chunk := inp.read(CHUNK_BYTES):
                second_counts.update(chunk)
                second_checksum = zlib.crc32(chunk, second_checksum)
                for symbol in chunk:
                    if symbol not in codes:
                        raise InputError("Исходный файл изменился между проходами")
                    writer.write(*codes[symbol])
            if (second_checksum != checksum or
                    any(second_counts[a] != frequencies[a] for a in range(256)) or
                    writer.total_bits != bits):
                raise InputError("Исходный файл изменился между проходами")
            writer.finish()
    return {"output": str(output), **statistics(frequencies, lengths, bits, checksum)}


def read_header(inp: BinaryIO) -> tuple[int, int, int, dict[int, int]]:
    """Прочитать и проверить заголовок; оставить поток в начале кодовых данных.

    Вернуть (исходный размер, полезные биты, CRC32 исходника, длины кодов).
    Проверяются сигнатура, CRC32 служебных полей, полный размер контейнера
    и допустимость модели; чужой, обрезанный и повреждённый файлы различаются.
    """
    header = inp.read(FIXED_HEADER_BYTES)
    if len(header) < len(MAGIC) and MAGIC.startswith(header):
        raise TruncatedArchive("Обрезанный архив: неполная сигнатура")
    if header[:4] != MAGIC:
        raise ForeignFormat("Чужой формат: ожидается сигнатура ZMH1")
    if len(header) < FIXED_HEADER_BYTES:
        raise TruncatedArchive("Обрезанный архив: неполный заголовок")
    metadata = header[:METADATA.size]
    if zlib.crc32(metadata) != CHECKSUM.unpack(header[METADATA.size:])[0]:
        raise CorruptArchive("Повреждённый архив: CRC32 служебных полей не совпадает")
    _, size, bits, count, checksum = METADATA.unpack(metadata)
    if count > 256 or count > size:
        raise CorruptArchive("Повреждённый архив: неверное число символов модели")
    expected = FIXED_HEADER_BYTES + 2 * count + (bits + 7) // 8
    actual = os.fstat(inp.fileno()).st_size
    if actual < expected:
        raise TruncatedArchive("Обрезанный архив: не хватает модели или сжатых данных")
    if actual > expected:
        raise CorruptArchive("Повреждённый архив: лишние данные в конце")
    raw = inp.read(2 * count)
    if len(raw) != 2 * count:
        raise TruncatedArchive("Обрезанный архив: неполная модель")
    symbols = list(raw[::2])
    if symbols != sorted(set(symbols)):
        raise CorruptArchive("Повреждённый архив: символы модели должны строго возрастать")
    lengths = dict(zip(symbols, raw[1::2]))
    if size == 0:
        if count or bits or checksum:
            raise CorruptArchive("Повреждённый архив: неверное описание пустого файла")
    elif not count:
        raise CorruptArchive("Повреждённый архив: отсутствует модель")
    try:
        canonical_codes(lengths)
    except InputError as exc:
        raise CorruptArchive(f"Повреждённый архив: {exc}") from exc
    if lengths:
        minimum = min(lengths.values())
        maximum = max(lengths.values())
        # Каждый символ модели обязан встретиться хотя бы раз; остальные
        # size-count байтов дают от minimum до maximum битов каждый.
        one_each_bits = sum(lengths.values())
        minimum_bits = one_each_bits + (size - count) * minimum
        maximum_bits = one_each_bits + (size - count) * maximum
        if not minimum_bits <= bits <= maximum_bits:
            raise CorruptArchive("Повреждённый архив: число битов несовместимо с моделью и размером")
    return size, bits, checksum, lengths


def decode_payload(
    inp: BinaryIO, out: BinaryIO, size: int, bits: int, lengths: dict[int, int],
) -> tuple[list[int], int]:
    """Восстановить данные по проверенной модели; вернуть 256 частот и CRC32.

    inp стоит после заголовка, out — временный выходной поток. Пустой вход
    и один символ обрабатываются без чтения битов; обычный поток читается
    порциями с проверкой заполнения и границ кодовых слов. Итоговую CRC32
    с ожидаемой сравнивает verify_result.
    """
    frequencies = [0] * 256
    checksum = produced = 0
    if not lengths:
        return frequencies, checksum
    if len(lengths) == 1:
        symbol = next(iter(lengths))
        frequencies[symbol] = size
        while produced < size:
            chunk = bytes([symbol]) * min(CHUNK_BYTES, size - produced)
            out.write(chunk)
            checksum = zlib.crc32(chunk, checksum)
            produced += len(chunk)
        return frequencies, checksum

    tree = decoding_tree(canonical_codes(lengths))
    node = tree
    buffer = bytearray()
    remaining_bits = bits
    remaining_bytes = (bits + 7) // 8
    while remaining_bytes:
        chunk = inp.read(min(CHUNK_BYTES, remaining_bytes))
        if not chunk:
            raise TruncatedArchive("Обрезанный архив: поток закончился при чтении данных")
        remaining_bytes -= len(chunk)
        for byte in chunk:
            useful = min(8, remaining_bits)
            if useful < 8 and byte & ((1 << (8 - useful)) - 1):
                raise CorruptArchive("Повреждённый архив: ненулевые биты заполнения")
            # Слева направо: бит 0 ведёт в левую ветвь, 1 — в правую.
            # Дойдя до листа (int), выдаём байт и возвращаемся к корню.
            for shift in range(7, 7 - useful, -1):
                node = node[(byte >> shift) & 1]
                if isinstance(node, int):
                    if produced >= size:
                        raise CorruptArchive("Повреждённый архив: восстановлено больше заявленного размера")
                    buffer.append(node)
                    frequencies[node] += 1
                    produced += 1
                    node = tree
            remaining_bits -= useful
            if len(buffer) >= CHUNK_BYTES:
                out.write(buffer)
                checksum = zlib.crc32(buffer, checksum)
                buffer.clear()
    if node is not tree or produced != size:
        raise CorruptArchive("Повреждённый архив: неполное слово или неверный исходный размер")
    out.write(buffer)
    checksum = zlib.crc32(buffer, checksum)
    return frequencies, checksum


def verify_result(
    frequencies: list[int], checksum: int, size: int,
    expected_crc: int, lengths: dict[int, int],
) -> None:
    """Проверить размер, CRC32 и использование модели до публикации файла."""
    if sum(frequencies) != size or checksum != expected_crc:
        raise CorruptArchive("Повреждённый архив: CRC32 исходных данных не совпадает")
    if {a for a, n in enumerate(frequencies) if n} != lengths.keys():
        raise CorruptArchive("Повреждённый архив: модель содержит неиспользованные символы")


def decompress(source: str | Path, output: str | Path | None = None) -> dict:
    """Прочитать заголовок → декодировать данные → проверить результат.

    Вернуть путь, verified=True и статистику только после успешной проверки.
    По умолчанию снимается суффикс .zmh, а у иного имени добавляется .out.
    Конечный файл создаётся после проверок; существующий не перезаписывается.
    """
    source = Path(source)
    if output is None:
        name = source.name[:-4] if source.name.endswith(".zmh") else source.name + ".out"
        output = source.with_name(name or "restored.bin")
    else:
        output = Path(output)
    with source.open("rb") as inp:
        size, bits, expected_crc, lengths = read_header(inp)
        with atomic_output(output, source) as out:
            frequencies, checksum = decode_payload(inp, out, size, bits, lengths)
            verify_result(frequencies, checksum, size, expected_crc, lengths)
    return {"output": str(output), "verified": True, **statistics(frequencies, lengths, bits, checksum)}
