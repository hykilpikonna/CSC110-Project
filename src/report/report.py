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
        if not line.startswith('@include'):
            continue

        path = line[line.index('`') + 1:]
        path = path[:path.index('`')]
        md[i] = read(REPORT_DIR + path)

        # Cut lines
        # Format: @include-cut `path` <start, inclusive> [end, not inclusive]
        if line.startswith('@include-cut'):
            args = [int(i) for i in line.split()[2:]]
            if len(args) == 1:
                md[i] = '\n'.join(md[i].split('\n')[args[0]:])
            if len(args) == 2:
                md[i] = '\n'.join(md[i].split('\n')[args[0]:args[1]])

        # Specific lines
        # Format: @include-lines `path` <...lines>
        # Example: @include-lines `path` 1 2 5
        if line.startswith('@include-lines'):
            args = [int(i) for i in line.split()[2:]]
            lines = md[i].split('\n')
            lines = [lines[ln] for ln in range(len(lines)) if ln in args]
            md[i] = '\n'.join(lines)


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
