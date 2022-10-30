from utils.variables import Global, Constants
from utils.error_messages import ErrorMessages

app = Global.app


# /!\ Needs to be called before all of the other API endpoints
# so it only overrides the missing endpoints /!\
@app.route('/api/', defaults={'path': ''})
@app.route('/api/<path:path>')
def catch_all_api(path):
    return f"{ErrorMessages.INVALID_API_PATH} (URL requested: /api/{path})"


@app.route("/api/get_current_version")
@app.route("/api/get_api_version")
def get_current_version():
    return Constants.CAV
