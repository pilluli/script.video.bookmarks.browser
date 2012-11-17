import xbmc, xbmcgui, xbmcaddon
import simplejson
import re
import sys
import os
import random
import time
    

def log(txt):
    message = 'script.video.bookmarks.browser: %s' % txt
    #xbmc.log(msg=message, level=xbmc.LOGDEBUG)

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
        self.LIMIT = int( params.get( "limit", "10" ) )
        self.VIDEOCATEGORY = params.get( "videocategory", "both" )
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
                  timestr = ('%d ' + str(self.__language__(90001))) % hh
              if hh > 1:
                  timestr = ('%d ' + str(self.__language__(90002))) % hh
              if mm > 0:
                  if mm == 1:
                      timestr = timestr + ((' %d ' + str(self.__language__(90003))) % mm)
                  else:
                      timestr = timestr + ((' %d ' + str(self.__language__(90004))) % mm)
              if hh == 0 and mm == 0:
                  timestr = '0 ' + str(self.__language__(90004))
              timestr = timestr + ' ' + str(self.__language__(90005))
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
      if self.VIDEOCATEGORY=='movies' or self.VIDEOCATEGORY=='both' or self.VIDEOCATEGORY=='bothseparated':
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
                        self.videos.append((resumetime, totaltime,   'movie',     label, tagline,        '',       '', year, fanart, thumbnail, path, rating, totaltime-resumetime))
            log('Time executing movie parsing: ' + str(time.time() - start) + ' sec')


    def _check_duplicated_episode( self, path, season, episode ):
      ret = True
      for i,v in enumerate(self.videos):
        if v[10] == path:
          # Check if episode is later
          ranking_old = int(v[5])*100 + int(v[6])
          ranking_new = int(season)*100 + int(episode)
          if ranking_new > ranking_old:
              self.videos.pop(i)
          else:
              ret = False
      return ret

    def _fetch_episodes( self ):
      if self.VIDEOCATEGORY=='episodes' or self.VIDEOCATEGORY=='both' or self.VIDEOCATEGORY=='bothseparated':
        start = time.time()
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "properties": ["title","resume", "playcount", "plot", "season", "episode", "showtitle", "firstaired", "thumbnail", "fanart", "file", "rating"]}, "id": 1}')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('episodes'):
            log('Time executing episodes json query: ' + str(time.time() - start) + ' sec')
            start = time.time()
            for item in json_response['result']['episodes']:
                if item['resume']['position'] > 0:
                    if item['playcount'] == 0:
                        # this is the episode we need
                        label = item['title']
                        fanart = item['fanart']
                        episode = "%.2d" % float(item['episode'])
                        path = item['file']
                        season = "%.2d" % float(item['season'])
                        thumbnail = item['thumbnail']
                        showtitle = item['showtitle']
                        firstaired = item['firstaired']
                        rating = str(round(float(item['rating']),1))
                        title = "S%sE%s - %s" % ( season,  episode, label)
                        totaltime = item['resume']['total']
                        resumetime = item['resume']['position']
                        if self._check_duplicated_episode(path,season,episode):
                            self.videos.append((resumetime, totaltime, 'episode', showtitle,   title, season, episode, firstaired, fanart, thumbnail, path, rating, totaltime-resumetime))
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

            self.WINDOW.clearProperty( "MovieBookmark.%d.RemainingTime" % ( count ) )
            self.WINDOW.clearProperty( "MovieBookmark.%d.Title" % ( count ) )
            self.WINDOW.clearProperty( "MovieBookmark.%d.Extra" % ( count ) )
            self.WINDOW.clearProperty( "MovieBookmark.%d.Date" % ( count ) )
            self.WINDOW.clearProperty( "MovieBookmark.%d.Fanart" % ( count ) )
            self.WINDOW.clearProperty( "MovieBookmark.%d.Thumb" % ( count ) )
            self.WINDOW.clearProperty( "MovieBookmark.%d.Path" % ( count ) )
            self.WINDOW.clearProperty( "MovieBookmark.%d.Rating" % ( count ) )

            self.WINDOW.clearProperty( "EpisodeBookmark.%d.RemainingTime" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.Title" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.Extra" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.EpisodeNo" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.Date" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.Fanart" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.Thumb" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.Path" % ( count ) )
            self.WINDOW.clearProperty( "EpisodeBookmark.%d.Rating" % ( count ) )

    def _set_properties( self ):
      from operator import itemgetter, attrgetter
      self.videos.sort(key=itemgetter(12))

      for count, v in enumerate( self.videos ):
            count += 1
            #self.videos.append((resumetime, totaltime,   'movie',     label, tagline,     '',      '',       year, fanart, thumbnail, path, rating))
            #self.videos.append((resumetime, totaltime, 'episode', showtitle,   title, season, episode, firstaired, fanart, thumbnail, path, rating))

            if self.VIDEOCATEGORY=='both':
                log('Adding video with bookmark = "' + v[3] + '" ' + str(v[0]) + ' - ' + str(v[1]))
                self.WINDOW.setProperty( "VideoBookmark.%d.RemainingTime" % ( count ), self._seconds_to_string(v[0],v[1],'long') )
                self.WINDOW.setProperty( "VideoBookmark.%d.Type" % ( count ), v[2] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Title" % ( count ), v[3] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Extra" % ( count ), v[4] )
                self.WINDOW.setProperty( "VideoBookmark.%d.EpisodeNo" % ( count ), "S%sE%s" % (v[5],v[6]) )
                self.WINDOW.setProperty( "VideoBookmark.%d.Date" % ( count ), v[7] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Fanart" % ( count ), v[8] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Thumb" % ( count ), v[9] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Path" % ( count ), v[10] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Rating" % ( count ), v[11] )
                if count == self.LIMIT:
                    break

            elif self.VIDEOCATEGORY=='movies' or (self.VIDEOCATEGORY=='bothseparated' and v[2]=='movie'):
                log('Adding movie with bookmark = "' + v[3] + '" ' + str(v[0]) + ' - ' + str(v[1]))
                self.WINDOW.setProperty( "MovieBookmark.%d.RemainingTime" % ( count ), self._seconds_to_string(v[0],v[1],'long') )
                self.WINDOW.setProperty( "MovieBookmark.%d.Title" % ( count ), v[3] )
                self.WINDOW.setProperty( "MovieBookmark.%d.Extra" % ( count ), v[4] )
                self.WINDOW.setProperty( "MovieBookmark.%d.Date" % ( count ), v[7] )
                self.WINDOW.setProperty( "MovieBookmark.%d.Fanart" % ( count ), v[8] )
                self.WINDOW.setProperty( "MovieBookmark.%d.Thumb" % ( count ), v[9] )
                self.WINDOW.setProperty( "MovieBookmark.%d.Path" % ( count ), v[10] )
                self.WINDOW.setProperty( "MovieBookmark.%d.Rating" % ( count ), v[11] )
                if count == self.LIMIT:
                    break

            elif self.VIDEOCATEGORY=='episodes' or (self.VIDEOCATEGORY=='bothseparated' and v[2]=='episode'):
                log('Adding episode with bookmark = "' + v[3] + '" ' + str(v[0]) + ' - ' + str(v[1]))
                self.WINDOW.setProperty( "EpisodeBookmark.%d.RemainingTime" % ( count ), self._seconds_to_string(v[0],v[1],'long') )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Type" % ( count ), v[2] )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Title" % ( count ), v[3] )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Extra" % ( count ), v[4] )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.EpisodeNo" % ( count ), "S%sE%s" % (v[5],v[6]) )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Date" % ( count ), v[7] )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Fanart" % ( count ), v[8] )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Thumb" % ( count ), v[9] )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Path" % ( count ), v[10] )
                self.WINDOW.setProperty( "EpisodeBookmark.%d.Rating" % ( count ), v[11] )
                if count == self.LIMIT:
                    break

if ( __name__ == "__main__" ):
    Main()
