import time
import math
import json
import csv
import pandas as pd
import requests

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CSV_DIR = Path("database/csv")
PDF_DIR = Path("pdf/open_access")
PDF_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_TIMEOUT = 300

UNPAYWALL_EMAIL = "email@example.com"  # needed for unpaywall request

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/pdf,text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
}

skipped_counter = 0
succeeded_counter = 0
failed_counter = 0
unpaywall_fallback_counter = 0


def build_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = build_session()


def clean_value(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def log_error(work_id: str, error_message: str):
    log_path = PDF_DIR / "error_log" / "errors.log"
    is_new = not log_path.exists()
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["id", "error_message"])
        writer.writerow([work_id, error_message])


def get_unpaywall_pdf(doi: str) -> str | None:
    doi_clean = doi.replace("https://doi.org/", "").strip()
    try:
        resp = SESSION.get(
            f"https://api.unpaywall.org/v2/{doi_clean}",
            params={"email": UNPAYWALL_EMAIL},
            timeout=30,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        loc = data.get("best_oa_location") or {}
        return loc.get("url_for_pdf") or loc.get("url")
    except Exception as e:
        # log_error(work_id, f"Unpaywall-Request failed for DOI {doi_clean}: {e}")
        print(f"Unpaywall-Request failed for DOI {doi_clean}: {e}")
        return None


def try_download(url: str, dest_path: Path, work_id: str) -> bool:
    try:
        resp = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=BROWSER_HEADERS,
            allow_redirects=True,
        )
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and resp.content[:4] != b"%PDF":
            # log_error(work_id, f"Response is not a pdf (Content-Type: {content_type}, URL: {url})")
            print(
                f"{work_id}, Response is not a pdf (Content-Type: {content_type}, URL: {url})"
            )
            return False

        dest_path.write_bytes(resp.content)
        return True

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        # log_error(work_id, f"HTTP {status} for URL {url}")
        print(f"{work_id}, HTTP {status} for URL {url}")
        return False
    except Exception as e:
        # log_error(work_id, f"PDF download failed for URL {url}: {e}")
        print(f"{work_id}, PDF download failed for URL {url}: {e}")
        return False


def download_pdf(
    counter: int, length: int, work_id: str, doi, pdf_url, dest_path: Path
) -> bool:
    global skipped_counter, succeeded_counter, failed_counter, unpaywall_fallback_counter

    if dest_path.exists():
        skipped_counter += 1
        print(
            f"Processed ({counter}/{length}) -> {work_id}, PDF download skipped (already exists)"
        )
        return True

    # Step 1: try pdf_url directly, if present
    if isinstance(pdf_url, str) and pdf_url.strip():
        if try_download(pdf_url, dest_path, work_id):
            succeeded_counter += 1
            print(
                f"Processed ({counter}/{length}) -> {work_id}, PDF download succeeded"
            )
            return True

    # Step 2: Fallback for Unpaywall, if DOI is present
    if isinstance(doi, str) and doi.strip():
        time.sleep(0.3)  # Unpaywall-Rate-Limit
        fallback_url = get_unpaywall_pdf(doi)
        if fallback_url:
            if try_download(fallback_url, dest_path, work_id):
                succeeded_counter += 1
                unpaywall_fallback_counter += 1
                print(
                    f"Processed ({counter}/{length}) -> {work_id}, PDF download succeeded via Unpaywall"
                )
                return True
            else:
                # log_error(work_id, f"Unpaywall-URL also failed: {fallback_url}")
                print(f"{work_id}, Unpaywall-URL also failed: {fallback_url}")
        else:
            # log_error(work_id, f"No Unpaywall-Link for DOI {doi}")
            print(f"{work_id}, No Unpaywall-Link for DOI {doi}")

    failed_counter += 1
    print(
        f"Processed ({counter}/{length}) -> {work_id}, PDF download failed on all attempts"
    )
    return False


def main():

    start_timestamp = time.time()
    start_time = datetime.fromtimestamp(
        start_timestamp, tz=ZoneInfo("Europe/Berlin")
    ).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Start time: {start_time}")

    df = pd.read_csv(CSV_DIR / "open_access.csv")
    len_df = len(df)

    df_with_pdf_url = df.dropna(subset=["pdf_url"])
    len_df_with_pdf_url = len(df_with_pdf_url)

    df_without_pdf_url = df.drop(df_with_pdf_url.index).copy()
    df_without_pdf_url["processed"] = False
    len_df_without_pdf_url = len(df_without_pdf_url)

    records = df_without_pdf_url.to_dict(orient="records")
    records = [{k: clean_value(v) for k, v in row.items()} for row in records]

    print(f"Open access works with pdf_url: {len_df_with_pdf_url}")
    print(f"Open access works without pdf_url: {len_df_without_pdf_url}")
    print(f"Total open access works: {len_df_with_pdf_url + len_df_without_pdf_url}")

    with open(PDF_DIR / "open_access_without_pdf_url.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        print(
            f"Worte open access works without pdf_url to json file. (manual download required)"
        )

    counter = 0
    for row in df.itertuples():
        counter += 1
        downloaded = download_pdf(
            counter,
            len_df,
            row.id,
            row.doi,
            row.pdf_url,
            PDF_DIR / f"{row.id}.pdf",
        )
        if not downloaded:
            log_error(row.id, row.doi)
        time.sleep(0.5)  # polite delay

    print(f"\nTotal PDF-Download skipped: {skipped_counter}")
    print(f"Total PDF-Download succeeded: {succeeded_counter}")
    print(f"PDF-Download succeeded by Unpaywall-Fallback: {unpaywall_fallback_counter}")
    print(f"Total PDF-Download failed: {failed_counter}")

    end_timestamp = time.time()
    end_time = datetime.fromtimestamp(
        end_timestamp, tz=ZoneInfo("Europe/Berlin")
    ).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Start time: {start_time}")
    print(f"End time:   {end_time}")
    print("Total minutes: %s" % ((end_timestamp - start_timestamp) / 60))


if __name__ == "__main__":
    main()
