import mysql.connector
import pandas as pd
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# --- Utility Functions ---

def connect_mysql(force_db=None):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=force_db or os.getenv("ACTIVE_DB")
    )

def clean_column_names(columns):
    return [re.sub(r"[^\w]", "", col.strip().lower().replace(" ", "_")) for col in columns if pd.notna(col)]

# --- CSV to Table Creation ---

def create_table_from_csv(csv_file, db_name):
    df = pd.read_csv(csv_file)
    df = df.loc[:, df.columns.notna()]
    df = df.dropna(how='all')

    if "sars_2003_complete_dataset_clean" in csv_file.lower():
        df.columns = [
            'date',
            'country',
            'cumulative_number_of_cases',
            'number_of_deaths',
            'number_recovered'
        ]
    elif "summary_data_clean" in csv_file.lower():
        df.columns = [
            'countryregion',
            'cumulative_male_cases',
            'cumulative_female_cases',
            'cumulative_total_cases',
            'no_of_deaths',
            'case_fatalities_ratio_',
            'date_onset_first_probable_case',
            'date_onset_last_probable_case',
            'median_age',
            'age_range',
            'number_of_imported_cases',
            'percentage_of_imported_cases',
            'number_of_hcw_affected',
            'percentage_of_hcw_affected'
        ]
    else:
        df.columns = clean_column_names(df.columns)

    df.columns = df.columns.astype(str)
    df = df.loc[:, (df.columns != 'nan') & (df.columns != '')]

    table_name = os.path.splitext(os.path.basename(csv_file))[0]

    conn = connect_mysql(db_name)
    cursor = conn.cursor()

    column_definitions = []
    for col, dtype in df.dtypes.items():
        if "int" in str(dtype):
            column_definitions.append(f"`{col}` INT")
        elif "float" in str(dtype):
            column_definitions.append(f"`{col}` FLOAT")
        else:
            column_definitions.append(f"`{col}` TEXT")

    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
    cursor.execute(f"CREATE TABLE `{table_name}` ({', '.join(column_definitions)})")
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Table `{table_name}` created successfully.")
    return table_name

# --- Data Insertion ---

def insert_csv_data(csv_file, table_name, db_name):
    df = pd.read_csv(csv_file)
    df = df.loc[:, df.columns.notna()]
    df.columns = clean_column_names(df.columns)

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].where(pd.notna(df[col]), None)

    conn = connect_mysql(db_name)
    cursor = conn.cursor()

    columns = ", ".join([f"`{col}`" for col in df.columns])
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"

    success_count = 0
    fail_count = 0

    try:
        for idx, row in df.iterrows():
            try:
                cursor.execute(insert_query, tuple(row))
                success_count += 1
            except mysql.connector.Error as err:
                print(f"⚠️ Row {idx + 1} failed to insert: {err}")
                fail_count += 1
        conn.commit()
        print(f"✅ Inserted {success_count} rows into `{table_name}`. Failed inserts: {fail_count}")
    finally:
        cursor.close()
        conn.close()

def get_schema(db_name):
    conn = connect_mysql(db_name)
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]

    schema_info = []
    for table in tables:
        cursor.execute(f"DESCRIBE `{table}`")
        columns = cursor.fetchall()
        while cursor.nextset():  # Clear any remaining result sets
            pass
        schema_info.append(f"Table: `{table}`, Columns: {[col[0] for col in columns]}")

    cursor.close()
    conn.close()
    return "\n".join(schema_info)

# --- Main execution block ---

if __name__ == "__main__":
    # SARS Files
    sars_files = [
        "C:\\Users\\alpha\\OneDrive\\Desktop\\DSCI 551\\Python Projs\\Project_Stuff\\DSCI 551 Project SQL\\Sars\\sars_2003_complete_dataset_clean.csv",
        "C:\\Users\\alpha\\OneDrive\\Desktop\\DSCI 551\\Python Projs\\Project_Stuff\\DSCI 551 Project SQL\\Sars\\summary_data_clean.csv"
    ]
    for file in sars_files:
        table = create_table_from_csv(file, os.getenv("DB_SARS"))
        insert_csv_data(file, table, os.getenv("DB_SARS"))

    # MovieLens Files
    movie_files = [
        "C:\\Users\\alpha\\OneDrive\\Desktop\\DSCI 551\\Python Projs\\Project_Stuff\\DSCI 551 Project SQL\\ml-latest-small\\movies_clean.csv",
        "C:\\Users\\alpha\\OneDrive\\Desktop\\DSCI 551\\Python Projs\\Project_Stuff\\DSCI 551 Project SQL\\ml-latest-small\\ratings.csv",
        "C:\\Users\\alpha\\OneDrive\\Desktop\\DSCI 551\\Python Projs\\Project_Stuff\\DSCI 551 Project SQL\\ml-latest-small\\links_clean.csv"
    ]

    # Drop movie_genres first to avoid FK constraint errors
    conn = connect_mysql(os.getenv("DB_MOVIELENS"))
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS movie_genres")
    conn.commit()
    cursor.close()
    conn.close()

    for file in movie_files:
        table = create_table_from_csv(file, os.getenv("DB_MOVIELENS"))
        insert_csv_data(file, table, os.getenv("DB_MOVIELENS"))
