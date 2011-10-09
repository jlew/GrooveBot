from MediaSource import MediaSource


import time
class DummySource(MediaSource):
    def search(self, text):
        print "text"
        time.sleep(5)
        return []
