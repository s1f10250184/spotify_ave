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
    profile = sp.current_user()

    term = request.session.get("time_range", "short_term")
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=term)
    items = top_tracks["items"]
    for t in items:
        track_name = t["name"]
        artist_name = t["artists"][0]["name"]
        print(f"{track_name} {artist_name}")

    if term == "short_term":
        term_label = "1か月"
    elif term == "medium_term":
        term_label = "6か月"
    else:
        term_label = "1年"

    return render(request, "music_analyzer/result.html", {
        "tracks": items,
        "limit": limit,
        "term_label":term_label,
    })



sp_oauth = SpotifyOAuth(
    client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
    client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
    redirect_uri="http://127.0.0.1:8000/callback/",
    scope="user-top-read user-read-recently-played"
)

def spotify_login(request):
    limit = request.GET.get("music_num")
    term = request.GET.get("time_range")
    if not limit:
        limit = 20
    else:
        limit = int(limit)
    
    if not term:
        term = "short_term"

    request.session["limit"] = limit
    request.session["time_range"] = term
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)
