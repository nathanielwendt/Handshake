import webapp2
from webapp2_extras import jinja2
from handler_utils import WebException, InternalAPIRequest
from appengine_config import jinja_environment

class WebBaseHandler(webapp2.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)
        self.data = {}

        paths = {
            "home": self.request.application_url,
            #"manage": self.request.application_url + webapp2.uri_for('Web-ManageStream'),
        }
        self.data["paths"] = paths
        self.base_uri = self.request.application_url

        self.data["resources"] = {
            "js": [],
            "css": []
        }

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    def render_template(self, filename, context):
        template = jinja_environment.get_template(filename)
        self.response.out.write(template.render(context))

    def redirect_template(self, uri, data):
        self.render_template(uri, data)

    def get(self, **kwargs):
        try:
            self.handle_get(**kwargs)
        except WebException, e:
            self.data["error"] = e.data
            print self.data
            self.redirect_template(e.redirect_uri, self.data)

    def post(self, **kwargs):
        try:
            self.handle_post(**kwargs)
        except WebException, e:
            self.data["error"] = e.data
            self.redirect_template(e.redirect_uri, self.data)

    def handle_get(self, **kwargs):
        self.abort(405)

    def handle_post(self, **kwargs):
        self.abort(405)

    def get_param(self, param, required=True):
        try:
            return self.request.params[param]
        except KeyError, e:
            if required:
                self.abort(400)
            else:
                return ""

    #convenience method that automatically includes self.request.application_url in creating request
    def get_internal_api_request(self, method, endpoint_name, uri_args={}):
        return InternalAPIRequest(method, endpoint_name, self.request.application_url, uri_args)


class WebHomeHandler(WebBaseHandler):
    def get(self, **kwargs):
        self.data["stuff"] = "that"
        self.render_template("index.html", self.data)