import os
import csv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

artists=['Post Malone','21 Savage']
track='rockstar'

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())		# SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables have been set in Windows
str = 'track:"'+track+'" artist:'+' '.join(artists)+''		# will accept artist names separated by a space
result = sp.search(q=str,type='track',limit=50)

track_count=0
track_data={
	'name':None,
	'artists':[],
	'album_type':None,
	'release_date':None,
	'duration_ms':None
}

for item in result['tracks']['items']:
	if item['album']['album_type']=='single' and item['name']==track:		# second condition is to weed out remixes etc.
		track_count+=1
		track_data['name']=item['name']
		for artist in item['artists']:
			track_data['artists'].append(artist['name'])
		track_data['album_type']=item['album']['album_type']
		track_data['release_date']=item['album']['release_date']
		track_data['duration_ms']=item['duration_ms']
		print(track_data)
	elif item['album']['album_type']=='album' and item['name']==track:
		track_count+=1
		track_data['name']=item['name']
		for artist in item['artists']:
			track_data['artists'].append(artist['name'])
		track_data['album_type']=item['album']['album_type']
		track_data['release_date']=item['album']['release_date']
		track_data['duration_ms']=item['duration_ms']
		print(track_data)
