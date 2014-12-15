# User API 

------------
##[POST] /v1/user##

Creates a new user.

#####Params#####
`name` name of the user (varchar, required)

`phoneNumbers` phone numbers made available for route creation (num_list, required)

`email` email for user account purposes (email, required)

`emails` emails made available for route creation (email_list, required)

`id` unique identifier for user, used to link with external service like Google API (id, required)

#####Response#####

~~~~
{'email': '+',
 'emails': '+',
 'id': '+',
 'name': '+',
 'phoneNumbers': '+'}
~~~~

------------
##[PUT] /v1/user/{id}/notifications##

Registers a user with push notifications

#####Params#####
`pushRegKey` GCM key obtained from Google (id, required)

#####Response#####

~~~~
{'status': 'success'}
~~~~

------------
##[GET] /v1/user/{id}##

Retrieves a user entry by id

#####Params#####

None

#####Response#####

~~~~
{'email': '+',
 'emails': '+',
 'id': '+',
 'name': '+',
 'phoneNumbers': '+'}
~~~~

