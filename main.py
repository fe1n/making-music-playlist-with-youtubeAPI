import httplib2
import os

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
        scope=YOUTUBE_UPLOAD_SCOPE,
        message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))

youtube = get_authenticated_service()

def get_my_content():
    request = youtube.channels().list(
        part="contentDetails",
        mine=True
    )

    response = request.execute()
    return response


def get_video_id_in_playlist(playlistId):
    video_id_list = []

    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        playlistId=playlistId,
        fields="nextPageToken,items/snippet/resourceId/videoId"
    )
    while request:
        response = request.execute()
        video_id_list.extend(list(map(lambda item: item["snippet"]["resourceId"]["videoId"], response["items"])))
        request = youtube.playlistItems().list_next(request, response)

    return video_id_list

def create_playlist(title):
    playlists_insert_response = youtube.playlists().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
            title=title
            ),
            status=dict(
            privacyStatus="private"
            )
        )
    ).execute()
    return playlists_insert_response["id"]

def get_video_category(id):
    request = youtube.videos().list(
        part="snippet",
        id=id
    )
    response = request.execute()['items'][0]['snippet']['categoryId']
    return response

def make_music_playlist(source_playlist, name):
    music_playlist = create_playlist(name)
    videos = get_video_id_in_playlist(source_playlist)
    cnt = 0
    for video in videos:
        cnt+=1
        if(cnt%50==0):
            print(cnt, " / ", len(videos))
        try:
            category = get_video_category(video)
            if category=="10":
                request_body = {
                    'snippet': {
                        'playlistId': music_playlist,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video
                        }
                    }
                }
                youtube.playlistItems().insert(
                    part='snippet',
                    body=request_body
                ).execute()
        except:
            continue

    print('finish!')


response = get_my_content()
likedId = response['items'][0]['contentDetails']['relatedPlaylists']['likes']
make_music_playlist(likedId, "Music")