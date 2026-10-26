"""Private subprocess entry used by run_http_matrix; binds an OS-selected port."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from werkzeug.serving import make_server


if __name__ == '__main__':
    server = make_server('127.0.0.1', 0, create_app(), threaded=True)
    print(json.dumps({'port':server.server_port}), flush=True)
    server.serve_forever()
