# MongoDB Database Structure

**Database:** `music_album_archive`  
**Connection:** `mongodb://localhost:27017/`  
**Collections:** `artists`, `albums`, `songs`

---

## Collection: `artists`

### Schema

```
_id          ObjectId   — auto-generated unique identifier
name         String     — artist/band name (required)
country      String     — country of origin
genre        String     — primary music genre
active_year  Integer    — year the artist became active
```

### Sample Documents

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1"),
  "name": "Billie Eilish",
  "country": "United States",
  "genre": "Alt Pop",
  "active_year": 2015
}

{
  "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e2"),
  "name": "Bad Bunny",
  "country": "Puerto Rico",
  "genre": "Reggaeton",
  "active_year": 2013
}

{
  "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e3"),
  "name": "Rihanna",
  "country": "Barbados",
  "genre": "R&B / Pop",
  "active_year": 2003
}

{
  "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e4"),
  "name": "Teddy Swims",
  "country": "United States",
  "genre": "Soul / R&B",
  "active_year": 2020
}

{
  "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e5"),
  "name": "Tate McRae",
  "country": "Canada",
  "genre": "Pop",
  "active_year": 2017
}
```

---

## Collection: `albums`

### Schema

```
_id           ObjectId   — auto-generated unique identifier
title         String     — album title (required)
release_year  Integer    — year of release
genre         String     — album genre
artist_id     ObjectId   — REFERENCE → artists._id  (required)
```

> `artist_id` is stored as an **ObjectId**, not a string.  
> The artist name is never duplicated here — it is resolved via `$lookup`.

### Sample Documents

```json
{
  "_id": ObjectId("66b1c2d3e4f5a6b7c8d9e0f1"),
  "title": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?",
  "release_year": 2019,
  "genre": "Alt Pop",
  "artist_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")
}

{
  "_id": ObjectId("66b1c2d3e4f5a6b7c8d9e0f2"),
  "title": "Hit Me Hard and Soft",
  "release_year": 2024,
  "genre": "Alt Pop",
  "artist_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")
}

{
  "_id": ObjectId("66b1c2d3e4f5a6b7c8d9e0f3"),
  "title": "Un Verano Sin Ti",
  "release_year": 2022,
  "genre": "Reggaeton / Latin Pop",
  "artist_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e2")
}

{
  "_id": ObjectId("66b1c2d3e4f5a6b7c8d9e0f4"),
  "title": "Anti",
  "release_year": 2016,
  "genre": "R&B / Alt R&B",
  "artist_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e3")
}
```

---

## Collection: `songs`

### Schema

```
_id           ObjectId   — auto-generated unique identifier
title         String     — song title (required)
duration      String     — duration in m:ss format (e.g. "3:31")
track_number  Integer    — track position on the album
album_id      ObjectId   — REFERENCE → albums._id  (required)
artist_id     ObjectId   — REFERENCE → artists._id (denormalized for query efficiency)
```

> `artist_id` is stored directly in songs to avoid a double-join when querying  
> "all songs by artist" without going through albums first.

### Sample Documents

```json
{
  "_id": ObjectId("77c1d2e3f4a5b6c7d8e9f0a1"),
  "title": "BIRDS OF A FEATHER",
  "duration": "3:31",
  "track_number": 4,
  "album_id":  ObjectId("66b1c2d3e4f5a6b7c8d9e0f2"),
  "artist_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")
}

{
  "_id": ObjectId("77c1d2e3f4a5b6c7d8e9f0a2"),
  "title": "bad guy",
  "duration": "3:14",
  "track_number": 2,
  "album_id":  ObjectId("66b1c2d3e4f5a6b7c8d9e0f1"),
  "artist_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")
}

{
  "_id": ObjectId("77c1d2e3f4a5b6c7d8e9f0a3"),
  "title": "Work",
  "duration": "3:39",
  "track_number": 1,
  "album_id":  ObjectId("66b1c2d3e4f5a6b7c8d9e0f4"),
  "artist_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e3")
}
```

---

## Relationships Diagram

```
artists
  _id ◄──────────────────────┐
  name                        │  artist_id (ObjectId reference)
  country                     │
  genre               albums ─┘
  active_year           _id ◄─────────────────────┐
                        title                      │  album_id (ObjectId reference)
                        release_year               │
                        genre               songs ─┘
                        artist_id ──►         _id
                                              title
                                              duration
                                              track_number
                                              album_id ──► albums._id
                                              artist_id ──► artists._id
```

---

## Key Aggregation Queries

### Albums with artist name (used in Albums tab)

```javascript
db.albums.aggregate([
  { $lookup: {
      from: "artists",
      localField: "artist_id",
      foreignField: "_id",
      as: "artist_info"
  }},
  { $unwind: { path: "$artist_info", preserveNullAndEmptyArrays: true } }
])
```

### Songs with album and artist (used in Songs tab)

```javascript
db.songs.aggregate([
  { $lookup: {
      from: "albums",
      localField: "album_id",
      foreignField: "_id",
      as: "album_info"
  }},
  { $unwind: { path: "$album_info", preserveNullAndEmptyArrays: true } },
  { $lookup: {
      from: "artists",
      localField: "artist_id",
      foreignField: "_id",
      as: "artist_info"
  }},
  { $unwind: { path: "$artist_info", preserveNullAndEmptyArrays: true } }
])
```

### Songs count per artist

```javascript
db.songs.aggregate([
  { $group: { _id: "$artist_id", song_count: { $sum: 1 } } },
  { $lookup: {
      from: "artists",
      localField: "_id",
      foreignField: "_id",
      as: "artist_info"
  }},
  { $unwind: "$artist_info" },
  { $project: { artist: "$artist_info.name", song_count: 1, _id: 0 } },
  { $sort: { song_count: -1 } }
])
```
