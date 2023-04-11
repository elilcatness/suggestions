import os
from shutil import rmtree
from csv import DictWriter
from time import time
from multiprocessing import Pool

from dotenv import load_dotenv

from src.constants import *
from src.utils import log, get_time, get_time_from_secs, process, number_filename

processed_total = 0
used = []


def job(task: dict):
    global processed_total, used
    while task['queries']:
        task['queries'], processed = process(task['queries'], task['symbols'], task['repeats'],
                                             used, processed_total, API_URL,
                                             task['output_filename'], DEFAULT_API_PARAMS,
                                             task['thread_n'])
        processed_total += processed


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
    process_count = 0
    while not process_count:
        try:
            process_count = int(input('Введите количество потоков: '))
            assert process_count > 0
            break
        except (ValueError, AssertionError):
            print('Должно быть введено натуральное число')
    if process_count > len(queries):
        process_count = len(queries)
    if process_count > 1:
        if os.path.exists(THREADS_FOLDER):
            if input(f'Папка {THREADS_FOLDER} очистится. '
                     f'Вы хотите продолжить? (y\\n): ').lower() != 'y':
                return
            rmtree(THREADS_FOLDER)
        os.mkdir(THREADS_FOLDER)
        for i in range(1, process_count + 1):
            with open(os.path.join(THREADS_FOLDER, number_filename(
                    output_filename, i)), 'w', newline='', encoding='utf-8') as f:
                DictWriter(f, FIELDNAMES, delimiter=';').writeheader()
    tasks = [{'queries': [queries[j] for j in range(i, len(queries), process_count)],
              'symbols': symbols, 'repeats': repeats, 'output_filename': output_filename,
              'thread_n': i + 1}
             for i in range(process_count)]
    st_time = time()
    Pool(processes=process_count).map(job, tasks)
    log(f'Completed in {get_time_from_secs(int(time() - st_time))}')
    log(f'Totally processed: {processed_total}')


if __name__ == '__main__':
    load_dotenv()
    main()
