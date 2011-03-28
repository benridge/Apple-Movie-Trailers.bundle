import re

AMT_SITE_URL   = 'http://trailers.apple.com'
AMT_JSON_URL   = 'http://trailers.apple.com/trailers/home/feeds/%s.json'
AMT_SEARCH_URL = 'http://trailers.apple.com/trailers/home/scripts/quickfind.php?q=%s'
AMT_VIDEOS     = 'http://trailers.apple.com/moviesxml%sindex.xml'
AMT_VIDEOS_NS  = {'a':'http://www.apple.com/itms/'}

ART          = 'art-default.jpg'
ICON_DEFAULT = 'logo.png'
ICON_SEARCH  = 'icon-search.png'
ICON_PREFS   = 'icon-prefs.png'

PREF_MAP = {'1080p':'1080p', '720p':'720p', '480p':'480p', 'Large':'640w', 'Medium':'480', 'Small':'320'}
ORDER    = ['1080p', '720p', '480p', '640w', '480', '320']

####################################################################################################

def Start():
  # Current artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
  Plugin.AddPrefixHandler('/video/amt', MainMenu, 'Apple Movie Trailers', 'icon-default.png', ART)
  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

  MediaContainer.title1 = 'Apple Movie Trailers'
  MediaContainer.userAgent = 'Apple Mac OS X v10.6.7 CoreMedia v1.0.0.10J869'
  MediaContainer.art = R(ART)
  MediaContainer.viewGroup = 'List'

  DirectoryItem.thumb = R(ICON_DEFAULT)
  VideoItem.thumb = R(ICON_DEFAULT)

  HTTP.CacheTime = 7200
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27'

####################################################################################################

def MainMenu():
  dir = MediaContainer()

  dir.Append(Function(DirectoryItem(JsonMenu, title='Just Added'), name='just_added'))
  dir.Append(Function(DirectoryItem(JsonMenu, title='Exclusive'), name='exclusive'))
  dir.Append(Function(DirectoryItem(JsonMenu, title='Just HD', thumb=R('thumb-just_hd.png')), name='just_hd'))
  dir.Append(Function(DirectoryItem(JsonMenu, title='Most Popular'), name='most_pop'))
  dir.Append(Function(DirectoryItem(GenresMenu, title='Genres')))
  dir.Append(Function(DirectoryItem(StudiosMenu, title='Movie Studios')))
  dir.Append(Function(InputDirectoryItem(Search, title='Search Trailers', prompt='Search for movie trailer', thumb=R(ICON_SEARCH))))
  dir.Append(PrefsItem(title='Preferences', thumb=R(ICON_PREFS)))

  return dir

####################################################################################################

def JsonMenu(sender, name):
  dir = MediaContainer(title2=sender.itemTitle)

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % name):
    url   = trailer['location']
    title = trailer['title']
    thumb = trailer['poster']
    dir.Append(Function(DirectoryItem(Videos, title=title, thumb=Function(Thumb, url=thumb)), url=url, thumb=thumb))

  return dir

####################################################################################################

def GenresMenu(sender):
  dir = MediaContainer(title2='Genres')
  genres = []
  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'genres'):
    for genre in trailer['genre']:
      if genre not in genres:
        genres.append(genre)
  genres.sort()
  for genre in genres:
    dir.Append(Function(DirectoryItem(GenreMenu, title=genre)))

  return dir

####################################################################################################

def GenreMenu(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'genres'):
    if sender.itemTitle in trailer['genre']:
      url   = trailer['location']
      title = trailer['title']
      thumb = trailer['poster']
      dir.Append(Function(DirectoryItem(Videos, title=title, thumb=Function(Thumb, url=thumb)), url=url, thumb=thumb))

  return dir

####################################################################################################

def StudiosMenu(sender):
  dir = MediaContainer(title2='Studios')
  studios = []
  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'studios'):
    if trailer['studio'] not in studios:
      studios.append(trailer['studio'])
  studios.sort()
  for studio in studios:
    dir.Append(Function(DirectoryItem(StudioMenu, title=studio)))

  return dir

####################################################################################################

def StudioMenu(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'studios'):
    if trailer['studio'] == sender.itemTitle:
      url   = trailer['location']
      title = trailer['title']
      thumb = trailer['poster']
      dir.Append(Function(DirectoryItem(Videos, title=title, thumb=Function(Thumb, url=thumb)), url=url, thumb=thumb))

  return dir

####################################################################################################

def Search(sender, query):
  dir = MediaContainer(title2=sender.itemTitle)

  for trailer in JSON.ObjectFromURL(AMT_SEARCH_URL % String.Quote(query))['results']:
    url   = trailer['location']
    title = trailer['title'].replace('%u2019', "'")
    thumb = AMT_SITE_URL + trailer['poster']
    dir.Append(Function(DirectoryItem(Videos, title=title, thumb=Function(Thumb, url=thumb)), url=url, thumb=thumb))

  if len(dir) == 0:
    return MessageContainer('No results', 'Your search query didn\'t return any matches')
  else:
    return dir

####################################################################################################

def Videos(sender, url, thumb):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle)

  xml = XML.ElementFromURL(AMT_VIDEOS % url.replace('trailers', 's'), errors='ignore')
  summary = xml.xpath('//a:ScrollView//comment()[contains(.,"DESCRIPTION")]/following-sibling::a:TextView[1]/a:SetFontStyle', namespaces=AMT_VIDEOS_NS)[0].text.strip()

  for video in xml.xpath('//a:HBoxView/a:GotoURL', namespaces=AMT_VIDEOS_NS):
    title = video.xpath('.//parent::a:HBoxView//a:b', namespaces=AMT_VIDEOS_NS)[0].text
    url = AMT_SITE_URL + video.get('url')
    dir.Append(Function(VideoItem(PlayVideo, title=title, summary=summary, thumb=Function(Thumb, url=thumb)), url=url))

  return dir

####################################################################################################

def PlayVideo(sender, url):
  user_quality = Prefs['VideoQuality']
  pref_value = PREF_MAP[user_quality]
  available = {}

  for res in XML.ElementFromURL(url).xpath('//a:TrackList//a:array/a:dict', namespaces=AMT_VIDEOS_NS):
    video_url = res.xpath('./a:key[text()="previewURL"]/following-sibling::*[1]', namespaces=AMT_VIDEOS_NS)[0].text
    q = re.search('_h(320|480|640w|480p|720p|1080p)\.mov$', video_url)
    if q:
      q = q.group(1)
      if q in ORDER:
        available[q] = video_url

  for i in range(ORDER.index(pref_value), len(ORDER)):
    quality = ORDER[i]
    if quality in available:
      video_url = available[quality]
      break

  return Redirect(video_url)

####################################################################################################

def Thumb(url):
  try:
    large_thumb = url.replace('.jpg', '-large.jpg')
    data = HTTP.Request(large_thumb, cacheTime=CACHE_1MONTH).content
    return DataObject(data, 'image/jpeg')
  except:
    try:
      data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
      return DataObject(data, 'image/jpeg')
    except:
      pass

  return Redirect(R(ICON_DEFAULT))
