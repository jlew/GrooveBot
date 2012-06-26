from groovebot.ActionType import MediaSource
from groovebot.utils.FilePlayer import FilePlayer
from groovebot.GrooveBot import updateStatus
from groovebot.Constants import States

from groovebot.db import Session
from groovebot.db import MediaObject, MediaObjectAttribute
import os
from mutagen import mutagen
from hashlib import sha1

from twisted.internet import reactor

from sqlalchemy import or_

class FileData(MediaSource):
    def __init__(self):
        
        def stateChange(state, text):
            updateStatus(state, text)
        self.fp = FilePlayer(stateChange)
       
        reactor.callInThread(self.readFiles)
        
    def readFiles(self):
        print "Starting to index files"
        session = Session()
        fileList = []
        hashList = []
        for root, dirs, files in os.walk("/home/jlew/Music"):
            for f in files:
                fileList.append( root + "/" + f )
        
        fileLen = len(fileList)
        print "Found %d Files" % fileLen
        
        for i,f in enumerate(fileList):
            filePath = f.decode('utf-8')
            filePathSha = sha1(filePath).hexdigest()
            hashList.append(filePathSha)
            fileTime = str(os.path.getmtime(f)).decode('UTF-8')
            
            item = session.query(MediaObject)\
                .filter(MediaObject.source_id==filePathSha)\
                .filter(MediaObject.source==self.__module__).first()
            
            if item:
                if item.valid == False:
                    item.setValid(True)
                    
                for attribute in item.attributes:
                    if attribute.key == u"filetime" and attribute.value != fileTime:                        
                        title,artist,album = self.getTagInfo(f)
                        item.title = title
                        item.artist = artist
                        item.album = album
                        attribute.value = fileTime
                        print "Updated", item
            else:    
                title,artist,album = self.getTagInfo(f)
                print "Indexed %s %s %s" % (artist,album, title)
                
                m = MediaObject(self.__module__,title,artist,album, source_id = filePathSha)
                session.add(m)
                session.flush() # Flush the session so we get the ID
                session.add(MediaObjectAttribute(m.id,u"filename", filePath))
                session.add(MediaObjectAttribute(m.id,u"filetime", fileTime))
            
        session.commit()
        
        # Invalidate Files that are no longer found
        print "Files indexed, checking for missing files"
        query = session.query(MediaObject)\
                .filter(MediaObject.source==self.__module__)\
                .filter(MediaObject.valid==True)
                
        for obj in query:
            if obj.source_id not in hashList:
                print "DEACTIVATED", obj
                obj.setValidState(False)
        session.commit()
        session.close()
        print "File Indexing Completed"
    
    
    def getTagInfo(self, f):
        tagFile = mutagen.File(f)
            
        artist = u"-UNKNOWN-"
        if tagFile.has_key("artist"):
            artist = tagFile.get("artist")[0].decode('UTF-8')
    
        title = u"-UNKNOWN-"
        if tagFile.has_key("title"):
            title = tagFile.get("title")[0].decode('UTF-8')
    
        album = u"-UNKNOWN-"
        if tagFile.has_key("album"):
            album = tagFile.get("album")[0].decode('UTF-8')
        return title, artist, album
    
    def search(self, text):
        mediaList = []
        session = Session()
        
        searchText = "%" + text + "%"
        query = session.query(MediaObject).filter(MediaObject.source==self.__module__)\
            .filter(or_(
                        MediaObject.title.like(searchText),
                        MediaObject.album.like(searchText),
                        MediaObject.artist.like(searchText)
                        ))
        
        for row in query:
            mediaList.append(row)

        return mediaList

    def play(self, mediaObject):
        assert(mediaObject.source == self.__module__)
        
        for attribute in mediaObject.attributes:
            if attribute.key==u"filename":
                self.fp.playFile(attribute.value)
                return
        updateStatus(States.STOP, "Did Not Find Filename Attribute")

    def pause(self):
        self.fp.pause()
        
    def resume(self):
        self.fp.resume()

    def stop(self):
        self.fp.stop()

    def status(self):
        state, pos, dur = self.fp.get_time()
        return state, "%s/%s" % (pos, dur)
