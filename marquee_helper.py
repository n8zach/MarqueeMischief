from random import shuffle, choice

def message_to_letters(message):
    letters = list(message.strip().replace(' ','').lower())
    shuffle(letters)
    return sorted(letters)

def remove_punctuation(input):
    punc = '''!1234567890()-[]{};’:'"\,<>./?@#$%^&*_~''' + '\n' + '\r'
    for letter in input:
        if letter in punc:
            input = input.replace(letter, "")
    return input.replace('\\\"','\"')


def letter_use(message, letters):
    la = list(message.lower())
    lb = list(letters)
    extra = []
    for letter in la:
        if letter in lb:
            lb.remove(letter)
        else:
            extra.append(letter)
    return lb, extra

def parse_return(data):
    split = data.split("\n")
    messages = []
    for message in split:
        messages.append(message)
    return messages

def validate_messages(messages, letters):
    validated = {}
    validated["good"] = []
    validated["bad"] = []

    for message in messages:
        m = remove_punctuation(message).replace(' ','')
        unused, extra  = letter_use(m, letters)
        if message == "":
            continue
        if(len(extra) > 0):
            validated["bad"].append(
                {"text":remove_punctuation(message).strip().upper(),
                 "extra":','.join(extra),
                 "unused":','.join(unused)})
            continue
        validated["good"].append(
            {"text":remove_punctuation(message).strip().upper(),
             "unused":','.join(unused)})
    return validated

def format_extra_letters(message, letters):
    m = message.upper()
    l = letters.upper()

    out = ""
    for l in message:
        if letters.count(l) != 0:
            out = out + l
            letters = letters.replace(l, '', 1)
        else:
            out = out + "<b>" + l.lower() + "</b>"

    return out
#validate_messages(["A fat lady farted very loud"], 'feed your faith and your fears will starve to death')
#bad, good = validate_messages(["Farts smell bad.","Toilet paper is gross.","Boogers are gross.","Stupid people are dumb.","Poopy pants are smelly.","Pee is gross.","Poop is gross.","Farting is gross.","Farts are gross.","Toilet paper is smelly.","Boogers are smelly.","Stupid people are poopy.","Dumb people are poopy.","Farting is poopy.","Farts are poopy.","Toilet paper is poopy.","Boogers are poopy.","Stupid people are gross.","Dumb people are gross.","Farting is gross."], "a, a, a, a, a, d, d, d, e, e, e, e, e, f, f, f, h, h, i, i, l, l, n, o, o, o, r, r, r, r, s, s, t, t, t, t, u, u, v, w, y, y")
#print(bad)
#print(good)