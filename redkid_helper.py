import textwrap

def message_to_image_url(message):

    line1 = line2 = line3 = line4 = ""
    lines = textwrap.wrap(message, 25)

    if (len(lines) == 1):
        line2 = lines[0].replace(' ', "+")
    elif (len(lines) == 2):
        line2 = lines[0].replace(' ', "+")
        line3 = lines[1].replace(' ', "+")
    elif (len(lines) == 3):
        line1 = lines[0].replace(' ', "+")
        line2 = lines[1].replace(' ', "+")
        line3 = lines[2].replace(' ', "+")
    else:
        line1 = lines[0].replace(' ', "+")
        line2 = lines[1].replace(' ', "+")
        line3 = lines[2].replace(' ', "+")
        line4 = lines[4].replace(' ', "+")

    url = f"https://process.filestackapi.com/AhTgLagciQByzXpFGRI0Az/crop=d:%5B85,155,475,138%5D/http:/www.redkid.net/generator/roosevelt/newsign.php?line1={line1}&line2={line2}&line3={line3}&line4={line4}&Go+Bulldogs%21=Go+Bulldogs%21"
    return url