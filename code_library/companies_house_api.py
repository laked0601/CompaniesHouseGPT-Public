import requests
from json import dumps
import os
from time import sleep

AUTH = ('YOUR-API-KEY-HERE', '')
COY_ENDPOINT = "https://api.company-information.service.gov.uk"
DCM_ENDPOINT = "https://document-api.company-information.service.gov.uk"


class CompanyDocument:
    def __init__(self, json_element):
        json_keys = [key for key in json_element.keys()]
        for key in (
                'action_date', 'category', 'date', 'description', 'description_values', 'links', 'type', 'pages',
                'barcode', 'transaction_id'
        ):
            if key in json_keys:
                setattr(self, key, json_element[key])
            else:
                setattr(self, key, None)
        self.json = json_element


doc_extention_table = {
    "application/pdf": ".pdf",
    "application/xhtml+xml": ".html",
}
def filepath_safe_string(stringobj):
    for char in ('<', '>', ':', '"', '/', '\\', '|', '?', '*', '/'):
        stringobj = stringobj.replace(char, '_')
    return stringobj



class UKCompany:
    def __init__(self, company_number):
        self.company_number_param = company_number

        self.links = None
        self.has_charges = None
        self.jurisdiction = None
        self.type = None
        self.registered_office_address = None
        self.undeliverable_registered_office_address = None
        self.company_number = None
        self.registered_office_is_in_dispute = None
        self.date_of_creation = None
        self.etag = None
        self.accounts = None
        self.has_insolvency_history = None
        self.sic_codes = []
        self.company_status = None
        self.company_name = None
        self.has_super_secure_pscs = None
        self.date_of_cessation = None
        self.can_file = None

        self._keys = [
            x for x in dir(self)
            if x[0:2] != "__"
            and x[-2:] != "__"
            and getattr(self, x) is None
        ]
        self.json = {}

    def get_profile(self):
        r = get_company_profile(self.company_number_param)
        for key, value in r.items():
            if key in self._keys:
                setattr(self, key, value)
        self.json = r

    def get_filing_history(self):
        r = ch_get("/company/%s/filing-history" % (self.company_number_param,), params={"items_per_page": 50}).json()
        for key, value in r.items():
            if key in self._keys:
                setattr(self, key, value)
        self.json = r

    @staticmethod
    def get_document_simple(document_url):
        if document_url[0:59] != "https://find-and-update.company-information.service.gov.uk/":
            return False
        r = requests.get(document_url)
        if r.status_code != 200:
            return False
        return doc_extention_table[r.headers["Content-Type"]], r.content


    @staticmethod
    def get_document(transaction_id):
        r = ch_get(endpoint=DCM_ENDPOINT, url="/document/%s/content" % (transaction_id,))
        return doc_extention_table[r.headers["Content-Type"]], r.content

    def download_company_documents(self, doc_type=None, max_download=None):
        print("Downloading Documents for %s..." % (self.company_number_param,))
        if not os.path.exists("Documents"):
            os.mkdir("Documents")
        self.get_filing_history()
        for i, document in enumerate(self.json["items"]):
            print(i, document["date"], document["description"], end=" ")
            if doc_type is not None and document["type"] != doc_type:
                continue
            if max_download is not None and i > max_download:
                continue
            if "document_metadata" not in document["links"]:
                print("NOT DOWNLOADABLE!")
                continue
            metadata_endpoint = document["links"]["document_metadata"]
            document_id = metadata_endpoint[metadata_endpoint.rfind('/') + 1:]
            dirname = filepath_safe_string(document["type"])
            if not os.path.exists("Documents/" + dirname):
                os.mkdir("Documents/" + dirname)
            filename = "%s - %s - %s - %s" % (self.company_number_param, document["date"], document["barcode"], document["category"])
            filename = filepath_safe_string(filename)
            filepath = "Documents/%s/%s" % (dirname, filename)
            if os.path.exists(filepath + ".pdf") or os.path.exists(filepath + ".html"):
                print("file '%s' already exists!" % (filename,))
                continue
            extention, content = self.get_document(document_id)
            new_filepath = "Documents/%s/%s%s" % (dirname, filename, extention)
            with open(new_filepath, 'wb') as wf:
                wf.write(content)
            print("DONE!")

    def get_filing_history_item(self):
        pass

    def __str__(self):
        return_dict = {}
        for k in self._keys:
            v = getattr(self, k)
            try:
                dumps(v)
                return_dict[k] = v
            except TypeError:
                return_dict[k] = str(v)
        return dumps(return_dict, indent=4)


def ch_get(url, endpoint=COY_ENDPOINT, params=None, headers=None):
    with requests.session() as s:
        s.auth = AUTH
        r = s.get(endpoint + url, )
        if r.status_code == 429:
            print("sleeping 5 mins...")
            sleep(5 * 60)
            r = s.get(endpoint + url, )
    validate_response(r)
    return r


def validate_response(http_response_object):
    if http_response_object.status_code == 200:
        return True
    else:
        print(http_response_object.status_code, http_response_object.reason)
        print(http_response_object.headers)
        print(http_response_object.text[0:200])


def get_company_profile(company_number):
    r = ch_get("/company/%s" % (company_number,))
    return r.json()


def get_registered_office_address(company_number):
    r = ch_get("/company/%s/registered-office-address" % (company_number,))
    return r.json()


def get_filing_history(company_number):
    r = ch_get("/company/%s/registered-office-address" % (company_number,))
    return r.json()


def get_filing_transaction(company_number, transaction_id):
    r = ch_get("/company/%s/filing-history/%s" % (company_number, transaction_id))
    return r.json()

