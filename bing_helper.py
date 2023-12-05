import json
import http.client
from marquee_helper import message_to_letters, validate_messages    

def ask_bing(payload, use_proxy=False):
    if use_proxy:
        conn = http.client.HTTPSConnection("proxy.server", 3128)
        conn.set_tunnel("bingchat-chatgpt-4-api.p.rapidapi.com")
    else:
        conn = http.client.HTTPSConnection("bingchat-chatgpt-4-api.p.rapidapi.com")
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

    letters = message_to_letters(message)

    payload = "{\r\n \"question\": \"Create 10 funny, witty, ironic, complete sentences using only the letters in this multiset: " + letters + ". "
    payload = payload + "Try to use words that a 10 year old would find funny like fart, farts, toilet, doo doo, boogers, stupid, dumb, poopy, and poop. "
    # payload = payload + "For example ""Thats a loud fart"" and ""He made a poop sandwich. "
    payload = payload + "Do this in the style of Dav Pilkey. "
    # payload = payload + "Do not use a letter more times than it appears in the multiset. "
    # payload = payload + "You do not need to use all the letters.\n"
    count = int(len(message.replace(' ',''))/8)
    payload = payload + f" Keep each sentence to {count} words or less. "
    #payload = payload + "For example: from this multiset *f,e,e,d,y,o,u,r,f,a,i,t,h,a,n,d,y,o,u,r,f,e,a,r,s,w,i,l,l,s,t,a,r,v,e,t,o,d,e,a,t,h* you can create *A fat lady farted very loud*"
    payload = payload + "\",\r\n    \"bing_u_cookie\": \"1LiFx8h_xlL8RNv4Q9Qs68aAKjF_NTMz91VU5pXuUcQxRrmvrLgrQ4pW1oGXLSjkkABZDdSMKSuOPtRqNPLSQdQP_m7k4RyWJGWHPaNh4HNGX-KkYsJc5qL91_nSYxftcbQW3u58lVc53PRZqD9zIJEvRuuP_yWh2DrQeiRhY5MwbHbUF2JuQyXNiBjjTYsN29NcyPa9lZuDP46A3u3afRD\",\r\n    "
    payload = payload + "\"conversation_style\": \"precise\"\r\n}"

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
    pick_funniest(good, use_proxy)

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

