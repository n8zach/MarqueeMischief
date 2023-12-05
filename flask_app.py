from flask import Flask,render_template,request
from marquee_mischief_bing import message_to_messages
from bing_helper import pick_funniest
from marquee_helper import remove_punctuation

USE_PROXY = False

app = Flask(__name__, template_folder='templates', static_url_path='/static')

@app.route('/data/', methods = ['POST', 'GET'])
def data():
    if request.method == 'GET':
        form_data = {}
        return render_template('data.html', form_data = form_data) 
    if request.method == 'POST':
        form_data = request.form
        return render_template('thinking.html', form_data = form_data)

@app.route('/thinking/', methods = ['POST', 'GET']) 
def thinking(): 
    form_data = request.form
    message = form_data.getlist('OriginalMessage')[0]
    messages = message_to_messages(remove_punctuation(message), USE_PROXY)
    data = {}
    data["OriginalMessage"] = form_data.getlist('OriginalMessage')[0]
    data["NewMessages"] = messages.replace('\n','<br>')
    #print(pick_funniest(messages)) 
    return render_template('data.html', form_data = data)


if __name__ == '__main__':
    app.run()