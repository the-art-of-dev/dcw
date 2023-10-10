# pylint: skip-file
import colorlog
import logging

colorlog_fmt = "{log_color}{levelname}: {message}"
colorlog.basicConfig(level=logging.DEBUG,
                     style="{", format=colorlog_fmt, stream=None)

logger = logging.getLogger()
