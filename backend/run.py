import sys
import os
from app.common import clean_directories, start_periodic_cleanup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app import create_app

clean_directories()
start_periodic_cleanup()

app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)