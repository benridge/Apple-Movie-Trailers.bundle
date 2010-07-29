from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
import re

AMT_PLUGIN_PREFIX   = "/video/amt"
AMT_SITE_URL        = "http://trailers.apple.com"
AMT_JSON_URL        = "http://trailers.apple.com/trailers/home/feeds/%s.json"
AMT_THUMB_URL       = "http://images.apple.com/trailers"
AMT_SEARCH_URL      = "http://trailers.apple.com/trailers/home/scripts/quickfind.php?callback=searchCallback&q=%s"

####################################################################################################
def Start():
  # Curent artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
  Plugin.AddPrefixHandler(AMT_PLUGIN_PREFIX, MainMenu, L('Apple Movie Trailers'), 'icon-default.png', 'art-default.png')
  MediaContainer.title1 = 'Apple Movie Trailers'
  MediaContainer.content = 'Items'
  MediaContainer.userAgent = 'Apple Mac OS X v10.6.1 CoreMedia v1.0.0.10B504'
  DirectoryItem.thumb = R('icon-default.png')
  MediaContainer.art = R('art-default.png')
  HTTP.SetCacheTime(7200)
  
####################################################################################################
def CreatePrefs():
  Prefs.Add(id='VideoQuality', type='enum', default='Small', label='Video Quality', values='1080p|720p|480p|Large|Medium|Small')

####################################################################################################
def MainMenu():
    dir = MediaContainer(title1="Apple Movie Trailers")
    dir.Append(Function(DirectoryItem(JSONMenu, title="Just Added"), name="just_added"))
    dir.Append(Function(DirectoryItem(JSONMenu, title="Exclusive"), name="exclusive"))
    dir.Append(Function(DirectoryItem(JSONMenu, title="Just HD", thumb=R("thumb-just_hd.png")), name="just_hd"))
    dir.Append(Function(DirectoryItem(JSONMenu, title="Most Popular"), name="most_pop"))
    dir.Append(Function(DirectoryItem(GenresMenu, title="Genres")))
    dir.Append(Function(DirectoryItem(StudiosMenu, title="Movie Studios")))
    dir.Append(Function(SearchDirectoryItem(Search, title="Search trailers", prompt="Search for movie trailer", thumb=R("search.png"))))
    dir.Append(PrefsItem(title="Preferences"))
    return dir

def JSONMenu(sender, name, query=None):
	return ContainerFromJSONName(name)
	
def GenresMenu(sender, query=None):
  dir = MediaContainer(title1="Apple Movie Trailers", title2="Genres")
  dict = JSON.ObjectFromURL(AMT_JSON_URL % "genres")
  genres = []
  for item in dict:
    for genre in item["genre"]:
      if genre not in genres:
        genres.append(genre)
  genres.sort()
  for genre in genres:
    dir.Append(Function(DirectoryItem(GenreMenu, title=genre)))
  return dir

def GenreMenu(sender, query=None):
  dir = MediaContainer(title1="Genres", title2=sender.itemTitle)
  dict = JSON.ObjectFromURL(AMT_JSON_URL % "genres")
  for item in dict:
    if sender.itemTitle in item["genre"]:
      key = AMT_SITE_URL + item["location"]
      thumb = item["poster"]
      dir.Append(Function(VideoItem(getVideo, title=item["title"], thumb=thumb), url=key))
  return dir

def StudiosMenu(sender, query=None):
    dir = MediaContainer(title1="Apple Movie Trailers", title2="Studios")
    dict = JSON.ObjectFromURL(AMT_JSON_URL % "studios")
    studios = []
    for item in dict:
      if item["studio"] not in studios:
        dir.Append(Function(DirectoryItem(StudioMenu, title=item["studio"])))
        studios.append(item["studio"])
    return dir

def StudioMenu(sender, query=None):
  dir = MediaContainer(title1="Studios", title2=sender.itemTitle)
  dict = JSON.ObjectFromURL(AMT_JSON_URL % "studios")
  for item in dict:
    if item["studio"] == sender.itemTitle:
      key = AMT_SITE_URL + item["location"]
      thumb = item["poster"]
      dir.Append(Function(VideoItem(getVideo, title=item["title"], thumb=thumb), url =key))
  return dir

