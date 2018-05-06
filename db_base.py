import redis
import config

cache_pool = redis.ConnectionPool(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD, db=0)
red = redis.Redis(connection_pool=cache_pool)

if __name__ == '__main__':
    red.set('faceset_token_downtown_test', '7161a5c44fabf6cfc010d64a90f12a98')