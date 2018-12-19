import os
import settings
import pymongo

if os.environ.get("MONGODB_URI"):
    mongo_client = pymongo.MongoClient(os.environ.get("MONGODB_URI"))
    mongo_db = mongo_client.get_database()
else:
    mongo_client = pymongo.MongoClient(
        host=os.environ.get("MONGODB_HOST", "localhost"),
        port=int(os.environ.get("MONGODB_PORT", 27017))
    )
    mongo_db = mongo_client.get_database(os.environ.get("MONGODB_DBNAME"))