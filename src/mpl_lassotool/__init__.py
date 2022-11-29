"Lasso selection tool for matplotlib."

from .lassotool import LassoTool
from .eventhandler import EventHandler, XYEventHandler

__all__ = ["LassoTool", "EventHandler", "XYEventHandler"]


def test():
    import numpy as np
    import matplotlib.pyplot as plt
    from logging.config import dictConfig

    dictConfig({
        "version": 1,
        "formatters": {
            "standard": {
                "format": '[%(asctime)s] %(name)s [%(levelname)s] %(message)s'
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
                "level": "NOTSET",
            },
        },
        "loggers": {
            "mpl_lassotool": {
                "level": "INFO",
                "handlers": ["console"]
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    })

    data = np.random.normal(size=(2, 10000))

    fig, ax = plt.subplots()
    ax.scatter(*data)
    _ = LassoTool(fig, EventHandler())
    plt.show()


if __name__ == "__main__":
    test()
