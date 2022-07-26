from collections import namedtuple
from matplotlib.axes import Axes
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from logging import getLogger
from shapely.geometry import Polygon, MultiPoint
from typing import Callable, Dict, Iterable, Tuple


class LassoTool:
    "Lasso selection tool for matplotlib."

    NAME = "mpl_lassotool"

    def __init__(
        self,
        fig: Figure,
        eventhandler: 'EventHandler' = None,
        on_open: Callable[["LassoTool"], None] = None,
        on_close: Callable[["LassoTool"], None] = None,
        modifiers=("control",),
    ) -> None:
        self._fig = fig
        self._ax = None
        self._line = None  # Lasso line.
        self._ends_to_cursor = None  # Closing lines.
        self._is_opened = False
        self._background = None
        self._points = []
        self._ls = ":"
        self._c = "k"
        self._lw = 1
        # Connect event handlers.
        self._fig.canvas.mpl_connect("key_press_event", self._on_key_press)
        self._fig.canvas.mpl_connect("key_release_event", self._on_key_release)
        self._fig.canvas.mpl_connect("button_press_event", self._on_press)
        self._fig.canvas.mpl_connect("motion_notify_event", self._on_move)
        self._fig.canvas.mpl_connect("button_release_event", self._on_release)
        if eventhandler is not None:
            self._eventhandler = eventhandler
        else:
            self._eventhandler = namedtuple(
                "EventHandler",
                "on_open, on_close"
            )(
                on_open if on_open is not None else lambda x: None,
                on_close if on_close is not None else lambda x: None)
        self._modifiers = {key: False for key in modifiers}

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

    def contains(self, x: Iterable, y: Iterable) -> Iterable[bool]:
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
    def _is_modifiers_pressed(self):
        return all(self._modifiers.values())

    def _on_key_press(self, event):
        getLogger(self.NAME).debug(event.key)

        for key in event.key.split("+"):
            if key in self._modifiers:
                self._modifiers[key] = True

    def _on_key_release(self, event):
        getLogger(self.NAME).debug(event)

        for key in event.key.split("+"):
            if key in self._modifiers:
                self._modifiers[key] = False

    def _on_press(self, event):
        "Mouse button press event."
        if (
            event.inaxes is not None and
            event.button == 1 and
            self._is_modifiers_pressed
        ):
            # Start the new lasso.
            if self._line is not None:
                self._ax.lines.remove(self._line)
            self._ax = event.inaxes
            self._background = self._fig.canvas.copy_from_bbox(self._ax.bbox)
            self._points.clear()
            self._points.append(event)
            self._eventhandler.on_open(self)
            # New lasso started.
            self._line, = self._ax.plot(
                event.xdata, event.ydata,
                c=self._c, ls=self._ls, lw=self._lw, animated=True)
            line0, line1 = self._get_ends_to_cursor(event)
            self._ends_to_cursor = (
                self._ax.plot(
                    *line0,
                    c=self._c, ls=self._ls, lw=self._lw, animated=True)[0],
                self._ax.plot(
                    *line1,
                    c=self._c, ls=self._ls, lw=self._lw, animated=True)[0],
            )
            self._ax.draw_artist(self._line)
            self._ax.draw_artist(self._ends_to_cursor[0])
            self._ax.draw_artist(self._ends_to_cursor[1])
            self._fig.canvas.blit(self._ax.bbox)
            self._is_opened = True

    def _on_move(self, event):
        "Mouse button motion event."
        if event.inaxes == self._ax and self._is_opened:
            self._points.append(event)
            self._line.set_data(self.x, self.y)
            line0, line1 = self._get_ends_to_cursor(event)
            self._ends_to_cursor[0].set_data(*line0)
            self._ends_to_cursor[1].set_data(*line1)
            # Redraw
            self._fig.canvas.restore_region(self._background)
            self._ax.draw_artist(self._line)
            self._ax.draw_artist(self._ends_to_cursor[0])
            self._ax.draw_artist(self._ends_to_cursor[1])
            self._fig.canvas.blit(self._ax.bbox)

    def _on_release(self, event):
        "Mouse button release event."
        getLogger(self.NAME).debug(event)
        if event.button == 1 and self._is_opened:
            self._ax.lines.remove(self._ends_to_cursor[0])
            self._ax.lines.remove(self._ends_to_cursor[1])
            self._ends_to_cursor = None
            self._is_opened = False
            self._line.set_data(
                np.r_[self.x, self.x[0]],
                np.r_[self.y, self.y[0]])
            if len(self._points) > 3:
                self._eventhandler.on_close(self)
            self._fig.canvas.draw()

    def _get_ends_to_cursor(self, event):
        return (
            ([self.x[0], event.xdata], [self.y[0], event.ydata]),
            ([self.x[-1], event.xdata], [self.y[-1], event.ydata])
        )


class EventHandler:
    "Basic event handler for figures with multiple axes."

    def __init__(self, xy: Dict[Axes, Tuple[Iterable, Iterable]]) -> None:
        self._xy = xy
        self._markers = {ax: None for ax in self._xy}

    def on_open(self, lt: LassoTool):
        if self._markers[lt.ax] is None:
            self._markers[lt.ax] = lt._ax.scatter([], [], marker="x", color="r")
        else:
            self._markers[lt.ax].set_visible(False)

    def on_close(self, lt: LassoTool):
        idx = lt.contains(*self._xy[lt.ax])
        for ax in self._markers:
            x, y = self._xy[ax]
            self._markers[ax].set_offsets(np.c_[x[idx], y[idx]])
            self._markers[ax].set_visible(True)
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
    _ = LassoTool(fig, EventHandler({ax: data}))
    plt.show()


if __name__ == "__main__":
    test()
