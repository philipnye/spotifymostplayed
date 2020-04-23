import os
import re
import csv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())		# SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables have been set in Windows

def spotify_search(artists,track):
	str = 'track:"'+track+'" artist:'+artists		# spotipy accepts artist names separated by a space
	result = sp.search(q=str,type='track',limit=50)

	track_data={
		'name':None,
		'artists':[],
		'album_type':None,
		'release_date':None,
		'duration_ms':None
	}

	for item in result['tracks']['items']:
		if track_data['release_date'] is None or item['album']['release_date']<track_data['release_date']:
			track_data['name']=item['name']
			track_data['artists'].clear()
			for artist in item['artists']:
				track_data['artists'].append(artist['name'])
			track_data['album_type']=item['album']['album_type']
			track_data['release_date']=item['album']['release_date']
			track_data['duration_ms']=item['duration_ms']

	print(track_data)

with open('list.csv', newline='') as infile:
	reader = csv.DictReader(infile)
	for row in reader:
		artists=re.split(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist'])		# This works fine for the current top 100, but we'll come unstuck when new artist 'featuring&&&69' hits the streets. 'and' is case sensitive and ignores 'And's in artist names.
		track=row['track']
		artists=' '.join(artists)
		str = 'track:"'+track+'" artist:'+artists		# spotipy accepts artist names separated by a space
		spotify_search(artists,track)
