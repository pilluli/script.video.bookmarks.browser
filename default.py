# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  this file was taken from http://xbmc-addons.googlecode.com/svn/packages/scripts/RecentlyAdded.py
# *  and modified to be a XBMC Add-on under gpl2 license on 20. November 2010.
# *
# *  Thanks to:
# *
# *  Nuka for the original RecentlyAdded.py
# *
# *  ronie and Hitcher for the improvements made while in official repo
# *  
# *  Team XBMC

import xbmc
import xbmcgui
from urllib import quote_plus, unquote_plus
import re
import sys
import os
import random
import time
    
class Main:
    
    # grab the home window
    WINDOW = xbmcgui.Window( 10000 )

    def _seconds_to_string( self, seconds, tseconds, format ):
        str = ''
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
                  str = '%d hour' % hh
              if hh > 1:
                  str = '%d hours' % hh
              if mm > 0:
                  if mm == 1:
                      str = str + (' %d minute' % mm)
                  else:
                      str = str + (' %d minutes' % mm)
              if hh == 0 and mm == 0:
                  str = '0 minutes'
          if format == 'short':
              strm = ''
              if hh > 0:
                  str = '%dh' % hh
                  strm = ' '
              if mm > 0:
                  str = str + strm + ('%02dmin' % mm)
              if hh == 0 and mm == 0:
                  str = '0min'
        except:
          str = '?'
  
        return str

    def _get_media( self, fullpath, file):
        # set default values
        play_path = fanart_path = thumb_path = fullpath
        # we handle stack:// media special
        if ( file.startswith( "stack://" ) ):
            play_path = fanart_path = file
            thumb_path = file[ 8 : ].split( " , " )[ 0 ]
        # we handle rar:// and zip:// media special
        if ( file.startswith( "rar://" ) or file.startswith( "zip://" ) ):
            play_path = fanart_path = thumb_path = file
        # return media info
        return xbmc.getCacheThumbName( thumb_path ), xbmc.getCacheThumbName( fanart_path ), play_path

    def _parse_argv( self ):
        try:
            # parse sys.argv for params
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
        except:
            # no params passed
            params = {}
        # set our preferences
        self.LIMIT = int( params.get( "limit", "10" ) )
        self.UNIQUE = int( params.get( "unique", "0" ) )
        self.RESUME = int( params.get( "resume", "0" ) )
    
    def __init__( self ):

        print '***JRH*** Executing script.video.bookmarks.browser string = ' + xbmc.getLocalizedString(90001)
        
        # parse argv for any preferences
        self._parse_argv()

	# If XBMC is updating the library something bad happens :-?
	time.sleep(1)

        # format our records start and end
        xbmc.executehttpapi( "SetResponseFormat()" )
        xbmc.executehttpapi( "SetResponseFormat(OpenRecord,%s)" % ( "<record>", ) )
        xbmc.executehttpapi( "SetResponseFormat(CloseRecord,%s)" % ( "</record>", ) )
        # check if we were executed internally

        # clear properties
        #self._clear_properties()
        
        # set any alarm
        #self._set_alarm()
        
        self._fetch_unfinished_videos_info()


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
