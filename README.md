# DSCI551-ChatDB
This project implements a natural language interface that allows users to interact with both a MySQL and a MongoDB database using plain English queries. It supports multiple databases (SARS, MovieLens, Sample_mflix) and uses an OpenAI API to translate natural language into executable queries.

---

# Project Structure

```
Project_Stuff/
├── main.py
├── SQL_API.py
├── mongoMain.py
├── TableSetup.py
├── GenreSetup.py
├── config.py
├── mongo_client.py
├── openai_client.py
├── translator.py
├── .env              # Contains environment variables (not shared)
├── requirements.txt
├── README.md
```

---
!!!!! Prerequisites
Before running the code, make sure you have the following:

### Required Software
- Python 3.8+
- MySQL Server (with `movielens_db` and `sars_db` created)
- Active MongoDB server
- OpenAI API access

### Python Libraries
Install via:
```bash
pip install -r requirements.txt
```

---

## 🔐 API Key / DB Setup

1. Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_api_key_here
DB_HOST=localhost
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
ACTIVE_DB=chatdb
DB_SARS=sars_db
DB_MOVIELENS=movielens_db
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "key-here")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb+srv://cleahey:Yonderelk89%2A@dsci551-mongodb.ofzw9.mongodb.net/?retryWrites=true&w=majority")
```

2. Replace `"your_api_key_here"` with your actual OpenAI API key.
3. Replace username, password, and dbName in MONGO_URI with appropriate credentials.

---

##  Setup Instructions

1. Clone this repository or download the ZIP.
2. Create databases by running the included SQL:
```sql
CREATE DATABASE IF NOT EXISTS sars_db;
CREATE DATABASE IF NOT EXISTS movielens_db;
-- Run additional table creation scripts if needed
```

3. Run the table and data setup for the SQL database:
```bash
python TableSetup.py
```

4. Run the alteration to the movies_clean table and create the movie
    genre table:
```bash
# To allow for foreign key constraint for movie_genres
ALTER TABLE movies_clean ADD PRIMARY KEY (movieid);

CREATE TABLE movie_genres (
    `movieid` INT,
    `genre` VARCHAR(255),
    FOREIGN KEY (`movieid`) REFERENCES `movies_clean`(`movieid`)
);
```

5. Run the genre population script (once):
```bash
python GenreSetup.py
```

6. Ensure you properly set the MongoDB path:

Create a MongoDB account, the dataset used was sample_mflix. This should come standard with the creation of your database.
Ensure the path is set properly as shown in "API Key Setup" Section.


---

## Running the Interface

Run the main python file.

```bash
python main.py
```

This will give you two options:

1. Run the SQL interface:

You can then enter queries like:
- "Which genre has the highest average rating?"
- "What countries had the most SARS deaths?"
- "List the top 5 Horror movies."

---
2. Run the MongoDB interface

You can then enter queries like:
- "Find movies with cast containing Tom Hanks and show title and runtime"
- "Find the movie titled 'Inception' and lookup its comments, show the title and comments."
- "Insert a new user with name Alice, email alice@example.com and password s3cret"

## Features

- Natural language to SQL conversion
- Natural language to MongoDB conversion
- Automatic schema inference
- GPT-3.5 powered translation
- Table creation and data insertion from CSVs

---

## Authors

John Cargasacchi — MS Applied Data Science @ USC

Colin Leahey - MS Applied Data Science @ USC

---
