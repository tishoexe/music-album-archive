# 🎵 Music Album Archive

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-6%2B-47A248?style=flat&logo=mongodb&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-blue?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

A desktop application for organizing music albums, songs, and artists — built with Python, Tkinter, and a local MongoDB database.

> Course project for the **Global Databases** discipline, demonstrating MongoDB References, `$lookup` aggregation, filters, and CRUD operations through a modern graphical interface.

---

## Screenshots

> *(Add screenshots here after first run)*

---

## Features

- **Artists** — Add, edit, delete, and filter artists by name, country, or genre
- **Albums** — Full CRUD with artist resolved via MongoDB `$lookup` (not stored as plain text)
- **Songs** — Double `$lookup` to display album title and artist name in one table
- **Statistics** — Aggregation reports: albums per artist, songs per album, songs per artist, albums by genre, and more
- **Filters** — Live search across all tabs using `$regex`
- **Sorting** — Click any column header to sort ascending ▲ or descending ▼
- **References** — `artist_id` and `album_id` stored as MongoDB `ObjectId` references
- **Validation** — Input validation with user-friendly error messages
- **One-click launch** — `start.command` script handles venv and dependencies automatically

---

## Tech Stack

| Layer     | Technology          |
|-----------|---------------------|
| Language  | Python 3.10+        |
| GUI       | Tkinter + ttk       |
| Database  | MongoDB 6+ (local)  |
| Driver    | pymongo 4.6+        |

---

## Project Structure

```
MAA/
├── app.py              — GUI application (entry point)
├── database.py         — MongoDB connection and all DB operations
├── seed_data.py        — Inserts sample data (5 artists, 9 albums, 17 songs)
├── start.command       — macOS one-click launcher
├── requirements.txt
├── LICENSE
└── docs/
    ├── documentation.md    — Full project documentation (Bulgarian)
    ├── mongo_structure.md  — Database schema and sample documents
    └── defense_notes.md    — Notes for the oral defense
```

---

## Database Schema

```
artists                albums                  songs
───────                ──────                  ─────
_id        ◄───────    _id        ◄─────────   _id
name               │   title              │    title
country            │   release_year       │    duration
genre              │   genre              │    track_number
active_year        └── artist_id (ref)    └─── album_id  (ref)
                                               artist_id (ref) ──► artists._id
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- MongoDB running locally on `localhost:27017`

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/music-album-archive.git
cd music-album-archive

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Seed sample data

```bash
python seed_data.py
```

Inserts 5 artists, 9 albums, and 17 songs. Running it again when data already exists will skip silently.

### Run the application

```bash
python app.py
```

**macOS shortcut:** double-click `start.command` — it handles the venv and dependencies automatically.

---

## MongoDB Collections

### `artists`
```json
{
  "_id": "ObjectId",
  "name": "Billie Eilish",
  "country": "United States",
  "genre": "Alt Pop",
  "active_year": 2015
}
```

### `albums`
```json
{
  "_id": "ObjectId",
  "title": "Hit Me Hard and Soft",
  "release_year": 2024,
  "genre": "Alt Pop",
  "artist_id": "ObjectId → artists._id"
}
```

### `songs`
```json
{
  "_id": "ObjectId",
  "title": "BIRDS OF A FEATHER",
  "duration": "3:31",
  "track_number": 4,
  "album_id":  "ObjectId → albums._id",
  "artist_id": "ObjectId → artists._id"
}
```

---

## Key MongoDB Operations Used

| Operation | Where |
|-----------|-------|
| `$lookup` | Albums tab (artist name), Songs tab (album + artist), Statistics |
| `$group`  | Statistics — count per artist/album/genre |
| `$match`  | Filters after `$lookup` |
| `$regex`  | Text search in all filter fields |
| `$sort`   | Ordering results |
| `$avg`    | Average songs per album |
| `insert_one / update_one / delete_one` | All CRUD operations |

---

## License

This project is licensed under the [MIT License](LICENSE).
