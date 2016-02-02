from . import main


@main.app_errorhandler(404)
def page_not_found(e):
    return "Page you are looking for was not found."


@main.app_errorhandler(500)
def internal_server_error(e):
    return "Oops! This one's our fault."
