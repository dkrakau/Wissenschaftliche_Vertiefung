import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(
        description="Combine crawler and requester JSONL results"
    )

    parser.add_argument(
        "--crawler",
        required=True,
        help="Crawler result JSONL file"
    )

    parser.add_argument(
        "--requester",
        required=True,
        help="Requester result JSONL file"
    )

    args = parser.parse_args()

    output_file = f"result-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jsonl"

    with open(output_file, "w", encoding="utf-8") as outfile:
        for filename in [args.crawler, args.requester]:
            with open(filename, "r", encoding="utf-8") as infile:
                for line in infile:
                    outfile.write(line)

    print(f"Collected all results in {output_file}")

if __name__ == "__main__":
    main()