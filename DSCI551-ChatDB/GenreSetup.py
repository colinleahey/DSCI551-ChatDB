import mysql.connector
import os
import ast
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

def connect_mysql(force_db=None):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=force_db or os.getenv("ACTIVE_DB")
    )

def populate_movie_genres():
    conn = connect_mysql(os.getenv("DB_MOVIELENS"))
    cursor = conn.cursor()

    cursor.execute("SELECT movieid, genres FROM movies_clean")
    rows = cursor.fetchall()

    insert_query = "INSERT INTO movie_genres (movieid, genre) VALUES (%s, %s)"
    success, failed = 0, 0

    for movieid, genre_list in rows:
        try:
            if genre_list and genre_list.strip() and genre_list != '(no genres listed)':
                genres = ast.literal_eval(genre_list)
                for genre in genres:
                    cursor.execute(insert_query, (movieid, genre.strip()))
                    success += 1
        except Exception as e:
            print(f"⚠️ Skipped movieid {movieid}: {e}")
            failed += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Inserted {success} genres. ❌ Failed: {failed}")

if __name__ == "__main__":
    populate_movie_genres()
