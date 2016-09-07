#!/usr/bin/env python3
#
# Example3 - routerclass
#

from growler import App
from growler.router import routerclass


@routerclass
class QuickRoute:
    """
    An example class showing how to use @routerclass decorator
    """

    def __init__(self, param):
        """
        Construct a QuickRoute object
        """
        self.param = param
        self.name_dict = dict()

    def get_root(self, req, res):
        """ /
        return the root of the object
        """
        res.send_json({'param': self.param})

    def post_name(self, req, res):
        """ /name
        Submit your name to the server
        """
        name = req.get_body()
        if name in self.name_dict:
            txt = "Already Created %s (%d)" % (name, self.name_dict[name])
        else:
            self.name_dict[name] = 0
            txt = "Created name %s." % (name)
        res.render_text(txt)

    def get_name(self, req, res):
        """ /name/:name
        Return the number of times this name has been returned
        """
        name = req.params['name']
        try:
            self.name_dict[name] += 1
            txt = "%s : %d" % (name, self.name_dict[name])
        except KeyError:
            txt = "No name %s." % (name)
        res.render_text(txt)


app = App("Example3")

app.use(QuickRoute('Helloo'), '/')
app.print_middleware_tree()

app.create_server_and_run_forever(port=8000, host='127.0.0.1')
