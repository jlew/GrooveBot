from groovebot.ActionType import MediaController
from groovebot.GrooveBot import queue, initiateSearch
from groovebot.SearchContext import SearchContext
from twisted.internet import reactor

class ConsoleReader(MediaController):
    def __init__(self):
#        def doSearch():
#            while(True):
#                searchText = raw_input(">")
#                initiateSearch(SearchContext(self), searchText)
#            
#        
#        reactor.callInThread(doSearch)
        pass
    def searchCompleted(self, context, search_results):
        media_item = None
        for media_item in search_results:
            print "Searh Result: \"%s\" by \"%s\" on \"%s\"." % \
                (media_item.title, media_item.artist, media_item.album)
        
        # play last one DEBUG!!!!!
        if media_item:
            queue(media_item)