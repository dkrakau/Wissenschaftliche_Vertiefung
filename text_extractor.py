from pathlib import Path
import pymupdf

PDF_DIR = Path("pdf/open_access")
TXT_DIR = Path("pdf/open_access/text")
TXT_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = pymupdf.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def main():
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"{len(pdf_files)} PDF files found.")

    succeeded = 0
    failed = 0

    max_signs = 0
    for i, pdf_path in enumerate(pdf_files, start=1):
        txt_path = TXT_DIR / f"{pdf_path.stem}.txt"

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
