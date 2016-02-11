ITUNES_JSON_URL = 'http://movietrailers.apple.com/trailers/home/feeds/%s.json'
MOVIE_JSON_URL = 'http://movietrailers.apple.com/trailers/%s/%s/data/page.json'
MOVIE_URL = 'http://movietrailers.apple.com/trailers/%s/%s/#%s'
RE_URL_INFO = Regex('trailers\/([^\/]+)\/([^\/]+)')

####################################################################################################
def Start():

	ObjectContainer.title1 = 'iTunes Movie Trailers'
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/601.4.4 (KHTML, like Gecko) Version/9.0.3 Safari/601.4.4'

####################################################################################################
@handler('/video/amt', 'iTunes Movie Trailers')
def MainMenu():

	oc = ObjectContainer()

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

	oc = ObjectContainer(title2=L(name))

	for trailer in JSON.ObjectFromURL(ITUNES_JSON_URL % (name)):

		url = trailer['location']
		title = trailer['title']
		thumb = trailer['poster']

		if not thumb.startswith('http://'):
			thumb = 'http://movietrailers.apple.com/%s' % thumb.lstrip('/')

		thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg').replace('http://trailers.apple.com/', 'http://movietrailers.apple.com/')
		thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg').replace('http://trailers.apple.com/', 'http://movietrailers.apple.com/')

		oc.add(DirectoryObject(
			key = Callback(Videos, url=url, title=title),
			title = title,
			thumb = Resource.ContentsOfURLWithFallback(url=[thumb_xlarge, thumb_large, thumb])
		))

	return oc

####################################################################################################
@route('/video/amt/genres')
def Genres():

	oc = ObjectContainer(title2=L('genres'))
	genres = []

	for trailer in JSON.ObjectFromURL(ITUNES_JSON_URL % ('genres')):

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

	oc = ObjectContainer(title2=genre)

	for trailer in JSON.ObjectFromURL(ITUNES_JSON_URL % ('genres')):

		if genre in trailer['genre']:

			url = trailer['location']
			title = trailer['title']
			thumb = trailer['poster']

			if not thumb.startswith('http://'):
				thumb = 'http://movietrailers.apple.com/%s' % thumb.lstrip('/')

			thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg').replace('http://trailers.apple.com/', 'http://movietrailers.apple.com/')
			thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg').replace('http://trailers.apple.com/', 'http://movietrailers.apple.com/')

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(url=[thumb_xlarge, thumb_large, thumb])
			))

	return oc

####################################################################################################
@route('/video/amt/studios')
def Studios():

	oc = ObjectContainer(title2=L('genres'))
	studios = []

	for trailer in JSON.ObjectFromURL(ITUNES_JSON_URL % ('studios')):

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

	oc = ObjectContainer(title2=studio)

	for trailer in JSON.ObjectFromURL(ITUNES_JSON_URL % ('studios')):

		if studio == trailer['studio']:

			url = trailer['location']
			title = trailer['title']
			thumb = trailer['poster']

			if not thumb.startswith('http://'):
				thumb = 'http://movietrailers.apple.com/%s' % thumb.lstrip('/')

			thumb_large = thumb.replace('poster.jpg', 'poster-large.jpg').replace('http://trailers.apple.com/', 'http://movietrailers.apple.com/')
			thumb_xlarge = thumb.replace('poster.jpg', 'poster-xlarge.jpg').replace('http://trailers.apple.com/', 'http://movietrailers.apple.com/')

			oc.add(DirectoryObject(
				key = Callback(Videos, url=url, title=title),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(url=[thumb_xlarge, thumb_large, thumb])
			))

	return oc

####################################################################################################
@route('/video/amt/videos', allow_sync=True)
def Videos(url, title):

	oc = ObjectContainer(title2=title)

	(studio, movie_title) = RE_URL_INFO.findall(url)[0]
	json_obj = JSON.ObjectFromURL(MOVIE_JSON_URL % (studio, movie_title))

	for clip in json_obj['clips']:

		clip_type = String.Quote(clip['title'])

		try:
			oc.add(URLService.MetadataObjectForURL(MOVIE_URL % (studio, movie_title, clip_type)))
		except:
			pass

	if len(oc) < 1:
		return ObjectContainer(header="Empty", message="There aren't any items")

	return oc
