from groovebot.ActionType import MediaSource
from groovebot.utils.FilePlayer import FilePlayer
from groovebot.MediaObject import MediaObject
from groovebot.GrooveBot import updateStatus


import os
from mutagen import mutagen
import unicodedata
import sqlite3
import base64


class FileData(MediaSource):
    def __init__(self):
        
        def stateChange(state, text):
            updateStatus(state, text)
        self.fp = FilePlayer(stateChange)
        
        self.db = sqlite3.connect(':memory:', check_same_thread = False)
        self.db.execute('''CREATE TABLE files (artist text collate nocase, album text collate nocase, title text collate nocase, filename text)''')
        self.db.commit()
        self.readFiles()
        
    def readFiles(self):
        fileList = []
        for root, dirs, files in os.walk("/home/jlew/Music"):
            for f in files:
                fileList.append( root + "/" + f )
        
        fileLen = len(fileList)
        print "Found %d Files" % fileLen
        
        for i,f in enumerate(fileList):
            tagFile = mutagen.File(f)
        
            author = "-UNKNOWN-"
            if tagFile.has_key("artist"):
                author = unicodedata.normalize('NFKD', tagFile.get("artist")[0]).encode('ascii','ignore')
        
            title = "-UNKNOWN-"
            if tagFile.has_key("title"):
                title = unicodedata.normalize('NFKD', tagFile.get("title")[0]).encode('ascii','ignore')
        
            album = "-UNKNOWN-"
            if tagFile.has_key("album"):
                album = unicodedata.normalize('NFKD', tagFile.get("album")[0]).encode('ascii','ignore')
        
            #print "Indexed %s %s %s" % (author,album, title)
            
            self.db.execute("insert into files values(?,?,?,?)", 
                            (author, album, title, base64.b64encode(f)))
            
        self.db.commit()
        
    def search(self, text):
        mediaList = []
        
        for row in self.db.execute("SELECT * FROM files where artist like ? or album like ? or title like ?",
                                   ("%"+text+"%","%"+text+"%","%"+text+"%")):
            mediaList.append(MediaObject(self, base64.b64decode(row[3]), title=row[2], artist=row[0], album=row[1]))
        
        return mediaList

    def play(self, mID):
        self.fp.playFile(mID)

    def pause(self):
        self.fp.pause()

    def stop(self):
        self.fp.stop()

    def status(self):
        state, pos, dur = self.fp.get_time()
        return state, "%s/%s" % (pos, dur)
