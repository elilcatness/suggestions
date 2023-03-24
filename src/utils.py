from csv import DictWriter
from datetime import datetime
from itertools import product

from lxml import etree
from requests import ConnectTimeout, ReadTimeout
from torpy.http.requests import tor_requests_session

from src.constants import MAX_REPEATS, FIELDNAMES, DELIMITER
from src.exceptions import *


def get_ip(session):
    return session.get('https://httpbin.org/ip').json().get('origin')


def get_time():
    return datetime.now().strftime('%H:%M:%S')


def get_tree(session, url: str, **params):
    r = session.get(url, params=params)
    if r.status_code != 200:
        return r.status_code
    return etree.fromstring(r.text) if r.text else None


def get_suggestions(session, url: str, q: str, **params):
    tree = get_tree(session, url, q=q, **params)
    if isinstance(tree, int):
        return tree
    # noinspection PyUnresolvedReferences
    return [x for x in tree.xpath('//suggestion/@data') if x != q]


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


def log(message: str, logs_filename: str = 'logs.txt'):
    t = get_time()
    print(f'[{t}] {message}')
    with open(logs_filename, 'a', encoding='utf-8') as f:
        print(f'[{t}] {message}', file=f)


def parse(queries: list, symbols: str, repeats: int, used: list, processed_total: int,
          api_url: str, output_filename: str, api_params: dict = None):
    with tor_requests_session() as session:
        try:
            ip = get_ip(session)
        except (ConnectTimeout, ReadTimeout):
            return parse(queries, symbols, repeats, used, processed_total, api_url, output_filename,
                         api_params)
        log(f'Starting with IP: {ip}')
        processed = 0
        while queries:
            queued_query = queries.pop(0)
            if isinstance(queued_query, str):
                queued_query = [queued_query]
            for q in queued_query:
                processed += 1
                processed_total += 1
                if processed % 50 == 0:
                    log(f'Processed: {processed}')
                if q in used:
                    continue
                suggestions = get_suggestions(session, api_url, q, **api_params)
                if not suggestions:
                    continue
                if isinstance(suggestions, int):
                    log(f'Code: {suggestions}. Processed with {ip}: {processed}')
                    log('Refreshing IP...')
                    if not isinstance(queued_query, list):
                        queries.insert(0, queued_query)
                    queries.insert(0, q)  # проверить!
                    processed -= 1
                    processed_total -= 1
                    return parse(queries, symbols, repeats, used, processed_total,
                                 api_url, output_filename, api_params)
                with open(output_filename, 'a', newline='', encoding='utf-8') as f:
                    DictWriter(f, FIELDNAMES, delimiter=DELIMITER).writerows(
                        [{'Query': q, 'Suggestion': s} for s in suggestions])
                queries.extend(suggestions)
                queries.append(get_combinations(q, symbols, repeats))
                used.append(q)
