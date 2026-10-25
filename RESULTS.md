# Результаты задачи 1.1

Вариант s=2. Seed=2.

Проверенная версия Python: 3.13.13.

Воспроизведение: `python3 tools/record_results.py`.
Полные JSON-выводы и реализации лежат в `results/task_1_1/`.

## Параметры

```json
{
  "s": 2,
  "k": 3,
  "M": 4,
  "L": 5,
  "d": 3,
  "q": 5,
  "epsilon": "1/10000"
}
```

## iid

Команда: `python3 main.py analyze examples/task_1_1/iid.json --n 1000000 --word A B --seed 2`

Первые 20 символов (`generate`, те же seed и источник):

```text
A A A B A B B A A A C C B C B A A B B C
```

| N | Частота | Отклонение от первого такта | Отклонение от среднего |
|---:|---:|---:|---:|
| 100 | 0.151515152 | 0.006470960 | 0.006470960 |
| 1000 | 0.156156156 | 0.001829955 | 0.001829955 |
| 10000 | 0.158815882 | 0.000829770 | 0.000829770 |
| 100000 | 0.158921589 | 0.000935478 | 0.000935478 |
| 1000000 | 0.158413158 | 0.000427047 | 0.000427047 |

## periodic

Команда: `python3 main.py analyze examples/task_1_1/periodic.json --n 1000000 --word A B --seed 2`

Первые 20 символов (`generate`, те же seed и источник):

```text
A B A B B B B C A B C C C C B A A C B C
```

| N | Частота | Отклонение от первого такта | Отклонение от среднего |
|---:|---:|---:|---:|
| 100 | 0.161616162 | 0.131786616 | 0.011963384 |
| 1000 | 0.149149149 | 0.144253629 | 0.000503629 |
| 10000 | 0.150515052 | 0.142887726 | 0.000862274 |
| 100000 | 0.149611496 | 0.143791282 | 0.000041282 |
| 1000000 | 0.150152150 | 0.143250628 | 0.000499372 |

## markov

Команда: `python3 main.py analyze examples/task_1_1/markov.json --n 1000000 --word A B --seed 2`

Первые 20 символов (`generate`, те же seed и источник):

```text
A A C A B C A A B C C C C C A A C B C C
```

| N | Частота | Отклонение от первого такта | Отклонение от среднего |
|---:|---:|---:|---:|
| 100 | 0.141414141 | 0.030303030 | 0.030303030 |
| 1000 | 0.104104104 | 0.007007007 | 0.007007007 |
| 10000 | 0.112911291 | 0.001800180 | 0.001800180 |
| 100000 | 0.110231102 | 0.000880009 | 0.000880009 |
| 1000000 | 0.111518112 | 0.000407000 | 0.000407000 |

## nonergodic

Команда: `python3 main.py analyze examples/task_1_1/nonergodic.json --n 1000000 --word A B --seed 2`

Первые 20 символов (`generate`, те же seed и источник):

```text
A A B A B B A A A C C B C B A A B B C C
```

| N | Частота | Отклонение от первого такта | Отклонение от среднего |
|---:|---:|---:|---:|
| 100 | 0.161616162 | 0.037484217 | 0.037484217 |
| 1000 | 0.156156156 | 0.032024212 | 0.032024212 |
| 10000 | 0.158815882 | 0.034683937 | 0.034683937 |
| 100000 | 0.158921589 | 0.034789645 | 0.034789645 |
| 1000000 | 0.158414158 | 0.034282214 | 0.034282214 |

## deterministic

Команда: `python3 main.py analyze examples/task_1_1/deterministic.json --n 1000000 --word A A --seed 2`

Первые 20 символов (`generate`, те же seed и источник):

```text
A A A A A A A A A A A A A A A A A A A A
```

| N | Частота | Отклонение от первого такта | Отклонение от среднего |
|---:|---:|---:|---:|
| 100 | 1.000000000 | 0.000000000 | 0.000000000 |
| 1000 | 1.000000000 | 0.000000000 | 0.000000000 |
| 10000 | 1.000000000 | 0.000000000 | 0.000000000 |
| 100000 | 1.000000000 | 0.000000000 | 0.000000000 |
| 1000000 | 1.000000000 | 0.000000000 | 0.000000000 |

## Сводная таблица

