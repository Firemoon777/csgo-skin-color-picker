from pathlib import Path


def load(file: Path, encoding="utf-8") -> dict:
    """
    Loads json-like files as dicts of dicts
    """
    result = dict()
    context = []

    with file.open(encoding=encoding) as f:
        for line in f:
            line = line.strip()

            if line.startswith("//"):
                continue

            if line == "{":
                continue

            if line == "}":
                context.pop()
                continue

            count = line.count('"')
            if count == 2:
                context.append(line.strip('"').lower())

            if count == 4:
                data = line.split("\t")
                # Sometimes space is delimiter, so first space is ok
                if len(data) == 1:
                    data = line.split(" ", 1)

                key = data[0].strip().strip('"').lower()
                value = data[-1].strip().strip('"')

                ptr = result
                for entry in context:
                    if entry not in ptr:
                        ptr[entry] = dict()

                    ptr = ptr[entry]
                ptr[key] = value

    return result


def load_kv(file: Path, encoding="utf-8") -> dict:
    result = dict()

    with file.open(encoding=encoding) as f:
        for line in f:
            if line.startswith("#"):
                continue
            key, value = line.strip().split("=", 1)

            result[key] = value

    return result
