from groovebot.ActionType import MediaController
from groovebot.GrooveBot import queue
class ConsoleReader(MediaController):
    
    def searchCompleted(self, context, search_results):
        for media_item in search_results:
            print "Searh Result: \"%s\" by \"%s\" on \"%s\"." % \
                (media_item.title, media_item.artist, media_item.album)
        
        # play last one DEBUG!!!!!
        if media_item:
            queue(media_item)