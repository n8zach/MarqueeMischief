import json
import http.client
from marquee_helper import message_to_letters, validate_messages, remove_punctuation    
import random
import string


def ask_bing(payload, use_proxy=False):

    # pre = "1LiFx8h"
    # change the cookie so each conversation is new (is this the best way?)
    #pre = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(7))
    #cookie = pre + "_xlL8RNv4Q9Qs68aAKjF_NTMz91VU5pXuUcQxRrmvrLgrQ4pW1oGXLSjkkABZDdSMKSuOPtRqNPLSQdQP_m7k4RyWJGWHPaNh4HNGX-KkYsJc5qL91_nSYxftcbQW3u58lVc53PRZqD9zIJEvRuuP_yWh2DrQeiRhY5MwbHbUF2JuQyXNiBjjTYsN29NcyPa9lZuDP46A3u3afRD"

    cookie = "1LiFx8h_xlL8RNv4Q9Qs68aAKjF_NTMz91VU5pXuUcQxRrmvrLgrQ4pW1oGXLSjkkABZDdSMKSuOPtRqNPLSQdQP_m7k4RyWJGWHPaNh4HNGX-KkYsJc5qL91_nSYxftcbQW3u58lVc53PRZqD9zIJEvRuuP_yWh2DrQeiRhY5MwbHbUF2JuQyXNiBjjTYsN29NcyPa9lZuDP46A3u3afRD"
    #cookie = "Please replace this string with a string representing your Bing _U cookie. You can obtain your _U cookie by accessing the Developer Console and searching for the _U cookie name. Please follow this link for guidance: https://i.ibb.co/94YWpQD/1676391128.png"
    
    if use_proxy:
        conn = http.client.HTTPSConnection("proxy.server", 3128)
        conn.set_tunnel("bingchat-chatgpt-4-api.p.rapidapi.com")
    else:
        conn = http.client.HTTPSConnection("bingchat-chatgpt-4-api.p.rapidapi.com")
    
    #payload = "{\r\n    \"question\": \"square root of 12"
    
    payload = payload + "\",\r\n    \"bing_u_cookie\": \"" + cookie + "\",\r\n    "
    payload = payload + "\"conversation_style\": \"precise\"\r\n}"

    

    print(payload)
    headers = {
    'content-type': "application/json",
    'X-RapidAPI-Key': "678d81279emsh53c4aa5a6ed048ep10a184jsn83b7fe729eaa",
    'X-RapidAPI-Host': "bingchat-chatgpt-4-api.p.rapidapi.com"
    }

    conn.request("POST", "/bingchat", payload, headers)

    res = conn.getresponse()
    data = res.read()

    #print(data.decode("utf-8"))
    return(json.loads(data)["response"]["text"])

def message_to_messages(message, use_proxy=False):

    fixed = remove_punctuation(message)
    letters = message_to_letters(fixed)

    payload = "{\r\n \"question\": \""

    payload = payload + "Create 15 funny, complete sentences using only the letters in this multiset: " + letters + ". "
    payload = payload + "If possible, use words that a 10 year old would find funny like fart, farts, gross, toilet, boogers, stupid, dumb, poopy, smelly, pee, poop, etc. "
    # payload = payload + "For example ""Thats a loud fart"" and ""He made a poop sandwich. "
    # payload = payload + "For example ""Thats a loud fart"" and ""He made a poop sandwich. "
    # payload = payload + "Do this in the style of Dav Pilkey. "
    # payload = payload + "Do not use a letter more times than it appears in the multiset. "
    # payload = payload + "You do not need to use all the letters.\n"
    count = max(4, min(7, int((len(letters)+2)/3/6)))
    payload = payload + f" Keep each sentence to {count} words or less. "
    #payload = payload + "For example: from this multiset *f,e,e,d,y,o,u,r,f,a,i,t,h,a,n,d,y,o,u,r,f,e,a,r,s,w,i,l,l,s,t,a,r,v,e,t,o,d,e,a,t,h* you can create *A fat lady farted very loud*"
    
    response = ask_bing(payload, use_proxy)
    messages = parse_return(response)
    bad, good = validate_messages(messages, letters)

    #now try to insert a funny adjective with the leftover letters
    # for message in good:    
    #     new_message = add_adjective(message, letters)
    #     bad2, good2 = validate_messages([new_message], letters)
    #     bad = bad + bad2
    #     if(good2 != []):
    #         good.remove(message)
    #         good.append(good2[0])
    
    # pick_funniest(good, use_proxy)
    good.append(payload)
    good = good + bad
    return bad, good

