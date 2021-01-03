import sys
from beancount import loader
from beancount.parser import printer


def main():
    entries, errors, options = loader.load_file(sys.argv[1])

    for entry in entries:
        printer.print_entry(entry)

    print(options, file=sys.stderr)

    for error in errors:
        printer.print_error(error, file=sys.stderr)


if __name__ == '__main__':
    main()
