import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import SpotifyUser, TopTrackSnapshot


# OAuth設定
def get_sp_oauth():
    return SpotifyOAuth(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI"),
        scope="user-top-read user-read-recently-played",
)


def index(request):
    return render(request, "music_analyzer/index.html")


def spotify_login(request):
    limit = request.GET.get("music_num")
    term = request.GET.get("time_range")

    if limit:
        request.session["limit"] = int(limit)
    else:
        request.session.setdefault("limit", 20)

    if term:
        request.session["time_range"] = term
    else:
        request.session.setdefault("time_range", "short_term")
    if request.session.get("spotify_user_id"):
        return redirect("result")
    sp_oauth = get_sp_oauth()
    return redirect(sp_oauth.get_authorize_url())



def _term_label(term: str) -> str:
    return {"short_term": "1か月", "medium_term": "6か月", "long_term": "1年"}.get(term, "1年")


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
        if getattr(e, "http_status", None) == 401 and user.refresh_token:
            sp_oauth = get_sp_oauth
            new = sp_oauth.refresh_access_token(user.refresh_token)
            user.access_token = new["access_token"]
            user.save(update_fields=["access_token"])
            return spotipy.Spotify(auth=user.access_token)
        raise


def _save_snapshot(user: SpotifyUser, items: list, term: str, limit: int):
    tracks = []
    for t in items:
        tracks.append({
            "name": t["name"],
            "artists": t["artists"],
            "album": {"images": t["album"]["images"]},
            "external_urls": t["external_urls"],
        })

    TopTrackSnapshot.objects.create(
        user=user,
        term=term,
        limit=limit,
        data={"tracks": tracks},
    )


def spotify_callback(request):
    code = request.GET.get("code")
    token_info = sp_oauth.get_access_token(code)
    sp_oauth = get_sp_oauth
    access_token = token_info["access_token"]
    refresh_token = token_info.get("refresh_token")

    sp = spotipy.Spotify(auth=access_token)
    spotify_user_id = sp.current_user()["id"]

    user, created = SpotifyUser.objects.get_or_create(
        spotify_user_id=spotify_user_id,
        defaults={"access_token": access_token, "refresh_token": refresh_token or ""},
    )
    if not created:
        user.access_token = access_token
        if refresh_token:
            user.refresh_token = refresh_token
        user.save()

    request.session["spotify_user_id"] = spotify_user_id

    # ここは session から読む（キーを統一）
    term = request.session.get("time_range", "short_term")
    limit = int(request.session.get("limit", 20))

    has_snap = TopTrackSnapshot.objects.filter(user=user, term=term, limit=limit).exists()
    if not has_snap:
        top_tracks = sp.current_user_top_tracks(limit=limit, time_range=term)
        _save_snapshot(user, top_tracks["items"], term, limit)

    return redirect("result")


def result(request):
    user = _current_user_row(request)
    if not user:
        return redirect("spotify_login")

    term = request.session.get("time_range", "short_term")
    limit = int(request.session.get("limit", 20))

    snap = (TopTrackSnapshot.objects
            .filter(user=user, term=term, limit=limit)
            .order_by("-fetched_at")
            .first())

    tracks = snap.data.get("tracks", []) if snap else []

    return render(request, "music_analyzer/result.html", {
        "tracks": tracks,
        "limit": limit,
        "term_label": _term_label(term),
        "need_refresh": (snap is None),
    })


@require_POST
def refresh_top(request):
    user = _current_user_row(request)
    if not user:
        return redirect("spotify_login")

    sp = _spotify_client(user)

    term = request.session.get("time_range", "short_term")
    limit = int(request.session.get("limit", 20))

    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=term)
    _save_snapshot(user, top_tracks["items"], term, limit)

    return redirect("result")
