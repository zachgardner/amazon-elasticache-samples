import os
import json

import redis
import pymysql
from rediscluster import RedisCluster
import time
from reader import feed

class DB:
    def __init__(self, **params):
        params.setdefault("charset", "utf8mb4")
        params.setdefault("cursorclass", pymysql.cursors.DictCursor)

        self.mysql = pymysql.connect(**params)

    def query(self, sql):
        with self.mysql.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def record(self, sql, values):
        with self.mysql.cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.fetchone()


# Time to live for cached data
TTL = 10

# Read the Redis credentials from the REDIS_URL environment variable.
REDIS_URL = os.environ.get('REDIS_URL')

# Read the DB credentials from the DB_* environment variables.
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')

# Initialize the database
Database = DB(host='ecdemo.cluster-c2cgok5lktay.us-east-1.rds.amazonaws.com', user='ecdemo', password='', db='tutorial')

startup_nodes = [{"host": "microclusternossl.l8t0qy.clustercfg.use1.cache.amazonaws.com", "port": "6379"}]

Cache = RedisCluster( startup_nodes=startup_nodes,decode_responses=True, skip_full_coverage_check=True )

def fetch(sql, cache):
    """Retrieve records from the cache, or else from the database."""
    if cache:
        res = Cache.get(sql)

        if res:
            return json.loads(res)


    res = Database.query(sql)
    Cache.setex(sql, TTL, json.dumps(res))
    return res


def planet(id):
    """Retrieve a record from the cache, or else from the database."""
    key = f"planet:{id}"
    res = Cache.hgetall(key)

    if res:
        return res

    sql = "SELECT `id`, `name` FROM `planet` WHERE `id`=%s"
    res = Database.record(sql, (id,))

    if res:
        Cache.hmset(key, res)
        Cache.expire(key, TTL)

    return res


# Display the result of some queries
tic = time.perf_counter()
for i in range(0,1000):
    fetch("SELECT * FROM planet", cache=True)
# Display the result of some queries
toc = time.perf_counter()
print(f"Time from cache in {toc - tic:0.4f} seconds")
tic = time.perf_counter()
for i in range(0,1000):
    fetch("SELECT * FROM planet", cache=False)
toc = time.perf_counter()
print(f"Time from sql in {toc - tic:0.4f} seconds")
