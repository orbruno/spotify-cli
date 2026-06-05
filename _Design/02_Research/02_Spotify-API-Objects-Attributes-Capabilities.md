# Spotify API — Objects, Attributes & Capabilities

**Created**: 2026-06-03
**Author**: Orlando Bruno
**Status**: Draft

---

## TL;DR

- **Summary**: Maps all Spotify Web API objects (Track, Artist, Album, Playlist, User) with their available attributes, covering what can be read, what can be created, and what was permanently removed in 2024.
- **Relevance**: Understanding the full attribute surface determines what the CLI can filter, curate, and present — and where the LLM must compensate for data Spotify no longer exposes.
- **Decision**: Use `genres[]` on Artist + `popularity` + `release_date` on Album as the primary filter dimensions for curation; rely on the LLM for mood/energy/style judgments that audio_features used to provide.

---

## Context

Before implementing any filtering, curation, or playlist-building logic in the CLI, we need a precise map of what the Spotify Web API actually exposes today. The API underwent a significant contraction in November 2024, permanently removing several high-value endpoints (audio features, recommendations, related artists). This research documents the current read/write surface of all core objects, the discography traversal pattern the CLI will use, and the design implications of the removed endpoints. The central question: **what metadata can we rely on programmatically, and where must the LLM fill the gap?**

---

## Findings

### What the API Can READ

#### Track Object

| Attribute | Type | Notes |
|-----------|------|-------|
| `id` | string | Spotify ID |
| `uri` | string | `spotify:track:{id}` — used for playlist operations |
| `name` | string | Canonical track title |
| `duration_ms` | integer | Track duration in milliseconds |
| `explicit` | boolean | Explicit content flag |
| `popularity` | 0–100 | Spotify's proprietary score (recency-weighted streams) |
| `track_number` | integer | Position on the album |
| `disc_number` | integer | Disc number (multi-disc releases) |
| `preview_url` | string | 30-second audio clip URL (may be null) |
| `is_local` | boolean | Whether it's a locally uploaded file |
| `is_playable` | boolean | Availability in the user's market |
| `external_ids.isrc` | string | International Standard Recording Code — cross-platform identity |
| `artists[]` | array | Simplified artist objects (id, name, uri) |
| `album` | object | Simplified album object |

#### Artist Object

| Attribute | Type | Notes |
|-----------|------|-------|
| `id` | string | Spotify ID |
| `uri` | string | `spotify:artist:{id}` |
| `name` | string | Canonical artist name |
| `genres[]` | array of strings | e.g. `["classic country", "outlaw country"]` — most useful filter dimension |
| `popularity` | 0–100 | Proprietary score |
| `followers.total` | integer | Total follower count |
| `images[]` | array | `{url, width, height}` |

#### Album Object

| Attribute | Type | Notes |
|-----------|------|-------|
| `id` | string | Spotify ID |
| `uri` | string | `spotify:album:{id}` |
| `name` | string | Canonical album title |
| `album_type` | enum | `album` \| `single` \| `compilation` |
| `release_date` | string | `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` |
| `release_date_precision` | enum | `year` \| `month` \| `day` |
| `total_tracks` | integer | |
| `genres[]` | array of strings | Often empty at album level; more reliable on Artist |
| `popularity` | 0–100 | |
| `label` | string | Record label name |
| `copyrights[]` | array | Copyright statements |
| `external_ids.upc` | string | Universal Product Code |
| `artists[]` | array | Album artists |
| `tracks` | paginated object | Simplified track objects |

#### Playlist Object

| Attribute | Type | Notes |
|-----------|------|-------|
| `id` | string | Spotify ID |
| `uri` | string | `spotify:playlist:{id}` |
| `name` | string | |
| `description` | string | Plain text or HTML |
| `public` | boolean | Visibility |
| `collaborative` | boolean | Whether others can add tracks |
| `followers.total` | integer | |
| `snapshot_id` | string | Version fingerprint — changes on any modification |
| `owner` | object | User object of creator |
| `images[]` | array | Playlist cover images |
| `tracks` | paginated object | Full track objects with `added_at` and `added_by` |

#### User Object

| Attribute | Type | Notes |
|-----------|------|-------|
| `id` | string | Spotify user ID (used in playlist creation) |
| `display_name` | string | |
| `email` | string | Requires `user-read-email` scope |
| `country` | string | ISO 3166-1 alpha-2 |
| `product` | enum | `premium` \| `free` |
| `followers.total` | integer | |
| `images[]` | array | Profile pictures |

---

### What the API Can CREATE / WRITE

| Operation | Endpoint | Scope Required | Notes |
|-----------|----------|----------------|-------|
| Create playlist | `POST /me/playlists` | `playlist-modify-public` or `playlist-modify-private` | Body: `name`, `description`, `public`, `collaborative` |
| Add tracks to playlist | `POST /playlists/{id}/items` | same as above | Up to 100 URIs per request; can specify position |
| Reorder tracks | `PUT /playlists/{id}/tracks` | same | Reorder by range |
| Remove tracks | `DELETE /playlists/{id}/tracks` | same | By URI |
| Update playlist details | `PUT /playlists/{id}` | same | Name, description, public flag |
| Upload playlist cover | `PUT /playlists/{id}/images` | `ugc-image-upload` + modify scope | Base64 JPEG, max 256KB |
| Save tracks to library | `PUT /me/tracks` | `user-library-modify` | Up to 50 IDs per request |

