"""Мелкие вспомогательные функции."""


def count_lines(path):
    with open(path) as handle:
        return sum(1 for _ in handle)
