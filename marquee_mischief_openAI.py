# This code is for v1 of the openai package: pypi.org/project/openai
import requests
import openai
import os
import time
from marquee_helper import validate_messages, message_to_letters, letter_use

client = openai.OpenAI()

def message_to_messages(message, use_proxy = False):
 
    letters = message_to_letters(message)
    count = min(4,int((len(letters)/6)))
    proxy = "proxy.server:3128"

    if(use_proxy):
        session = requests.Session()
        session.proxies = {'http': proxy, 'https': proxy}
        #openai.api_base = 'https://api.openai.com/v1'
        openai.session = session

    #client = openai.OpenAI()

    str_letters = ', '.join(letters)
    #prompt = f"Create 15 complete coherant sentences that are ironic, funny, witty, creative, silly, or snarky using only the letters in the provided multiset. "
    prompt = f"Create 15 complete sentences that a 10 year old would find funny using only the letters in the provided multiset. "
    #prompt = prompt + "Use potty humor words if possible. "
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
    
    return validated

def message_to_messages_using_agent(message, use_proxy = False):
    letters = message_to_letters(message)

    proxy = "proxy.server:3128"
    if(use_proxy):
        session = requests.Session()
        session.proxies = {'http': proxy, 'https': proxy}
        #openai.api_base = 'https://api.openai.com/v1'
        openai.session = session

    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=', '.join(letters) 
    )
    
    run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id="asst_GbXvW8WFa9wIEQ52GWCAYoUB",
    )

    run = wait_on_run(run, thread)

    response = client.beta.threads.messages.list(thread_id=thread.id)

    messages = response.data[0].content[0].text.value.split('\n')

    validated = validate_messages(messages, letters)
    
    return validated

def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

#print(message_to_messages("PLEASE WAIT TO BE SEATED", False))
#print(message_to_messages_using_agent("PLEASE WAIT TO BE SEATED", False))
