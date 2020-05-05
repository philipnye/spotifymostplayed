import os
import re
import csv
import time
import numpy as np
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())		# SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables have been set in Windows

track_data = {
	'rank': None,
	'title': None,
	'artists': None,
	'album_type': None,
	'release_date': None,
	'release_date_precision': None,
	'release_date_wiki': None,
	'release_date_diff': None,
	'duration_ms': None,
	'streams': None,
	'collaboration': None,
	'lead_artist_category': None
}

def spotify_search(row):
	global track_data

	title=row['title']
	artists=re.split(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist'])

	collaboration=False
	if re.findall(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist']):		# this works fine for the current top 100, but we'll come unstuck when new artist '666 featuring & 99' hits the streets. 'and' is case sensitive and ignores 'And's in artist names.
		collaboration=True

	q_title = title.replace('\'','')		# the API is tripped up by apostrophes
	q_artists=' '.join(artists).replace('\'','')		# turns artists list into a string of artist names separated by spaces, which can be used in the search string
	q_str = 'track:"' + q_title + '" artist:' + q_artists		# spotipy accepts artist names separated by a space
	result = sp.search(q=q_str,type='track',limit=50)

	track_data = dict.fromkeys(track_data, None)		# set all values to None

	track_data['rank'] = row['rank']
	track_data['artists'] = []
	track_data['release_date_wiki'] = datetime.strptime(row['release_date'], "%d/%m/%Y")
	track_data['streams'] = row['streams']
	track_data['collaboration'] = collaboration
	track_data['lead_artist_category'] = row['lead_artist_category']

	for item in result['tracks']['items']:
		item_title=re.split(r' \(feat\..*\)', item['name'])[0]		# ditch details of collaborators from the track name that Spotify sometimes adds e.g. '(feat. Young Thug)'
		item_title=re.split(r' \(with .*\)', item_title)[0]		# handle a couple more cases of collaborators being listed in the track name. Fine until there's a track title that legitimately contains this string pattern...
		if item_title.lower() == title.lower():		# in the absence of an exact match functionality in the API search
			if item['album']['release_date_precision'] == 'day':		# some albums only have precision in years or months, not days
				if track_data['release_date'] is None or datetime.strptime(item['album']['release_date'], "%Y-%m-%d") < track_data['release_date']:
					track_data['title'] = item_title
					track_data['artists'].clear()
					for artist in item['artists']:
						track_data['artists'].append(artist['name'])
					track_data['album_type'] = item['album']['album_type']
					track_data['release_date'] = datetime.strptime(item['album']['release_date'], "%Y-%m-%d")
					track_data['release_date_diff'] = track_data['release_date'] - track_data['release_date_wiki']
					track_data['release_date_precision'] = item['album']['release_date_precision']
					track_data['duration_ms'] = item['duration_ms']
			elif item['album']['release_date_precision'] == 'year':		# our dataset doesn't have any tracks with precision of 'month'
				if track_data['release_date'] is None or int(item['album']['release_date']) < track_data['release_date'].year:
					track_data['title'] = item_title
					track_data['artists'].clear()
					for artist in item['artists']:
						track_data['artists'].append(artist['name'])
					track_data['album_type'] = item['album']['album_type']
					track_data['release_date'] = datetime.strptime(item['album']['release_date'], "%Y")
					track_data['release_date_diff'] = None
					track_data['release_date_precision'] = item['album']['release_date_precision']
					track_data['duration_ms'] = item['duration_ms']
			else:
				print(item_title + ' has release date precision of ' + item['album']['release_date_precision'])

	return(track_data)


with open('list.csv', newline='') as infile:
	reader = csv.DictReader(infile)
	with open('outputlist.csv', 'w', newline='') as outfile:
		w = csv.DictWriter(outfile, track_data.keys())
		w.writeheader()
		sleep_min = 2
		sleep_max = 5
		start_time = time.time()
		request_count = 0
		for row in reader:
			track = spotify_search(row)
			w.writerow(track)
			request_count += 1
			if request_count % 5 == 0:
				time.sleep(np.random.uniform(sleep_min, sleep_max))
