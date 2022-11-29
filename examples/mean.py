"Compute mean of selected X and Y coordinates."
import numpy as np
import matplotlib.pyplot as plt
from mpl_lassotool import LassoTool, EventHandler


class CustomEventHandler(EventHandler):
    "For each artist, mean of selected X and Y are computed."
    def on_close(self, lt: LassoTool):
        data = super().on_close(lt)
        for artist, index in data.items():
            print(artist)
            x, y = self.get_xy_from_artist(artist)
            print("mean X: {:.3g}, mean Y: {:.3g}".format(
                np.mean(x[index]), np.mean(y[index])
            ))


fig, ax = plt.subplots()

data = np.random.normal(size=(2, 10000))
ax.scatter(*data)

_ = LassoTool(fig, CustomEventHandler(marker="x", color="r"))
plt.show()
