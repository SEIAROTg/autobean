from typing import Dict, Optional


def extract_from_file(filename: str) -> dict[int, str]:
    ret = {}
    with open(filename) as f:
        for i, line in enumerate(f):
            narration = extract_from_line(line)
            if narration is not None:
                ret[i + 1] = narration
    return ret


def extract_from_line(s: str) -> Optional[str]:
    segs = s.strip().split(';')
    return segs[2].strip() if len(segs) > 2 and not segs[1] else None
