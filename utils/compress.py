def compress_plan(plan: str) -> str:
    lines = plan.split('\n')
    compressed = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('|'):
            compressed.append(line)
        elif line and line[0].isdigit() and '.' in line[:3]:
            compressed.append(line)
        elif line.startswith('##') or line.startswith('Phase'):
            compressed.append(line)
        elif line.startswith('-') and any(
            kw in line for kw in [
                'Fill', 'Parse', 'Strip', 'Encode',
                'Scale', 'Extract', 'Drop', 'Flag',
                'MEAN', 'MEDIAN', 'MODE', 'INCLUDED',
                'SKIPPED', 'TARGET', 'NUMERIC', 'TEMPORAL'
            ]
        ):
            compressed.append(line)
    return '\n'.join(compressed)