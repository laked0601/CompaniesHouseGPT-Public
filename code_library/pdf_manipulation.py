import os
import re
import subprocess


def get_pdf_pages(filepath):
    file_data = str(subprocess.run(["pdfinfo.exe", filepath], capture_output=True).stdout)
    page_count_re = re.compile("Pages:\s+(\d+)", re.DOTALL)
    page_count = int(page_count_re.search(file_data).group(1))
    return page_count


def temp_file(extension=".pdf", dir_location=None):
    if dir_location is None:
        dir_location = "Tempfiles"
    if not os.path.exists(dir_location):
        os.mkdir(dir_location)
    i = 0
    while os.path.exists("%s/temp%d%s" % (dir_location, i, extension)):
        i += 1
    return "%s/temp%d%s" % (dir_location, i, extension)


def merge_pdf(mainpdf, secondarypdf, temp_file_location=None):
    output_pdf = temp_file(extension=".pdf", dir_location=temp_file_location)
    subprocess.run(["pdfunite.exe", mainpdf, secondarypdf, output_pdf])
    os.remove(mainpdf)
    os.rename(output_pdf, mainpdf)
    return mainpdf


def html_to_pdf(html_file_path, output_pdf_path):
    if output_pdf_path[-5:] == ".html":
        output_pdf_path = output_pdf_path[0:-5] + ".pdf"
    elif output_pdf_path[-4:] == ".htm":
        output_pdf_path = output_pdf_path[0:-4] + ".pdf"

    subprocess.run(
        ["wkhtmltopdf.exe", html_file_path, output_pdf_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )


def ocr_pdf(filepath, output_filepath, temp_file_location=None):
    if (temp_file_location is not None) and (not os.path.exists(temp_file_location)):
        os.mkdir(temp_file_location)
    page_count = get_pdf_pages(filepath)
    png_path = pdf_to_png(filepath, 0, temp_file_location=temp_file_location)
    main_output_file = temp_file(".pdf", temp_file_location)
    pdf_path = png_to_pdf(png_path, main_output_file, temp_file_location=temp_file_location)
    os.remove(png_path)
    for x in range(2, page_count + 1):
        png_path = pdf_to_png(filepath, x, temp_file_location=temp_file_location)
        pdf_path = png_to_pdf(png_path, temp_file_location=temp_file_location)
        merge_pdf(main_output_file, pdf_path, temp_file_location=temp_file_location)
        os.remove(png_path)
        os.remove(pdf_path)
    os.rename(main_output_file, output_filepath)


def pdf_to_png(filepath, pagenum, temp_file_location=None):
    png_path = temp_file(extension=".png", dir_location=temp_file_location)
    with open(png_path, 'wb') as wf:
        subprocess.run(
            ["pdftoppm.exe", "-f", str(pagenum), "-l", str(pagenum), "-png", filepath],
            stdout=wf,
            stderr=subprocess.DEVNULL
        )
    return png_path


def png_to_pdf(png_path, output_file=None, temp_file_location=None):
    if output_file is None:
        pdf_path = temp_file(extension=".pdf", dir_location=temp_file_location)
    else:
        pdf_path = output_file
    pdf_path = pdf_path[0:-4]
    subprocess.run(
        ["tesseract.exe", png_path, pdf_path, "PDF"],
    )
    pdf_path += ".pdf"
    return pdf_path


def convert_pdf_to_text(ocr_pdf_path, temp_dir_path=None):
    temp_txt = temp_file(".txt", dir_location=temp_dir_path)
    subprocess.run(["pdftotext.exe", "-layout", ocr_pdf_path, temp_txt])
    with open(temp_txt, 'r', encoding="utf-8") as rf:
        text_data = rf.read() + '\n'
    os.remove(temp_txt)
    return text_data


def read_and_replace_file(file_object):
    return file_object.read().decode('utf-8', 'ignore')
