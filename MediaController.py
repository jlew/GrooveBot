from PluginFramework import MediaControllerMount

class MediaController(object):
    __metaclass__ = MediaControllerMount
    def __init__(self):
        pass

    def statusChange(self, status):
        print "Status Changed: ", status

    def searchCompleted(self, search_results):
        print "Search Completed: ", search_results
