# mpl_lassotool

Lasso selection tool for matplotlib.

## Install

```
pip install .
```

## Example

Run `mpl_lassotool-test` command in the terminal to see a running example.

1. Hold `Ctrl` and press the left button of the mouse on the plot axes.
2. Drag to draw an arbitrary shape to encircle target points.

### Usage

You can also override `EventHandler` to do custom computation.

```Python
import numpy as np
import matplotlib.pyplot as plt
from mpl_lassotool import LassoTool, EventHandler


data = np.random.normal(size=(2, 10000))

fig, ax = plt.subplots()
ax.scatter(*data)
_ = LassoTool(fig, EventHandler())
plt.show()
```