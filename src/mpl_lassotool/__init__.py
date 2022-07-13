import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from logging import getLogger
from shapely.geometry import Polygon, MultiPoint
from typing import Callable, Iterable


class LassoTool:
    "Lasso selection tool for matplotlib."

    NAME = "mpl_lassotool"

    def __init__(
        self,
        fig: Figure,
        on_open: Callable[["LassoTool"], None] = None,
        on_close: Callable[["LassoTool"], None] = None
    ) -> None:
        self._fig = fig
        self._ax = None
        self._line = None  # Lasso line.
        self._ends_to_cursor = None  # Closing lines.
        self._points = []
        self._ls = ":"
        self._c = "k"
        self._lw = 1
        # Connect event handlers.
        self._fig.canvas.mpl_connect("button_press_event", self._on_press)
        self._fig.canvas.mpl_connect("motion_notify_event", self._on_move)
        self._fig.canvas.mpl_connect("button_release_event", self._on_release)
        self._on_open = on_open
        self._on_close = on_close

    @property
    def ax(self):
        return self._ax

    @property
    def x(self):
        "X coordinates of the lasso polygon."
        return np.array([e.xdata for e in self._points])

    @property
    def y(self):
        "Y coordinates of the lasso polygon."
        return np.array([e.ydata for e in self._points])

    @property
    def polygon(self):
        "The lasso polygon."
        return Polygon(zip(self.x, self.y))

    def on_open(self):
        "Fired when the lasso polygon is opened."
        if self._on_open is not None:
            self._on_open(self)
        else:
            getLogger(self.NAME).debug("Lasso tool started.")

    def on_close(self):
        "Fired when lasso polygon is closed."
        if self._on_close is not None:
            self._on_close(self)
        else:
            getLogger(self.NAME).debug(f"{self.polygon}")

    def contains(self, x: np.ndarray, y: np.ndarray) -> Iterable[bool]:
        """Return boolean array that indicates if points (x, y) are contained
            in the lasso polygon.

        Args:
            x, y: Data points to be judged.

        Returns:
            A boolean array.
            `True` indicate that the point (x, y) is within the lasso polygon.
        """
        polygon = self.polygon
        points = MultiPoint(list(zip(x, y)))
        return np.array([polygon.contains(p) for p in points.geoms])

    def update(self):
        self._fig.canvas.draw()

    @property
    def _is_opened(self):
        "Indicate if the lasso polygon is opened."
        return self._ends_to_cursor is not None

    def _on_press(self, event):
        "Mouse button press event."
        if event.button == 1:  # Left click, start the lasso.
            # Start the new lasso.
            if self._line is not None:
                self._ax.lines.remove(self._line)
            self._ax = event.inaxes
            self._points.clear()
            self._points.append(event)
            self.on_open()
            # New lasso started.
            self._line, = self._ax.plot(
                event.xdata, event.ydata,
                c=self._c, ls=self._ls, lw=self._lw)
            line0, line1 = self._get_ends_to_cursor(event)
            self._ends_to_cursor = (
                self._ax.plot(
                    *line0, c=self._c, ls=self._ls, lw=self._lw)[0],
                self._ax.plot(
                    *line1, c=self._c, ls=self._ls, lw=self._lw)[0],
            )

    def _on_move(self, event):
        "Mouse button motion event."
        if event.inaxes == self._ax and self._is_opened:
            self._points.append(event)
            self._line.set_data(self.x, self.y)
            line0, line1 = self._get_ends_to_cursor(event)
            self._ends_to_cursor[0].set_data(*line0)
            self._ends_to_cursor[1].set_data(*line1)
            self.update()

    def _on_release(self, event):
        "Mouse button release event."
        getLogger(self.NAME).debug(event)
        if event.button == 1:
            if self._is_opened:
                self._ax.lines.remove(self._ends_to_cursor[0])
                self._ax.lines.remove(self._ends_to_cursor[1])
                self._ends_to_cursor = None
                self._line.set_data(
                    np.r_[self.x, self.x[0]],
                    np.r_[self.y, self.y[0]])
                if len(self._points) > 3:
                    self.on_close()

    def _get_ends_to_cursor(self, event):
        return (
            ([self.x[0], event.xdata], [self.y[0], event.ydata]),
            ([self.x[-1], event.xdata], [self.y[-1], event.ydata])
        )


class ExampleEventHandler:
    "An example implementation for event handler."

    def __init__(self, x, y):
        self._x = x
        self._y = y
        self._markers = None

    def on_open(self, lt: LassoTool):
        if self._markers is None:
            self._markers = lt._ax.scatter([], [], marker="x", color="r")
        else:
            self._markers.set_visible(False)

    def on_close(self, lt: LassoTool):
        idx = lt.contains(self._x, self._y)
        self._markers.set_offsets(np.c_[self._x[idx], self._y[idx]])
        self._markers.set_visible(True)
        lt.update()
        getLogger(lt.NAME).debug(f"{np.nonzero(idx)}")


def test():
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
                "level": "DEBUG",
                "handlers": ["console"]
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    })

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # Some data.
    data = np.random.normal(size=(2, 100))
    ax.scatter(*data)
    eh = ExampleEventHandler(*data)
    _ = LassoTool(fig, on_open=eh.on_open, on_close=eh.on_close)
    plt.show()


if __name__ == "__main__":
    test()
