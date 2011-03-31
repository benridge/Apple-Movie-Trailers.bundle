import re

AMT_SITE_URL   = 'http://trailers.apple.com'
AMT_JSON_URL   = 'http://trailers.apple.com/trailers/home/feeds/%s.json'
AMT_SEARCH_URL = 'http://trailers.apple.com/trailers/home/scripts/quickfind.php?callback=searchCallback&q=%s'
AMT_VIDEOS     = 'http://trailers.apple.com/moviesxml%sindex.xml'
AMT_VIDEOS_NS  = {'a':'http://www.apple.com/itms/'}

ART          = 'art-default.jpg'
ICON_DEFAULT = 'icon-default.png'
ICON_SEARCH  = 'icon-search.png'
ICON_PREFS   = 'icon-prefs.png'

####################################################################################################
def Start():
  # Current artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
  Plugin.AddPrefixHandler('/video/amt', MainMenu, 'Apple Movie Trailers', ICON_DEFAULT, ART)
  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

  ObjectContainer.title1 = 'Apple Movie Trailers'
  ObjectContainer.userAgent = 'Apple Mac OS X v10.6.7 CoreMedia v1.0.0.10J869'
  ObjectContainer.content = ContainerContent.GenericVideos
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON_DEFAULT)
  VideoClipObject.thumb = R(ICON_DEFAULT)

  HTTP.CacheTime = 7200
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27'

####################################################################################################
def MainMenu():
  oc = ObjectContainer(viewGroup='List')

  oc.add(DirectoryObject(key=Callback(JsonMenu, name='just_added'), title='Just Added'))
  oc.add(DirectoryObject(key=Callback(JsonMenu, name='exclusive'), title='Exclusive'))
  oc.add(DirectoryObject(key=Callback(JsonMenu, name='just_hd'), title='Just HD', thumb=R(ICON_PREFS)))
  oc.add(DirectoryObject(key=Callback(JsonMenu, name='most_pop'), title='Most Popular'))
#  oc.add(DirectoryObject(key=Callback(GenresMenu), title='Genres'))
#  oc.add(DirectoryObject(key=Callback(StudiosMenu), title='Movie Studios'))
#  oc.add(InputDirectoryObject(key=Callback(Search), title='Search Trailers', prompt='Search for movie trailer', thumb=R(ICON_SEARCH)))
#  oc.add(PrefsObject(title='Preferences', thumb=R(ICON_PREFS)))

  return oc

####################################################################################################
def JsonMenu(name):
  oc = ObjectContainer(viewGroup='List', title2=L(name))

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % name):
    url   = trailer['location']
    title = trailer['title']
    thumb = trailer['poster'].replace('.jpg', '-large.jpg')
    oc.add(DirectoryObject(key=Callback(Videos, url=url, title=title), title=title, thumb=Callback(Thumb, url=thumb)))

  return oc

####################################################################################################
def Videos(url, title):
  oc = ObjectContainer(viewGroup='InfoList', title2=title)
  url = AMT_VIDEOS % (url.replace('trailers', 's'))
  xml = XML.ElementFromURL(url, errors='ignore')

  oc.mediaTagVersion = 32423424;
  oc.mediaTagPrefix = "/system/bundle/media/flags/"

  for video in xml.xpath('//a:HBoxView/a:GotoURL', namespaces=AMT_VIDEOS_NS):
    
    # Figure out the override title.
    title = video.xpath('.//parent::a:HBoxView//a:b', namespaces=AMT_VIDEOS_NS)[0].text
    
    # Get the URL and compute the canonical URL.
    xml_url = AMT_SITE_URL + video.get('url')
    xml_url_components = xml_url.split('/')
    canonical_url = '/'.join(xml_url_components[0:3] + ['trailers'] + xml_url_components[5:-1]) + '#' + title.lower()

    # Add the video.
    video = URLService.MetadataObjectForURL(canonical_url)
    video.title = title
    oc.add(video)

  return oc

####################################################################################################
def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON_DEFAULT))
