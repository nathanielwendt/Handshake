import webapp2
import uuid
import urllib
import urllib2
import json

import lib.formencode
from lib.formencode import validators
from utils import APIUtils
import datetime
import view_models
import cloudstorage
import time
import models
from google.appengine.ext import ndb
import random

class IDTYPE():
    USER = "user"
    COUNTER = "count"
    ACCESS_SLOT = "accsl"
    ROUTE = "route"
    MESSAGE = "msg"

class NamingGenerator(object):
    NOUN_KEY = "nouns"
    ADJ_KEY = "adjectives"
    ANIM_KEY = "animals"
    FILES = {
        "adjectives": "adjectives.txt",
        "animals": "animals.txt",
        "nouns": "nouns.txt"
    }
    PATH_BASE = "/handshake-app.appspot.com/"

    @staticmethod
    #retrieves a route name that is guaranteed to be unique
    #will continue trying routes until it finds a unique entry
    #the route entry will be created with the route name used as an id and placeholder
    #to 'save' the spot of the route entry for the assigned name
    def get_route_name():
        adjectives = models.Naming.get_by_id(NamingGenerator.ADJ_KEY)
        nouns = models.Naming.get_by_id(NamingGenerator.NOUN_KEY)

        while True:
            time_seed = int(time.time() * 100) #time in deci-seconds
            adjective = adjectives.get_random_entry(time_seed)
            noun = nouns.get_random_entry(time_seed)
            cand_route_name = adjective + " " + noun
            try:
                NamingGenerator.create_route(cand_route_name)
                return cand_route_name
            except UtilsException:
                continue

    @staticmethod
    @ndb.transactional
    #creates a dummy route entry to reserve the name (subsequent requests will see that it now exists)
    #if the route already exists, throws an exception
    def create_route(cand_route_name):
        route = models.Route.get_by_id(cand_route_name)
        if route is None:
            models.Route(id=cand_route_name).put()
        else:
            raise UtilsException("route exists for that name")

    @staticmethod
    def get_route_member_name(route_entity):
        animals = models.Naming.get_by_id(NamingGenerator.ANIM_KEY)
        animals_length = len(animals.items)

        created_animals = models.RouteMember.query(ancestor=route_entity.key).fetch()
        created_animals_length = len(created_animals)

        multiple = created_animals_length / animals_length
        index = created_animals_length % animals_length + 1

        if multiple == 0:
            append_item = ''
        else:
            append_item = str(multiple)

        animal = animals.items[index] + append_item
        animal_entry = models.RouteMember(parent=route_entity.key, id=animal)
        animal_entry.put()
        return animal


    @staticmethod
    # Populates the Naming model with an entry for each item in FILES
    # Does not check if the file size is too large to itemize into the datastore entry
    # so it is assumed that check is made in creating the input files
    def initialize_ds_names():
        for name,file in NamingGenerator.FILES.iteritems():
            valid_items = []
            delim = ""

            gcs_file = cloudstorage.open(filename=NamingGenerator.PATH_BASE + file, mode='r')
            for line in gcs_file:
                line = line.strip()
                if not line or\
                        len(line.split(" ")) > 1 or\
                        line.find("-") > 0 or\
                        len(line) > 8:
                    continue

                valid_items.append(line)

            entry = models.Naming(id=name)
            entry.items = valid_items
            entry.put()






class Namer(object):
    ROUTE_STRINGS = ["green_tea", "solo_chief", "bag_town", "upper_dime", "total_hat", "grand_stuff"]
    route_index = 0
    route_length = len(ROUTE_STRINGS)

    @staticmethod
    def get_next():
        next = Namer.ROUTE_STRINGS[Namer.route_index % Namer.route_length]
        Namer.route_index += 1
        return next

def getUUID(type):
    return type + str(uuid.uuid4())
    #return base64.urlsafe_b64decode(uuid.uuid4().bytes)[:-2]

class InternalAPIRequest(object):
    def __init__(self, method='GET', endpoint_name='', base_uri='', uri_args={}):
        if endpoint_name == '':
            self.endpoint = "/"
        else:
            self.endpoint = webapp2.uri_for(endpoint_name, **uri_args)
        self.method = method
        self.base_uri = base_uri
        self.response = ''
        self.params = {}
        self.response_data = ''

    def send(self):
        if self.method == 'POST':
            data = urllib.urlencode(self.params)
            req = urllib2.Request(self.base_uri + self.endpoint, data)
        else:
            endpoint_with_params = self.base_uri + self.endpoint + "?"
            prefix = ""
            for key,value in self.params.items():
                endpoint_with_params += prefix + key + "=" + value
                prefix = "&"
            req = endpoint_with_params

        try:
            resp = urllib2.urlopen(req)
            return json.loads(resp.read())
        except urllib2.HTTPError as e:
            self.response_code = e.code
            self.response_data = e.read()
            return None

class UtilsException(Exception):
    def __init__(self, message):
        self.message = message


class WebException(Exception):
    def __init__(self, redirect_uri, data):
        self.data = data
        self.redirect_uri = redirect_uri

class MetaData(object):
    def __init__(self):
        self.exists = False
        self.general = ""
        self.params = {}

    def form(self):
        vals = {
            "has_meta_data": self.exists,
            "meta_data": {
                "params": self.params,
                "general": self.general
            }
        }
        return vals

class APIBaseHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.api_response = {}
        self.resp_code = '400'
        self.meta_data = MetaData()
        self.view_model = {}
        self.safe_params = {}
        self.param_violations = []
        self.param_violations = []

    def set_response_code(self, code):
        self.resp_code = code

    def set_meta_data(self, meta_data):
        self.meta_data = meta_data

    def set_response_view_model(self, view_model):
        self.view_model = view_model

    # Makes the objects data uniform according the the API specs
    # All json will be formatted as follows
    # all values will be strings EXCEPT for lists
    # the values within a list will adhere to the same rules
    def uniform_output(self, object):
        for key,value in object.items():
            if isinstance(value, list):
                temp_list = []
                for item in value:
                    if isinstance(item, dict):
                        self.uniform_output(item)
                    temp_list.append(item)
                object[key] = temp_list
            elif isinstance(value, dict):
                self.uniform_output(value)
            elif not isinstance(value, basestring):
                object[key] = str(value)
            else:
                object[key] = value


    def send_response(self):
        if self.view_model:
            def verify_true_action(exp, printout):
                if not exp:
                    Log.create_entry("Outgoing Contract [" + self.__class__.__name__ + "]", printout)

            APIUtils.check_contract_conforms(self.view_model, self.api_response, verify_true_action)

        if self.meta_data.exists:
            meta_data = self.meta_data.form()
            self.final_response = dict(self.api_response.items() + meta_data.items())
        else:
            self.final_response = self.api_response

        self.uniform_output(self.final_response)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(self.final_response))

    def get_param(self, param, safe=True):
        try:
            if safe and self.safe_params:
                return self.safe_params[param]
            else:
                return self.request.params[param]
        except KeyError, e:
            return None

    def check_params_conform(self, contract):
        filter = Filter()
        for key, value in contract.items():
            if value[1] == "+":
                param = self.get_param(key, safe=False)
                filter.validate(key, param, value[0], True)
                self.safe_params[key] = param
            elif value[1] == "*":
                try:
                    param = self.get_param(key, safe=False)
                    filter.validate(key, param, value[0], False)
                    self.safe_params[key] = param
                except:
                    self.safe_params[key] = None
                    continue

        if filter.warnings:
            self.meta_data.exists = True
            self.meta_data.general = "Optional parameter(s) were not formatted properly, will be omitted"
            self.meta_data.params = {}
            for violation, filter_type in filter.warnings.items():
                self.meta_data.params[violation] = "not formatted according to " + filter_type

        if filter.violations:
            self.response.status_code = 400
            self.meta_data.exists = True
            self.meta_data.general = "Required parameter(s) were not formatted properly"
            self.meta_data.params = {}
            for violation, filter_type in filter.violations.items():
                self.meta_data.params[violation] = "not formatted according to " + filter_type
            self.send_response()
            raise Exception()


#Allow deeper nesting of list items
#will not give detailed error messages if printed, but will still allow nesting
class CustomValidators(object):
    class SlotValidator(object):
        def to_python(self, entry):
            def verify_true_action(val, message):
                if not val:
                    raise CustomValidatorException(message)
            contract = view_models.AccessSlot.create_contract()
            APIUtils.check_contract_conforms(contract, entry, verify_true_action)

class CustomValidatorException(BaseException):
    def __init__(self, message):
        self.message = message



#does not maintain state of values checked
#simply maintains a list of warnings and violations for checked values
class Filter():
    #TODO: improve validation strength
    # GEO - check if coordinates make sense
    # timestamp - check if time can possibly be in that range
    def __init__(self):
        self.violations = {}
        self.warnings = {}
        self.filters = {}
        self.filters["bool"] = validators.StringBoolean()
        self.filters["url"] = validators.URL()
        self.filters["id"] = validators.String()
        self.filters["num"] = validators.Int()
        self.filters["geo"] = validators.String()
        self.filters["varchar"] = validators.String()
        self.filters["timestamp"] = validators.String()
        self.filters["email"] = validators.Email()
        self.filters["password"] = validators.String()
        self.filters["slot"] = CustomValidators.SlotValidator()

    def validate(self, name, value, filter_type, required):
        #exception check here is for Nonetype values
        try:
            value = urllib.unquote(value)
        except:
            if required and name not in self.violations:
                self.violations[name] = filter_type + ", missing"
            elif not required and name not in self.warnings:
                self.warnings[name] = filter_type + ", missing"
            return

        entries = []
        if "list" in filter_type:
            index = filter_type.find("_")
            filter_type = filter_type[0:index]
            entries = json.loads(value)
        elif "tuple" in filter_type:
            index = filter_type.find("_")
            filter_type = filter_type[0:index]
        else:
            entries = [value]

        # Loop through items in case it is a list
        for entry in entries:
            try:
                self.filters[filter_type].to_python(entry)
            except (lib.formencode.Invalid, CustomValidatorException), e:
                if required and name not in self.violations:
                    self.violations[name] = filter_type
                elif not required and name not in self.warnings:
                    self.warnings[name] = filter_type

class Log(object):
    @staticmethod
    def create_entry(tag, message):
        print tag , " >> ", message