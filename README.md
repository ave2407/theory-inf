# Теория информации — ДЗ №1

Вариант: **s=2**. Python **3.11+**, только стандартная библиотека.

```sh
python3 main.py --variant
python3 main.py generate examples/task_1_1/periodic.json --n 20 --seed 2
python3 main.py analyze examples/task_1_1/periodic.json --n 10000 --word A B --seed 2
python3 -m unittest discover -v
```

Скрипт запуска из любого каталога: `sh /путь/к/theory-inf/run.sh --variant`.

Параметры варианта вычисляются в `theory_inf/variant.py`. Исходные файлы
преподавателя не ограничиваются параметрами нашего варианта: эти параметры
определяют собственные примеры и измерения.
