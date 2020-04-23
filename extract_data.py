import os
import re
import csv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())		# SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables have been set in Windows

def spotify_search(artists,track):
	q_track = track.replace('\'','')		# the API is tripped up by apostrophes
	q_artists=' '.join(artists).replace('\'','')		# turns artists list into a string of artist names separated by spaces, which can be used in the search string
	q_str = 'track:"' + q_track + '" artist:' + q_artists		# spotipy accepts artist names separated by a space
	result = sp.search(q=q_str,type='track',limit=50)

	track_data={
		'name':None,
		'artists':[],
		'album_type':None,
		'release_date':None,
		'duration_ms':None
	}

	for item in result['tracks']['items']:
		item_name=re.split(r' \(feat\..*\)', item['name'])[0]		# ditch details of collaborators from the track name that Spotify sometimes adds e.g. '(feat. Young Thug)'
		item_name=re.split(r' \(with .*\)', item_name)[0]		# handle a couple more cases of collaborators being listed in the track name. Fine until there's a track title that legitimately contains this string pattern...
		if item_name.lower() == track.lower():		# in the absence of an exact match functionality in the API search
			if track_data['release_date'] is None or item['album']['release_date'] < track_data['release_date']:
				track_data['name'] = item_name
				track_data['artists'].clear()
				for artist in item['artists']:
					track_data['artists'].append(artist['name'])
				track_data['album_type'] = item['album']['album_type']
				track_data['release_date'] = item['album']['release_date']
				track_data['duration_ms'] = item['duration_ms']

	print(track_data)

with open('list.csv', newline='') as infile:
	reader = csv.DictReader(infile)
	for row in reader:
		collaboration=False
		track=row['track']
		artists=re.split(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist'])
		if re.findall(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist']):		# this works fine for the current top 100, but we'll come unstuck when new artist '666 featuring & 99' hits the streets. 'and' is case sensitive and ignores 'And's in artist names.
			collaboration=True
		spotify_search(artists,track)
