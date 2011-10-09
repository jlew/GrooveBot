# Import twisted libraries
from twisted.internet import reactor
from twisted.python import log

# Import GrooveBot Classes
from groovebot.GrooveBot import GrooveBot
import sys

if __name__ == "__main__":
    #log.startLogging(open('log.txt', 'w'))
    log.startLogging(sys.stdout)

    from groovebot.SearchContext import SearchContext

    g = GrooveBot()
    reactor.callLater(2, g.initiateSearch, SearchContext("user",None), "TEST")
    reactor.run()
