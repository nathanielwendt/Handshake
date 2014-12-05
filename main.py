#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from api_handlers import *
from web_handlers import *

v1_routes = [
    webapp2.Route(r'/v1/user', handler=UserCreationHandler, name="User-Creation"),
    webapp2.Route(r'/v1/user/<id:[\w-]+>', handler=UserHandler, name="User"),

    #[App Names]
    #Fleet
    #Groovy

    #[Channel Names]
    #Route
    #Groove
    #Trail
    #Track
    #Line
    #Knit
    #Notch
    webapp2.Route(r'/v1/route', handler=RouteCreationHandler, name="Route-Creation"),
    webapp2.Route(r'/v1/route/<name:([\w|\W])+>', handler=RouteHandler, name="Route"),


    webapp2.Route(r'/v1/message/out', handler=MessageNativeCreationHandler, name="Message-OutCreation"),
    webapp2.Route(r'/v1/message/in', handler=MessageSMSCreationHandler, name="Message-InTextCreation")
]

web_routes = [
    webapp2.Route(r'/', handler=WebHomeHandler, name="Web-HomeHandler")
]

routes = v1_routes + web_routes
app = webapp2.WSGIApplication(routes = routes, debug=True)