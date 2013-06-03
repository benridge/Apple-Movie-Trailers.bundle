AMT_SITE_URL = 'http://trailers.apple.com'
AMT_JSON_URL = 'http://trailers.apple.com/trailers/home/feeds/%s.json'
ALL_VIDEOS_INC = '%s/includes/automatic.html'

####################################################################################################
def Start():

	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

	ObjectContainer.content = ContainerContent.GenericVideos
	ObjectContainer.title1 = 'Apple Movie Trailers'

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/536.29.13 (KHTML, like Gecko) Version/6.0.4 Safari/536.29.13'

####################################################################################################
@handler('/video/amt', 'Apple Movie Trailers')
def MainMenu():

	oc = ObjectContainer(view_group='List')

	oc.add(DirectoryObject(key=Callback(Categories, name='just_added'), title=L('just_added')))
	oc.add(DirectoryObject(key=Callback(Categories, name='exclusive'), title=L('exclusive')))
	oc.add(DirectoryObject(key=Callback(Categories, name='most_pop'), title=L('most_pop')))
	oc.add(DirectoryObject(key=Callback(Genres), title=L('genres')))
	oc.add(DirectoryObject(key=Callback(Studios), title=L('movie_studios')))
	oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.amt', title='Search Trailers', prompt='Search for Movie Trailers', term=L('Trailers')))

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

		thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg')
		thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg')

		oc.add(DirectoryObject(
			key = Callback(Videos, url=url, title=title),
			title = title,
			thumb = Resource.ContentsOfURLWithFallback([thumb_xlarge, thumb_large, thumb])
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

			if not thumb.startswith('http://'):
				thumb = '%s%s' % (AMT_SITE_URL, thumb)

			thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg')
			thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg')

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback([thumb_xlarge, thumb_large, thumb])
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

			if not thumb.startswith('http://'):
				thumb = '%s%s' % (AMT_SITE_URL, thumb)

			thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg')
			thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg')

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback([thumb_xlarge, thumb_large, thumb])
			))

	return oc

####################################################################################################
@route('/video/amt/videos', allow_sync=True)
def Videos(url, title):

	oc = ObjectContainer(view_group='InfoList', title2=title)

	if not url.startswith('http://'):
		url = '%s%s' % (AMT_SITE_URL, url)

	inc_html = HTML.ElementFromURL(ALL_VIDEOS_INC % url.strip('/'))

	for video in inc_html.xpath('//a/h4/parent::a/@href'):
		video = video.split('/')[1]

		try:
			oc.add(URLService.MetadataObjectForURL('%s#%s' % (url, video)))
		except:
			pass

	if len(oc) < 1:
		return ObjectContainer(header="Empty", message="There aren't any items")

	return oc
