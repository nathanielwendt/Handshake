import os.path
import sys
import jinja2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))