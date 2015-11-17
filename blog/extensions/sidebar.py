from jinja2 import nodes
from jinja2.ext import Extension


class GetSidebar(Extension):
    tags = set(['get_sidebar'])

    def __init__(self, environment):
        super(GetSidebar, self).__init__(environment)
