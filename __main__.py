# Import twisted libraries
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor, task
from twisted.python import log
from twisted.python.logfile import LogFile

   

log.startLogging(LogFile("tw.log","./"))

# Import GrooveBot Classes
from groovebot import GrooveBot
#from groovebot.SearchContext import SearchContext
#reactor.callLater(2, GrooveBot.initiateSearch, SearchContext("NO SOURCE"), "paint it")

#def p():
#    status = GrooveBot.getStatus()
#    if status:
#        print status
#    
#t = task.LoopingCall(p)
#t.start(1.0)

reactor.run()