def add_adjective(message, letters, use_proxy=False):
    words = find_funny_adjective(message, letters)
    payload = "{\r\n \"question\": \"Insert this adjective *" + words + "* into this sentence *" + message + "* to make a new sentence. "
    payload = payload + "Do not add or remove any words from the original sentence. "
    payload = payload + "Put the new sentence on a new line with $ on each side so I can parse it easily."
    payload = payload + "\",\r\n    \"bing_u_cookie\": \"2LiFx8h_xlL8RNv4Q9Qs68aAKjF_NTMz91VU5pXuUcQxRrmvrLgrQ4pW1oGXLSjkkABZDdSMKSuOPtRqNPLSQdQP_m7k4RyWJGWHPaNh4HNGX-KkYsJc5qL91_nSYxftcbQW3u58lVc53PRZqD9zIJEvRuuP_yWh2DrQeiRhY5MwbHbUF2JuQyXNiBjjTYsN29NcyPa9lZuDP46A3u3afRD\",\r\n    "
    payload = payload + "\"conversation_style\": \"creative\"\r\n}"
    response = ask_bing(payload, use_proxy)
    print(f"{response}")
    return(response.replace('\n', '').split('$')[1:-1][0])

def find_funny_adjective(message, letters, use_proxy=False):
    message = message.lower()
    letters = letters.replace(', ', '')
    while(len(message) > 0):
        letters = letters.replace(message[0], '', 1)
        message = message.replace(message[0], '', 1)
    
    payload = "{\r\n \"question\": \"Unscramble these letters into one funny and common adjective that would be found in the dictionary:"
    payload = payload + letters + ". "
    payload = payload + "You do not need to use all the letters. "
    payload = payload + "Put the adjective on a new line with $ on each side so I can parse it easily. "
    payload = payload + "\",\r\n    \"bing_u_cookie\": \"3LiFx8h_xlL8RNv4Q9Qs68aAKjF_NTMz91VU5pXuUcQxRrmvrLgrQ4pW1oGXLSjkkABZDdSMKSuOPtRqNPLSQdQP_m7k4RyWJGWHPaNh4HNGX-KkYsJc5qL91_nSYxftcbQW3u58lVc53PRZqD9zIJEvRuuP_yWh2DrQeiRhY5MwbHbUF2JuQyXNiBjjTYsN29NcyPa9lZuDP46A3u3afRD\",\r\n    "
    payload = payload + "\"conversation_style\": \"creative\"\r\n}"

    response = ask_bing(payload, use_proxy)
    return(response.replace('\n', '').split('$')[1:-1][0])

def pick_funniest(messages, use_proxy=False):
    payload = "{\r\n \"question\": \"pick the funniest sentence from this list of sentences:"
    payload = payload + ', '.join(messages) 
    payload = payload + "\",\r\n    \"bing_u_cookie\": \"4LiFx8h_xlL8RNv4Q9Qs68aAKjF_NTMz91VU5pXuUcQxRrmvrLgrQ4pW1oGXLSjkkABZDdSMKSuOPtRqNPLSQdQP_m7k4RyWJGWHPaNh4HNGX-KkYsJc5qL91_nSYxftcbQW3u58lVc53PRZqD9zIJEvRuuP_yWh2DrQeiRhY5MwbHbUF2JuQyXNiBjjTYsN29NcyPa9lZuDP46A3u3afRD\",\r\n    "
    payload = payload + "\"conversation_style\": \"creative\"\r\n}"

    response = ask_bing(payload, use_proxy)
    print(response)

def parse_return(data):
    split = data.split("\n")
    messages = []
    for message in split:
        if message != '' and not "Sure, here are" in message and not "I hope you" in message:
            messages.append(message)
    return messages

