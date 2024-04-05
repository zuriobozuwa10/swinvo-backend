from pdf_text_scraper import PdfTextScraper

scraper = PdfTextScraper()

text_list = scraper.Scrape("../pdfs/constitution.pdf")

for text in text_list:
  print("\n\n\nNEW PAGE\n")
  print(text)