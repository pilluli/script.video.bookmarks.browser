import xbmc, xbmcgui, xbmcaddon
import simplejson
import re
import sys
import os
import random
import time
    
__addon__        = xbmcaddon.Addon(id='script.video.bookmarks.browser')
__language__     = __addon__.getLocalizedString
__addonversion__ = __addon__.getAddonInfo('version')
__cwd__          = __addon__.getAddonInfo('path')

def log(txt):
    message = 'script.watchlist: %s' % txt
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

class Main:
    
    def __init__( self ):
        self._init_vars()
        self._fetch_movies()
        self._fetch_tvshows()
        self._fetch_episodes()
        self._clear_properties()
        self._set_properties()

    def _init_vars( self ):
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
          timestr = '?'
  
        return timestr

    def _fetch_movies( self ):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["resume", "genre", "studio", "tagline", "runtime", "fanart", "thumbnail", "file", "plot", "plotoutline", "year", "lastplayed", "rating"]}, "id": 1}')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('movies'):
            for item in json_response['result']['movies']:
                if item['resume']['position'] > 0:
                    # this item has a resume point
                    label = item['label']
                    year = str(item['year'])
                    genre = item['genre']
                    studio = item['studio']
                    plot = item['plot']
                    plotoutline = item['plotoutline']
                    tagline = item['tagline']
                    runtime = item['runtime']
                    fanart = item['fanart']
                    thumbnail = item['thumbnail']
                    path = item['file']
                    rating = str(round(float(item['rating']),1))
                    lastplayed = item['lastplayed']
                    if not lastplayed == "":
                        # catch exceptions where the item has been partially played, but playdate wasn't stored in the db
                        datetime = strptime(lastplayed, "%Y-%m-%d %H:%M:%S")
                        lastplayed = str(mktime(datetime))
                    remainingtime = 9999999999.9
                    try:
                        remainingtime = float(item['resume']['total']) - float(item['resume']['position'])
                    except:
                        pass

                    self.videos.append((remainingtime, 'movie', lastplayed, label, year, genre, studio, plot, plotoutline, tagline, runtime, fanart, thumbnail, path, rating))



    def _fetch_episodes( self ):
        for tvshow in self.tvshows:
            lastplayed = ""
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "properties": ["resume","playcount", "plot", "season", "episode", "showtitle", "thumbnail", "fanart", "file", "lastplayed", "rating"], "sort": { "method": "episode" }, "tvshowid":%s }, "id": 1}' % tvshow[0])
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["resume", "genre", "studio", "tagline", "runtime", "fanart", "thumbnail", "file", "plot", "plotoutline", "year", "lastplayed", "rating"]}, "id": 1}')
            json_response = simplejson.loads(json_query)
            if json_response['result'].has_key('episodes'):
                for item in json_response['result']['episodes']:
                    playcount = item['playcount']
                    if playcount != 0:
                        # this item has been watched, record play date (we need it for sorting the final list) and continue to next item
                        lastplayed = item['lastplayed']
                        if not lastplayed == "":
                            # catch exceptions where the item has been played, but playdate wasn't stored in the db
                            datetime = strptime(lastplayed, "%Y-%m-%d %H:%M:%S")
                            lastplayed = str(mktime(datetime))
                        continue
                    else:
                        # this is the first unwatched item, check if it's partially watched
                        playdate = item['lastplayed']
                        if (lastplayed == "") and (playdate == ""):
                            # it's a tv show with 0 watched episodes, continue to the next tv show
                            break
                        else:
                            # this is the episode we need
                            label = item['label']
                            fanart = item['fanart']
                            episode = "%.2d" % float(item['episode'])
                            path = item['file']
                            plot = item['plot']
                            season = "%.2d" % float(item['season'])
                            thumbnail = item['thumbnail']
                            showtitle = item['showtitle']
                            rating = str(round(float(item['rating']),1))
                            episodeno = "s%se%s" % ( season,  episode, )
                            if not playdate == "":
                                # if the episode is partially watched, use it's playdate for sorting
                                datetime = strptime(playdate, "%Y-%m-%d %H:%M:%S")
                                lastplayed = str(mktime(datetime))
                                resumable = "True"
                                log('### episode "' + showtitle + ' - ' + label + '" partially watched')
                            else:
                                resumable = "False"
                            showthumb = tvshow[1]
                            studio = tvshow[2]
                            seasonthumb = self._fetch_seasonthumb(tvshow[0], season)
                            if item['resume']['position'] > 0:
                                pass
                            else:
                                self.episodes.append((lastplayed, label, episode, season, plot, showtitle, path, thumbnail, fanart, episodeno, studio, showthumb, seasonthumb, resumable, rating))
                                # we have found our episode, collected all data, so continue to next tv show
                                break
        self.episodes.sort(reverse=True)
        log("episode list: %s items" % len(self.episodes))



    def _clear_properties( self ):
        for count in range( self.LIMIT ):
            count += 1
            self.WINDOW.clearProperty( "VideoBookMark.%d.Type" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookMark.%d.Title" % ( count ) )
            self.WINDOW.clearProperty( "VideoBookMark.%d.RemainingTime" % ( count ) )


    def _fetch_unfinished_videos_info( self ):
        # sql statement (in bookmarks)
        sql_movies = "select movieview.*, bookmark.type, bookmark.idBookmark, bookmark.thumbNailImage, bookmark.timeInSeconds, bookmark.totalTimeInSeconds from movieview join bookmark on (movieview.idFile = bookmark.idFile) limit %d" % ( self.LIMIT, )
        # query the database
        movies_xml = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % quote_plus( sql_movies ), )
        # separate the records
        movies = re.findall( "<record>(.+?)</record>", movies_xml, re.DOTALL )

        # sql statement (in bookmarks)
        sql_episodes = "select episodeview.*, bookmark.type, bookmark.idBookmark, bookmark.thumbNailImage, bookmark.timeInSeconds, bookmark.totalTimeInSeconds from episodeview join bookmark on (episodeview.idFile = bookmark.idFile) limit %d" % ( self.LIMIT, )
        # query the database
        episodes_xml = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % quote_plus( sql_episodes ), )
        # separate the records
        episodes = re.findall( "<record>(.+?)</record>", episodes_xml, re.DOTALL )

        # put all records in a dictionary so we can sort them
        videos = {}
        for movie in movies:
            fields = re.findall( "<field>(.*?)</field>", movie, re.DOTALL )
            if fields[-5] == '1' or self.RESUME == 1:
                idFile = int(fields[1])
                if self.UNIQUE==0:
                    idFile = int(fields[1]+fields[-4])            
                remainingtime = 9999999999.9
                try:
                    remainingtime = float(fields[-1]) - float(fields[-2])
                except:
                    pass
                if idFile in videos:
                    if remainingtime < videos[idFile][0]:
                        videos[idFile] = (remainingtime,"movie",fields)
                else:
                    videos[idFile] = (remainingtime,"movie",fields)
        for episode in episodes:
            fields = re.findall( "<field>(.*?)</field>", episode, re.DOTALL )
            if fields[-5] == '1' or self.RESUME == 1:
                idFile = int(fields[1])
                if self.UNIQUE==0:
                    idFile = int(fields[1]+fields[-4])            
                remainingtime = 9999999999.9
                try:
                    remainingtime = float(fields[ -1 ]) - float(fields[ -2 ])            
                except:
                    pass
                if idFile in videos:
                    if remainingtime < videos[idFile][0]:
                        videos[idFile] = (remainingtime,"episode",fields)
                else:
                    videos[idFile] = (remainingtime,"episode",fields)
                
        # Go for all records in videos 
        count = 0
        #for v in sorted(videos.keys(),reverse=True):
        for v in sorted(videos.values()):
            if v[1] == 'movie':

                # set properties
                self.WINDOW.setProperty( "VideoBookmark.%d.Type" % ( count + 1, ), 'movie' )
                self.WINDOW.setProperty( "VideoBookmark.%d.Title" % ( count + 1, ), v[2][ 2 ] )
                #self.WINDOW.setProperty( "VideoBookmark.%d.Extra" % ( count + 1, ), '' + v[2][ 9 ] + ' - ' + v[2][ 13 ].split("|")[0])
                self.WINDOW.setProperty( "VideoBookmark.%d.Extra" % ( count + 1, ), '')
                self.WINDOW.setProperty( "VideoBookmark.%d.Year" % ( count + 1, ), v[2][ 9 ] )
                self.WINDOW.setProperty( "VideoBookmark.%d.RunningTime" % ( count + 1, ), v[2][ 13 ].split("|")[0] )
                self.WINDOW.setProperty( "VideoBookmark.%d.RemainingTime" % ( count + 1, ), self._seconds_to_string( v[2][-2],v[2][-1],'long' ) )
                # get cache names of path to use for thumbnail/fanart and play path
                thumb_cache, fanart_cache, play_path = self._get_media( v[2][ 24 ], v[2][ 26 ] )
                if os.path.isfile("%s.dds" % (xbmc.translatePath( "special://profile/Thumbnails/Video/%s/%s" % ( "Fanart", os.path.splitext(fanart_cache)[0],) ) )):
                    fanart_cache = "%s.dds" % (os.path.splitext(fanart_cache)[0],)
                self.WINDOW.setProperty( "VideoBookmark.%d.Path" % ( count + 1, ), play_path )
                self.WINDOW.setProperty( "VideoBookmark.%d.Trailer" % ( count + 1, ),  v[2][ 21 ] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Fanart" % ( count + 1, ), "special://profile/Thumbnails/Video/%s/%s" % ( "Fanart", fanart_cache, ) )
                # initial thumb path
                thumb = "special://profile/Thumbnails/Video/%s/%s" % ( thumb_cache[ 0 ], thumb_cache, )
                # if thumb does not exist use an auto generated thumb path
                if ( not os.path.isfile( xbmc.translatePath( thumb ) ) ):
                    thumb = "special://profile/Thumbnails/Video/%s/auto-%s" % ( thumb_cache[ 0 ], thumb_cache, )
                ###self.WINDOW.setProperty( "VideoBookmark.%d.Thumb" % ( count + 1, ), thumb )
                self.WINDOW.setProperty( "VideoBookmark.%d.Thumb" % ( count + 1, ), "special://profile/Thumbnails/Video/%s/%s" % ( "Fanart", fanart_cache, ) )

                count = count + 1


            if v[1] == 'episode':
                episode_label = "S%02dE%02d" % ( int( v[2][ 14 ] ), int( v[2][ 15 ] ), )
                # set properties
                self.WINDOW.setProperty( "VideoBookmark.%d.Type" % ( count + 1, ), 'episode' )
                self.WINDOW.setProperty( "VideoBookmark.%d.ShowTitle" % ( count + 1, ), v[2][ 28 ] )
                self.WINDOW.setProperty( "VideoBookmark.%d.EpisodeTitle" % ( count + 1, ), v[2][ 2 ] )
                self.WINDOW.setProperty( "VideoBookmark.%d.Title" % ( count + 1, ), v[2][ 30 ] )
                self.WINDOW.setProperty( "VideoBookmark.%d.EpisodeNo" % ( count + 1, ), episode_label )
                self.WINDOW.setProperty( "VideoBookmark.%d.Extra" % ( count + 1, ), episode_label + ' - ' + v[2][2])
                self.WINDOW.setProperty( "VideoBookmark.%d.RemainingTime" % ( count + 1, ), self._seconds_to_string( v[2][ -2 ],v[2][ -1 ],'long' ) )

                # get cache names of path to use for thumbnail/fanart and play path
                thumb_cache, fanart_cache, play_path = self._get_media( v[2][ 20 ], v[2][ 26 ] )

                # get fanart from series not episode
                fanart_cache = xbmc.getCacheThumbName( v[2][ 27 ] )
                
                self.WINDOW.setProperty( "VideoBookmark.%d.Path" % ( count + 1, ), play_path )
                self.WINDOW.setProperty( "VideoBookmark.%d.Fanart" % ( count + 1, ), "special://profile/Thumbnails/Video/%s/%s" % ( "Fanart", fanart_cache ) )
                # initial thumb path
                thumb = "special://profile/Thumbnails/Video/%s/%s" % ( thumb_cache[ 0 ], thumb_cache, )
                # if thumb does not exist use an auto generated thumb path
                if ( not os.path.isfile( xbmc.translatePath( thumb ) ) ):
                    thumb = "special://profile/Thumbnails/Video/%s/auto-%s" % ( thumb_cache[ 0 ], thumb_cache, )
                self.WINDOW.setProperty( "VideoBookmark.%d.Thumb" % ( count + 1, ), thumb )

                count = count + 1

            if count == self.LIMIT:
                break

        # Put all else to 0
        for c in range(count,self.LIMIT ):
            self.WINDOW.clearProperty( "VideoBookmark.%d.Type" % ( c + 1, ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Title" % ( c + 1, ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Extra" % ( c + 1, ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.RemainingTime" % ( c + 1, ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Fanart" % ( c + 1, ) )
            self.WINDOW.clearProperty( "VideoBookmark.%d.Thumb" % ( c + 1, ) )


if ( __name__ == "__main__" ):
    Main()
