import os
from csv import DictWriter

from dotenv import load_dotenv

from src.constants import *
from src.utils import parse, get_time


def main():
    queries_filename = os.getenv('queries_filename', 'queries.txt')
    symbols_filename = os.getenv('symbols_filename', 'symbols.txt')
    output_filename = os.getenv('output_filename', 'output.csv')
    with open('logs.txt', 'w', encoding='utf-8') as f:
        print(f'[{get_time()}] The script has started', file=f)
    with open(queries_filename, encoding='utf-8') as f:
        queries = [x.strip() for x in f]
    if not queries:
        raise Exception('Нет запросов')
    with open(symbols_filename, encoding='utf-8') as f:
        symbols = f.read().strip()
    repeats = None
    while repeats is None:
        try:
            repeats = int(input('Введите длину перебора: '))
            assert 0 <= repeats <= MAX_REPEATS
            break
        except (ValueError, AssertionError):
            print(f'Должно быть введено целое число от 0 до {MAX_REPEATS}')
    with open(output_filename, 'w', newline='', encoding='utf-8') as f:
        DictWriter(f, FIELDNAMES, delimiter=DELIMITER).writeheader()
    parse(queries, symbols, repeats, [], 0, API_URL, output_filename, DEFAULT_API_PARAMS)


if __name__ == '__main__':
    load_dotenv()
    main()
