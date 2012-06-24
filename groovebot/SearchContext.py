from datetime import datetime

class SearchContext(object):
    def __init__(self, source, state=None):
        self.source = source
        self.search_time = datetime.now()
        self.state = state
