import sys
import argparse
import pandas as pd
import psycopg2

def parse_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""

    max_pos = max(pos for positions in inverted_index.values() for pos in positions)

    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word

    return " ".join(words)

def main():
    parser = argparse.ArgumentParser(description="Process a JSONL file.")
    parser.add_argument("file", help="Path to the .jsonl file to process")
    args = parser.parse_args()

    file = args.file

    df = pd.read_json(file, lines=True)
    print(df)

    for chunk in pd.read_json(file, lines=True, chunksize=100):
        # process each chunk here
        print(chunk.shape)

        # example processing
        # chunk["new_column"] = ...
        # save results, aggregate, filter, etc.

if __name__ == '__main__':
    main()

# python importer.py ../result-2026-07-30_14-09-51.jsonl