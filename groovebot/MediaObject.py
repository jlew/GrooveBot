class MediaObject(object):
    def __init__(self, mediaSource, mid, title=None, artist=None, album=None):
        self.source = mediaSource
        self.mid = mid
        self.artist=artist
        self.album=album
        self.title=title
        
    def __str__(self):
        return "%s by %s(%s)" % (self.title, self.artist, self.album)