| Источник | Блок | P на первом такте | Среднее по L | Частота при N=10⁶ |
|---|---|---:|---:|---:|
| iid | AB | 91/576 | 91/576 | 0.158413158 |
| periodic | AB | 169/576 | 431/2880 | 0.150152150 |
| markov | AB | 1/9 | 1/9 | 0.111518112 |
| nonergodic | AB | 143/1152 | 143/1152 | 0.158414158 |
| deterministic | AA | 1 | 1 | 1.000000000 |

## Некорректные входы

- `generate broken.json` → код 2; `Ошибка: JSON: строка 1, столбец 11: Expecting value`
- `analyze broken.json` → код 2; `Ошибка: JSON: строка 1, столбец 11: Expecting value`
- `generate empty_source.json` → код 2; `Ошибка: source: ожидается непустой список переключателей`
- `analyze empty_source.json` → код 2; `Ошибка: source: ожидается непустой список переключателей`
- `generate negative.json` → код 2; `Ошибка: models.A_only.A: отрицательная вероятность`
- `analyze negative.json` → код 2; `Ошибка: models.A_only.A: отрицательная вероятность`
- `generate unknown_model.json` → код 2; `Ошибка: switches.A: неизвестные ссылки missing`
- `analyze unknown_model.json` → код 2; `Ошибка: switches.A: неизвестные ссылки missing`
- `generate unknown_switch.json` → код 2; `Ошибка: source: неизвестный переключатель`
- `analyze unknown_switch.json` → код 2; `Ошибка: source: неизвестный переключатель`
- `generate unnormalized.json` → код 2; `Ошибка: models.A_only: сумма вероятностей должна равняться 1`
- `analyze unnormalized.json` → код 2; `Ошибка: models.A_only: сумма вероятностей должна равняться 1`

# Результаты задачи 1.2

Вариант s=2, q=5, ε=1/10000, n_max=50.

Python 3.13.13. `python3 tools/record_uniform_results.py`.

Случайности в задаче 1.2 нет. Полные таблицы и описания кодов — `results/task_1_2/`.

## below

`python3 main.py uniform examples/task_1_2/iid.json --rate 1 --n-max 50 --code-output results/task_1_2/below_code.json`

Асимптотика: R<H: P_e(n)→1; подходящие малые n этим не исключаются.

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 11/24 | 0.458333333 |
| 2 | 0 | 1 | 407/576 | 0.706597222 |
| 3 | 1 | 5 | 3701/6912 | 0.535445602 |
| 4 | 1 | 5 | 241699/331776 | 0.728500555 |
| 10 | 4 | 625 | 12833959292501/15850845241344 | 0.809670342 |
| 11 | 4 | 625 | 42242944461043/47552535724032 | 0.888342626 |
| 25 | 10 | 9765625 | 15636107506726409765551217674097047/16004829322203409493388977674125312 | 0.97696184 |
| 50 | 21 | 476837158203125 | 1022778617237321095475081965399589038929139690136195987226310643783305/1024618246531448192529486101931556275808450117982966277666337116389376 | 0.998204571 |

## above

`python3 main.py uniform examples/task_1_2/iid.json --rate 3/2 --n-max 50 --code-output results/task_1_2/above_code.json`

Асимптотика: R>H: P_e(n)→0.

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 11/24 | 0.458333333 |
| 2 | 1 | 5 | 121/576 | 0.210069444 |
| 3 | 1 | 5 | 3701/6912 | 0.535445602 |
| 4 | 2 | 25 | 109541/331776 | 0.330165533 |
| 10 | 6 | 15625 | 3016982715977/15850845241344 | 0.190335763 |
| 11 | 7 | 78125 | 113218281697579/1521681143169024 | 0.0744034203 |
| 25 | 16 | 152587890625 | 1158548684443225958910407484980407/16004829322203409493388977674125312 | 0.0723874439 |
| 50 | 32 | 23283064365386962890625 | 8579949245897425468148696877697739389815527160048320867713608261799/128077280816431024066185762741444534476056264747870784708292139548672 | 0.0669904076 |

## full

`python3 main.py uniform examples/task_1_2/iid.json --rate 2 --n-max 50 --code-output results/task_1_2/full_code.json`

