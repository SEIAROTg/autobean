import copy
import decimal
import io
from autobean.refactor import models, parser, printer

_FILE_COMPLEX = f'''\
2000-01-01 * "foo"
    Assets:Foo  -100.00 USD
    Assets:Bar   100.00 USD
'''

p = parser.Parser()
file = p.parse(_FILE_COMPLEX, models.File)


for token in file.token_store:
    print(f'!!! {token!r}')

for directive in file.directives:
    if isinstance(directive, models.Transaction) and directive.narration == 'foo':
        print(directive._meta.placeholder)
        print(directive._postings.placeholder)

        directive.meta['foo'] = 'bar'
        # directive.raw_postings.append(models.Posting.from_value('Assets:Foo', decimal.Decimal(100), 'USD'))


        # directive.meta['foo'] = 'bbb'
        # directive.postings[1].currency = 'GBP'
        # directive.postings[1].raw_price = models.TotalPrice.from_value(None, None)
        # directive.postings[0].inline_comment = 'Updated posting'
        # directive.postings.append(copy.deepcopy(directive.postings[0]))
        # directive.postings[2].number = decimal.Decimal('5.00')
        # assert directive.postings[2].raw_number is not None
        # directive.postings[2].raw_number *= decimal.Decimal(2)
        # directive.postings[2].raw_account.spacing_after = ' ' * 20
        # directive.postings.append(copy.deepcopy(directive.postings[1]))
        # directive.postings[-1].number = decimal.Decimal('-10.00')


for token in file.token_store:
    print(f'!!! {token!r}')

print(printer.print_model(file, io.StringIO()).getvalue())
