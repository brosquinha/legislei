import os

from legislei import controllers
from legislei import settings
from legislei.app import app
from legislei.cron import scheduler
from legislei.db import db_connect

if __name__ == '__main__':
    app.debug = os.environ.get('DEBUG', 'True') in ['True', 'true']
    port = int(os.environ.get('PORT', 5000))
    scheduler.start()
    db_connect(
        db_name=os.environ.get("MONGODB_DBNAME"),
        db_uri=os.environ.get("MONGODB_URI"),
        db_host=os.environ.get("MONGODB_HOST", "localhost"),
        db_port=os.environ.get("MONGODB_PORT", 27017)
    )
    app.run(host='0.0.0.0', port=port, threaded=True)
