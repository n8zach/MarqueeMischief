from random import shuffle, choice

def message_to_letters(message):
    letters = list(message.strip().replace(' ','').lower())
    shuffle(letters)
    return ', '.join(sorted(letters))

def remove_punctuation(input):
    punc = '''!1234567890()-[]{};:'"\,<>./?@#$%^&*_~'''
    for letter in input:
        if letter in punc:
            input = input.replace(letter, "")
    return input.replace('\\\"','\"')

def extra_letters(a, b):
    la = list(a.lower())
    lb = list(b)
    extra = []  
    for letter in la:
        if letter in lb:
            lb.remove(letter)
        else:
            extra.append(letter)
    return extra

def parse_return(data):
    split = data.split("\n")
    messages = []
    for message in split:
        messages.append(message)
    return messages

def validate_messages(messages, letters):
    validated = []
    bad = []
    for message in messages:
        m = remove_punctuation(message).replace(' ','')
        extra = extra_letters(m, letters)
        if(len(extra) > 0):
            bad.append("[fail: " + message.replace('\\', '') + " " + ','.join(extra) + "]")
            continue
        #print(remove_punctuation(message).strip())
        validated.append(remove_punctuation(message).strip())
    return bad, validated

#validate_messages(["A fat lady farted very loud"], 'feed your faith and your fears will starve to death')