Асимптотика: R>H: P_e(n)→0.

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 11/24 | 0.458333333 |
| 2 | 1 | 5 | 121/576 | 0.210069444 |
| 3 | 2 | 25 | 11/864 | 0.0127314815 |
| 4 | 3 | 81 | 0 | 0 |
| 10 | 8 | 59049 | 0 | 0 |
| 11 | 9 | 177147 | 0 | 0 |
| 25 | 21 | 847288609443 | 0 | 0 |
| 50 | 43 | 717897987691852588770249 | 0 | 0 |

## at_entropy

`python3 main.py uniform examples/task_1_2/iid.json --rate H --n-max 50 --code-output results/task_1_2/at_entropy_code.json`

Асимптотика: R=H, неравномерный iid-источник: P_e→1/2; при ε=1/2 достаточность следует из поправки −(log₂ n)/2 к log₂ M*(n,ε).

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 11/24 | 0.458333333 |
| 2 | 1 | 5 | 121/576 | 0.210069444 |
| 3 | 1 | 5 | 3701/6912 | 0.535445602 |
| 4 | 2 | 25 | 109541/331776 | 0.330165533 |
| 10 | 6 | 15625 | 3016982715977/15850845241344 | 0.190335763 |
| 11 | 6 | 15625 | 318545354884903/760840571584512 | 0.418675563 |
| 25 | 15 | 30517578125 | 2320401100818629032621203452520367/8002414661101704746694488837062656 | 0.289962617 |
| 50 | 30 | 931322574615478515625 | 393619097686507470534825215453820186576683792532039331330169553244697/1024618246531448192529486101931556275808450117982966277666337116389376 | 0.38416171 |

## uniform_boundary

`python3 main.py uniform examples/task_1_2/uniform.json --rate H --n-max 50 --code-output results/task_1_2/uniform_boundary_code.json`

Асимптотика: R=H, равномерный источник: дробные части n·log_q(|support|) плотны; sup P_e=1−1/q.

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 2/3 | 0.666666667 |
| 2 | 1 | 5 | 4/9 | 0.444444444 |
| 3 | 2 | 25 | 2/27 | 0.0740740741 |
| 4 | 2 | 25 | 56/81 | 0.691358025 |
| 10 | 6 | 15625 | 43424/59049 | 0.735389253 |
| 11 | 7 | 78125 | 99022/177147 | 0.558982088 |
| 25 | 17 | 762939453125 | 84349156318/847288609443 | 0.0995518592 |
| 50 | 34 | 582076609134674072265625 | 135821378557178516504624/717897987691852588770249 | 0.189193146 |

## dyadic_boundary

`python3 main.py uniform examples/task_1_2/dyadic.json --rate 3/2 --n-max 50 --code-output results/task_1_2/dyadic_boundary_code.json`

Асимптотика: R=H, неравномерный iid-источник: P_e→1/2; при ε=1/2 достаточность следует из поправки −(log₂ n)/2 к log₂ M*(n,ε).

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 1/2 | 0.5 |
| 2 | 1 | 5 | 1/4 | 0.25 |
| 3 | 1 | 5 | 5/8 | 0.625 |
| 4 | 2 | 25 | 7/16 | 0.4375 |
| 10 | 6 | 15625 | 677/2048 | 0.330566406 |
| 11 | 7 | 78125 | 22503/131072 | 0.171684265 |
| 25 | 16 | 152587890625 | 115754687857/549755813888 | 0.210556551 |
| 50 | 32 | 23283064365386962890625 | 5425873706045014941321/18889465931478580854784 | 0.287243362 |

## small_n

`python3 main.py uniform examples/task_1_2/skewed.json --rate 0 --n-max 50 --code-output results/task_1_2/small_n_code.json`

Асимптотика: R<H: P_e(n)→1; подходящие малые n этим не исключаются.

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 1/100000 | 1e-05 |
| 2 | 0 | 1 | 199999/10000000000 | 1.99999e-05 |
| 3 | 0 | 1 | 29999700001/1000000000000000 | 2.99997e-05 |
| 4 | 0 | 1 | 3999940000399999/100000000000000000000 | 3.99994e-05 |
| 10 | 0 | 1 | 9999550011999790002519979000119999550000999999/100000000000000000000000000000000000000000000000000 | 9.99955001e-05 |
| 11 | 0 | 1 | 1099945001649967000461995380032999835000549998900001/10000000000000000000000000000000000000000000000000000000 | 0.0001099945 |
| 25 | 0 | 1 | 24997000229987350531282290480689184454294231284573479975200255426326873957035815701930177099468701264997700002999997500001/100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 | 0.000249970002 |
| 50 | 0 | 1 | 4998775195976972118601102987903146403309809535524838974114036851503392077641358901709459781021625754515577891640576096195587358741800514773718136684889589526544781262696698922930460722436360774688428331223488424109321187576970019599987750004999999/10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 | 0.00049987752 |

