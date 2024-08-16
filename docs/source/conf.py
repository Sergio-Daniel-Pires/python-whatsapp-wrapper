import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from whatsapp import __version__

project = 'python-whatsapp-wrapper'
copyright = '2024, Regios'
author = 'Regios'
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_copybutton"
]

exclude_patterns = []

pygments_style = "sphinx"
html_theme = "furo"
# FIXME return to default when _static get some content
# html_static_path = ['_static']
html_static_path = []
