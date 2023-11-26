import json
import http.client
from marquee_helper import message_to_letters, validate_messages


def message_to_messages(message, use_proxy=False):

    letters = message_to_letters(message)

    if use_proxy:
        conn = http.client.HTTPSConnection("proxy.server", 3128)
        conn.set_tunnel("bingchat-chatgpt-4-api.p.rapidapi.com")
    else:
        conn = http.client.HTTPSConnection("bingchat-chatgpt-4-api.p.rapidapi.com")
        
    payload = "{\r\n \"question\": \"Create 10 funny complete sentences using only the letters in this multiset: "
    payload = payload + letters + ". "
    payload = payload + "Do not use a letter more times than it appears in the multiset. "
    payload = payload + "You do not need to use all the letters. "
    payload = payload + "Keep sentences to 6 words or less."
    payload = payload + "\",\r\n    \"bing_u_cookie\": \"1LiFx8h_xlL8RNv4Q9Qs68aAKjF_NTMz91VU5pXuUcQxRrmvrLgrQ4pW1oGXLSjkkABZDdSMKSuOPtRqNPLSQdQP_m7k4RyWJGWHPaNh4HNGX-KkYsJc5qL91_nSYxftcbQW3u58lVc53PRZqD9zIJEvRuuP_yWh2DrQeiRhY5MwbHbUF2JuQyXNiBjjTYsN29NcyPa9lZuDP46A3u3afRA\",\r\n    "
    payload = payload + "\"conversation_style\": \"precise\"\r\n}"

    #print(payload)

    headers = {
    'content-type': "application/json",
    'X-RapidAPI-Key': "678d81279emsh53c4aa5a6ed048ep10a184jsn83b7fe729eaa",
    'X-RapidAPI-Host': "bingchat-chatgpt-4-api.p.rapidapi.com"
    }

    conn.request("POST", "/bingchat", payload, headers)

    res = conn.getresponse()
    data = res.read()

    #print(data.decode("utf-8"))
    response = json.loads(data)["response"]["text"]
    messages = parse_return(response)
    return validate_messages(messages, letters)

def parse_return(data):
    split = data.split("\n")
    messages = []
    for message in split:
        if message != '' and not "Sure, here are" in message and not "I hope you" in message:
            messages.append(message)
    return messages