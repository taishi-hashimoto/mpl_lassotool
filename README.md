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

### Usage in the code

```Python
from mpl_lassotool import LassoTool, EventHandler

# Create a figure.
fig = plt.figure()
ax = fig.add_subplot(111)

# Plot some data.
data = np.random.normal(size=(2, 10000))
ax.scatter(*data)

# Prepare lasso tool.
# Note the instance must be bound to a local variable
# to make the event handler work.
_ = LassoTool(fig, EventHandler({ax: data}))

plt.show()
```