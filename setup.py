from setuptools import setup
from setuptools import find_packages


variables = {}
exec(open("src/mpl_lassotool/__version__.py").read(), {}, variables)

package_dir = "src"

setup(name='mpl_lassotool',
      version=variables["__version__"],
      description="Lasso selection tool for matplotlib.",
      package_dir={
            "": package_dir
      },
      packages=find_packages(package_dir),
      package_data={
      },
      install_requires=[
          "numpy",
          "matplotlib",
          "shapely",
      ],
      entry_points={
            "console_scripts": [
                  'mpl_lassotool-test=mpl_lassotool.__init__:test',
            ]
      },
      author="Taishi Hashimoto",
      author_email="hashimoto.taishi@outlook.com")
