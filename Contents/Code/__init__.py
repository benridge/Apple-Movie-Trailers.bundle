AMT_SITE_URL     = 'http://trailers.apple.com'
AMT_JSON_URL     = 'http://trailers.apple.com/trailers/home/feeds/%s.json'
AMT_VIDEOS       = 'http://trailers.apple.com/moviesxml/%s/index.xml'
AMT_WEB_PLAYLIST = 'http://trailers.apple.com/%s/includes/playlists/web.inc'
CANONICAL_URL    = 'http://trailers.apple.com/trailers/%s/%s/#%s'
AMT_VIDEOS_NS    = {'a':'http://www.apple.com/itms/'}
XML_HTTP_HEADERS = {'User-Agent':'iTunes/10.7'}
RE_XML_URL       = Regex('^/moviesxml/s/([^/]+)/([^/]+)/(.+)\.xml$')

# Current artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
ART = 'art-default.jpg'
ICON = 'icon-default.png'

####################################################################################################
def Start():

  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

  ObjectContainer.art = R(ART)
  ObjectContainer.content = ContainerContent.GenericVideos
  ObjectContainer.title1 = 'Apple Movie Trailers'
  DirectoryObject.thumb = R(ICON)
  VideoClipObject.thumb = R(ICON)

  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.14 (KHTML, like Gecko) Version/6.0.1 Safari/536.26.14'

####################################################################################################
@handler('/video/amt', 'Apple Movie Trailers', art = ART, thumb = ICON)
def MainMenu():

  oc = ObjectContainer(view_group='List')

  oc.add(DirectoryObject(key=Callback(Categories, name='just_added'), title=L('just_added')))
  oc.add(DirectoryObject(key=Callback(Categories, name='exclusive'), title=L('exclusive')))
  oc.add(DirectoryObject(key=Callback(Categories, name='just_hd'), title=L('just_hd'), thumb=R('icon-justhd.png')))
  oc.add(DirectoryObject(key=Callback(Categories, name='most_pop'), title=L('most_pop')))
  oc.add(DirectoryObject(key=Callback(Genres), title=L('genres')))
  oc.add(DirectoryObject(key=Callback(Studios), title=L('movie_studios')))
  oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.amt', title='Search Trailers', prompt='Search for movie trailer', thumb=R('icon-search.png')))

  return oc

####################################################################################################
@route('/video/amt/categories/{name}')
def Categories(name):

  oc = ObjectContainer(view_group='List', title2=L(name))

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % name):
    url   = trailer['location']
    title = trailer['title']
    thumb = trailer['poster']
    oc.add(DirectoryObject(key=Callback(Videos, url=url, title=title), title=title, thumb=Callback(Thumb, url=thumb)))

  return oc

####################################################################################################
@route('/video/amt/genres')
def Genres():

  oc = ObjectContainer(view_group='List', title2=L('genres'))
  genres = []

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'genres'):
    for genre in trailer['genre']:
      if genre not in genres:
        genres.append(genre)

  genres.sort()

  for genre in genres:
    oc.add(DirectoryObject(key=Callback(Genre, genre=genre), title=genre))

  return oc

####################################################################################################
@route('/video/amt/genre/{genre}')
def Genre(genre):

  oc = ObjectContainer(view_group='List', title2=genre)

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'genres'):
    if genre in trailer['genre']:
      url   = trailer['location']
      title = trailer['title']
      thumb = trailer['poster']
      oc.add(DirectoryObject(key=Callback(Videos, url=url, title=title), title=title, thumb=Callback(Thumb, url=thumb)))

  return oc

####################################################################################################
@route('/video/amt/studios')
def Studios():

  oc = ObjectContainer(view_group='List', title2=L('genres'))
  studios = []

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'studios'):
    if trailer['studio'] not in studios:
      studios.append(trailer['studio'])

  studios.sort()

  for studio in studios:
    oc.add(DirectoryObject(key=Callback(Studio, studio=studio), title=studio))

  return oc

####################################################################################################
@route('/video/amt/studio/{studio}')
def Studio(studio):

  oc = ObjectContainer(view_group='List', title2=studio)

  for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'studios'):
    if studio == trailer['studio']:
      url   = trailer['location']
      title = trailer['title']
      thumb = trailer['poster']
      oc.add(DirectoryObject(key=Callback(Videos, url=url, title=title), title=title, thumb=Callback(Thumb, url=thumb)))

  return oc

####################################################################################################
@route('/video/amt/videos', allow_sync = True)
def Videos(url, title):

  oc = ObjectContainer(view_group='InfoList', title2=title)

  url = url.strip('/')
  xml_url = AMT_VIDEOS % url.replace('trailers', 's')

  try:
    xml = XML.ElementFromURL(xml_url, headers=XML_HTTP_HEADERS)
  except:
    try:
      xml = XML.ElementFromURL(xml_url.replace('index.xml', 'trailer.xml'), headers=XML_HTTP_HEADERS)
    except:
      Log(" --> Couldn't find an xml file.")
      return ObjectContainer(header="Empty", message="There aren't any items.")

  tracklist = xml.xpath('//a:TrackList//a:array/a:dict', namespaces=AMT_VIDEOS_NS)

  if len(tracklist) > 0:
    for clip in xml.xpath('//a:HBoxView/a:GotoURL', namespaces=AMT_VIDEOS_NS):

      # Get the URL and compute the canonical URL.
      xml_url = clip.get('url') ### Example: /moviesxml/s/disney/piratesofthecaribbeanonstrangertides/trailer2.xml
      studio, title, video = RE_XML_URL.findall(xml_url)[0]
      canonical_url = CANONICAL_URL % (studio, title, video)
      Log(" --> Canonical url: %s" % canonical_url)

      # Add the video.
      try:
        video = URLService.MetadataObjectForURL(canonical_url)
        oc.add(video)
      except:
        pass

  if len(oc) == 0:
    Log(" --> Couldn't find any video in the xml file(s), going to do a web/playlist lookup.")
    junk, studio, title = url.split('/')

    inc_url = AMT_WEB_PLAYLIST % url
    playlist = HTTP.Request(inc_url).content
    html = HTML.ElementFromString('<div>%s</div>' % playlist)

    # If we have a big "Watch Now" link, there is just 1 trailer and the HTML looks different from where we have multiple videos.
    if len(html.xpath('//h2//a[contains(text(), "Watch Now")]')) == 1:
      video = html.xpath('//h3')[0].text
      video = '%s%s' % (String.Quote(video), '/web')
      canonical_url = CANONICAL_URL % (studio, title, video)
      Log(" --> Canonical url: %s" % canonical_url)

      # Add the video.
      try:
        video = URLService.MetadataObjectForURL(canonical_url)
        oc.add(video)
      except:
        pass

    else:
      for clip in html.xpath('//li[contains(@class, "trailer")]'):
        video = clip.xpath('.//h3')[0].text
        video = '%s%s' % (String.Quote(video), '/web')
        canonical_url = CANONICAL_URL % (studio, title, video)
        Log(" --> Canonical url: %s" % canonical_url)

        # Add the video.
        try:
          video = URLService.MetadataObjectForURL(canonical_url)
          oc.add(video)
        except:
          pass

  if len(oc) == 0:
    return ObjectContainer(header="Empty", message="There aren't any items")
  else:
    return oc

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

  return Redirect(R(ICON))
