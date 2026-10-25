# Источники

## Дополнительная теория задачи 1.2

- [Chen, Effros, Kostina — Lossless Source Coding](https://par.nsf.gov/servlets/purl/10232706).
  Источник поправки третьего порядка, используемой при разборе R=H и ε=1/2;
  программный код из статьи не заимствовался.

## Реальные входные документы архиватора

- [Vaswani et al. — Attention Is All You Need, arXiv:1706.03762v7](https://arxiv.org/pdf/1706.03762v7).
  Оригинальный PDF без изменений: `examples/task_1_3/attention_is_all_you_need.pdf`.
  Дата получения, размер и SHA-256 — `examples/task_1_3/real_sources.json`.
- `examples/task_1_3/konstituciya_rossiyskoy_federacii.pdf` — Конституция РФ,
  PDF предоставлен пользователем 25.10.2026. Исходный URL и редакция не установлены.
  55 страниц без текстового слоя; исходный PDF используется без изменений.
  Размер и SHA-256 зафиксированы в `examples/task_1_3/real_sources.json`.

## Код

- почти весь код написал Codex, но я сам говорил ему что и как писать, а не "сделай все"