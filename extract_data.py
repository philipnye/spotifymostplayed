#!/usr/bin/env python

import os
import re
import csv
import time
import math
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plot
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials())		# SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables have been set in Windows

def spotify_track_search(row):
	title = row['title']
	artists = re.split(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist'])

	collaboration = False
	if re.findall(r'\sand\s|\s&\s|,\s|\sfeaturing\s', row['artist']):		# this works fine for the current top 100, but we'll come unstuck when new artist '666 featuring & 99' hits the streets. 'and' is case sensitive and ignores 'And's in artist names.
		collaboration = True

	q_title = title.replace('\'', '')		# the API is tripped up by apostrophes
	q_artists = ' '.join(artists).replace('\'', '')		# turns artists list into a string of artist names separated by spaces, which can be used in the search string
	q_str = 'track:"' + q_title + '" artist:' + q_artists		# spotipy accepts artist names separated by a space
	result = sp.search(q = q_str, type = 'track', limit = 50)

	df.at[index, 'artists'] = []
	df.at[index, 'spotify_artist_IDs'] = []
	df['release_date_wiki'] = pd.to_datetime(df['release_date_wiki'], format='%d/%m/%Y')
	df.at[index, 'release_date'] = datetime.now()
	df.at[index, 'collaboration'] = collaboration

	for track_item in result['tracks']['items']:
		track_title = re.split(r' \(feat\..*\)', track_item['name'])[0]		# ditch details of collaborators from the track name that Spotify sometimes adds e.g. '(feat. Young Thug)'
		track_title = re.split(r' \(with .*\)', track_title)[0]		# handle a couple more cases of collaborators being listed in the track name. Fine until there's a track title that legitimately contains this string pattern...
		if track_title.lower() == title.lower():		# in the absence of an exact match functionality in the API search
			if track_item['album']['release_date_precision'] == 'day':		# some albums only have precision in years or months, not days
				if datetime.strptime(track_item['album']['release_date'], '%Y-%m-%d') < df.at[index, 'release_date']:
					df.at[index, 'title'] = track_title		# go with the styling conventions applied in Spotify
					df.at[index, 'artists'].clear()
					df.at[index, 'spotify_artist_IDs'].clear()
					for artist in track_item['artists']:
						df.at[index, 'artists'].append(artist['name'])
						df.at[index, 'spotify_artist_IDs'].append(artist['id'])
					df.at[index, 'album_type'] = track_item['album']['album_type']
					df.at[index, 'release_date'] = datetime.strptime(track_item['album']['release_date'], '%Y-%m-%d')
					df.at[index, 'duration_ms'] = track_item['duration_ms']
			elif track_item['album']['release_date_precision'] == 'year':
				if int(track_item['album']['release_date']) < df.at[index, 'release_date'].year:
					df.at[index, 'title'] = track_title
					df.at[index, 'artists'].clear()
					df.at[index, 'spotify_artist_IDs'].clear()
					for artist in track_item['artists']:
						df.at[index, 'artists'].append(artist['name'])
						df.at[index, 'spotify_artist_IDs'].append(artist['id'])
					df.at[index, 'album_type'] = track_item['album']['album_type']
					df.at[index, 'release_date'] = datetime.strptime(track_item['album']['release_date'], '%Y')
					df.at[index, 'duration_ms'] = track_item['duration_ms']
			else:
				print(track_title + ' has release date precision of ' + track_item['album']['release_date_precision'])

def spotify_artist_search(row, artist):
	q_str = 'artist:' + artist
	result = sp.search(q = q_str, type = 'artist', limit = 50)

	for artist_item in result['artists']['items']:
		if artist_item['name'] == artist:
			df.at[index, 'genres'].append(artist_item['genres'])
			df.at[index, 'followers'].append(artist_item['followers']['total'])
			break		# takes the top artist, matching exactly on artist name


df = pd.read_csv('list.csv', index_col = 0, encoding = 'cp1252')		# standard Windows encoding
df['artists'] = None		# add column
df['artists'] = df['artists'].astype('object')		# set datatype to object, so that artists column can hold a list
df['spotify_artist_IDs'] = None
df['spotify_artist_IDs'] = df['spotify_artist_IDs'].astype('object')
df['primary_artists'] = None
df['primary_artists'] = df['primary_artists'].astype('object')
df['contributing_artists'] = None
df['contributing_artists'] = df['contributing_artists'].astype('object')
df['genres'] = None
df['followers'] = None
df['streams'] = pd.to_numeric(df['streams'].str.replace(',', ''))
sleep_min = 1
sleep_max = 3
request_count = 0
for index, row in df.iterrows():
	spotify_track_search(row)
	df.at[index, 'genres'] = []
	df.at[index, 'followers'] = []
	for artist in df.at[index, 'artists']:
		spotify_artist_search(row, artist)
	request_count += 1
	if request_count % 5 == 0:
		time.sleep(np.random.uniform(sleep_min, sleep_max))


## Analysis
df.head()
df.dtypes

# Streams
df[['artist', 'streams']].plot.bar(rot = 0, title = 'Top 100 Spotify hits by streams')
df['streams'].median()
df['streams'].max()
df['streams'].min()

# Gender
df[['artist', 'lead_artist_category']].groupby('lead_artist_category').count()
df.loc[(df['lead_artist_category'].str.len() == 1) & (df['lead_artist_category'] != 'G'), ['artist','lead_artist_category']].groupby('lead_artist_category').count()
ch1 = df.loc[(df['lead_artist_category'].str.len() == 1) & (df['lead_artist_category'] != 'G'), ['artist','lead_artist_category']].groupby('lead_artist_category').count().plot.barh(rot = 0, title = 'Solo top 100 Spotify hits by gender')
ch1.get_legend().remove()

# Release year
ch2 = sns.countplot(df.release_date.dt.year, order = list(range(1975,2021)))		# needs to be one higher than what we actually want to plot
ch2.set(xlabel = 'Release year', ylabel = '')

# Artist
a = pd.Series(sum([item for item in df.artists], []))
df2 = a.groupby(a).size().rename_axis('artist').reset_index(name = 'tally')
df2.sort_values(['tally', 'artist'], ascending = [False, True]).reset_index(drop = True)

# Collaboration
df[['artist', 'collaboration']].groupby('collaboration').count()
