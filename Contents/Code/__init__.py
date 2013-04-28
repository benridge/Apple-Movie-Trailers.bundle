AMT_SITE_URL = 'http://trailers.apple.com'
AMT_JSON_URL = 'http://trailers.apple.com/trailers/home/feeds/%s.json'
AMT_XML_NS = {'a': 'http://www.apple.com/itms/'}
XML_HTTP_HEADERS = {'User-Agent': 'iTunes/10.7'}
RE_XML_URL = Regex('^/moviesxml/s/([^/]+)/([^/]+)/(.+)\.xml$')
CANONICAL_URL = 'http://trailers.apple.com/trailers/%s/%s/#%s'

####################################################################################################
def Start():

	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

	ObjectContainer.content = ContainerContent.GenericVideos
	ObjectContainer.title1 = 'Apple Movie Trailers'

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17'

####################################################################################################
@handler('/video/amt', 'Apple Movie Trailers')
def MainMenu():

	oc = ObjectContainer(view_group='List')

	oc.add(DirectoryObject(key=Callback(Categories, name='just_added'), title=L('just_added')))
	oc.add(DirectoryObject(key=Callback(Categories, name='exclusive'), title=L('exclusive')))
	oc.add(DirectoryObject(key=Callback(Categories, name='most_pop'), title=L('most_pop')))
	oc.add(DirectoryObject(key=Callback(Genres), title=L('genres')))
	oc.add(DirectoryObject(key=Callback(Studios), title=L('movie_studios')))
	oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.amt', title='Search Trailers', prompt='Search for movie trailer', term=L('Trailers')))

	return oc

####################################################################################################
@route('/video/amt/categories/{name}')
def Categories(name):

	oc = ObjectContainer(view_group='List', title2=L(name))

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % name):
		url = trailer['location']
		title = trailer['title']
		thumb = trailer['poster']

		if not thumb.startswith('http://'):
			thumb = '%s%s' % (AMT_SITE_URL, thumb)

		large_thumb = thumb.replace('.jpg', '-large.jpg')

		oc.add(DirectoryObject(
			key = Callback(Videos, url=url, title=title),
			title = title,
			thumb = Resource.ContentsOfURLWithFallback([large_thumb, thumb])
		))

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
		oc.add(DirectoryObject(
			key = Callback(Genre, genre=genre),
			title = genre
		))

	return oc

####################################################################################################
@route('/video/amt/genre/{genre}')
def Genre(genre):

	oc = ObjectContainer(view_group='List', title2=genre)

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'genres'):
		if genre in trailer['genre']:
			url = trailer['location']
			title = trailer['title']
			thumb = trailer['poster']

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Callback(Thumb, url=thumb)
			))

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
		oc.add(DirectoryObject(
			key = Callback(Studio, studio=studio),
			title = studio
		))

	return oc

####################################################################################################
@route('/video/amt/studio/{studio}')
def Studio(studio):

	oc = ObjectContainer(view_group='List', title2=studio)

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % 'studios'):
		if studio == trailer['studio']:
			url = trailer['location']
			title = trailer['title']
			thumb = trailer['poster']

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Callback(Thumb, url=thumb)
			))

	return oc

####################################################################################################
@route('/video/amt/videos', allow_sync=True)
def Videos(url, title):

	oc = ObjectContainer(view_group='InfoList', title2=title)
	xml = None
	url = '%s/%s/itsxml/%%s.xml' % (AMT_SITE_URL, url.strip('/'))

	for clip_type in ('trailer', 'teaser', 'clip', 'trailer1', 'featurette', 'internationaltrailer', 'firstlook'):
		try:
			xml = XML.ElementFromURL(url % clip_type, headers=XML_HTTP_HEADERS)
			break
		except:
			pass

	if not xml:
		Log(" --> Couldn't find an xml file.")
		return ObjectContainer(header="Empty", message="There aren't any items.")

	# Get the URL and compute the canonical URL.
	# Example: /moviesxml/s/disney/piratesofthecaribbeanonstrangertides/trailer2.xml
	for xml_url in xml.xpath('//a:HBoxView/a:GotoURL/@url', namespaces=AMT_XML_NS):
		(studio, title, video) = RE_XML_URL.findall(xml_url)[0]
		canonical_url = CANONICAL_URL % (studio, title, video)
		Log(" --> Canonical url: %s" % canonical_url)

		# Add the video.
		try:
			video = URLService.MetadataObjectForURL(canonical_url)
			oc.add(video)
		except:
			pass

	if len(oc) < 1:
		return ObjectContainer(header="Empty", message="There aren't any items")

	return oc
