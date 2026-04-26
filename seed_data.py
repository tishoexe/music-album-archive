from pymongo import MongoClient
from bson import ObjectId

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME   = "music_album_archive"


def seed():
    client = MongoClient(MONGO_URI)
    db     = client[DB_NAME]

    if db.artists.count_documents({}) > 0:
        print("Database already contains data. Skipping seed.")
        print("To re-seed: drop the 'music_album_archive' database in MongoDB Compass and run again.")
        return

    print("Seeding database...\n")

    # ── Artists ──────────────────────────────────────────────────────────
    artists_raw = [
        {"name": "Billie Eilish", "country": "United States", "genre": "Alt Pop",    "active_year": 2015},
        {"name": "Bad Bunny",     "country": "Puerto Rico",   "genre": "Reggaeton",  "active_year": 2013},
        {"name": "Rihanna",       "country": "Barbados",      "genre": "R&B / Pop",  "active_year": 2003},
        {"name": "Teddy Swims",   "country": "United States", "genre": "Soul / R&B", "active_year": 2020},
        {"name": "Tate McRae",    "country": "Canada",        "genre": "Pop",        "active_year": 2017},
    ]

    artist_ids = {}
    for a in artists_raw:
        result = db.artists.insert_one(a.copy())
        artist_ids[a["name"]] = result.inserted_id
        print(f"  [Artist]  {a['name']}")

    # ── Albums ───────────────────────────────────────────────────────────
    albums_raw = [
        {"title": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?",
         "release_year": 2019, "genre": "Alt Pop",              "artist": "Billie Eilish"},
        {"title": "Happier Than Ever",
         "release_year": 2021, "genre": "Alt Pop",              "artist": "Billie Eilish"},
        {"title": "Hit Me Hard and Soft",
         "release_year": 2024, "genre": "Alt Pop",              "artist": "Billie Eilish"},
        {"title": "Un Verano Sin Ti",
         "release_year": 2022, "genre": "Reggaeton / Latin Pop","artist": "Bad Bunny"},
        {"title": "YHLQMDLG",
         "release_year": 2020, "genre": "Reggaeton",            "artist": "Bad Bunny"},
        {"title": "Anti",
         "release_year": 2016, "genre": "R&B / Alt R&B",        "artist": "Rihanna"},
        {"title": "Good Girl Gone Bad",
         "release_year": 2007, "genre": "Pop / R&B",            "artist": "Rihanna"},
        {"title": "I've Tried Everything But Therapy",
         "release_year": 2023, "genre": "Soul / R&B",           "artist": "Teddy Swims"},
        {"title": "THINK LATER",
         "release_year": 2023, "genre": "Pop",                  "artist": "Tate McRae"},
    ]

    album_ids = {}
    print()
    for al in albums_raw:
        doc = {
            "title":        al["title"],
            "release_year": al["release_year"],
            "genre":        al["genre"],
            "artist_id":    artist_ids[al["artist"]],
        }
        result = db.albums.insert_one(doc)
        album_ids[al["title"]] = result.inserted_id
        print(f"  [Album]   {al['title']}  ({al['release_year']})")

    # ── Songs ────────────────────────────────────────────────────────────
    songs_raw = [
        # WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?
        {"title": "bad guy",              "duration": "3:14", "track_number": 2,
         "album": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?", "artist": "Billie Eilish"},
        {"title": "bury a friend",        "duration": "3:13", "track_number": 8,
         "album": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?", "artist": "Billie Eilish"},
        {"title": "when the party's over","duration": "3:16", "track_number": 9,
         "album": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?", "artist": "Billie Eilish"},
        # Happier Than Ever
        {"title": "Happier Than Ever",    "duration": "4:58", "track_number": 15,
         "album": "Happier Than Ever", "artist": "Billie Eilish"},
        {"title": "Therefore I Am",       "duration": "2:54", "track_number": 5,
         "album": "Happier Than Ever", "artist": "Billie Eilish"},
        # Hit Me Hard and Soft
        {"title": "BIRDS OF A FEATHER",   "duration": "3:31", "track_number": 4,
         "album": "Hit Me Hard and Soft", "artist": "Billie Eilish"},
        {"title": "LUNCH",                "duration": "2:38", "track_number": 2,
         "album": "Hit Me Hard and Soft", "artist": "Billie Eilish"},
        {"title": "CHIHIRO",              "duration": "5:11", "track_number": 5,
         "album": "Hit Me Hard and Soft", "artist": "Billie Eilish"},
        # Un Verano Sin Ti
        {"title": "Tití Me Preguntó",     "duration": "3:48", "track_number": 8,
         "album": "Un Verano Sin Ti", "artist": "Bad Bunny"},
        # YHLQMDLG
        {"title": "Dakiti",               "duration": "3:10", "track_number": 1,
         "album": "YHLQMDLG", "artist": "Bad Bunny"},
        # Anti
        {"title": "Work",                 "duration": "3:39", "track_number": 1,
         "album": "Anti", "artist": "Rihanna"},
        {"title": "Love On The Brain",    "duration": "3:34", "track_number": 11,
         "album": "Anti", "artist": "Rihanna"},
        # Good Girl Gone Bad
        {"title": "Umbrella",             "duration": "4:30", "track_number": 1,
         "album": "Good Girl Gone Bad", "artist": "Rihanna"},
        # I've Tried Everything But Therapy
        {"title": "Lose Control",         "duration": "3:23", "track_number": 1,
         "album": "I've Tried Everything But Therapy", "artist": "Teddy Swims"},
        {"title": "The Door",             "duration": "3:52", "track_number": 3,
         "album": "I've Tried Everything But Therapy", "artist": "Teddy Swims"},
        # THINK LATER
        {"title": "greedy",               "duration": "2:11", "track_number": 1,
         "album": "THINK LATER", "artist": "Tate McRae"},
        {"title": "exes",                 "duration": "2:47", "track_number": 4,
         "album": "THINK LATER", "artist": "Tate McRae"},
    ]

    print()
    for s in songs_raw:
        db.songs.insert_one({
            "title":        s["title"],
            "duration":     s["duration"],
            "track_number": s["track_number"],
            "album_id":     album_ids[s["album"]],
            "artist_id":    artist_ids[s["artist"]],
        })
        print(f"  [Song]    {s['title']}  —  {s['album']}")

    print()
    print("✓ Seed completed successfully!")
    print(f"  Artists : {db.artists.count_documents({})}")
    print(f"  Albums  : {db.albums.count_documents({})}")
    print(f"  Songs   : {db.songs.count_documents({})}")


if __name__ == "__main__":
    seed()
