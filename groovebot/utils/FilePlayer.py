# Note This file requires gobject.
# GrooveBot provides this
#import gobject
#gobject.threads_init() 
#
#import threading
#g_loop = threading.Thread(target=gobject.MainLoop().run)
#g_loop.daemon = True
#g_loop.start()

import pygst
pygst.require("0.10")
import gst
import os

from groovebot.Constants import States 

STATUS_MAPPING = {
                  gst.STATE_READY:States.BUFFER, # TODO: Is this correct?
                  gst.STATE_PLAYING:States.PLAY,
                  gst.STATE_NULL:States.STOP,
                  gst.STATE_PAUSED:States.PAUSE
                  }
class FilePlayer:
    def __init__(self, status_callback=None):
        self.player = gst.element_factory_make("playbin", "player")
        self.status_callback = status_callback


        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
    
    def playStream(self, stream):
        self.player.set_property('uri', stream)
        self.player.set_state(gst.STATE_PLAYING)
        self.sendStatus()
    
    def playFile(self, file_path):
        if os.path.isfile(file_path):
            self.playStream("file://%s" % file_path)
        else:
            raise Exception("File Not Found")
            
    def stop(self):
        self.player.set_state(gst.STATE_NULL)
        self.sendStatus()
        
    def pause(self):
        self.player.set_state(gst.STATE_PAUSED)
        self.sendStatus()
        
    def resume(self):
        self.player.set_state(gst.STATE_PLAYING)
        self.sendStatus()
        
    def seek(self, seconds):
        self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, seconds * gst.SECOND)
        self.sendStatus()
        
    def get_time(self):
        state = self.player.get_state()
        
        if state[1] == gst.STATE_NULL:
            return States.STOP, "00:00", "00:00"
        
        dur_int = self.player.query_duration(gst.FORMAT_TIME, None)[0]
        pos_int = self.player.query_position(gst.FORMAT_TIME, None)[0]
        
        return STATUS_MAPPING.get(state[1], "UNKNOWN"), self.convert_ns(pos_int), self.convert_ns(dur_int)
        
            
    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            
            if self.status_callback:
                self.status_callback(States.STOP, "End Of File")

        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(gst.STATE_NULL)
            
            if self.status_callback:
                self.status_callback(States.STOP, "Error playing file: %s" % err)
                
    def sendStatus(self):
        if self.status_callback:
            state, pos, dur = self.get_time()
            self.status_callback(state, "%s/%s" % (pos, dur))
            
            
    def convert_ns(self, t):
        s,ns = divmod(t, 1000000000)
        m,s = divmod(s, 60)

        if m < 60:
            return "%02i:%02i" %(m,s)
        else:
            h,m = divmod(m, 60)
            return "%i:%02i:%02i" %(h,m,s)


    