"Event handler for LassoTool."
import numpy as np
from logging import getLogger
from typing import Dict, Iterable, Tuple, TYPE_CHECKING
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.artist import Artist
from matplotlib.lines import Line2D

if TYPE_CHECKING:
    from .lassotool import LassoTool


class EventHandler:
    """Default event handler to pick data points in plotted artists.

    Currently `PathCollection` (scatter) and `Line2D` (plot) are supported.
    """
    def __init__(self, **kwargs):
        """

        Parameters
        ----------
        kwargs:
            Parameters to draw picked points.
            It is deregated to `matplotlib.pyplot.scatter`.
        """
        self._markers = {}
        self._kwargs = kwargs

    def on_open(self, lt: 'LassoTool') -> None:
        "Called when lasso selection is started."
        if lt.ax not in self._markers:
            self._markers[lt.ax] = lt.ax.scatter([], [], **self._kwargs)
        else:
            self._markers[lt.ax].set_visible(False)

    def on_close(self, lt: 'LassoTool') -> Dict[Artist, Iterable[bool]]:
        """Called when lasso tool is closed.

        Returns
        -------
        `Dict[Artist, Iterable[bool]]`
            A mapping from artists to indices of selected points within them.
        """
        offsets = []
        picked = {}
        for artist in lt.ax.get_children():
            if artist in [lt._line, *list(self._markers.values())]:
                continue  # Known artists that are created by LassoTool.
            else:
                if isinstance(artist, PathCollection):  # scatter
                    x, y = artist.get_offsets().T
                elif isinstance(artist, Line2D):  # plot
                    x, y = artist.get_data(orig=True)
                else:
                    getLogger(lt.NAME).debug(
                        f"Artist {artist} is not supported, skipping.")
                    continue  # Otherwise it is not supported.
                idx = lt.contains(x, y)
                if any(idx):
                    getLogger(lt.NAME).info(np.nonzero(idx)[0])
                    offsets.append(np.c_[x[idx], y[idx]])
                    picked[artist] = idx
        if offsets:
            self._markers[lt.ax].set_offsets(np.vstack(offsets))
            self._markers[lt.ax].set_visible(True)
            lt.update()
        return picked


class XYEventHandler(EventHandler):
    """Event handler with given XY coordinates for specified axes.

    This event handler does not consider what is plotted in the axes.
    Just value or XY coordinates are used.
    """

    def __init__(
        self, xy: Dict[Axes, Tuple[Iterable, Iterable]],
        **kwargs
    ) -> None:
        """
        
        Parameters
        ----------
        xy: `Dict[Axes, Tuple[Iterable, Iterable]]`
            A mapping from `Axes` to given data `(x, y)`.
        kwargs:
            Parameters to draw picked points.
            It is deregated to `matplotlib.pyplot.scatter`.
        """
        super().__init__(**kwargs)
        self._xy = xy
        self._markers = {ax: None for ax in self._xy}

    def on_open(self, _: 'LassoTool') -> None:
        for ax in self._markers:
            if self._markers[ax] is None:
                self._markers[ax] = ax.scatter([], [], **self._kwargs)
            else:
                self._markers[ax].set_visible(False)

    def on_close(self, lt: 'LassoTool') -> Iterable[bool]:
        """Called when lasso tool is closed.

        Returns
        -------
        `Iterable[bool]`
            An boolean array indicating the chosen indices.
        """
        idx = lt.contains(*self._xy[lt.ax])
        for ax in self._markers:
            x, y = self._xy[ax]
            self._markers[ax].set_offsets(np.c_[x[idx], y[idx]])
            self._markers[ax].set_visible(True)
        lt.update()
        return idx
