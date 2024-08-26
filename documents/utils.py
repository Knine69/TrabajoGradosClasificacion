from pdfminer.high_level import extract_text


def pdf_to_bytes(pdf_path):
    all_text = extract_text(pdf_path)
    text_bytes = all_text.encode('utf-8')

    return text_bytes
