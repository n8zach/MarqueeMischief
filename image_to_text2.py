import requests
import base64

def image_to_text(filepath):
    url = "https://ocr-100-image-text-extractor.p.rapidapi.com/ocr"

    with open(filepath, "rb") as image_file:
        data = "data:image/jpeg;base64," + str(base64.b64encode(image_file.read()).decode('ascii'))

    payload = {
        "data": data,
        "lang": "eng"
    }
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "X-RapidAPI-Key": "678d81279emsh53c4aa5a6ed048ep10a184jsn83b7fe729eaa",
        "X-RapidAPI-Host": "ocr-100-image-text-extractor.p.rapidapi.com"
    }

    response = requests.post(url, data=payload, headers=headers)
    return(response.content.decode('ascii')).replace('\n', ' ').replace('\\', '')