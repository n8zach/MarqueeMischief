from flask import Flask,render_template,request
from marquee_mischief_bing import message_to_messages

app = Flask(__name__, template_folder='templates')

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
    messages = message_to_messages(message)
    data = {}
    data["OriginalMessage"] = form_data.getlist('OriginalMessage')[0]
    data["NewMessages"] = messages.replace('\n','<br>')
    return render_template('data.html', form_data = data)


app.debug = True 
app.run(host='localhost', port=5000)