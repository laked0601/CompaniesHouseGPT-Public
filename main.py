from code_library import companies_house_api as CH
from code_library import data_manipulation as DM
import openai


def main():
    # Write the company numbers you want to download in company_numbers.txt
    DM.download_company_data("company_numbers.txt")

    # All financial accounts under 'Documents/AA' will be OCR'ed and added to 'Documents/OCR-AA'
    DM.ocr_all_documents(lower_file_size=0, upper_file_size=1024 ** 3)

    # Convert the OCR'ed pdfs to plaintext files under 'Documents/AA/OCR-AA-txt'
    DM.ocr_pdfs_to_txt()

    # Extract the names of the auditor from each file. This uses a large number of OpenAI tokens, so I recommend you use
    # a small sample size of files at first!
    DM.extract_auditor_from_text_files()


if __name__ == "__main__":
    openai.api_key = "YOUR-OPENAI-API-KEY"
    CH.AUTH = ("YOUR-COMPANIES-HOUSE-API-KEY", '')
    main()
