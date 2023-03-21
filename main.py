import os
from itertools import product
from dotenv import load_dotenv

from utils import get_suggestions
from constants import *


def main():
    queries_filename = os.getenv('queries_filename', 'queries.txt')
    symbols_filename = os.getenv('symbols_filename', 'symbols.txt')
    output_filename = os.getenv('output_filename', 'output.csv')
    with open(queries_filename, encoding='utf-8') as f:
        queries = [x.strip() for x in f]
    mode = None
    while mode is None:
        try:
            mode = int(input('Выберите вариант подстановок:\n1 – подставить только в начало\n'
                             '2 – подставить только в конец'
                             '\n3 – подставить везде (начало, после каждого слова, конец)\n'))
            assert 1 <= mode <= 3
        except (ValueError, AssertionError):
            print('Должно быть введено число 1, 2 или 3')
    # print(f'Total count: {len(queries)}')
    # for i in range(len(queries)):
    #     count = len(get_suggestions(API_URL, queries[i], **DEFAULT_API_PARAMS))
    #     print(f'{i + 1}. {count}')


if __name__ == '__main__':
    load_dotenv()
    main()
