import logging
import sys


def setup_logging(config):
    
    level = logging.DEBUG if getattr(config, "DEBUG", False) else logging.INFO
    filename = getattr(config, "LOG_FILENAME", "employee_app_logs.log")

    logging.basicConfig(
        filename=filename,
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if getattr(config, "DEBUG", False):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logging.getLogger().addHandler(console_handler)
