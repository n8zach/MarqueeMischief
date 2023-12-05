from marquee_helper import message_to_letters, remove_punctuation, extra_letters, parse_return
import bing_helper
from image_to_text2 import image_to_text

def message_to_messages(message, use_proxy=False):
    print("[" + message + "]")
    print("Getting new messages...")
    bad, good = bing_helper.message_to_messages(message, use_proxy)
    print(bad)
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