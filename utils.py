from itertools import product
import requests as req
from lxml import etree

from constants import MAX_REPEATS
from exceptions import *


def get_tree(url: str, **kwargs):
    r = req.get(url, **kwargs)
    return etree.fromstring(r.text) if r and r.text else None


def get_suggestions(url: str, q: str, **params):
    tree = get_tree(url, params={'q': q, **params})
    return tree.xpath('//suggestion/@data')


def get_combinations(text: str, symbols: str, repeats: int):  # mode: str = 'before'
    if repeats > MAX_REPEATS:
        raise TooManyRepeatsException('Время исполнения программы улетает в стратосферу. '
                                      f'Повторов должно быть не более {MAX_REPEATS}')
    if len(symbols) != len(set(symbols)):
        raise NotUniqueSymbolsException('Символы перебора должны быть уникальны!')
    if not text:
        raise CombinatonException('Пустой текст')
    yield text
    a = text.split()
    positions = len(a) + 1
    for r in range(1, repeats + 1):
        for comb in product(symbols, repeat=r):
            comb = ''.join(comb)
            for i in range(positions):
                a0 = a[:]
                a0.insert(i, comb)
                yield ' '.join(a0)


if __name__ == '__main__':
    main()