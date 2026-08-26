import argparse
import pymupdf
from pathlib import Path


def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = pymupdf.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def main():
    parser = argparse.ArgumentParser(description="Process a folder with pdfs inside.")
    parser.add_argument("folder", help="Path to pdf folder to process")
    args = parser.parse_args()

    PDF_FOLDER = Path(args.folder)
    PDF_FOLDER.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(PDF_FOLDER.glob("*.pdf"))
    print(f"{len(pdf_files)} PDF files found.")

    succeeded = 0
    failed = 0

    max_signs = 0
    for i, pdf_path in enumerate(pdf_files, start=1):
        txt_path = PDF_FOLDER / "text" / f"{pdf_path.stem}.txt"

        if txt_path.exists():
            print(
                f"Processed ({i}/{len(pdf_files)}) {pdf_path.name} -> skipped (already extracted)"
            )
            continue

        try:
            text = extract_text_from_pdf(pdf_path)
            txt_path.write_text(text, encoding="utf-8")
            signs = len(text)
            print(
                f"Processed ({i}/{len(pdf_files)}) {pdf_path.name} -> {signs} signs extracted"
            )
            succeeded += 1
            if max_signs < signs:
                max_signs = signs
        except Exception as e:
            print(f"Processed ({i}/{len(pdf_files)}) {pdf_path.name} -> FAILED: {e}")
            failed += 1

    print(f"Done. Succeeded: {succeeded}, failed: {failed}")
    print(f"Max signs: {max_signs}")


if __name__ == "__main__":
    main()

# py text_extractor.py pdf/open_access
# py text_extractor.py pdf/not_open_access
