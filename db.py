import os
import pymongo

if os.getenv("MONGODB_URI"):
    mongo_client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
else:
    mongo_client = pymongo.MongoClient(
        host=os.getenv("MONGODB_HOST", "localhost"),
        port=int(os.getenv("MONGODB_PORT", 27017))
    )