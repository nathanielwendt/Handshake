import webapp2
import urllib
import urllib2
import json

import lib.formencode
from lib.formencode import validators
from utils import APIUtils, MessageUtils
import view_models

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

    def set_default_success_response(self):
        self.nom_response = view_models.Default.view_contract()

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
                #if param is being retrieved, actually exists, and is malformed
                #should treat the param as a required param and throw an error
                if self.meta_data.params.get(param) is not None and\
                            self.safe_params[param] is not None:
                    self.abort(400, "optional param: " + param + " was included and malformed >> "
                               +self.meta_data.params.get(param))

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
            self.response.status_int = 400
            self.meta_data.exists = True
            self.meta_data.general = "Required parameter(s) were not formatted properly"
            self.meta_data.params = {}
            for violation, filter_type in filter.violations.items():
                self.meta_data.params[violation] = "not formatted according to " + filter_type
                print violation + " not formatted according to " + filter_type
            self.send_response()
            raise ValidatorException()


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

    #Twilio number are sent with a '+DIGIT' prefix where DIGIT indicates country code,
    # this is simply an adapter that wraps the phone number validator after stripping the country code
    class CustomPhoneNumber(object):
        def to_python(self, entry):
            entry = MessageUtils.strip_country_code_from_number(entry)
            validator = validators.PhoneNumber()
            return validator.to_python(entry)

class CustomValidatorException(BaseException):
    def __init__(self, message):
        self.message = message

class ValidatorException(BaseException):
    pass

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
        self.filters["phone"] = CustomValidators.CustomPhoneNumber()

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