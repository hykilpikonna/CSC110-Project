import base64
import json
import os.path
import traceback
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

    # Process line by line
    for i in range(len(md)):
        line = md[i]
        if not line.startswith('@include'):
            continue

        # Process @include statements
        try:
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

        # Handle errors. (It prompts "too broad an exception clause" but I actually need to catch
        # every possible exception.)
        except Exception as e:
            md[i] = f"<pre class=\"error\">" \
                    f"\nInvalid @include statement. \n{traceback.format_exc()}" \
                    f"</pre>"

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
        # Generate markdown report and JSON encode it (which works as JS code! amazing
        md_json = json.dumps({'content': generate_report()})
        # Inject into HTML
        html = read(str(src_dir.joinpath('report_page.html'))) \
            .replace('`{{markdown}}`', md_json)
        # Return
        return html

    @app.route('/<path:path>')
    def res(path: str) -> Response:
        """
        Resources endpoint. This maps report queries to the report directory

        :param path: Path of the resource
        :return: File resource or 404
        """
        return send_from_directory(Path(REPORT_DIR).absolute(), path)

    @app.route('/resources/<path:path>')
    def js_res(path: str) -> Response:
        """
        JS Resource endpoint. This maps JS and CSS queries to the resources directory

        :param path: Path of the resource
        :return: File resource or 404
        """
        return send_from_directory(os.path.join(src_dir, 'resources'), path)

    # Run app
    webbrowser.open("http://localhost:5000")
    app.run()


if __name__ == '__main__':
    serve_report()
