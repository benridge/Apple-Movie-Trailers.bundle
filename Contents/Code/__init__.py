AMT_JSON_URL = 'http://%s/trailers/home/feeds/%s.json'
ALL_VIDEOS_INC = '%s/includes/automatic.html'

####################################################################################################
def Start():

	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

	ObjectContainer.content = ContainerContent.GenericVideos
	ObjectContainer.title1 = 'Apple Movie Trailers'

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1'
	HTTP.Headers['Host'] = 'trailers.apple.com'

####################################################################################################
@handler('/video/amt', 'Apple Movie Trailers')
def MainMenu():

	oc = ObjectContainer(view_group='List')

	oc.add(DirectoryObject(key=Callback(Categories, name='just_added'), title=L('just_added')))
	oc.add(DirectoryObject(key=Callback(Categories, name='exclusive'), title=L('exclusive')))
	oc.add(DirectoryObject(key=Callback(Categories, name='most_pop'), title=L('most_pop')))
	oc.add(DirectoryObject(key=Callback(Genres), title=L('genres')))
	oc.add(DirectoryObject(key=Callback(Studios), title=L('movie_studios')))

	if Client.Product not in ('PlexConnect'):
		oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.amt', title='Search Trailers', prompt='Search for Movie Trailers', term=L('Trailers')))

	return oc

####################################################################################################
@route('/video/amt/categories/{name}')
def Categories(name):

	oc = ObjectContainer(view_group='List', title2=L(name))

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % (GetHost(), name)):
		url = trailer['location']
		title = trailer['title']
		thumb = trailer['poster']

		if not thumb.startswith('http://'):
			thumb = 'http://trailers.apple.com/%s' % thumb.lstrip('/')

		thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg')
		thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg')

		oc.add(DirectoryObject(
			key = Callback(Videos, url=url, title=title),
			title = title,
			thumb = Callback(GetThumb, thumbs=[thumb_xlarge, thumb_large, thumb], client=Client.Product)
		))

	return oc

####################################################################################################
@route('/video/amt/genres')
def Genres():

	oc = ObjectContainer(view_group='List', title2=L('genres'))
	genres = []

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % (GetHost(), 'genres')):
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

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % (GetHost(), 'genres')):
		if genre in trailer['genre']:
			url = trailer['location']
			title = trailer['title']
			thumb = trailer['poster']

			if not thumb.startswith('http://'):
				thumb = 'http://trailers.apple.com/%s' % thumb.lstrip('/')

			thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg')
			thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg')

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Callback(GetThumb, thumbs=[thumb_xlarge, thumb_large, thumb], client=Client.Product)
			))

	return oc

####################################################################################################
@route('/video/amt/studios')
def Studios():

	oc = ObjectContainer(view_group='List', title2=L('genres'))
	studios = []

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % (GetHost(), 'studios')):
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

	for trailer in JSON.ObjectFromURL(AMT_JSON_URL % (GetHost(), 'studios')):
		if studio == trailer['studio']:
			url = trailer['location']
			title = trailer['title']
			thumb = trailer['poster']

			if not thumb.startswith('http://'):
				thumb = 'http://trailers.apple.com/%s' % thumb.lstrip('/')

			thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg')
			thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg')

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Callback(GetThumb, thumbs=[thumb_xlarge, thumb_large, thumb], client=Client.Product)
			))

	return oc

####################################################################################################
@route('/video/amt/videos', allow_sync=True)
def Videos(url, title):

	oc = ObjectContainer(view_group='InfoList', title2=title)

	if not url.startswith('http://'):
		url = 'http://%s/%s' % (GetHost(), url.lstrip('/'))
	else:
		url = 'http://%s/%s' % (GetHost(), url.split('.apple.com/')[-1])

	inc_html = HTML.ElementFromURL(ALL_VIDEOS_INC % url.strip('/'))

	for video in inc_html.xpath('//a/h4/parent::a/@href'):
		video = video.split('/')[1]

		try:
			oc.add(URLService.MetadataObjectForURL('%s#%s' % (url.replace('www.apple.com', 'trailers.apple.com'), video)))
		except:
			pass

	if len(oc) < 1:
		return ObjectContainer(header="Empty", message="There aren't any items")

	return oc

####################################################################################################
def GetHost():

	if Client.Product == 'PlexConnect':
		return 'www.apple.com'
	else:
		return 'trailers.apple.com'

####################################################################################################
def GetThumb(thumbs=[], client=''):

	for url in thumbs:
		if client == 'PlexConnect':
			url = url.replace('http://trailers.apple.com/', 'http://www.apple.com/')

		try:
			data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
			return DataObject(data, 'image/jpeg')
		except:
			continue

	return Redirect('http://resources-cdn.plexapp.com/image/source/com.plexapp.plugins.amt.jpg')
