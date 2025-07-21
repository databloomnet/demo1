# rate_limiter.py
from collections import deque 
import time


class RateLimiter:
    def __init__(self, max_requests, interval_sec):
        self.max_requests = max_requests
        self.interval = interval_sec
        self.timestamps = deque() # double ended queue 

    def allow(self):
        now = time.time()
        while self.timestamps and now - self.timestamps[0] > self.interval:
            # while 1+ timestamps and the oldest timestamp is greater than interval seconds ago... pop it off
            self.timestamps.popleft()

        # room for another request?
        if len(self.timestamps) < self.max_requests:
            self.timestamps.append(now)
            return True
        
        # throttle
        return False

    def status(self):
        # delete old timestamps
        now = time.time()
        while self.timestamps and now - self.timestamps[0] > self.interval:
            self.timestamps.popleft()

        return f"{len(self.timestamps)} of {self.max_requests} over {self.interval} seconds"

