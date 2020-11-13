from flask import Flask 

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST', 'PUT'])
def home():
    return "<html>\
                <body>\
                    <h1> Hi there, Fellas! </h1>\
                </body>\
            </html>"

app.run(debug = True)