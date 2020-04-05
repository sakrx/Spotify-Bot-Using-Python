'''
Step 1: Log into youtube
Step 2: Grab our liked videos
Step 3: Create a new playlist on spotify
Step 4: Add liked song into spotify playlist
'''

import json
import os

from exceptions import ResponseException
from secrets import spotify_user_id as id
from secrets import spotify_token

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
import requests

class CreatePlaylist:

    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    def get_youtube_client(self):
        # copied from YouTube Data Api
        os.environ["OAUTH_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials = credentials)

        return youtube_client
        


    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        # get liked video and their important info
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            # get song name and artist name from youtube_dl
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)

            song_name = video["track"]
            artist_name = video["artist"]

            if song_name is not None and artist_name is not None :
                # save info
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist_name": artist_name,

                    # add the uri
                    "spotify_uri": self.get_spotify_uri(song_name, artist_name)
                }



    def create_playlist(self):
        # create new playlist
        request_body = json.dumps({
            "name": "YouTube Liked Songs",
            "description": "Liked Youtube Songs",
            "public": True
            })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()

        # playlist id
        return response_json["id"]

    def get_spotify_uri(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=tract%3A{}+artist%3A{}&tyoe=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # only use the first song
        uri = songs[0]["uri"]

        return uri




    def add_song_to_playlist(self):
        # populate our songs dictionary
        self.get_liked_videos()

        # collect all of uri
        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        # create playlist
        playlist_id = self.create_playlist()

        # add all songs into playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }

        )

        # make sure response status is 200
        if response.status_code != 200:
            raise ResponseException(response.status_code)


        response_json = response.json()
        return response_json


 if __name__ =='__main__':
        cp = CreatePlaylist()
        cp.add_song_to_playlist()