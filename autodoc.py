import os
import re
import main
import inspect
import pprint
import view_models
import handler_utils

#Will enable print statements to quickly find cause of handler which does not
#conform to autodocs expectations
DEBUG = False

base_location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

#configure for project here
project_routes = main.v1_routes
wiki_location = base_location + "/wiki"


class AutoDocException(BaseException):
    pass

def extract_comments_and_params(comment_block):
    std_comments = []
    param_comments = {}
    for comment_raw in comment_block.splitlines():
        if not comment_raw:
            continue

        comment = comment_raw.lstrip()
        #print comment


        if comment.find(":param") == 0:
            param_definition = comment[len(":param") + 1:]
            colon_loc = param_definition.find(":")
            param_name = param_definition[: colon_loc]
            param_desc = param_definition[colon_loc + 1 :].strip()
            param_comments[param_name] = param_desc
        else:
            std_comments.append(comment)

    return {
        "std": std_comments,
        "params": param_comments
    }

def convert_method_to_nice_name(method_name):
    method_name_safe = method_name.strip().lower()
    vals = {
        "delete": "[DELETE]",
        "get": "[GET]",
        "put": "[PUT]",
        "post": "[POST]",
    }
    if not vals.get(method_name_safe):
        raise AutoDocException("could not find proper method name")

    return vals[method_name_safe]

def extract_contract_from_source(source):
    match = re.search(r'contract(\s)*(\=)(\s)*(\{)(.)+?(\})', source, flags=re.DOTALL)
    if match:
        valid_str = re.search(r'(\{)(.?)*(\})', match.group(), flags=re.DOTALL).group()
        contract_obj = eval(valid_str)
        return contract_obj
    else:
        return None

def extract_response_from_source(source):
    # match_response = re.search(r'self.view_model(.)*?(\=)(.)*?view_models(.)*?(\))', source)
    # if match_response:
    #     match_str = match_response.group()
    #     splits = match_str.split("=")
    #     return eval(splits[1].lstrip())

    match_response = re.search(r'self.set_response_view_model(\(){1}(.)*?(\)){1}', source)
    if match_response:
        match_str = match_response.group()
        splits = match_str.split("(")
        return eval(splits[1] + "()")

    match_default = re.search(r'set_default_success_response', source)
    if match_default:
        return view_models.Default.view_contract()

    raise AutoDocException("could not find response from source")


#expects route names to be in format: Resource-HandlerName
#route_full_name_to_group_name("Comment-Creation") -> "Comment"
#route_full_name_to_group_name("Comment") -> "Comment
def extract_resource_from_name(route_name):
    splits = route_name.split("-")
    return splits[0].title()


# converts the route template to a friendly name
# all regex matches are converted to their variable names
# /v1/comment/<id:[\w-]+>/ ---> /v1/comment/{id}
def extract_friendly_route_name(route_template):
    portions = route_template.split("/")
    friendly_name = ""
    delimiter = ""
    for portion in portions:
        match = re.search("\<(.)*?(:)", portion)
        if match:
            friendly_name += delimiter + "{" + match.group()[1: len(match.group()) - 1] + "}"
        else:
            friendly_name += delimiter + portion
        delimiter = "/"
    return friendly_name


def merge(req_contract, comments):
    merge = {}
    for req_param, req_meta_data in req_contract.iteritems():
        entry = {}
        param_comment = comments.get(req_param)

        if param_comment:
            entry["comment"] = param_comment

        entry["type"] = req_meta_data[0]
        if req_meta_data[1] == "+":
            entry["required"] = True
        elif req_meta_data[1] == "*":
            entry["required"] = False
        else:
            raise AutoDocException("param type not known: " + req_meta_data[1] + " for param: " + req_param)

        merge[req_param] = entry
    return merge

def create_docs():
    api_docs = {}
    for route in project_routes:
        if DEBUG:
            print route.name
        if not hasattr(route, 'name'):
            continue
        #route name is required
        #if not route.name:
        #    raise AutoDocException("All routes must have a name: " + str(route))

        for name, method in route.handler.__dict__.iteritems():
            if callable(method) and method.__doc__:
                method_entry = {}
                if DEBUG:
                    print method

                source = inspect.getsource(method)
                comments = extract_comments_and_params(inspect.getdoc(method))
                req_contract = extract_contract_from_source(source)
                resp_contract = extract_response_from_source(source)

                if req_contract:
                    method_entry["req_contract"] = merge(req_contract, comments["params"])
                else:
                    method_entry["req_contract"] = {}

                if comments["std"]:
                    method_entry["comments"] = comments["std"]
                else:
                    method_entry["comments"] = []

                if not resp_contract:
                    raise AutoDocException("must detect a response from handler!")
                else:
                    method_entry["resp_contract"] = resp_contract

                method_entry["name"] = extract_friendly_route_name(route.template)
                method_entry["type"] = convert_method_to_nice_name(name)

                api_resource = extract_resource_from_name(route.name)
                if api_docs.get(api_resource):
                    api_docs[api_resource].append(method_entry)
                else:
                    api_docs[api_resource] = [method_entry]

    return api_docs


def debug_print_api_docs(api_docs):
    for resource, resource_data in api_docs.iteritems():
        print resource
        pprint.pprint(resource_data)

def write_docs(api_docs):
    for resource, resource_data in api_docs.iteritems():
        with open(wiki_location + "/" + resource + "-API.md", 'w') as file:
            file.write("# " + resource + " API \n\n")
            for method in resource_data:
                file.write("------------\n")
                file.write("##" + method["type"] + " ")
                file.write(method["name"] + "##\n\n")
                for comment in method["comments"]:
                    file.write(comment + "\n")

                file.write("\n")
                file.write("#####Params#####\n")

                if not method["req_contract"]:
                    file.write("\nNone\n\n")

                for param_name, param_data in method["req_contract"].iteritems():
                    if param_data.get("comment") is None:
                        raise AutoDocException("comment does not exist for: " + param_name)
                    file.write("`" + param_name + "`" + " " + param_data["comment"])
                    file.write(" (" + param_data["type"] + ", ")
                    if param_data["required"]:
                        file.write("required")
                    else:
                        file.write("optional")
                    file.write(")")
                    file.write("\n\n")

                file.write("#####Response#####\n\n")
                file.write("~~~~\n" + pprint.pformat(method["resp_contract"], width=60) + "\n~~~~")
                file.write("\n\n")


if __name__ == "__main__":
    api_docs = create_docs()
    write_docs(api_docs)


