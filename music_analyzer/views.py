from django.shortcuts import render, redirect
from django.http import HttpResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from spotipy.exceptions import SpotifyException
from django.views.decorators.http import require_POST
from .models import SpotifyUser, TopTracksSnapshot



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
    refresh_token = token_info.get("refresh_token")
    sp = spotipy.Spotify(auth=access_token)

    limit = int(request.session.get("limit", 20))
    profile = sp.current_user()
    spotify_user_id = profile["id"]

    user = SpotifyUser.objects.filter(spotify_user_id=spotify_user_id).first()
    if user:
        user.access_token = access_token
        if refresh_token:
            user.refresh_token = refresh_token
        user.save()
    else:
        if not refresh_token:
            return redirect("spotify_login")
        SpotifyUser.objects.create(
            spotify_user_id=spotify_user_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )
    
    request.session["spotify_user_id"] = spotify_user_id

    return redirect("result")



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

def _current_user_row(request):
    spotify_user_id = request.session.get("spotify_user_id")
    if not spotify_user_id:
        return None
    return SpotifyUser.objects.filter(spotify_user_id=spotify_user_id).first()

def _spotify_client(user: SpotifyUser) -> spotipy.Spotify:
    sp = spotipy.Spotify(auth=user.access_token)
    try:
        sp.current_user()
        return sp
    except SpotifyException as e:
        if getattr(e, "http_status", None) == 401:
            new = sp_oauth.refresh_access_token(user.refresh_token)
            user.access_token = new["access_token"]
            user.save(update_fields=["access_token"])
            return spotipy.Spotify(auth=user.access_token)
        raise

@require_POST
def refresh_top(request):
    user = _current_user_row(request)
    if not user:
        return redirect("spotify_login")
    
    sp = _spotify_client(user)

    term = request.session.get("time_range", "short_term")
    limit = int(request.session.get("limit", 20))

    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=term)

    tracks = []
    for t in top_tracks["items"]:
        tracks.append({
            "name": t["name"],
            "article": t["article"],
            "album": {"images": t["album"]["images"]},
            "external_urls": t["external_urls"]
        })

    TopTracksSnapshot.objects.create(
        user=user,
        term=term,
        limit=limit,
        dat={"tracks": tracks},
    )

    return redirect("result")

def result(request):
    user = _current_user_row(request)
    if not user:
        return redirect("spotify_login")
    
    term = request.session.get("time_range", "short_term")
    limit = int(request.session.get("limit", 20))

    snap = (TopTracksSnapshot.objects
            .filter(user=user, term=term, limit=limit)
            .order_by("-fetched_at")
            .first())
    
    tracks = snap.data.get("tracks", []) if snap else []

    term_label = "1か月" if term == "short=term" else "6か月" if term == "medium_term" else "1年"

    return render(request, "music_analyzer/result.html", {
        "tracks": tracks,
        "limit" : limit,
        "term_label": term_label,
        "need_refresh": (snap is None),
    })
