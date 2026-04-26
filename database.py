from pymongo import MongoClient
from bson import ObjectId

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME   = "music_album_archive"

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client[DB_NAME]


def check_connection():
    try:
        MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000).server_info()
        return True
    except Exception:
        return False


# ── Artists ────────────────────────────────────────────────────────────────

def get_all_artists(name_filter="", country_filter="", genre_filter=""):
    db    = get_db()
    query = {}
    if name_filter:
        query["name"] = {"$regex": name_filter, "$options": "i"}
    if country_filter:
        query["country"] = {"$regex": country_filter, "$options": "i"}
    if genre_filter:
        query["genre"] = {"$regex": genre_filter, "$options": "i"}
    return list(db.artists.find(query).sort("name", 1))


def insert_artist(name, country, genre, active_year):
    return get_db().artists.insert_one(
        {"name": name, "country": country, "genre": genre, "active_year": active_year}
    )


def update_artist(artist_id, name, country, genre, active_year):
    get_db().artists.update_one(
        {"_id": ObjectId(artist_id)},
        {"$set": {"name": name, "country": country, "genre": genre, "active_year": active_year}},
    )


def delete_artist(artist_id):
    db    = get_db()
    count = db.albums.count_documents({"artist_id": ObjectId(artist_id)})
    if count > 0:
        return False, f"This artist cannot be deleted because it has {count} album(s)."
    db.artists.delete_one({"_id": ObjectId(artist_id)})
    return True, "Artist deleted successfully."


# ── Albums ─────────────────────────────────────────────────────────────────

def get_all_albums(title_filter="", artist_filter="", genre_filter="", year_filter=""):
    db       = get_db()
    pipeline = [
        {"$lookup": {
            "from": "artists", "localField": "artist_id",
            "foreignField": "_id", "as": "artist_info",
        }},
        {"$unwind": {"path": "$artist_info", "preserveNullAndEmptyArrays": True}},
    ]
    match = {}
    if title_filter:
        match["title"] = {"$regex": title_filter, "$options": "i"}
    if genre_filter:
        match["genre"] = {"$regex": genre_filter, "$options": "i"}
    if year_filter:
        try:
            match["release_year"] = int(year_filter)
        except ValueError:
            pass
    if artist_filter:
        match["artist_info.name"] = {"$regex": artist_filter, "$options": "i"}
    if match:
        pipeline.append({"$match": match})
    pipeline.append({"$sort": {"release_year": -1}})
    return list(db.albums.aggregate(pipeline))


def insert_album(title, release_year, genre, artist_id):
    return get_db().albums.insert_one({
        "title": title, "release_year": release_year,
        "genre": genre, "artist_id": ObjectId(artist_id),
    })


def update_album(album_id, title, release_year, genre, artist_id):
    get_db().albums.update_one(
        {"_id": ObjectId(album_id)},
        {"$set": {
            "title": title, "release_year": release_year,
            "genre": genre, "artist_id": ObjectId(artist_id),
        }},
    )


def delete_album(album_id):
    db    = get_db()
    count = db.songs.count_documents({"album_id": ObjectId(album_id)})
    if count > 0:
        return False, f"This album cannot be deleted because it has {count} song(s)."
    db.albums.delete_one({"_id": ObjectId(album_id)})
    return True, "Album deleted successfully."


# ── Songs ──────────────────────────────────────────────────────────────────

def get_all_songs(title_filter="", album_filter="", artist_filter=""):
    db       = get_db()
    pipeline = [
        {"$lookup": {
            "from": "albums", "localField": "album_id",
            "foreignField": "_id", "as": "album_info",
        }},
        {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "artists", "localField": "artist_id",
            "foreignField": "_id", "as": "artist_info",
        }},
        {"$unwind": {"path": "$artist_info", "preserveNullAndEmptyArrays": True}},
    ]
    match = {}
    if title_filter:
        match["title"] = {"$regex": title_filter, "$options": "i"}
    if album_filter:
        match["album_info.title"] = {"$regex": album_filter, "$options": "i"}
    if artist_filter:
        match["artist_info.name"] = {"$regex": artist_filter, "$options": "i"}
    if match:
        pipeline.append({"$match": match})
    pipeline.append({"$sort": {"album_info.title": 1, "track_number": 1}})
    return list(db.songs.aggregate(pipeline))


