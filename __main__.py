# Import twisted libraries
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor, task
from twisted.python import log

   
import sys
log.startLogging(sys.stdout)

# Import GrooveBot Classes
from groovebot import GrooveBot
#from groovebot.SearchContext import SearchContext
#reactor.callLater(2, GrooveBot.initiateSearch, SearchContext("NO SOURCE"), "paint it")

def p():
    status = GrooveBot.getStatus()
    if status:
        print status
    
t = task.LoopingCall(p)
t.start(1.0)

reactor.run()
