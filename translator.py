import re
import textwrap
from openai_client import get_openai_client

# ───────────────────────── Static schema summary ──────────────────────────────
SCHEMA_INFO = textwrap.dedent(
    """
    Database: sample_mflix

    Collections & Fields (with types)
    • theaters
      - _id (ObjectId)
      - theaterId (string)
      - location (object)

    • sessions
      - _id (ObjectId)
      - user_id (ObjectId)
      - jwt (string)

    • embedded_movies
      - _id (ObjectId)
      - plot (string)
      - genres (array of strings)
      - runtime (number)
      - cast (array of strings)
      - num_mflix_comments (number)
      - title (string)
      - fullplot (string)
      - languages (array of strings)
      - released (string ISO date)
      - directors (array of strings)
      - writers (array of strings)
      - awards (object)
      - lastupdated (string ISO date)
      - year (number)
      - imdb (object)
      - countries (array of strings)
      - type (string)
      - tomatoes (object)
      - plot_embedding (array of numbers)

    • comments
      - _id (ObjectId)
      - name (string)
      - email (string)
      - movie_id (ObjectId)
      - text (string)
      - date (string ISO date)

    • users
      - _id (ObjectId)
      - name (string)
      - email (string)
      - password (string)

    • movies
      - _id (ObjectId)
      - plot (string)
      - genres (array of strings)
      - runtime (number)
      - cast (array of strings)
      - num_mflix_comments (number)
      - poster (string)
      - title (string)
      - lastupdated (string ISO date)
      - languages (array of strings)
      - released (string ISO date)
      - directors (array of strings)
      - rated (string)
      - awards (object)
      - year (number)  # use this for release‑year filters
      - imdb (object)
      - countries (array of strings)
      - type (string)
      - tomatoes (object)

    Relationships
    - comments.movie_id → movies._id
    - sessions.user_id  → users._id
    """
)

# ───────────────────────── Translator helpers ─────────────────────────────────
def _sanitize_dollar_keys(expr: str) -> str:
    """Remove accidental spaces before $ operators (e.g., '" $match"')."""
    return re.sub(r'"\s+\$', '"$', expr)

def _strip_code_fences(expr: str) -> str:
    """Remove any Markdown code fences (```), backticks, or language hints."""
    expr = re.sub(r'```[\s\S]*?```', '', expr)  # strip triple‑backtick blocks
    expr = expr.replace('`', '')                # strip single backticks
    return expr.strip()

# ───────────────────────── Translator function ───────────────────────────────
def translate_nl_to_code(nl_request: str) -> str:
    """Return a single PyMongo expression (string) for the user's request."""

    client = get_openai_client()

    prompt = textwrap.dedent(f"""
        You are a MongoDB assistant. Variable `db` is a PyMongo Database
        connected to **chatDB**.

        Dataset schema:
        {SCHEMA_INFO}

        Guidelines for output:
        - Use valid Python syntax with quoted string keys and values.
        - For simple filters + projections, use `db.collection.find(filter, projection)`.
        - For advanced ops (joins, grouping), use `db.collection.aggregate([...])`.
        - When filtering by release year (e.g., “released in 1915”), prefer `year` field:
            {{'year': 1915}}
        - When filtering on date‑time strings like `released`, you may use regex:
            {{'$regex': '^2020'}}
        - In projections, include `_id: 0` to exclude the `_id` field.
        - Avoid leading spaces before `$` in operator names (use "$match", not " $match").

        Output exactly one Python expression (no comments, imports, or built‑ins).
        Do NOT wrap your answer in any backticks or code fences.

        User request:
        {nl_request}

        Only output the code expression.
    """)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{'role': 'system', 'content': prompt}]
    )

    code = resp.choices[0].message.content.strip()
    code = _strip_code_fences(code)
    code = _sanitize_dollar_keys(code)
    return code
