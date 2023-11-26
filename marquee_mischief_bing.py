from marquee_helper import message_to_letters, remove_punctuation, extra_letters, parse_return
import bing_helper
from image_to_text2 import image_to_text

def message_to_messages(message):
    # message = 'Do unto others as you would have them do unto you'
    # message = 'feed your faith and your fears will starve to death'
    # message = 'If you are in deep water turn to the one who walked on it'
    # message = "Have a great summer School starts September 5th"
    # message = "Faith is an investment that never looses interest"
    # message = "God made you on purpose for a purpose"
    # message = "Come in and see our pretty armchairs"
    # message = "Please wear your socks on the gym floor"
    # message = "See our big football game today"
    # message = "new tasty cheese and lentil pot pies"

    print("[" + message + "]")
    print("Getting new messages...")
    bad, good = bing_helper.message_to_messages(message)

    if len(good) == 0:
        print("no valid messages found. Here is what we got...")
        print(bad)
    else:
        return('\n'.join(good))


def image_to_messages(filepath):
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\GiantPlantSale.jpg")
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\message.jpg")
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\salon.jpg")
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\starve.jpg")
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\Contrary.jpg")

    original_message = image_to_text(filepath)

    print("[" + original_message + "]")
    print("Getting New Messages...")
    bad, good = bing_helper.message_to_messages(original_message)

    if len(good) == 0:
        print("no valid messages found. Here is what we got...")
        print(bad)
    else:
        return('\n'.join(good))