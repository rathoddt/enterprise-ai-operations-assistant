# ----------------- v0 -----------------
import logging
import sys
from app.core.config import settings


def setup_logging():

    logging.basicConfig(
        level=settings.log_level.upper(),
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    # Suppress verbose SDK and HTTP logs.
    noisy_loggers = [
        "openai",
        "anthropic",
        "httpx",
        "httpx2",
        "httpcore",
        "httpcore2",
        "urllib3",
    ]


    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

def get_logger(name: str):
    return logging.getLogger(name)

# import sys
# import logging
# from app.core.config import settings

# def configure_logging():
#     logging.basicConfig(
#         level=logging.INFO,
#         format=(
#             "%(asctime)s | %(levelname)s | "
#             "%(name)s | %(message)s"
#         ),
#         force=True,
#     )

#     # Suppress verbose SDK and HTTP logs.
#     noisy_loggers = [
#         "openai",
#         "anthropic",
#         "httpx",
#         "httpx2",
#         "httpcore",
#         "httpcore2",
#         "urllib3",
#     ]

#     for logger_name in noisy_loggers:
#         logging.getLogger(logger_name).setLevel(logging.WARNING)

