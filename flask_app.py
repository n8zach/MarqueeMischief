from flask import Flask,render_template,request
#from marquee_mischief_bing import message_to_messages
from marquee_mischief_openAI import message_to_messages
#from bing_helper import pick_funniest
from marquee_helper import remove_punctuation, format_extra_letters
from json import decoder

USE_PROXY = True

app = Flask(__name__, template_folder='templates', static_url_path='/static')

@app.route('/test/')
def test():
    return render_template('EnterMessage.html')

@app.route('/home/', methods = ['POST', 'GET'])
def home():
    if request.method == 'GET':
        form_data = {}
        form_data["OriginalMessage"] = "PLEASE WAIT\nTO BE\nSEATED"
        return render_template('home.html', form_data = form_data)
    if request.method == 'POST':
        form_data = request.form
        return render_template('thinking.html', form_data = form_data)

@app.route('/thinking/', methods = ['POST'])
def thinking():
    form_data = request.form
    message = form_data.getlist('OriginalMessage')[0]
    try:
        messages = message_to_messages(remove_punctuation(message), USE_PROXY)
    except decoder.JSONDecodeError as error:
        messages = error.doc
    except Exception as error:
        messages = f"An exception occurred: {error}"

    data = {}
    data["OriginalMessage"] = form_data.getlist('OriginalMessage')[0]
    
    out = []
    out.append("\nGood Messages:\n")
    for g in messages["good"]:
        out.append(f"{g['text']} ({g['unused']})")
    out.append("\nClose Messages:\n")
    for b in messages["bad"]:
        if len(b["extra"]) == 1:
            out.append(f"{format_extra_letters(b['text'], message.upper())} ({b['unused']})")

    data["NewMessages"] = '\n'.join(out).replace('\n','<br>')

    #print(pick_funniest(messages))

    return render_template('home.html', form_data = data)


if __name__ == '__main__':
    app.run()

# god's goodness is not determined by your circumstances
# Toms nose is a booger mine

