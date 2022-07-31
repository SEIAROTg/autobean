def range_from_index(index: int | slice, length: int) -> range:
    if isinstance(index, int):
        try:
            index = range(length)[index]
        except IndexError:
            raise IndexError('list assignment index out of range')
        return range(index, index + 1)
    return range(length)[index]


def slice_from_range(r: range) -> slice:
    stop = r.stop if r.stop != -1 else None
    return slice(r.start, stop, r.step)
