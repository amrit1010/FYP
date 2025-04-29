from django.test import TestCase
from django.conf import settings
import redis

class RedisConnectionTestCase(TestCase):
    def test_connection_success_redis(self):
        try:
            r = redis.StrictRedis(
                host="69.69.6y9.69",
                port=6379,
                db=0,
                decode_responses=True
            )
            result = r.ping()
        except redis.exceptions.ConnectionError:
            result = False

        self.assertFalse(result, "Redis connection failed")
        print("Test Failed : Redis Connecton Failed")