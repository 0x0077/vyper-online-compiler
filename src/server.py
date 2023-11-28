from sanic import Sanic
from sanic_cors import CORS
from sanic.response import text, html
from views.implemention import imp
from views.test import ts


app = Sanic(__name__)
app.static('/statics', './statics')

app.config['CORS_AUTOMATIC_OPTIONS'] = True

CORS(app)

app.blueprint(imp)
app.blueprint(ts)


@app.route("/")
async def index(request):
    with open("templates/index.html", "r") as f:
        html_content = f.read()
    return html(html_content)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, fast=True, debug=True, access_log=False)

