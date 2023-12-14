from random import shuffle, choice

def message_to_letters(message):
    letters = list(message.strip().replace(' ','').lower())
    shuffle(letters)
    return sorted(letters)

def remove_punctuation(input):
    punc = '''!1234567890()-[]{};’:'"\,<>./?@#$%^&*_~'''
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
#bad, good = validate_messages(["Farts smell bad.","Toilet paper is gross.","Boogers are gross.","Stupid people are dumb.","Poopy pants are smelly.","Pee is gross.","Poop is gross.","Farting is gross.","Farts are gross.","Toilet paper is smelly.","Boogers are smelly.","Stupid people are poopy.","Dumb people are poopy.","Farting is poopy.","Farts are poopy.","Toilet paper is poopy.","Boogers are poopy.","Stupid people are gross.","Dumb people are gross.","Farting is gross."], "a, a, a, a, a, d, d, d, e, e, e, e, e, f, f, f, h, h, i, i, l, l, n, o, o, o, r, r, r, r, s, s, t, t, t, t, u, u, v, w, y, y")
#print(bad)
#print(good)