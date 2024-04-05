import pypdf

class PdfTextScraper:
  def __init__(self):
    pass

  def Scrape(self, pdf_file: str) -> [str]:
    reader = pypdf.PdfReader(pdf_file)

    text_by_page = []

    for page in reader.pages:
      text_by_page.append(page.extract_text())

    return text_by_page

