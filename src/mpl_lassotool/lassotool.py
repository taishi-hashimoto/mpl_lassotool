"Lasso selection tool for matplotlib."
import numpy as np
from matplotlib.figure import Figure
from logging import getLogger
from shapely.geometry import Polygon, Point
from typing import Callable, Iterable
from collections import namedtuple
from matplotlib.axes import Axes
from .eventhandler import EventHandler


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
        """Prepare the lasso tool and connect the event handlers.
        
        Parameters
        ----------
        fig: `Figure`
            Target figure.
        eventhandler: `EventHandler` or its subclass
            Event handler to be called when lasso selection is started/stopped.
        on_open: `Callable`
            Used when `eventhandler` is `None`.
            Called when lasso selection is started.
        on_close: `Callable`
            Used when `eventhandler` is `None`.
            Called when lasso selection is finished.
        modifiers: `tuple` of `str`
            Modifier keys to be pressed to start lasso selection.
            Default is `('control',)`.
        """
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
                on_close if on_close is not None else lambda x: None
            )
        self._modifiers = {key: False for key in modifiers}

    @property
    def ax(self) -> Axes:
        "The target axes on which the lasso tool is used."
        return self._ax

    @property
    def x(self) -> np.ndarray:
        "X coordinates of the lasso polygon."
        return np.array([e.xdata for e in self._points])

    @property
    def y(self) -> np.ndarray:
        "Y coordinates of the lasso polygon."
        return np.array([e.ydata for e in self._points])

    @property
    def polygon(self) -> Polygon:
        "The lasso polygon."
        return Polygon(zip(self.x, self.y))

    def contains(self, x: Iterable, y: Iterable) -> Iterable[bool]:
        """Return boolean array that indicates if points (x, y) are contained
            in the lasso polygon.

        Parameters
        ----------
        x: Data points to be judged.
        y: Data points to be judged.

        Returns
        -------
        Iterable[bool]
            `True` indicate that the point (x, y) is within the lasso polygon.
        """
        polygon = self.polygon
        return np.array([polygon.contains(Point(p)) for p in zip(x, y)])

    def update(self):
        "Redraw the figure."
        self._fig.canvas.draw()

    @property
    def _is_modifiers_pressed(self):
        "Indicate if all modifiers keys are pressed."
        return all(self._modifiers.values())

    def _on_key_press(self, event):
        "Keyboard press event."
        getLogger(self.NAME).debug(event.key)

        for key in event.key.split("+"):
            if key in self._modifiers:
                self._modifiers[key] = True

    def _on_key_release(self, event):
        "Keyboard release event."
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
