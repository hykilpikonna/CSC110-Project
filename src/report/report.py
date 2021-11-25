import os.path
import webbrowser
from pathlib import Path

from flask import Flask, send_from_directory, Response

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


def serve_report() -> None:
    """
    Serve report page in a http server.

    :return: None
    """
    # Create flask app
    app = Flask(__name__)

    @app.route('/')
    def root() -> str:
        """
        Generate report, put the report into the HTML template

        :return: HTML report
        """
        html = read(str(src_dir.joinpath('report_page.html'))) \
            .replace('{{markdown}}', generate_report().replace('`', '\\`'))
        return html

    @app.route('/<path:path>')
    def res(path: str) -> Response:
        """
        Resources endpoint

        :param path: Path of the resource
        :return: File resource or 404
        """
        path = os.path.join(REPORT_DIR, path)
        return send_from_directory(Path(path).absolute().parent, Path(path).name)

    # Run app
    webbrowser.open("http://localhost:5000")
    app.run()


if __name__ == '__main__':
    serve_report()
