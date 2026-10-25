"""Запуск из корня репозитория: python main.py --help."""

import argparse
import json

from theory_inf.variant import VARIANT


def main() -> int:
    parser = argparse.ArgumentParser(description="Теория информации, ДЗ №1")
    parser.add_argument("--variant", action="store_true", help="параметры варианта")
    args = parser.parse_args()
    if args.variant:
        print(json.dumps(VARIANT.as_dict(), ensure_ascii=False, indent=2))
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
