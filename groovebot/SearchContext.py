from datetime import datetime

class SearchContext(object):
    def __init__(self, user, source, state=None):
        self.user = user
        self.source = source
        self.search_time = datetime.now()
        self.state = state
