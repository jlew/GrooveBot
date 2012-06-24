# Import twisted libraries
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
from twisted.python import log

   
import sys
log.startLogging(sys.stdout)

# Import GrooveBot Classes
from groovebot import GrooveBot
from groovebot.SearchContext import SearchContext

reactor.callLater(2, GrooveBot.initiateSearch, SearchContext("NO SOURCE"), "TEST")

def p():
    print GrooveBot.getStatus()
    reactor.callLater(2, p)
reactor.callLater(2, p)
reactor.run()
