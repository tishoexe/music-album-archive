# Документация на курсов проект
## Music Album Archive

**Дисциплина:** Глобални бази данни  
**Технологии:** Python, MongoDB, Tkinter  
**База данни:** `music_album_archive` (локална MongoDB инсталация)

---

## 1. Увод

Проектът **Music Album Archive** е настолно приложение за организиране на музикални албуми, песни и изпълнители. Целта му е да демонстрира практическата употреба на документно-ориентирана NoSQL база данни (MongoDB) в комбинация с Python и графичен потребителски интерфейс.

Приложението позволява:
- Добавяне, редактиране и изтриване на изпълнители, албуми и песни
- Търсене и филтриране на записи по различни критерии
- Визуализиране на агрегирана статистическа информация
- Свързване на данни между колекции чрез MongoDB References и `$lookup`

---

## 2. Теоретична част

### 2.1 NoSQL бази данни

NoSQL (Not Only SQL) базите данни са проектирани за гъвкавост и мащабируемост. Те не изискват фиксирана схема и могат да съхраняват данни в различни формати — документи, ключ-стойност, графи и др.

### 2.2 MongoDB

MongoDB е документно-ориентирана NoSQL база данни. Данните се съхраняват в **документи** (BSON формат, подобен на JSON), организирани в **колекции**. Всеки документ има уникален идентификатор `_id` от тип `ObjectId`.

**Основни предимства:**
- Гъвкава схема — документите в една колекция могат да имат различна структура
- Поддръжка на вложени документи и масиви
- Мощни агрегационни pipeline-и
- Хоризонтална мащабируемост

### 2.3 References в MongoDB

Вместо да дублираме данни (embedded documents), можем да съхраняваме **reference** — `ObjectId` на документ от друга колекция. Това е аналог на Foreign Key в релационните бази данни.

**Пример:** Вместо да записваме цялата информация за изпълнителя в документа на всеки албум, записваме само `artist_id`.

### 2.4 $lookup агрегация

`$lookup` е stage в MongoDB Aggregation Pipeline, който изпълнява операция, аналогична на SQL `JOIN`. Позволява обединяване на документи от две колекции въз основа на съответствие между полета.

---

## 3. Практическа реализация

### 3.1 Структура на базата данни

Базата данни `music_album_archive` съдържа три колекции:

#### Колекция `artists`
Съхранява информация за музикалните изпълнители.

```json
{
  "_id": ObjectId("..."),
  "name": "Billie Eilish",
  "country": "United States",
  "genre": "Alt Pop",
  "active_year": 2015
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `_id` | ObjectId | Уникален идентификатор (автоматично генериран) |
| `name` | String | Име на изпълнителя |
| `country` | String | Държава на произход |
| `genre` | String | Музикален жанр |
| `active_year` | Integer | Година на начало на дейността |

#### Колекция `albums`
Съхранява информация за музикалните албуми.

```json
{
  "_id": ObjectId("..."),
  "title": "Hit Me Hard and Soft",
  "release_year": 2024,
  "genre": "Alt Pop",
  "artist_id": ObjectId("...")
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `_id` | ObjectId | Уникален идентификатор |
| `title` | String | Заглавие на албума |
| `release_year` | Integer | Година на издаване |
| `genre` | String | Музикален жанр |
| `artist_id` | ObjectId | **Reference** към `artists._id` |

#### Колекция `songs`
Съхранява информация за отделните песни.

```json
{
  "_id": ObjectId("..."),
  "title": "BIRDS OF A FEATHER",
  "duration": "3:31",
  "track_number": 4,
  "album_id": ObjectId("..."),
  "artist_id": ObjectId("...")
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `_id` | ObjectId | Уникален идентификатор |
| `title` | String | Заглавие на песента |
| `duration` | String | Продължителност (формат м:сс) |
| `track_number` | Integer | Номер на песента в албума |
| `album_id` | ObjectId | **Reference** към `albums._id` |
| `artist_id` | ObjectId | **Reference** към `artists._id` |

### 3.2 MongoDB References

В проекта се използват два вида references:

**albums → artists:**  
Полето `artist_id` в колекция `albums` съдържа `ObjectId` на съответния запис в колекция `artists`. Така един изпълнител може да има много албуми, без да дублираме данните му.

**songs → albums и songs → artists:**  
Полето `album_id` в колекция `songs` съдържа `ObjectId` на съответния албум. Полето `artist_id` е добавено директно в `songs` за по-ефективни заявки (без двоен lookup).

### 3.3 Използване на $lookup

#### Показване на Albums с Artist Name

```python
pipeline = [
    {
        "$lookup": {
            "from": "artists",
            "localField": "artist_id",
            "foreignField": "_id",
            "as": "artist_info"
        }
    },
    {"$unwind": {"path": "$artist_info", "preserveNullAndEmptyArrays": True}}
]
```

Резултатът съдържа всички полета на албума плюс `artist_info.name` — без да е необходимо да е записано текстово в документа на албума.

#### Показване на Songs с Album и Artist

```python
pipeline = [
    {"$lookup": {
        "from": "albums",
        "localField": "album_id",
        "foreignField": "_id",
        "as": "album_info"
    }},
    {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},
    {"$lookup": {
        "from": "artists",
        "localField": "artist_id",
        "foreignField": "_id",
        "as": "artist_info"
    }},
    {"$unwind": {"path": "$artist_info", "preserveNullAndEmptyArrays": True}}
]
```

Двоен `$lookup` — по `album_id` и по `artist_id` — позволява да се показват заглавие на песен, заглавие на албум и ime на изпълнителя в една таблица.

### 3.4 Филтри

Филтрите използват MongoDB query с `$regex` оператор за регистронезависимо търсене по текстови полета:

```python
query["name"] = {"$regex": name_filter, "$options": "i"}
```

За числови полета (Release Year) се използва точно съвпадение:

```python
query["release_year"] = int(year_filter)
```

Когато филтрирането касае поле от join-ната колекция (напр. artist name в Albums таба), филтърът се прилага след `$lookup` чрез `$match` stage в pipeline-а.

### 3.5 Aggregation Statistics

Статистическите справки използват `$group` за групиране и `$lookup` за разрешаване на имена:

```python
# Брой албуми по изпълнител
pipeline = [
    {"$group": {"_id": "$artist_id", "album_count": {"$sum": 1}}},
    {"$lookup": {"from": "artists", "localField": "_id",
                 "foreignField": "_id", "as": "artist_info"}},
    {"$unwind": "$artist_info"},
    {"$project": {"artist": "$artist_info.name", "album_count": 1, "_id": 0}},
    {"$sort": {"album_count": -1}}
]
```

---

## 4. Графичен интерфейс

Приложението използва **Tkinter** с `ttk` стилове за модерна визия:

- Светъл дизайн с тъмносин header
- Четири таба: Artists, Albums, Songs, Statistics
- Всеки таб има панел с филтри, таблица (ttk.Treeview) и бутони за операции
- Диалогови прозорци за Add/Edit с валидация на входа
- Потвърждение преди изтриване
- Проверка на MongoDB connection при стартиране

---

## 5. Заключение

Проектът демонстрира основните концепции на документно-ориентираните бази данни:
- Структура на документи и колекции
- Използване на References вместо дублиране на данни
- `$lookup` за обединяване на данни от различни колекции
- Aggregation Pipeline за статистически справки
- Текстово търсене с `$regex`

Приложението е реализирано с чист, четим Python код, разделен в отделни модули за GUI (`app.py`) и база данни (`database.py`).
