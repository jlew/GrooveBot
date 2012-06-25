# Import twisted libraries
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
from twisted.python import log
from twisted.python.logfile import LogFile

   
log.startLogging(LogFile("tw.log","./"))

# Import GrooveBot Classes
from groovebot import GrooveBot

reactor.run()
