from TableSetup import connect_mysql, get_schema
import mysql.connector
import openai
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv(".env")
openai.api_key = os.getenv("OPENAI_API_KEY")


query_cache = {}

# Find synonyms:
COUNTRY_SYNONYMS = {
    "vietnam": "viet nam",
    "south korea": "republic of korea",
    "usa": "united states",
    "u.s.": "united states",
    "u.s.a.": "united states",
    "us": "united states",
    "uk": "united kingdom",
    "u.k.": "united kingdom",
}

# replaces country name variations — like converting 'USA' to 'united states'
def normalize_query_input(nl_query):
    for user_term, db_term in COUNTRY_SYNONYMS.items():
        pattern = re.compile(rf'\b{re.escape(user_term)}\b', re.IGNORECASE)
        nl_query = pattern.sub(db_term, nl_query)
    return nl_query

# infers the desired database
def infer_database(nl_query: str) -> str:
    q = nl_query.lower()
    if "sars" in q or "country" in q:
        return os.getenv("DB_SARS")
    elif "movie" in q or "rating" in q or "genre" in q:
        return os.getenv("DB_MOVIELENS")
    else:
        return os.getenv("DB_NAME")  # default

# database execution
def execute_sql_query(natural_query):
    normalized_query = normalize_query_input(natural_query)

    # nl_to_sql now auto-infers the db internally
    sql_query, target_db = nl_to_sql(normalized_query)
    print(f"\nGPT-Generated SQL Query:\n{sql_query}")

    conn = connect_mysql(target_db)
    cursor = conn.cursor()

    try:
        if sql_query.strip().lower().startswith(("insert", "update", "delete")):
            confirm = input("!!!! This query modifies data. Proceed? (yes/no): ")
            if confirm.lower() != "yes":
                return "Query canceled."

        cursor.execute(sql_query)

        if cursor.description:
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return "\n".join([", ".join(str(item) for item in row) for row in results]) if results else "No results."

        conn.commit()
    except mysql.connector.Error as err:
        return f"SQL Error: {err}"
    finally:
        cursor.close()
        conn.close()

    return "Query executed."

# takes the user's natural language query, passes it to
# the OpenAI API with a detailed prompt that includes the
# schema, and returns the resulting SQL. Some parts are
# customized to fit outliers.
def nl_to_sql(natural_query):
    if natural_query in query_cache:
        print("Returning cached SQL query.")
        return query_cache[natural_query], infer_database(natural_query)

    # Automatically infer the correct database
    query_lower = natural_query.lower()
    if any(keyword in query_lower for keyword in ["sars", "country", "taiwan", "china", "deaths", "recovered", "imported", "fatalities"]):
        db_name = os.getenv("DB_SARS")
    else:
        db_name = os.getenv("DB_MOVIELENS")

    schema = get_schema(db_name)

    # SARS-specific prompt logic
    if db_name == os.getenv("DB_SARS"):
        prompt = f"""
        Convert the following natural language query into a MySQL SQL query.

        - Use only the table and column names provided in the schema.
        - If "attribute" in user_input or "column name" in user_input or "fields" in user_input or "schema" in user_input:
            return "SHOW COLUMNS FROM movies_clean;"
        - For JOINs on country names, normalize using: REPLACE(LOWER(column), ' ', '')
        - For WHERE conditions involving country names:
          • If the user says "not China", "except China", or "excluding China", use:
              REPLACE(LOWER(country), ' ', '') != 'china'
          • If the user says "not in China" or "outside China", use:
              REPLACE(LOWER(country), ' ', '') NOT LIKE '%china%'
          - If the user does not specify 'china', do not filter out China.
        - Always return original `country` field values (not normalized ones).
        - Use GROUP BY `country` when aggregating.
        - Always wrap table and column names in backticks.
        - Return only executable SQL — no explanations, comments, or markdown formatting.

        Schema:
        {schema}

        Natural Language Query:
        \"{natural_query}\"

        SQL Query:
        """
    else:
        # MovieLens or generic schema prompt
        prompt = f"""
        Convert the following natural language query into a MySQL SQL query.

        - Use only the table and column names provided in the schema.
        - Always wrap table and column names in backticks.
        - Support SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, OFFSET.
        - Support JOIN operations using matching keys like `movieId` where applicable.
        - When querying genres individually (e.g. "average rating for Horror"), join with `movie_genres` using `movieid`.
        - Use `movie_genres.genre` in WHERE, GROUP BY, or SELECT as needed.
        - When the user asks for 'no genre listed' or 'no genre' when searching, aggregate on genre: (no genres listed).
        - Use `SHOW TABLES` or 
          `SELECT table_name FROM information_schema.tables WHERE table_schema = '{db_name}'` to list tables.
        - If the user asks about the release year, extract it from `title` using:
            CAST(SUBSTRING(`title`, -5, 4) AS UNSIGNED)
        - If "attribute" in user_input or "column name" in user_input or "fields" in user_input or "schema" in user_input:
            return "SHOW COLUMNS FROM movies_clean;"

        Ranking and filtering logic:
        - When filtering by movie title, use LIKE '%<title>%' to allow partial title matching and avoid requiring exact year formatting.
        - If the user asks “which items have the highest rating?”, return all tied rows by comparing against the maximum (e.g., WHERE avg_rating = (SELECT MAX(...))) — do NOT use LIMIT 1.
        - If the user asks to “list the top N” or “top-rated” or “highest rated”, use:
            • GROUP BY the entity (e.g., `movieid`)
            • Aggregate with AVG(rating)
            • ORDER BY avg_rating DESC
            • Use LIMIT N (and OFFSET if requested)
            • Order ties lexicographically by title if needed
            - When the user asks to skip top results (e.g., “AFTER the top 10”, “skipping the first 5”), use `LIMIT` and `OFFSET` directly instead of subqueries.


        - Always return only executable SQL — no explanations, comments, or markdown formatting.

        Schema:
        {schema}

        Natural Language Query:
        \"{natural_query}\"

        SQL Query:
        """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert MySQL assistant that returns only executable SQL queries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )

    sql_query = response.choices[0].message.content.strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    query_cache[natural_query] = sql_query

    return sql_query, db_name

if __name__ == "__main__":
    while True:
        user_input = input("Enter your natural language query: ")
        if user_input.lower() in ("quit", "exit"):
            print("Exiting ChatDB. Goodbye.")
            break

        print(execute_sql_query(user_input))

