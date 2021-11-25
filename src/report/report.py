import os.path

import markdown

from constants import SRC_DIR, REPORT_DIR
from utils import read


def generate_report() -> str:
    """
    Do data visualization and generate a HTML report

    :return: HTML
    """
    # Load markdown
    md = read(f'{SRC_DIR}/report_document.md').replace('\r\n', '\n').split('\n')

    # Process @include statements
    for i in range(len(md)):
        line = md[i]
        if line.startswith('@include'):
            line = line[line.index('`') + 1:]
            line = line[:line.index('`')]
            md[i] = read(line)

    return markdown.markdown('\n'.join(md), extensions=['tables'])


if __name__ == '__main__':
    print(generate_report())