####################################################################################################
def Search(sender, query):
  callback = HTTP.Request(AMT_SEARCH_URL % String.Quote(query))
  if callback is None: return None
  callback = callback.lstrip("searchCallback(")[:-3]
  d = JSON.ObjectFromString(callback)
  dir = MediaContainer(title1="Search", title2=sender.itemTitle)
  for item in d["results"]:
    if item["location"].find("phobos.apple.com") == -1:
      thumb = item["poster"]
      dir.Append(Function(VideoItem(getVideo, title=item["title"], thumb=thumb), url=AMT_SITE_URL + item["location"]))
  if len(dir) == 0:
    dir.Append(DirectoryItem("%s/search" % AMT_PLUGIN_PREFIX, "(No Results)", ""))
  return dir

####################################################################################################
def ContainerFromJSONName(jsonName):
  HTTP.Request('http://www.apple.com/trailers/universal/thevampiresassistant/')
  cookies = HTTP.GetCookiesForURL(AMT_SITE_URL)
  
  dir = MediaContainer(title1="Apple Movie Trailers", title2=L(jsonName), httpCookies=cookies)
  dict = JSON.ObjectFromURL(AMT_JSON_URL % jsonName)
  
  for item in dict:
    key = AMT_SITE_URL + item["location"]
    thumb = item["poster"]
    dir.Append(Function(VideoItem(getVideo, title=item["title"], thumb=thumb), url=key))
  return dir

####################################################################################################
def getTrailers(html):
  # First look for trailers.
  trailers = re.findall('"(http://[^"]+tlr[^"]+[1-9][0-9]+[a-z]?\.mov[^"]*)"', html)
  if len(trailers) == 0:
    trailers = re.findall('"(http://[^"]+[1-9][0-9]+[a-z]?\.mov[^"]*)"', html)
  if len(trailers) == 0:
    matches = XML.ElementFromString(html, True).xpath('//li[@class="hd"]/a')
    for match in matches:
       content = match.get('href')
       if content.find('http') > -1:
          movUrl = content
       else:
          movUrl = AMT_SITE_URL + content
       if movUrl.find('.mov') > -1:
       		trailers.append(movUrl)
  return trailers

####################################################################################################
def getVideo(sender, url):
  url = url + "/includes/playlists/web.inc"
  userQuality = Prefs.Get("VideoQuality")

  order = ['1080p', '720p', '480p', '640w', '480', '320']
  prefMap = {'1080p':'1080p', '720p':'720p', '480p':'480p', 'Large':'640w', 'Medium':'480', 'Small':'320' }
  prefValue = prefMap[userQuality]
  
  # Get all the trailers.
  html = HTTP.Request(url)
  trailers = getTrailers(html)

  if len(trailers) == 0:
    # Could be a special landing page.
    matches = XML.ElementFromString(html, True).xpath("//div[@class='trailerlinks']//area[@alt='HD']")
    if len(matches) > 0:
      match = matches[1].get('href')
      html = HTTP.Request(url + match)
      trailers = getTrailers(html)
  
  trailerList = []
  for trailer in trailers:
    t = trailer.replace('_h.', '_h').replace('h640','h640w')
    if t.find('480p') != -1 and t.find('h480p') == -1:
    	t = t.replace('480p','h480p')
    if t.find('720p') != -1 and t.find('h720p') == -1:
    	t = t.replace('720p','h720p')
    if t.find('1080p') != -1 and t.find('h1080p') == -1:
    	t = t.replace('1080p','h1080p')
    
    #t = t.replace('480p','h480p').replace('720p','h720p').replace('1080p','h1080p')
    size = re.findall('([0-9]+[a-z]?)\.mov', t)[0]
    trailerList.append([size, t])

  # Find the appropriate one.
  desired = order.index(prefValue)
  for (size,url) in trailerList:
    found = order.index(size)
    Log("Found=%d, desired=%d" % (found, desired))
    if found == desired:
      Log("Using:"+url)
      return Redirect(url)
      
  # If we didn't find a match, then return the highest resolution one we can find.
  if len(trailerList) > 0:
    return Redirect(trailerList[-1][1])
      