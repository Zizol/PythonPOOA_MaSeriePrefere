from flask import Flask, render_template, url_for, request

app = Flask(__name__)

# Config options - Make sure you created a 'config.py' file.
app.config.from_object('config')
# To get one variable, tape app.config['MY_VARIABLE']

@app.route('/')
@app.route('/index/')
def index():
    return render_template('index.html')

@app.route('/result/')
def result():
    user_name = request.args.get("user_name")
    return render_template('result.html',
                           user_name=user_name,
                           description="Bonjou c'est moi dingue non ?",
                           blur=True)

@app.route('/contents/<content_id>/')
def content(content_id):
    return '%s' % content_id

if __name__ == "__main__":
    app.run()
