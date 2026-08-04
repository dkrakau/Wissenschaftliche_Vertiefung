import json

def load_work_types(): 
    with open("types/work_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_institution_types(): 
    with open("types/institution_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_soure_types(): 
    with open("types/source_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_license_types(): 
    with open("types/license_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_version_types(): 
    with open("types/version_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_indexed_in_types(): 
    with open("types/indexed_in_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_language_types(): 
    with open("types/iso-639-1-alpha-2-language-code_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_country_types(): 
    with open("types/iso-3166-1-alpha-2-country-code_types.json", "r", encoding="utf-8") as f:
        return json.load(f)