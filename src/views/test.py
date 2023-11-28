from sanic.response import json
from sanic import Blueprint


ts = Blueprint("test", url_prefix="test")


@ts.route("/get", methods=["GET"])
async def test_get(request):
    return json({"code": 200})