"""Учебный скрипт обучения."""

import sys


def load_config(path):
    # TODO: поддержать значения по умолчанию
    with open(path) as handle:
        return handle.read()


def main():
    print("training", sys.argv[1:])


if __name__ == "__main__":
    main()
