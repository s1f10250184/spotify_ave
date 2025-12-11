from django.shortcuts import render, redirect
from django.http import HttpResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os


# Create your views here.
def index(request):
    return render(request, 'music_analyzer/index.html')

def spotify_login_page(request):
    limit = request.GET.get("limit", 20) 
    request.session["limit"] = limit       
    return render(request, "music_analyzer/index.html", {"limit": limit})


def spotify_callback(request):
    code = request.GET.get("code")
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info["access_token"]
    sp = spotipy.Spotify(auth=access_token)

    limit = int(request.session.get("limit", 20))
    top_tracks = sp.current_user_top_tracks(limit=limit)
    items = top_tracks["items"]
    print(items[0])
    profile = sp.current_user()

#これ以降の部分は使えなくなったらしいけどどうにかして使いたい    
#    track_ids = [track["id"] for track in items]
#   all_features = []
#    print("TRACK IDS:", track_ids)
#    print("CHUNKS:")
#    for i in range(0, len(track_ids), 1):
#        chunk = track_ids[i : i+1]
#        feats = sp.audio_features(chunk)
#        all_features.extend(feats)
    
#    tracks = []
#    for track, f in zip(items, all_features):
#        if f is None:
#            continue

#    tracks.append({
#            "name" : track["name"],
#            "artist":track["artists"][0]["name"],
#            "image":track["album"]["images"][0]["url"],
#            "energy":f["energy"],
#            "tempo":f["tempo"],
#            "valence":f["valence"],
#            "key":f["key"],
#            "loudness":f["loudness"],
#        })
#    recent = sp.current_user_recently_played(limit=10)
#    items = recent["items"]
#    track_ids = [item["track"]["id"] for item in items]
#    features = sp.audio_features(track_ids)

#同じくここも使えない？
#    result = []
#    for track, feat in zip(items, features):
#        result.append({
#            "name":track["name"],
#            "artist":track["artists"][0]["name"],
#            "tempo":feat["tempo"],
#            "energy":feat["energy"],
#            "valence":feat["valence"],
#            "image":track["album"]["images"][0]["url"],
#        })

    return render(request, "music_analyzer/result.html", {
        "tracks": items,
        "limit": limit
    })



sp_oauth = SpotifyOAuth(
    client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
    client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
    redirect_uri="http://127.0.0.1:8000/callback/",
    scope="user-top-read user-read-recently-played"
)

def spotify_login(request):
    limit = request.GET.get("music_num")
    if not limit:
        limit = 20
    else:
        limit = int(limit)

    request.session["limit"] = limit
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


