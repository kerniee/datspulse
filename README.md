# DatsPulse

Решение команды **Соло боло** (команда из одного человека) для геймтона DatsPulse которое заняло 9 место в финальном рейтинге. Считаю Cursor своим сокомандником.

## Команды

`uv run ./src/main.py`
`uv run pytest`

## Профилирование

`python -m cProfile -o output.pstats src/main.py`
`uvx snakeviz .\output.pstats`
