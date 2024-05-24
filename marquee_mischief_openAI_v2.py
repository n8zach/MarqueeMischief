import openai
from marquee_helper import validate_messages, message_to_letters, letter_use
import time
import requests

def message_to_messages_using_assistant(message, use_proxy = False):
    letters = message_to_letters(message)

    proxy = "proxy.server:3128"
    if(use_proxy):
        session = requests.Session()
        session.proxies = {'http': proxy, 'https': proxy}
        #openai.api_base = 'https://api.openai.com/v1'
        openai.OpenAI.session = session

    client = openai.OpenAI()

    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=message,
    )

    run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id="asst_Tbi4s9QV2Nk8vXwudouT0eVP",
    )

    allowed_time_sec = 20
    start = time.time()
    validated = {}
    while run.status != 'completed':
        time.sleep(.5)
        if time.time() - start > allowed_time_sec:
            break

    if run.status == 'completed':
        response = client.beta.threads.messages.list(thread_id=thread.id)
        messages = response.data[0].content[0].text.value.split('\n')
        validated = validate_messages(messages, letters)

    else:
        validated["good"] = "ran out of time"


    validated["assistant"] = run.assistant_id
    print(validated)

    return validated


#print(message_to_messages_using_assistant_v1("O, D, H, A, A, D, G, H, E, L, S, S, T, T, W, O, R"))
