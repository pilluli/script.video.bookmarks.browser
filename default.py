import xbmc, xbmcgui, xbmcaddon
import simplejson
import re
import sys
import os
import random
import time
    

def log(txt):
    message = 'script.video.bookmarks.browser: %s' % txt
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

class Main:
    
    def __init__( self ):
        self._init_vars()
        self._fetch_movies()
        self._fetch_episodes()
        self._clear_properties()
        self._set_properties()

    def _init_vars( self ):
        self.__addon__        = xbmcaddon.Addon(id='script.video.bookmarks.browser')
        self.__language__     = self.__addon__.getLocalizedString
        self.__addonversion__ = self.__addon__.getAddonInfo('version')
        self.__cwd__          = self.__addon__.getAddonInfo('path')
        self.WINDOW = xbmcgui.Window( 10000 )
        try:
            # parse sys.argv for params
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
        except:
            # no params passed
            params = {}
        # set our preferences
        self.LIMIT = self.LIMIT = int( params.get( "limit", "10" ) )
        self.videos = []

    def _seconds_to_string( self, seconds, tseconds, format ):
        timestr = ''
        hh = mm = ss = 0
        try:
          time = float(tseconds) - float(seconds)
          if time > 0.0:
              hh = int(time / 3600)
              time = time % 3600
              mm = int(time / 60)
              ss = int(time % 60)
          if format == 'long':
              if hh == 1:
                  log('bookmarkk here1')
                  timestr = ('%d ' + str(self.__language__(90001))) % hh
                  log('bookmarkk here2')
              if hh > 1:
                  timestr = ('%d ' + str(self.__language__(90002))) % hh
              if mm > 0:
                  if mm == 1:
                      timestr = timestr + ((' %d ' + str(self.__language__(90003))) % mm)
                  else:
                      timestr = timestr + ((' %d ' + str(self.__language__(90004))) % mm)
              if hh == 0 and mm == 0:
                  timestr = '0 ' + str(self.__language__(90004))
          if format == 'short':
              strm = ''
              if hh > 0:
                  timestr = '%dh' % hh
                  strm = ' '
              if mm > 0:
                  timestr = timestr + strm + ('%02dmin' % mm)
              if hh == 0 and mm == 0:
                  timestr = '0min'
        except:
          timestr = 'why here?'
  
        return timestr

    def _fetch_movies( self ):
        start = time.time()
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["resume", "tagline", "fanart", "thumbnail", "file", "year", "rating", "plot", "playcount"]}, "id": 1}')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('movies'):
            log('Time executing movie json query: ' + str(time.time() - start) + ' sec')
            start = time.time()
            for item in json_response['result']['movies']:
                if item['resume']['position'] > 0:
                    if item['playcount'] == 0:
                        # this item has a resume point
                        label = item['label']
                        year = str(item['year'])
                        tagline = item['tagline']
                        fanart = item['fanart']
                        thumbnail = item['thumbnail']
                        path = item['file']
                        plot = item['plot']
                        rating = str(round(float(item['rating']),1))
                        totaltime = item['resume']['total']
                        resumetime = item['resume']['position']
                        self.videos.append((resumetime, totaltime,   'movie',     label, tagline,        '',       year, fanart, thumbnail, path, rating))
            log('Time executing movie parsing: ' + str(time.time() - start) + ' sec')


    def _fetch_episodes( self ):
        start = time.time()
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "properties": ["resume", "playcount", "plot", "season", "episode", "showtitle", "firstaired", "thumbnail", "fanart", "file", "rating"]}, "id": 1}')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('episodes'):
            log('Time executing episodes json query: ' + str(time.time() - start) + ' sec')
            start = time.time()
            for item in json_response['result']['episodes']:
                if item['resume']['position'] > 0:
                    if item['playcount'] == 0:
                        # this is the episode we need
                        label = item['label']
                        fanart = item['fanart']
                        episode = "%.2d" % float(item['episode'])
                        path = item['file']
                        season = "%.2d" % float(item['season'])
                        thumbnail = item['thumbnail']
                        showtitle = item['showtitle']
                        firstaired = item['firstaired']
                        rating = str(round(float(item['rating']),1))
                        title = "S%sE%s - %s" % ( season,  episode, label)
                        episodeno = "S%sE%s" % ( season,  episode)
                        totaltime = item['resume']['total']
                        resumetime = item['resume']['position']
                        self.videos.append((resumetime, totaltime, 'episode', showtitle,   title, episodeno, firstaired, fanart, thumbnail, path, rating))
            log('Time executing episodes parsing: ' + str(time.time() - start) + ' sec')

    def _clear_properties( self ):
        for count in range( self.LIMIT ):
            count += 1
            self.WINDOW.clearProperty( "VideoBookmark.%d.RemainingTime" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Type" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Title" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Extra" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.EpisodeNo" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Date" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Fanart" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Thumb" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Path" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Rating" % ( count ) )

    def _set_properties( self ):
        self.videos.sort(reverse=False)
        for count, v in enumerate( self.videos ):
            count += 1
            #self.videos.append((resumetime, totaltime, 'episode', showtitle,   title, episodeno, firstaired, fanart, thumbnail, path, rating))
            #self.videos.append((resumetime, totaltime,   'movie',     label, tagline,        '',       year, fanart, thumbnail, path, rating))
            log('Adding video with bookmarkk = "' + v[3] + '" ' + str(v[0]) + ' - ' + str(v[1]))
            self.WINDOW.setProperty( "VideoBookmark.%d.RemainingTime" % ( count ), self._seconds_to_string(v[0],v[1],'long') )
            self.WINDOW.setProperty( "VideoBookmark.%d.Type" % ( count ), v[2] )
            self.WINDOW.setProperty( "VideoBookmark.%d.Title" % ( count ), v[3] )
            self.WINDOW.setProperty( "VideoBookmark.%d.Extra" % ( count ), v[4] )
            self.WINDOW.setProperty( "VideoBookmark.%d.EpisodeNo" % ( count ), v[5] )
            self.WINDOW.setProperty( "VideoBookmark.%d.Date" % ( count ), v[6] )
            self.WINDOW.setProperty( "VideoBookmark.%d.Fanart" % ( count ), v[7] )
            self.WINDOW.setProperty( "VideoBookmark.%d.Thumb" % ( count ), v[8] )
            self.WINDOW.setProperty( "VideoBookmark.%d.Path" % ( count ), v[9] )
            self.WINDOW.setProperty( "VideoBookmark.%d.Rating" % ( count ), v[10] )
            if count == self.LIMIT:
                break

if ( __name__ == "__main__" ):
    Main()