---

### What Was REMOVED (November 2024)

These endpoints no longer exist. Any code or library that calls them receives 404.

| Removed Endpoint | What It Provided | Impact |
|-----------------|------------------|--------|
| `GET /audio-features/{id}` | BPM/tempo, energy, danceability, valence, acousticness, instrumentalness, loudness, key, mode, time_signature | Loss of the richest musical descriptor layer — no programmatic mood/style filtering |
| `GET /audio-features` (batch) | Same, for up to 100 tracks | |
| `GET /recommendations` | Algorithmic track suggestions seeded by tracks/artists/genres + audio feature targets | Loss of Spotify's curation engine |
| `GET /artists/{id}/related-artists` | Artists similar to a given artist | |
| `GET /browse/featured-playlists` | Editorial featured playlists | |
| `GET /browse/new-releases` | New album releases | |
| `GET /browse/categories` | Genre/mood browse categories | |
| `GET /me/top/{type}` | User's top tracks/artists | Removed from free tier; status unclear for Premium |
| `POST /users/{id}/playlists` | Create playlist (old path) | Use `POST /me/playlists` instead |

---

### Discography Traversal Pattern

To get all tracks for an artist programmatically:

```
1. GET /search?q={artist_name}&type=artist&limit=1
   → artist_id

2. GET /artists/{artist_id}/albums?include_groups=album,single&limit=50
   → paginate through all albums → album_ids[]

3. GET /albums/{album_id}/tracks (for each album)
   → track list with name + uri
```

This pattern is the recommended approach for building curated playlists from a known artist — the LLM selects from verified track URIs rather than guessing names.

**Filter dimensions available during traversal:**

- `album_type`: filter to `album` only to skip singles/compilations
- `release_date`: filter by decade or year range
- `genres[]` on artist: filter by genre tag
- `popularity` on track: filter to most-known tracks

---

### Search Capabilities

`GET /search?q={query}&type={types}&limit={n}&market={market}`

**Supported `type` values:** `track`, `artist`, `album`, `playlist`, `show`, `episode`, `audiobook`

**Query syntax supports field filters:**

```
track:Light My Fire artist:The Doors
album:American IV artist:Johnny Cash
year:1960-1970 genre:country
```

Search is fuzzy and tolerant of minor spelling variations and punctuation differences (e.g. "The Door's" matches "The Doors"). The returned object always contains the canonical Spotify name and URI.

---

## Comparison

The key trade-off this research surfaces is between two curation strategies, now that audio features are gone:

| Criteria | LLM-led curation (recommended) | Metadata-only filtering |
|----------|---------------------------------|------------------------|
| Mood/energy/style judgment | Strong — LLM infers from genre tags and track names | Not possible without audio features |
| Accuracy for known artists | High — selects from verified URI list | Moderate — limited to genre/popularity/date |
| Accuracy for obscure tracks | Moderate — LLM knowledge may be incomplete | Low — structured metadata alone is thin |
| Hallucination risk | Mitigated by discography-first pattern | None (pure API data) |
| Implementation complexity | Medium | Low |

---

## Recommendation

Use the **discography-first + LLM selection** approach as the primary curation strategy:

1. Pull the full artist discography via the traversal pattern to obtain verified track URIs.
2. Pass the structured track list (name, album, year, genre tags, popularity) to the LLM.
3. Let the LLM select and rank tracks based on the user's intent (mood, era, style).
4. Use `genres[]` on Artist, `release_date` on Album, and `album_type` as pre-filters to reduce the list before the LLM call.

This avoids hallucinated track names, compensates for the loss of audio features, and keeps API call volume predictable.

---

## Next Steps

- [ ] Implement OAuth flow covering all required scopes (`playlist-modify-public`, `playlist-modify-private`, `user-library-modify`, `user-read-email`)
- [ ] Build discography traversal utility (`artist → albums → tracks`) with pagination handling
- [ ] Design the LLM prompt schema that receives structured track metadata and returns a ranked selection with URIs
- [ ] Validate `genres[]` richness across a representative set of target artists to confirm filter viability
- [ ] Document rate limits and batching strategy for album/track fetch loops

---

## Sources

- [Spotify Web API Reference — Track Object](https://developer.spotify.com/documentation/web-api/reference/get-track)
- [Spotify Web API Reference — Artist Object](https://developer.spotify.com/documentation/web-api/reference/get-an-artist)
- [Spotify Web API Reference — Album Object](https://developer.spotify.com/documentation/web-api/reference/get-an-album)
- [Spotify Web API Reference — Playlist Object](https://developer.spotify.com/documentation/web-api/reference/get-playlist)
- [Spotify Web API Reference — User Object](https://developer.spotify.com/documentation/web-api/reference/get-current-users-profile)
- [Spotify Web API Reference — Search](https://developer.spotify.com/documentation/web-api/reference/search)
- [Spotify Developer Community — Audio Features Deprecation (November 2024)](https://community.spotify.com/t5/Spotify-for-Developers/Changes-to-Web-API/td-p/6540414)

---

Last Updated: 2026-06-03
