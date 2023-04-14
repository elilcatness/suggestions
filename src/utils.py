import os.path
from csv import DictWriter
from datetime import datetime
from itertools import product

from lxml import etree
from requests import ConnectTimeout, ReadTimeout
from torpy.http.requests import tor_requests_session

from src.constants import MAX_REPEATS, FIELDNAMES, DELIMITER, THREADS_FOLDER
from src.exceptions import *


def get_ip(session):
    return session.get('https://httpbin.org/ip').json().get('origin')


def get_time():
    return datetime.now().strftime('%H:%M:%S')


def get_time_from_secs(secs: int):
    return ':'.join([str(n).rjust(2, '0') for n in [secs // 3600, secs // 60 % 60, secs % 60]])


def number_filename(filename: str, n: int):
    parts = filename.split('.')
    return f'{".".join(parts[:-1])}{n}.{parts[-1]}'


def get_tree(session, url: str, **params):
    try:
        r = session.get(url, params=params)
    except ConnectionResetError:
        return 666
    if r.status_code != 200:
        return r.status_code
    return etree.fromstring(r.text) if r.text else None


def get_suggestions(session, url: str, q: str, **params):
    tree = get_tree(session, url, q=q, **params)
    if isinstance(tree, int):
        return tree
    # noinspection PyUnresolvedReferences
    return [x.strip().strip('\n') for x in tree.xpath('//suggestion/@data') if x != q]


def get_combinations(text: str, symbols: str, repeats: int):  # mode: str = 'before'
    if repeats > MAX_REPEATS:
        raise TooManyRepeatsException('Время исполнения программы улетает в стратосферу. '
                                      f'Повторов должно быть не более {MAX_REPEATS}')
    if len(symbols) != len(set(symbols)):
        raise NotUniqueSymbolsException('Символы перебора должны быть уникальны!')
    if not text:
        raise CombinatonException('Пустой текст')
    a = text.split()
    positions = len(a) + 1
    for r in range(1, repeats + 1):
        for comb in product(symbols, repeat=r):
            comb = ''.join(comb)
            for i in range(positions):
                a0 = a[:]
                a0.insert(i, comb)
                yield ' '.join(a0)


def log(message: str, logs_filename: str = 'logs.txt', thread_number: int = None):
    t = get_time()
    print(f'[{t}]{f" <Thread {thread_number}> " if thread_number else " "}{message}')
    if thread_number:
        logs_filename = os.path.join(THREADS_FOLDER, number_filename(logs_filename, thread_number))
    with open(logs_filename, 'a', encoding='utf-8') as f:
        print(f'[{t}] {message}', file=f)


def process(queries: list, symbols: str, repeats: int, used: list, processed_total: int,
            api_url: str, output_filename: str, api_params: dict = None,
            thread_number: int = None):
    further_queries = []
    if thread_number:
        output_filename = os.path.join(
            THREADS_FOLDER, number_filename(output_filename, thread_number))
    try:
        with tor_requests_session() as session:
            try:
                ip = get_ip(session)
            except (ConnectTimeout, ReadTimeout):
                return queries, processed_total
            log(f'Starting with IP: {ip}', thread_number=thread_number)
            processed = 0
            while queries:
                queued_query = queries.pop(0)
                if isinstance(queued_query, str):
                    queued_query = [queued_query]
                for q in queued_query:
                    processed += 1
                    processed_total += 1
                    if processed % 50 == 0:
                        log(f'Processed: {processed}', thread_number=thread_number)
                    if q in used:
                        continue
                    try:
                        suggestions = get_suggestions(session, api_url, q, **api_params)
                    except ConnectionResetError:
                        suggestions = 666
                    if not suggestions:
                        continue
                    if isinstance(suggestions, int):
                        log(f'Code: {suggestions}. Processed with {ip}: {processed}',
                            thread_number=thread_number)
                        log('Refreshing IP...', thread_number=thread_number)
                        if not isinstance(queued_query, list):
                            queries.insert(0, queued_query)
                        queries.insert(0, q)
                        processed -= 1
                        processed_total -= 1
                        return queries, processed_total, further_queries
                    with open(output_filename, 'a', newline='', encoding='utf-8') as f:
                        DictWriter(f, FIELDNAMES, delimiter=DELIMITER).writerows(
                            [{'Query': q, 'Suggestion': s} for s in suggestions])
                    further_queries.extend(suggestions)
                    further_queries.append(get_combinations(q, symbols, repeats))
                    used.append(q)
            return queries, processed_total, further_queries
    except ConnectionResetError:
        return queries, processed_total, further_queries
