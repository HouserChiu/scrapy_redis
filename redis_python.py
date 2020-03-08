import redis
import json
import pymongo
redis_client = redis.Redis(host='192.168.0.103', port=6379, db=0)
mongo_client = pymongo.MongoClient()
collection = mongo_client.room.sfw


while True:
    key, data = redis_client.blpop(['sfw:items'])
    print(key)
    d = json.loads(data)
    collection.insert(d)