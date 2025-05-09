import os

def run_sql_interface():
    from SQL_API.py import execute_sql_query
    print("\nYou are now connected to the SQL interface.")
    while True:
        user_input = input("Enter your natural language query (or type 'back' to return): ")
        if user_input.lower() in ("back", "exit", "quit"):
            break
        result = execute_sql_query(user_input)
        print("\nResult:\n", result)

def run_mongo_interface():
    from mongoMain.py import get_database
    from translator import translate_nl_to_code

    print("\nYou are now connected to the MongoDB interface.")
    db = get_database()

    while True:
        user_input = input("Enter your natural language query (or type 'back' to return): ")
        if user_input.lower() in ("back", "exit", "quit"):
            break

        try:
            code = translate_nl_to_code(user_input)
            print("\nGenerated code snippet:\n", code)
            local_vars = {'db': db}
            result = eval(code, {'__builtins__': {}}, local_vars)

            if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
                result = list(result)
            print("\nResult:\n", result)
        except Exception as e:
            print(f"Error executing MongoDB code: {e}")

if __name__ == "__main__":
    print("Welcome to ChatDB")
    while True:
        db_choice = input("\nWhat database do you want to access? ('SQL' / 'MongoDB') or type 'exit' to quit: ").strip().lower()

        if db_choice == "exit":
            print("Goodbye.")
            break
        elif db_choice == "sql":
            run_sql_interface()
        elif db_choice == "mongodb":
            run_mongo_interface()
        else:
            print("Invalid choice. Please enter 'SQL', 'MongoDB', or 'exit'.")
