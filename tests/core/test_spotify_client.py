import pytest
from unittest.mock import MagicMock, patch

from spotify_cli.core import spotify_client as client_mod
from spotify_cli.core.spotify_client import NotAuthenticatedError, get_spotify_client


def test_get_spotify_client_raises_when_no_cached_token():
    with patch.object(client_mod, "get_cached_token", return_value=None):
        with pytest.raises(NotAuthenticatedError, match="auth login"):
            get_spotify_client()


def test_get_spotify_client_returns_spotify_instance(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-client-id")
    token = {"access_token": "tok", "expires_at": 9999999999}
    mock_manager = MagicMock()
    with patch.object(client_mod, "get_cached_token", return_value=token), \
         patch.object(client_mod, "get_auth_manager", return_value=mock_manager), \
         patch.object(client_mod.spotipy, "Spotify") as mock_spotify:
        client = get_spotify_client()
    mock_spotify.assert_called_once_with(auth_manager=mock_manager)
    assert client is mock_spotify.return_value
