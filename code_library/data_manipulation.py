import openai
from . import companies_house_api as CH
from .pdf_manipulation import ocr_pdf, read_and_replace_file, convert_pdf_to_text, temp_file, get_pdf_pages, html_to_pdf
import os
from threading import Thread
from time import time
from json import dumps, loads
import re
import csv

def find_balance_sheets(text):
    keywords = ("assets", "liabilities", "balance sheet", "equity", "as at")
    groups = text.split("")
    valid_groups = []
    for x, group in enumerate(groups):
        i = 0
        for key in keywords:
            if group.lower().find(key) != -1:
                i += 1
        if i > 2:
            valid_groups.append(group)
    return valid_groups


def download_and_extract_accounts(url):
    extn, content = CH.UKCompany.get_document_simple(url)
    temp_pdf = temp_file(extension=".pdf")
    with open(temp_pdf, 'wb') as wf:
        wf.write(content)
    pdf_page_count = get_pdf_pages(temp_pdf)
    if pdf_page_count > 25:
        return False
    temp_text = convert_pdf_to_text(temp_pdf)
    with open(temp_file(extension=".txt", dir_location="example-simple-accounts"), 'w') as wf:
        wf.write(temp_text)
    os.remove(temp_pdf)


def download_company_data(from_file, specify_doctype=None, max_download=None, max_time=60*10):
    start_time = int(time())
    with open(from_file, 'r', encoding="utf-8") as rf:
        lines = rf.read().split('\n')
        for line in lines:
            if line == '':
                continue
            cpy = CH.UKCompany(line)
            cpy.download_company_documents(doc_type=specify_doctype, max_download=max_download)
            if time() - start_time > max_time:
                break


def get_input_documents(dirpath, valid_extn, lower_file_size, upper_file_size):
    files = []
    with os.scandir(dirpath) as direntry:
        for file in direntry:
            name, extn = os.path.splitext(file.name)
            if extn == valid_extn:
                res = os.stat(file.path)
                if upper_file_size > res.st_size > lower_file_size:  # 500kb
                    files.append((file.name, file.path))
    return files


def ocr_all_documents(lower_file_size=500 * 1024, upper_file_size=1000 * 1024, max_other_threads=2, timeout=10 * 60):
    if not os.path.exists("Documents/OCR-AA"):
        os.mkdir("Documents/OCR-AA")
    files = get_input_documents("Documents/AA", ".pdf", lower_file_size, upper_file_size)
    new_files = []
    for output_filename, input_path in files:
        if not os.path.exists("Documents/OCR-AA/" + output_filename):
            new_files.append((output_filename, input_path ))
        else:
            print("skipped", output_filename)
    files = new_files
    def process_function(files_list, start, temp_file_location):
        if not os.path.exists(temp_file_location):
            os.mkdir(temp_file_location)
        start_time = time()
        for filename, filepath in files_list:
            print(start, end=" ")
            start += 1
            ocr_filepath = "Documents/OCR-AA/" + filename
            print(filename)
            if time() - start_time > timeout:
                break
            while True:
                # try:
                ocr_pdf(filepath, ocr_filepath, temp_file_location=temp_file_location)
                break
                # except:
                #     pass
        rm_files = []
        if os.path.exists(temp_file_location):
            with os.scandir(temp_file_location) as direntry:
                for file in direntry:
                    rm_files.append(file.path)
            for file in rm_files:
                os.remove(file)
            os.rmdir(temp_file_location)
    print("Preparing to OCR %d documents..." % (len(files),))
    if max_other_threads > 0 and len(files) > max_other_threads:
        print("Running %d threads to increase OCR speed..." % (max_other_threads,))
        files_split = []
        file_count = len(files)
        block = file_count // (max_other_threads + 1)
        x = 0
        for i in range(0, block * max_other_threads, block):
            files_split.append(Thread(target=process_function, args=(files[i:i + block], i, "tempdir-%d" % (x,))))
            x += 1
        for thr in files_split:
            thr.start()
        process_function(files[block * max_other_threads:], block * max_other_threads, "tempdir-%d" % (x,))
        for thr in files_split:
            thr.join()
    else:
        process_function(files, 0, 'Tempfiles')
    print("Done!")


def html_to_pdf_all():
    files = get_input_documents("Documents/AA", ".html", lower_file_size=1024 * 200, upper_file_size=1024 * 10000)
    start_time = time()
    x = 0
    for output_filename, input_filepath in files:
        html_to_pdf(input_filepath, "Documents/OCR-AA/" + output_filename)
        x += 1
        if time() - start_time > 10 * 60:
            break


def ocr_pdfs_to_txt():
    output_dir = "Documents/OCR-AA-txt"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    files = get_input_documents("Documents/OCR-AA", valid_extn=".pdf", lower_file_size=0, upper_file_size=1024 ** 3)
    thrs = []
    files_length = len(files)
    blocksize = files_length // 4
    i = 0
    blocks = []
    for x in range(0, blocksize * 2, blocksize):
        blocks.append(files[x: x + blocksize])
    blocks.append(files[blocksize * 2:])
    def conv_txt(block, start, temp_dir_path):
        start_time = time()
        for output_name, input_path in block:
            output_path = "%s/%s" % (output_dir, output_name.replace(".pdf", ".txt"))
            if os.path.exists(output_path):
                print(start, "skipped")
            else:
                print(start, output_path)
                with open(output_path, 'w', encoding="utf-8") as wf:
                    wf.write(convert_pdf_to_text(input_path, temp_dir_path))
            start += 1
            if time() - start_time > 10 * 60:
                break
    for i, block in enumerate(blocks[0:-1]):
        thrs.append(Thread(target=conv_txt, args=(block, i * blocksize, "tempdir-%d" % (i,))))
    for thr in thrs:
        thr.start()
    conv_txt(blocks[-1], (len(blocks) - 1) * blocksize, "tempdir-%d" % (len(blocks),))
    for thr in thrs:
        thr.join()


