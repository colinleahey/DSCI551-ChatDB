import argparse
import json
import builtins
from translator import translate_nl_to_code
from mongo_client import get_database


def main():
    parser = argparse.ArgumentParser(
        description="Natural-language interface to MongoDB"
    )
    parser.add_argument(
        "--query", "-q", required=True,
        help="Your natural-language MongoDB request"
    )
    args = parser.parse_args()

    # 1) Get the database
    db = get_database()

    # 2) Translate NL → PyMongo code
    code = translate_nl_to_code(args.query)
    print("\nGenerated code snippet:\n", code)

    # 3) Execute the code safely
    local_vars = {'db': db}
    try:
        result = eval(code, {'__builtins__': {}}, local_vars)
    except Exception as e:
        print(f"Error executing MongoDB code: {e}")
        return

    # 4) Print results
    # If it's a cursor, convert to list
    if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
        try:
            output = list(result)
        except Exception:
            output = result
    else:
        output = result

    print("\nQuery results:", json.dumps(output, default=str, indent=2))

if __name__ == "__main__":
    main()
