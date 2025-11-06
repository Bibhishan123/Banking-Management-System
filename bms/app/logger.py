import logging
import sys


def setup_logging(config):
    """
    Simple logging setup: write to a file by default with a straightforward format.
    If DEBUG is enabled, also log to stdout.
    Uses Config.LOG_FILENAME if present, otherwise defaults to 'employee_app_logs.log'.
    """
    level = logging.DEBUG if getattr(config, "DEBUG", False) else logging.INFO
    filename = getattr(config, "LOG_FILENAME", "employee_app_logs.log")

    logging.basicConfig(
        filename=filename,
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # In debug mode, also mirror logs to stdout for convenience
    if getattr(config, "DEBUG", False):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logging.getLogger().addHandler(console_handler)
