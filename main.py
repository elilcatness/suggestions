import os
from csv import DictWriter
from shutil import rmtree
from threading import Thread
from time import time
from warnings import filterwarnings

from dotenv import load_dotenv

from src.constants import *
from src.utils import log, get_time, get_time_from_secs, process, number_filename


class Parser:
    def __init__(self, queries: list, symbols: str, repeats: int, output_filename: str):
        self._queries = queries[:]
        self.symbols = symbols
        self.repeats = repeats
        self.output_filename = output_filename
        self.processed = 0
        self.used = []

    def job(self, queries: list, thread_n: int):
        filterwarnings(action='ignore')
        while queries:
            queries, processed, further_queries = process(
                queries, self.symbols, self.repeats,
                self.used, 0, API_URL,
                self.output_filename, DEFAULT_API_PARAMS, thread_n)
            self.processed += processed
            self._queries += further_queries

    def has_queries(self):
        return bool(self._queries)

    def get_queries(self):
        return self._queries[:]

    def pop_queries(self):
        queries = self._queries[:]
        self._queries = []
        return queries


def main():
    queries_filename = os.getenv('queries_filename', 'queries.txt')
    symbols_filename = os.getenv('symbols_filename', 'symbols.txt')
    output_filename = os.getenv('output_filename', 'output.csv')
    with open('logs.txt', 'w', encoding='utf-8') as f:
        print(f'[{get_time()}] The script has started', file=f)
    with open(queries_filename, encoding='utf-8') as f:
        initial_queries = [x.strip().strip('\n') for x in f]
    if not initial_queries:
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
    max_process_count = 0
    while not max_process_count:
        try:
            max_process_count = int(input('Введите количество потоков: '))
            assert max_process_count > 0
            break
        except (ValueError, AssertionError):
            print('Должно быть введено натуральное число')
    if os.path.exists(THREADS_FOLDER):
        if input(f'Папка {THREADS_FOLDER} очистится. '
                 f'Вы хотите продолжить? (y\\n): ').lower() != 'y':
            return
        rmtree(THREADS_FOLDER)
    os.mkdir(THREADS_FOLDER)
    for i in range(1, max_process_count + 1):
        with open(os.path.join(THREADS_FOLDER, number_filename(
                output_filename, i)), 'w', newline='', encoding='utf-8') as f:
            DictWriter(f, FIELDNAMES, delimiter=';').writeheader()
    parser = Parser(initial_queries, symbols, repeats, output_filename)
    st_time = time()
    chunks = 0
    last_processed = 0
    while parser.has_queries():
        chunks += 1
        queries = parser.pop_queries()
        count = max_process_count if len(queries) >= max_process_count else len(queries)
        processes = []
        log(f'Starting Chunk #{chunks}. Threads: {count}')
        for i in range(count):
            processes.append(Thread(target=parser.job, args=(queries[i::count], i + 1)))
            processes[-1].start()
        for proc in processes:
            proc.join()
        log(f'Chunk #{chunks} is over. Threads: {count}. '
            f'Processed: {parser.processed - last_processed}')
    log(f'Completed in {get_time_from_secs(int(time() - st_time))}')
    log(f'Totally processed: {parser.processed}')


if __name__ == '__main__':
    load_dotenv()
    main()
