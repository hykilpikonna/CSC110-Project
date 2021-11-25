import os.path
from pathlib import Path

from flask import Flask, send_from_directory

from constants import REPORT_DIR
from utils import read

# Constants
src_dir = Path(os.path.realpath(__file__)).parent


def generate_report() -> str:
    """
    Compile the report document and generate a markdown report

    :return: Markdown report
    """
    # Load markdown
    md = read(str(src_dir.joinpath('report_document.md'))).replace('\r\n', '\n').split('\n')

    # Process @include statements
    for i in range(len(md)):
        line = md[i]
        if line.startswith('@include'):
            line = line[line.index('`') + 1:]
            line = line[:line.index('`')]
            md[i] = read(REPORT_DIR + line)

    return '\n'.join(md)


    return markdown.markdown('\n'.join(md), extensions=['tables'])


if __name__ == '__main__':
    print(generate_report())
