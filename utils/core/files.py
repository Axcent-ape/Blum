def get_all_lines(filepath: str):
    with open(filepath, 'r') as file:
        lines = file.readlines()

    if not lines:
        return []

    return [line.strip() for line in lines]
