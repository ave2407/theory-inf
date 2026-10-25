# Теория информации — ДЗ №1

Вариант: **s=2**. Python **3.11+**, только стандартная библиотека.

```sh
python3 main.py --variant
python3 main.py generate examples/task_1_1/periodic.json --n 20 --seed 2
python3 main.py analyze examples/task_1_1/periodic.json --n 10000 --word A B --seed 2
python3 main.py entropy examples/task_1_2/iid.json
python3 main.py uniform examples/task_1_2/iid.json --rate 2 --n-max 50 --code-output code.json
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
