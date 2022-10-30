from utils.variables import Constants

class ErrorMessages:
    GENERIC = "An exception happened."
    NO_URL = "Please add an URL to your request. Refeer to <a href=\"/documentation\">this page</a> for more info about the endpoints."
    INVALID_URL = "Invalid URL. Refeer to <a href=\"/supported\">this page</a> for a list of supported websites."
    INVALID_API_PATH = f"Invalid API path. Please make sure your API version is set correctly ({Constants.CAV}). Refeer to <a href=\"/documentation\">this page</a> for more info about the endpoints."
