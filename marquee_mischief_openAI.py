# This code is for v1 of the openai package: pypi.org/project/openai
import requests
import openai
import os
from marquee_helper import validate_messages, message_to_letters, letter_use

def message_to_messages(message, use_proxy = False):

    letters = message_to_letters(message)
    count = min(4,int((len(letters)/6)))
    proxy = "proxy.server:3128"

    if(use_proxy):
        session = requests.Session()
        session.proxies = {'http': proxy, 'https': proxy}
        #openai.api_base = 'https://api.openai.com/v1'
        openai.session = session

    client = openai.OpenAI()

    str_letters = ', '.join(letters)
    prompt = f"Create 15 complete sentences that a 10 year old would find funny using only the letters in the provided multiset. "
    prompt = prompt + "Use potty humor words if possible. "
    #prompt = prompt + "Use potty humor words if possible like fart, daiper, gross, toilet, boogers, stupid, dumb, poopy, smelly, pee, poop, etc.  "
    #prompt = prompt + f"Keep each sentence to {count} words or less. "
    #prompt = prompt + "Like in Scrabble, you can only use each letter from the multiset once. "
    prompt = prompt + "Keep each sentence length to 4 or 5 words. "
    #prompt = prompt + "Make three sentences with 3 words three with 4 words and three with 5 words. "
    
    prompt = prompt + f"the multiset to use is: {str_letters}"

    #print(prompt)
    response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
        "role": "user",
        "content": prompt
        },
    ],
    temperature=1, #0.01,
    max_tokens=256,
    top_p=1,
    frequency_penalty=.5,
    presence_penalty=.5
    )

    messages = response.choices[0].message.content.split('\n')

    validated = validate_messages(messages, letters)
    out = []
    out.append("\nGood Messages:")
    for g in validated["good"]:
        out.append(f"{g['text']} ({g['unused']})")
    out.append("\nClose Messages:")
    for b in validated["bad"]:
        if len(b["extra"]) == 1:
            out.append(f"{b['text']} [{b['extra']}] ({b['unused']})")

    out.append("\n\nUsing OpenAI")
    out.append("\nPrompt:")               
    out.append(prompt)
    return '\n'.join(out)
