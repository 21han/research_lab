"""
Error handers
"""
import logging

from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def error_404(error):
    """
    render error page 404
    :param error:
    :return:
    """
    logging.error("Error: %s", error)
    return render_template('errors/404.html'), 404


@errors.app_errorhandler(403)
def error_403(error):
    """
    render error page 403
    :param error:
    :return:
    """
    logging.error("Error: %s", error)
    return render_template('errors/403.html'), 403


@errors.app_errorhandler(500)
def error_500(error):
    """
    render error page 500
    :param error:
    :return:
    """
    logging.error("Error: %s", error)
    return render_template('errors/500.html'), 500
