from groovebot.ActionType import MediaController
from groovebot.GrooveBot import queue, initiateSearch, getStatus, getQueuedItems
from groovebot.SearchContext import SearchContext
from twisted.internet import reactor, task
from twisted.python import log

class ConsoleReader(MediaController):
    def __init__(self):
        class logObserver:
            def __init__(self, con):
                self.con = con

            def emit(self, eventDict):
                self.con.addLine(eventDict['message'][0])

        stdscr = curses.initscr() # initialize curses
        self.screen = Screen(stdscr)   # create Screen object
        log.addObserver(logObserver(self.screen).emit)
        stdscr.refresh()
        reactor.addReader(self.screen) # add screen object as a reader to the reactor
        
        task.LoopingCall(self.screen.updateDisplay).start(.25)

#        def doSearch():
#            while(True):
#                searchText = raw_input(">")
#                initiateSearch(SearchContext(self), searchText)
#            
#        
#        reactor.callInThread(doSearch)

    def searchCompleted(self, context, search_results):
        media_item = None
        for media_item in search_results:
            print "Searh Result: \"%s\" by \"%s\" on \"%s\"." % \
                (media_item.title, media_item.artist, media_item.album)
        
        # play last one DEBUG!!!!!
        if media_item:
            queue(media_item)
            
    def queueUpdated(self, action, queueObject):
        print "Queue %s @%s" % (action,queueObject)
        self.screen.updateQueue()

# System Imports
import curses

# Twisted imports
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.python import log

class TextBlock:
    def __init__(self, parent_screen, title, x, y, width, height, scroll=True):
        self.screen = parent_screen.derwin(height, width, y, x)
        self.title = title.center(width-2)
        self.messages = []
        self.height = height
        self.width = width
        self.scroll = scroll
        

    def add_message(self, message):
        self.messages.append(message[:self.width-4].ljust(self.width-4))

    def clear_messages(self):
        self.messages = []

    def draw(self):
        self.screen.clear()
        self.screen.box()
        self.screen.addstr(1,1, self.title, curses.A_BOLD)
        self.screen.hline(2,1, curses.ACS_HLINE, self.width - 2)
        if self.scroll:
            msg = self.messages[-(self.height - 4):]
        else:
            msg = self.messages[0:(self.height - 4)]
        for i, msg in enumerate( msg ):
            self.screen.addstr(i + 3, 2, msg)
        self.screen.refresh()

class ProgressBar:
    def __init__(self, parent_screen, x,y,width, color1, color2, title=None):
        self.screen = parent_screen.derwin(3, width+2, y, x)
        self.title = title
        # Find length of string in middle for color change effect
        if title:
            # "TITLE xxx%"
            self.pos = (width-(len(self.title)+6))/2
        else:
            # 4 = "xxx%"
            self.pos = (width-4)/2
        self.value = 0
        self.wper = width/100.0
        self.color1 = color1
        self.color2 = color2


    def set_value(self, value):
        self.value = value

    def draw(self):
        if self.title:
            display_str = (" " * self.pos) + ("%s %#3d%%" % (self.title,self.value)) + (" " * self.pos)
        else:
            display_str = (" " * self.pos) + ("%#3d%%" % self.value) + (" " * self.pos)
        pos_str = int(self.wper*self.value)
        
        self.screen.addstr(1,1, display_str[:pos_str], self.color1 )
        self.screen.addstr(1,1+pos_str, display_str[pos_str:], self.color2 )
        self.screen.refresh()

class CursesStdIO:
    """fake fd to be registered as a reader with the twisted reactor.
       Curses classes needing input should extend this"""

    def fileno(self):
        """ We want to select on FD 0 """
        return 0

    def doRead(self):
        """called when input is ready"""

    def logPrefix(self): return 'CursesClient'

class Screen(CursesStdIO):
    def __init__(self, stdscr):
        self.stdscr = stdscr

        self.searchText = ''

        # set screen attributes
        self.stdscr.nodelay(1) # this is used to make input calls non-blocking
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(1)
        curses.curs_set(0)     # no annoying mouse cursor

        self.rows, self.cols = self.stdscr.getmaxyx()
        curses.start_color()

        splitPoint = int((self.cols-4) * .80)
        print self.cols, splitPoint
        self.logBox = TextBlock(self.stdscr, "Log", 1,2, splitPoint,  self.rows-4)
        self.queueBox = TextBlock(self.stdscr, "Queue", splitPoint,2, self.cols-splitPoint, self.rows-4, scroll=False)
        # create color pair's 1 and 2
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)
#        self.color["RED_WHITE"] = curses.color_pair(1)
#        self.color["WHITE_RED"] = curses.color_pair(2)
        #curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        #curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.updateDisplay()

    def connectionLost(self, reason):
        self.close()

    def addLine(self, text):
        self.logBox.add_message(text)
        #self.updateDisplay()

    def updateQueue(self):
        self.queueBox.clear_messages()
        qitems = getQueuedItems()
        if qitems:
            self.queueBox.add_message("%d item(s) in the queue" % len(qitems))
            for item in qitems:
                self.queueBox.add_message("%s %s" % (item.queueDate.strftime('%I:%M:%S'), item.mediaObj.artist))
                self.queueBox.add_message("  %s" % (item.mediaObj.title))
        else:
            self.queueBox.add_message("Queue Is Empty")
    def updateDisplay(self):
        
        #stdscr.box()
        queue, statusLookup = getStatus()
        if queue:
            title = str(queue.mediaObj)
        else:
            title = "NOT PLAYING"
        
        if statusLookup:
            status, stat_text = statusLookup
        else:
            
            status = "IDLE"
            stat_text="Waiting for Activity" 
        
        
        offset = self.cols-(12+len(status)+len(stat_text))
            
        self.stdscr.addstr(0,0, " GrooveBot".ljust(self.cols), curses.color_pair(3))
        self.stdscr.addstr(1,2, title.ljust(offset), curses.A_BOLD)
        
        self.stdscr.addstr(1,offset, "Status:".ljust(self.cols-offset), curses.A_BOLD)
        self.stdscr.addstr(1,offset + 8, status, curses.A_UNDERLINE)
        self.stdscr.addstr(1,offset + 9 + len(status), stat_text)
  
        self.logBox.draw()
        self.queueBox.draw()

        self.stdscr.addstr(self.rows-1, 0, 
                           self.searchText + (' ' * (
                           self.cols-len(self.searchText)-2)))
        self.stdscr.move(self.rows-1, len(self.searchText))
        self.stdscr.refresh()

    def doRead(self):
        """ Input is ready! """
        curses.noecho()
        c = self.stdscr.getch() # read a character

        if c == curses.KEY_BACKSPACE:
            self.searchText = self.searchText[:-1]
            #self.updateDisplay()

        elif c == curses.KEY_ENTER or c == 10:
            line = self.searchText
            self.searchText = ''
            initiateSearch(SearchContext(self), line)
            #self.updateDisplay()

        else:
            if len(self.searchText) == self.cols-2: return
            self.searchText = self.searchText + chr(c)
            #self.updateDisplay()
        
        self.stdscr.addstr(self.rows-1, 0, 
                           self.searchText + (' ' * (
                           self.cols-len(self.searchText)-2)))
        self.stdscr.move(self.rows-1, len(self.searchText))
        self.stdscr.refresh()
        

    def close(self):
        """ clean up """

        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()