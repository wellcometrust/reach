"""
Minimal CLI for counting records in ES.
"""

from . import common

if __name__ == '__main__':
    parser = common.create_argument_parser(__doc__.strip())
    parser.add_argument('index_name')
    args = parser.parse_args()
    es = common.es_from_args(args)
    print(common.count_es(es, args.index_name))