## deterministic

`python3 main.py uniform examples/task_1_2/deterministic.json --rate 0 --n-max 50 --code-output results/task_1_2/deterministic_code.json`

Асимптотика: Ошибка всегда не больше ε.

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 0 | 0 |
| 2 | 0 | 1 | 0 | 0 |
| 3 | 0 | 1 | 0 | 0 |
| 4 | 0 | 1 | 0 | 0 |
| 10 | 0 | 1 | 0 | 0 |
| 11 | 0 | 1 | 0 | 0 |
| 25 | 0 | 1 | 0 | 0 |
| 50 | 0 | 1 | 0 | 0 |

## hidden

`python3 main.py uniform examples/task_1_2/iid_hidden.json --rate 2 --n-max 50 --code-output results/task_1_2/hidden_code.json`

Асимптотика: R>H: P_e(n)→0.

| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 7/12 | 0.583333333 |
| 2 | 1 | 5 | 715/2304 | 0.310329861 |
| 3 | 2 | 25 | 847/27648 | 0.0306351273 |
| 4 | 3 | 81 | 0 | 0 |
| 10 | 8 | 59049 | 0 | 0 |
| 11 | 9 | 177147 | 0 | 0 |
| 25 | 21 | 847288609443 | 0 | 0 |
| 50 | 43 | 717897987691852588770249 | 0 | 0 |

## Сводная таблица

| Вход | R | H, бит/символ | Первое n≤50 | P_e(50) | Условие выполнено для всех достаточно больших n |
|---|---:|---:|---:|---:|---|
| iid | 1 | 1.428412468 | — | 0.998204571 | нет |
| iid | 3/2 | 1.428412468 | — | 0.0669904076 | да |
| iid | 2 | 1.428412468 | 4 | 0 | да |
| iid | H | 1.428412468 | — | 0.38416171 | нет |
| uniform | H | 1.584962501 | — | 0.189193146 | нет |
| dyadic | 3/2 | 1.500000000 | — | 0.287243362 | нет |
| skewed | 0 | 0.000190523 | 1 | 0.00049987752 | нет |
| deterministic | 0 | 0.000000000 | 1 | 0 | да |
| iid_hidden | 2 | 1.543729626 | 4 | 0 | да |

## Диагностика

- `entropy periodic.json`: код 2, Ошибка: Источник нестационарен: распределение символа меняется на такте 2
- `uniform periodic.json`: код 2, Ошибка: Источник нестационарен: распределение символа меняется на такте 2
- `entropy markov.json`: код 2, Ошибка: Источник имеет память: вероятность 'A' зависит от префикса ['A', 'A', 'A']
- `uniform markov.json`: код 2, Ошибка: Источник имеет память: вероятность 'A' зависит от префикса ['A', 'A', 'A']
- `entropy nonergodic.json`: код 2, Ошибка: Источник имеет память: вероятность 'A' зависит от префикса ['A']
- `uniform nonergodic.json`: код 2, Ошибка: Источник имеет память: вероятность 'A' зависит от префикса ['A']

## Производительность

Отдельный контрольный вход k=5, n_max=50: **2.129 с** на Python 3.13.13.
Измерен полный CLI-процесс: чтение и проверка источника, 50 строк таблицы, сохранение кода и вывод JSON.
Этот вход проверяет требование k≤5 и отличается от собственного варианта k=3.
Подробности замера — `results/task_1_2/timing.json`. Время не включается в детерминированные результаты.

# Результаты задачи 1.3

Python 3.13.13. Воспроизведение: `python3 tools/record_archive_results.py`.

PNG синтетический, создан tools/build_archive_examples.py с seed=2. Контрольные тексты собственные, UTF-8.
Реальные документы и происхождение: `examples/task_1_3/real_sources.json`.

Проверка восстановления выполнена побайтовым сравнением и SHA-256.

## russian.txt

`python3 main.py compress examples/task_1_3/russian.txt --output results/task_1_3/russian.txt.zmh --stats`

