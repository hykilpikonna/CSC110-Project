import markdown

from constants import SRC_DIR
from utils import read


def generate_report() -> str:
    """
    Do data visualization and generate a HTML report

    :return: HTML
    """
    return markdown.markdown(read(f'{SRC_DIR}/report_document.md'))


if __name__ == '__main__':
    print(generate_report())
