#!/usr/bin/env python

import os
import re
import csv
import time
import math
import numpy as np
import pandas as pd
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())		# SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables have been set in Windows

def spotify_search(row):
	title = row['title']
	artists = re.split(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist'])

	collaboration = False
	if re.findall(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist']):		# this works fine for the current top 100, but we'll come unstuck when new artist '666 featuring & 99' hits the streets. 'and' is case sensitive and ignores 'And's in artist names.
		collaboration=True

	q_title = title.replace('\'','')		# the API is tripped up by apostrophes
	q_artists = ' '.join(artists).replace('\'','')		# turns artists list into a string of artist names separated by spaces, which can be used in the search string
	q_str = 'track:"' + q_title + '" artist:' + q_artists		# spotipy accepts artist names separated by a space
	result = sp.search(q = q_str, type = 'track', limit = 50)

	df.at[index,'artists'] = []
	df.at[index,'release_date_wiki'] = datetime.strptime(row['release_date_wiki'], "%d/%m/%Y")
	df.at[index,'release_date'] = datetime.now()
	df.at[index,'collaboration'] = collaboration

	for item in result['tracks']['items']:
		item_title=re.split(r' \(feat\..*\)', item['name'])[0]		# ditch details of collaborators from the track name that Spotify sometimes adds e.g. '(feat. Young Thug)'
		item_title=re.split(r' \(with .*\)', item_title)[0]		# handle a couple more cases of collaborators being listed in the track name. Fine until there's a track title that legitimately contains this string pattern...
		if item_title.lower() == title.lower():		# in the absence of an exact match functionality in the API search
			if item['album']['release_date_precision'] == 'day':		# some albums only have precision in years or months, not days
				if datetime.strptime(item['album']['release_date'], "%Y-%m-%d") < df.at[index,'release_date']:
					df.at[index,'title'] = item_title
					df.at[index,'artists'].clear()
					for artist in item['artists']:
						df.at[index,'artists'].append(artist['name'])
					df.at[index,'album_type'] = item['album']['album_type']
					df.at[index,'release_date'] = datetime.strptime(item['album']['release_date'], "%Y-%m-%d")
					df.at[index,'release_date_diff'] = df.at[index,'release_date'] - df.at[index,'release_date_wiki']
					df.at[index,'release_date_precision'] = item['album']['release_date_precision']
					df.at[index,'duration_ms'] = item['duration_ms']
			elif item['album']['release_date_precision'] == 'year':
				if int(item['album']['release_date']) < df.at[index,'release_date'].year:
					df.at[index,'title'] = item_title
					df.at[index,'artists'].clear()
					for artist in item['artists']:
						df.at[index,'artists'].append(artist['name'])
					df.at[index,'album_type'] = item['album']['album_type']
					df.at[index,'release_date'] = datetime.strptime(item['album']['release_date'], "%Y")
					df.at[index,'release_date_diff'] = None
					df.at[index,'release_date_precision'] = item['album']['release_date_precision']
					df.at[index,'duration_ms'] = item['duration_ms']
			else:
				print(item_title + ' has release date precision of ' + item['album']['release_date_precision'])

	return(df)


df = pd.read_csv('list.csv', index_col = 0, encoding = 'cp1252')		# standard Windows encoding
df['artists'] = None		# add column
df['artists'] = df['artists'].astype('object')		# set datatype to object, so that artists column can hold a listsleep_min = 1
sleep_max = 3
start_time = time.time()
request_count = 0
for index, row in df.iterrows():
	track = spotify_search(row)
	request_count += 1
	if request_count % 5 == 0:
		time.sleep(np.random.uniform(sleep_min, sleep_max))
df.to_csv('outputlist.csv', encoding='utf-8-sig')		# specify the encoding so that Windows doesn't assume it's been exported as cp1252
