import chardet

def get_text_encoding(path:str):
    with open(path, 'rb') as f:
        text = f.read()
        resp = chardet.detect(text)
    return resp['encoding']