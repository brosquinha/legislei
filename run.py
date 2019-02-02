import os

from legislei import settings
from legislei.app import app
from legislei.cron import scheduler

if __name__ == '__main__':
    app.debug = os.environ.get('DEBUG', 'True') in ['True', 'true']
    port = int(os.environ.get('PORT', 5000))
    scheduler.start()
    app.run(host='0.0.0.0', port=port, threaded=True)
