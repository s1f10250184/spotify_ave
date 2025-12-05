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
    profile = sp.current_user()

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
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