```json
{
  "output": "results/task_1_3/russian.txt.zmh",
  "original_bytes": 14920,
  "model_symbols": 38,
  "entropy_bits_per_byte": "3.8345465888660002077358712847085320970736570135408418903956998562197885957270100",
  "average_code_length_bits": {
    "fraction": "1448/373",
    "decimal": 3.8820375335120643
  },
  "header_bytes": 106,
  "data_bytes": 7240,
  "payload_bits": 57920,
  "archive_bytes": 7346,
  "compression_ratio": 0.4923592493297587,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "0c288693"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `01a085798196e7321d4ae6270df50169bc08f637422f854f06f164e17b462ce2`.

## english.txt

`python3 main.py compress examples/task_1_3/english.txt --output results/task_1_3/english.txt.zmh --stats`

```json
{
  "output": "results/task_1_3/english.txt.zmh",
  "original_bytes": 8200,
  "model_symbols": 29,
  "entropy_bits_per_byte": "4.2201557414433781337045425434650581830097011120053159935551062903116573945242465",
  "average_code_length_bits": {
    "fraction": "872/205",
    "decimal": 4.253658536585366
  },
  "header_bytes": 88,
  "data_bytes": 4360,
  "payload_bits": 34880,
  "archive_bytes": 4448,
  "compression_ratio": 0.5424390243902439,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "0f4aa9b2"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `c223dd09e29da3c91f3ea1195e6b44ff997e60a88da72f224bb6b31e97a207d0`.

## image.png

`python3 main.py compress examples/task_1_3/image.png --output results/task_1_3/image.png.zmh --stats`

```json
{
  "output": "results/task_1_3/image.png.zmh",
  "original_bytes": 49363,
  "model_symbols": 256,
  "entropy_bits_per_byte": "7.9946241285851985056375690249887657694694348328213069144802318738032120770368004",
  "average_code_length_bits": {
    "fraction": "394869/49363",
    "decimal": 7.999290966918542
  },
  "header_bytes": 542,
  "data_bytes": 49359,
  "payload_bits": 394869,
  "archive_bytes": 49901,
  "compression_ratio": 1.0108988513664081,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "6d9f5a6e"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `2dbf9a80afe6bfc9b3aaf08ee07e8541b28533fdeeba4937f0924948550d79cc`.

## repeated.bin

`python3 main.py compress examples/task_1_3/repeated.bin --output results/task_1_3/repeated.bin.zmh --stats`

```json
{
  "output": "results/task_1_3/repeated.bin.zmh",
  "original_bytes": 4096,
  "model_symbols": 1,
  "entropy_bits_per_byte": "0",
  "average_code_length_bits": {
    "fraction": "0",
    "decimal": 0.0
  },
  "header_bytes": 32,
  "data_bytes": 0,
  "payload_bits": 0,
  "archive_bytes": 32,
  "compression_ratio": 0.0078125,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "fea63440"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `6896d9ea3f73a4434f5832bc65714e7d066f177373f36f34dc8a6f735daa41b1`.

## empty.bin

`python3 main.py compress examples/task_1_3/empty.bin --output results/task_1_3/empty.bin.zmh --stats`

```json
{
  "output": "results/task_1_3/empty.bin.zmh",
  "original_bytes": 0,
  "model_symbols": 0,
  "entropy_bits_per_byte": "0",
  "average_code_length_bits": {
    "fraction": "0",
    "decimal": 0.0
  },
  "header_bytes": 30,
  "data_bytes": 0,
  "payload_bits": 0,
  "archive_bytes": 30,
  "compression_ratio": null,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "00000000"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## unicode.txt

`python3 main.py compress examples/task_1_3/unicode.txt --output results/task_1_3/unicode.txt.zmh --stats`

```json
{
  "output": "results/task_1_3/unicode.txt.zmh",
  "original_bytes": 4200,
  "model_symbols": 46,
  "entropy_bits_per_byte": "5.0463151943603265490895688659774298987223738900239587973700752169312084897761938",
  "average_code_length_bits": {
    "fraction": "178/35",
    "decimal": 5.085714285714285
  },
  "header_bytes": 122,
  "data_bytes": 2670,
  "payload_bits": 21360,
  "archive_bytes": 2792,
  "compression_ratio": 0.6647619047619048,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "c8f5e94c"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `b8c623d2ce52507b17f2e81dde20fde2ac7fd6ed0d94d221ec7b7871149bb43a`.

## all_bytes.bin

`python3 main.py compress examples/task_1_3/all_bytes.bin --output results/task_1_3/all_bytes.bin.zmh --stats`

```json
{
  "output": "results/task_1_3/all_bytes.bin.zmh",
  "original_bytes": 2048,
  "model_symbols": 256,
  "entropy_bits_per_byte": "8",
  "average_code_length_bits": {
    "fraction": "8",
    "decimal": 8.0
  },
  "header_bytes": 542,
  "data_bytes": 2048,
  "payload_bits": 16384,
  "archive_bytes": 2590,
  "compression_ratio": 1.2646484375,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "9f5edd58"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `10fc3c51a152e90e5b90319b601d92ccf37290ef53c35ff92507687d8a911a08`.

## attention_is_all_you_need.pdf

`python3 main.py compress examples/task_1_3/attention_is_all_you_need.pdf --output results/task_1_3/attention_is_all_you_need.pdf.zmh --stats`

```json
{
  "output": "results/task_1_3/attention_is_all_you_need.pdf.zmh",
  "original_bytes": 2215244,
  "model_symbols": 256,
  "entropy_bits_per_byte": "7.0719287570114142662778334382981720968773099354419949996065069296236788075007036",
  "average_code_length_bits": {
    "fraction": "15731333/2215244",
    "decimal": 7.101399665228751
  },
  "header_bytes": 542,
  "data_bytes": 1966417,
  "payload_bits": 15731333,
  "archive_bytes": 1966959,
  "compression_ratio": 0.8879197957425908,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "53acdb7e"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`.

## konstituciya_rossiyskoy_federacii.pdf

`python3 main.py compress examples/task_1_3/konstituciya_rossiyskoy_federacii.pdf --output results/task_1_3/konstituciya_rossiyskoy_federacii.pdf.zmh --stats`

```json
{
  "output": "results/task_1_3/konstituciya_rossiyskoy_federacii.pdf.zmh",
  "original_bytes": 3608472,
  "model_symbols": 256,
  "entropy_bits_per_byte": "7.7312145252000420256921971653304888349931750609251557746506418508643652074690207",
  "average_code_length_bits": {
    "fraction": "14004071/1804236",
    "decimal": 7.76177340436617
  },
  "header_bytes": 542,
  "data_bytes": 3501018,
  "payload_bits": 28008142,
  "archive_bytes": 3501560,
  "compression_ratio": 0.9703719469071673,
  "ratio_definition": "archive_bytes/original_bytes",
  "original_crc32": "88a45886"
}
```

Восстановление: CRC32 пройдена; байты совпали; SHA-256 `02599c8c149dcd94ed3d284c6ff0ec3669c20a62fad8b061479dc63d649e0393`.

## Диагностика

- `foreign.zmh`: код 2, Ошибка: Чужой формат: ожидается сигнатура ZMH1
- `truncated.zmh`: код 2, Ошибка: Обрезанный архив: не хватает модели или сжатых данных
- `corrupted.zmh`: код 2, Ошибка: Повреждённый архив: неполное слово или неверный исходный размер

## Сводная таблица

| Файл | Исходных байтов | H, бит/байт | Средняя длина, бит | Заголовок | Данные | Архив | Архив / исходник |
|---|---:|---:|---:|---:|---:|---:|---:|
| russian.txt | 14920 | 3.834547 | 3.882038 | 106 | 7240 | 7346 | 0.492359 |
| english.txt | 8200 | 4.220156 | 4.253659 | 88 | 4360 | 4448 | 0.542439 |
| image.png | 49363 | 7.994624 | 7.999291 | 542 | 49359 | 49901 | 1.010899 |
| repeated.bin | 4096 | 0.000000 | 0.000000 | 32 | 0 | 32 | 0.007812 |
| empty.bin | 0 | 0.000000 | 0.000000 | 30 | 0 | 30 | — |
| unicode.txt | 4200 | 5.046315 | 5.085714 | 122 | 2670 | 2792 | 0.664762 |
| all_bytes.bin | 2048 | 8.000000 | 8.000000 | 542 | 2048 | 2590 | 1.264648 |
| attention_is_all_you_need.pdf | 2215244 | 7.071929 | 7.101400 | 542 | 1966417 | 1966959 | 0.887920 |
| konstituciya_rossiyskoy_federacii.pdf | 3608472 | 7.731215 | 7.761773 | 542 | 3501018 | 3501560 | 0.970372 |
