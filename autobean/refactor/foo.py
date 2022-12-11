import cProfile
from autobean.refactor import parser as parser_lib
from autobean.refactor import models


_FILE_COMPLEX = '''\
; comment
2000-01-01 * "payee" "narration" #tag-a #tag-b ^link-a
    meta-a: 1
    ; comment
    meta-b: 2
    ; comment
    Assets:Foo       100.00 USD
        ; comment
        meta-c: 3
    Assets:Bar      -100.00 DSU {{}}
; comment

''' * 1000

if __name__ == '__main__':
    parser = parser_lib.Parser()
    f = parser.parse(_FILE_COMPLEX, models.File)
    for token in f.token_store:
        print(f'!! {token!r}')
    # cProfile.run('parser.parse(_FILE_COMPLEX, models.File)', 'foo.prof')