def insert_song(title, duration, track_number, album_id, artist_id):
    return get_db().songs.insert_one({
        "title": title, "duration": duration, "track_number": track_number,
        "album_id": ObjectId(album_id), "artist_id": ObjectId(artist_id),
    })


def update_song(song_id, title, duration, track_number, album_id, artist_id):
    get_db().songs.update_one(
        {"_id": ObjectId(song_id)},
        {"$set": {
            "title": title, "duration": duration, "track_number": track_number,
            "album_id": ObjectId(album_id), "artist_id": ObjectId(artist_id),
        }},
    )


def delete_song(song_id):
    get_db().songs.delete_one({"_id": ObjectId(song_id)})
    return True, "Song deleted successfully."


# ── Statistics (aggregation pipelines) ────────────────────────────────────

def stat_albums_per_artist():
    pipeline = [
        {"$group": {"_id": "$artist_id", "album_count": {"$sum": 1}}},
        {"$lookup": {"from": "artists", "localField": "_id",
                     "foreignField": "_id", "as": "artist_info"}},
        {"$unwind": "$artist_info"},
        {"$project": {"_id": 0, "artist": "$artist_info.name", "album_count": 1}},
        {"$sort": {"album_count": -1}},
    ]
    return list(get_db().albums.aggregate(pipeline))


def stat_songs_per_album():
    pipeline = [
        {"$group": {"_id": "$album_id", "song_count": {"$sum": 1}}},
        {"$lookup": {"from": "albums", "localField": "_id",
                     "foreignField": "_id", "as": "album_info"}},
        {"$unwind": "$album_info"},
        {"$project": {"_id": 0, "album": "$album_info.title", "song_count": 1}},
        {"$sort": {"song_count": -1}},
    ]
    return list(get_db().songs.aggregate(pipeline))


def stat_songs_per_artist():
    pipeline = [
        {"$group": {"_id": "$artist_id", "song_count": {"$sum": 1}}},
        {"$lookup": {"from": "artists", "localField": "_id",
                     "foreignField": "_id", "as": "artist_info"}},
        {"$unwind": "$artist_info"},
        {"$project": {"_id": 0, "artist": "$artist_info.name", "song_count": 1}},
        {"$sort": {"song_count": -1}},
    ]
    return list(get_db().songs.aggregate(pipeline))


def stat_albums_by_genre():
    pipeline = [
        {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "genre": "$_id", "count": 1}},
        {"$sort": {"count": -1}},
    ]
    return list(get_db().albums.aggregate(pipeline))


def stat_avg_songs_per_album():
    pipeline = [
        {"$group": {"_id": "$album_id", "song_count": {"$sum": 1}}},
        {"$group": {"_id": None, "avg": {"$avg": "$song_count"}}},
        {"$project": {"_id": 0, "avg": {"$round": ["$avg", 2]}}},
    ]
    result = list(get_db().songs.aggregate(pipeline))
    return result[0]["avg"] if result else 0


def stat_all_songs_with_details():
    pipeline = [
        {"$lookup": {"from": "albums", "localField": "album_id",
                     "foreignField": "_id", "as": "album_info"}},
        {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {"from": "artists", "localField": "artist_id",
                     "foreignField": "_id", "as": "artist_info"}},
        {"$unwind": {"path": "$artist_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "title": 1, "duration": 1, "track_number": 1,
            "album":  "$album_info.title",
            "artist": "$artist_info.name",
        }},
        {"$sort": {"artist": 1, "album": 1, "track_number": 1}},
    ]
    return list(get_db().songs.aggregate(pipeline))
