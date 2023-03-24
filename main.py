import os
from csv import DictWriter
from time import time

from dotenv import load_dotenv

from src.constants import *
from src.utils import log, get_time, get_time_from_secs, process


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
    used = []
    processed_total = 0
    st_time = time()
    while queries:
        queries, processed_total = process(queries, symbols, repeats, used, processed_total,
                                           API_URL, output_filename, DEFAULT_API_PARAMS)
    log(f'Completed in {get_time_from_secs(int(time() - st_time))}')
    log(f'Totally processed: {processed_total}')


if __name__ == '__main__':
    load_dotenv()
    main()
