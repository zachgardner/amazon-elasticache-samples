import redis
import random
import string
from rediscluster import RedisCluster

startup_nodes = [{"host": "microclusternossl.l8t0qy.clustercfg.use1.cache.amazonaws.com", "port": "6379"}]

redisClient = RedisCluster( startup_nodes=startup_nodes,decode_responses=True, skip_full_coverage_check=True )

def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

redisClient.set("me", "you")
redisPing = redisClient.ping()
print(redisClient.get("me"))
print(redisPing)

players = "Players"

print("Simulating Data")
for i in range(1,1000):
    score = random.randint(0, 10001) 
    playername = random_generator()
    mapping = {
        playername : score
    }
    redisClient.zadd(players, mapping)
    
print("Simulaiton Done")


print(redisClient.zrevrange(players, 0, 5, withscores=True))