def split_doc_to_pages(filepath):
    with open(filepath, 'r', encoding="utf-8") as rf:
        return rf.read().split('')


def filter_unneeded_spacing(page):
    mod_page = page.replace("    ", '\t')
    mod_page = mod_page.replace("  ", ' ')
    mod_page_len = len(mod_page)
    mod_page = mod_page.replace("\n\n\n", "\n\n")
    while len(mod_page) != mod_page_len:
        mod_page_len = len(mod_page)
        mod_page = mod_page.replace("\n\n\n", "\n\n")
    mod_page = mod_page.replace("\t\t\t\t", "\t")
    return mod_page


def sentence_describe_pages(filepath):
    pages = split_doc_to_pages(filepath)
    json_content = {"page_count": len(pages), "content": '', "token_count": 0}
    for i, page in enumerate(pages):
        mod_page = filter_unneeded_spacing(page)
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt="Summarize the below text:\n\n\"%s\"" % (mod_page[0:1920],),
            max_tokens=1000,
            temperature=1
        )
        json_content["token_count"] += response["usage"]["total_tokens"]
        json_content["content"] += '\n\n' + response["choices"][0]["text"]
        print(i, json_content["token_count"])
    json_content["total_cost"] = round((json_content["token_count"] / 1000) * 0.02, 2)
    with open("file_output3.json", 'w') as wf:
        wf.write(dumps(json_content, indent=4))


def repair_json(response_txt):
    try:
        return loads(response_txt)
    except:
        pass
    exception_txt = "Unable to repair json text '%s'" % (response_txt,)
    json_values_re = re.compile(
        r'\"audit[_\w]+name\"\s*: *(.*?),\s*"report[_\w]+date" *:\s*(.*?),\s*"exempt[_\w]+audit" *: *(.*?)}'
    )
    extracted_values = json_values_re.findall(response_txt)
    if len(extracted_values) != 1 and len(extracted_values[0]) != 3:
        raise Exception(exception_txt, " Extracted values were %s" % (str(extracted_values),))
    extracted_values = list(extracted_values[0])
    for i, value in enumerate(extracted_values):
        formatted_value = str(value).strip()
        if len(formatted_value) > 1:
            if formatted_value[0] == '"' and formatted_value[-1] == '"':
                formatted_value = formatted_value[1:-1]

        lower_value = formatted_value.lower()
        if lower_value == "null":
            formatted_value = None
        elif lower_value == "true":
            formatted_value = True
        elif lower_value == "false":
            formatted_value = False

        extracted_values[i] = formatted_value

    return {
        "auditor_name": extracted_values[0],
        "report_date": extracted_values[1],
        "exempt_audit": extracted_values[2],
    }






def determine_audit_status(filepath, max_pages=8):
    pages = split_doc_to_pages(filepath)
    auditor = None
    report_date = None
    exempt_audit = None
    token_count = 0
    for i, page in enumerate(pages):
        if i > max_pages:
            break
        mod_page = filter_unneeded_spacing(page)
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt="Respond in a json format on if the below text contains an auditor, the annual report date of "
                   "the document and if the reporting company is exempt from audit. "
                   "The json format should be {\"auditor_name\": {{null or Name of Auditor}},"
                   "\"report_date\": {{null or Date of Annual Report}}, \"exempt_audit\": {{null, true or false}}}:"
                   "\n\n\"%s\"" % (mod_page[0:1920],),
            max_tokens=1000,
            temperature=1
        )
        response_txt = response["choices"][0]["text"]
        token_count += response["usage"]["total_tokens"]
        try:
            json_variable = loads(response_txt)
            if auditor is None and exempt_audit is None:
                auditor = json_variable["auditor_name"]
                if json_variable["exempt_audit"]:
                    exempt_audit = json_variable["exempt_audit"]
            if report_date is None:
                report_date = json_variable["report_date"]
        except:
            print("unable to load page", response_txt)
        if report_date is not None and (auditor is not None or exempt_audit is not None):
            break
    return auditor, report_date, exempt_audit, token_count


def extract_auditor_from_text_files():
    if not os.path.exists("checked_comanies.txt"):
        with open("checked_companies.txt", 'w') as wf:
            pass
    with os.scandir("Documents/OCR-AA-txt") as direntry:
        company_number_re = re.compile("^(\d+)")
        with open("checked_companies.txt", 'r') as cc:
            checked_companies = cc.read().split('\n')
        with open("audit_status.csv", 'a', newline='') as wf:
            csv_writer = csv.writer(wf, quotechar='"', delimiter=',')
            csv_writer.writerow(["Auditor", "Report Date", "Exempt from Audit", "Token Count", "Company Number", "Filename"])
            for i, file in enumerate(direntry):
                if file.name in checked_companies:
                    continue
                with open("checked_companies.txt", 'w') as cc:
                    cc.write('\n'.join(checked_companies))
                company_number = company_number_re.search(file.name).group(1)
                auditor, report_date, exempt_audit, token_count = determine_audit_status(file.path)
                print(i, file.name, auditor, report_date, exempt_audit, token_count )
                csv_writer.writerow((auditor, report_date, exempt_audit, token_count, company_number, file.name))

