import argparse
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3.8:27b"
NUM_CTX = 65536
MAX_CHARS = 302_000
REQUEST_TIMEOUT = 300
TEXT_DIR = Path("pdf/open_access/text")
TEXT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("llm")
OUTPUT_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT_ABSTRACT = """
    You are analyzing abstracts of scientific papers on the topic of vector databases, in English and German.
    You receive ONLY the abstract of a paper, not the full text.
    Extract exclusively information that is explicitly stated in the abstract.
    Do NOT guess and do not infer anything implicitly.
    Respond EXCLUSIVELY with valid JSON according to exactly this schema, without any additional text:

    {
        "main_problem": "brief description of the addressed problem, if identifiable in the abstract",
        "method": "central method/approach, as described in the abstract",
        "mentioned_systems": ["concrete systems/tools, if mentioned in the abstract, e.g. FAISS, Milvus"],
        "application_domain": "primary application domain, e.g. NLP, image search, bioinformatics",
        "main_contribution": "1-2 sentences on the core contribution, as presented in the abstract",
        "index_type": ["e.g. HNSW, IVF, LSH - only if explicitly mentioned in the abstract"],
        "assumed_paper_type": "e.g. systems paper, benchmark, survey, algorithm proposal - assessment based on the wording",
        "relevance_score": "high/medium/low - how central is the vector database topic to this work",
        "core_focus_or_side_topic": "is the vector database the central topic, or only mentioned in passing (e.g. as a tool used within a larger pipeline)"
    }

    If a field is not addressed in the abstract, set the value to null.
"""

SYSTEM_PROMPT_FULLTEXT = """
    You analyze scientific papers on the topic of vector databases in English and German.
    Extract the following information from the given full text and respond EXCLUSIVELY with valid JSON according to exactly this schema, without additional text:
    
    {
        "main_problem": "brief description of the addressed problem",
        "method": "the central method/approach of the paper",
        "mentioned_systems": ["list of concrete systems/tools, e.g. FAISS, Milvus"],
        "indexing_methods": ["list of mentioned indexing methods, e.g. HNSW, IVF, PQ"],
        "application_domain": "primary application domain, e.g. NLP, image search, bioinformatics",
        "datasets": ["datasets used"],
        "evaluation_metrics": ["metrics used"],
        "main_contribution": "1-2 sentences on the core contribution of the paper",
        "limitations": "limitations mentioned",
        "explicit_research_gap": "open questions/future work explicitly named by the author, if present"
    }

    If a field is not addressed in the text, set the value to null.
"""


# ---------------------------------------------------------------------------
# Ollama-Request
# ---------------------------------------------------------------------------
def analyse_text(text: str, model: str = MODEL_NAME) -> dict:
    if len(text) > MAX_CHARS:
        print(
            f"Hint: Text shorted from {len(text)} to {MAX_CHARS} signs (Context-Safety-Limit)."
        )
        text = text[:MAX_CHARS]

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_ABSTRACT},
                {"role": "user", "content": text},
            ],
            "format": "json",
            "stream": False,
            "options": {
                "num_ctx": NUM_CTX,
                "temperature": 0.1,
            },
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    raw_response = response.json()["message"]["content"]

    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        # Fallback: Take only part between the first { and last },
        # in case the modell outputted additional text before and after JSON
        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1
        return json.loads(raw_response[start:end])


def main():
    parser = argparse.ArgumentParser(
        description="Process a folder with text files inside."
    )
    parser.add_argument("folder", help="Path to text files folder to process")
    args = parser.parse_args()
    TEXT_FOLDER = args.folder

    start_timestamp = time.time()
    start_time = datetime.fromtimestamp(
        start_timestamp, tz=ZoneInfo("Europe/Berlin")
    ).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Start time: {start_time}")

    text_files = sorted(TEXT_DIR.glob("*.txt"))
    print(f"{len(text_files)} text files found.")

    for text_file in text_files:
        text = text_file.read_text(encoding="utf-8")
        print(f"--- {text_file.name} ---")
        print(text)
        json_response = analyse_text(text)

        with open(OUTPUT_DIR / f"{text_file.name}.json", "w", encoding="utf-8") as f:
            json.dump(json_response, f, indent=2, ensure_ascii=False)

    end_timestamp = time.time()
    end_time = datetime.fromtimestamp(
        end_timestamp, tz=ZoneInfo("Europe/Berlin")
    ).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Start time: {start_time}")
    print(f"End time:   {end_time}")
    print("Total minutes: %s" % ((end_timestamp - start_timestamp) / 60))


if __name__ == "__main__":
    main()

# py llm_extractor pdf/open_access/text
# py llm_extractor pdf/not_open_access/text
