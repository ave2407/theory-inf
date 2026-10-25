# Теория информации — ДЗ №1

Вариант: **s=2**. Python **3.11+**, только стандартная библиотека.

```sh
python3 main.py --variant
python3 main.py generate examples/task_1_1/periodic.json --n 20 --seed 2
python3 main.py analyze examples/task_1_1/periodic.json --n 10000 --word A B --seed 2
python3 main.py entropy examples/task_1_2/iid.json
python3 main.py uniform examples/task_1_2/iid.json --rate 2 --n-max 50 --code-output code.json
python3 main.py compress examples/task_1_3/unicode.txt --output /tmp/unicode.txt.zmh --stats
python3 main.py decompress /tmp/unicode.txt.zmh --output /tmp/unicode-restored.txt --stats
python3 -m unittest discover -v
```

Скрипт запуска из любого каталога: `sh /путь/к/theory-inf/run.sh --variant`.

Параметры варианта вычисляются в `theory_inf/variant.py`. Исходные файлы
преподавателя не ограничиваются параметрами нашего варианта: эти параметры
определяют собственные примеры и измерения.

`entropy` проверяет, что источник стационарен и не имеет памяти, затем выводит
распределение и энтропию в битах на символ. Поддерживается расширенный формат:
наличие скрытого состояния само по себе не означает зависимость выходных символов.

`uniform` выводит таблицу ошибок для n=1…n_max, первое подходящее n и отдельный
ответ об асимптотике. По умолчанию q=5, ε=1/10000, n_max=50; переопределение —
`--q`, `--epsilon`, `--n-max`. `--rate` принимает неотрицательную дробь,
десятичное число или `H` для точного равенства R=H. `--output FILE` сохраняет
таблицу вместо stdout; описание кода всегда сохраняется в `--code-output`
(по умолчанию `code.json`, файл перезаписывается). Формат — `docs/UNIFORM_CODE_FORMAT.md`.
Случайности в этих двух режимах нет, параметр seed не нужен.

Воспроизведение входов и измерений задачи 1.2:

```sh
python3 tools/build_uniform_examples.py
python3 tools/record_uniform_results.py
```

Таблицы — `RESULTS.md`, полные JSON — `results/task_1_2/`.

`compress` сжимает бинарный файл в два прохода; без `--output` создаёт
`исходное_имя.zmh` (например, `input.txt.zmh`). `decompress` восстанавливает
байты и проверяет целостность; без `--output` удаляет последний суффикс `.zmh`.
Оба режима отказываются перезаписывать существующие файлы. Для вывода
энтропии, средней длины, размеров заголовка/данных и коэффициента сжатия
используется `--stats`. Модель — канонический Хаффман, формат — `docs/ZMH_FORMAT.md`.
Unicode обрабатывается как байты; кодировка и нормализация не меняются.

Воспроизведение входов и измерений архиватора:

```sh
python3 tools/build_archive_examples.py --seed 2
python3 tools/record_archive_results.py
```

Входы и ошибочные архивы — `examples/task_1_3/`, результаты и read-back —
`results/task_1_3/`. Происхождение адаптации Nayuki и лицензия описаны в `SOURCES.md`.
В реальный корпус также входят оригинальный PDF Attention Is All You Need
и предоставленный пользователем PDF Конституции РФ. Конституция — 55-страничный
скан без текстового слоя; архивируются исходные байты PDF.
Происхождение и SHA-256 — `examples/task_1_3/real_sources.json`.
