import requests

def image_to_text(filepath):
    url = "https://ocr43.p.rapidapi.com/v1/results"

    files = { "image": open(filepath, 'rb') }
    headers = {
        "X-RapidAPI-Key": "678d81279emsh53c4aa5a6ed048ep10a184jsn83b7fe729eaa",
        "X-RapidAPI-Host": "ocr43.p.rapidapi.com"
    }
    response = requests.post(url, files=files, headers=headers)
    text = response.json()["results"][0]["entities"][0]["objects"][0]["entities"][0]["text"]
    return (text.replace('\n', ' '))
