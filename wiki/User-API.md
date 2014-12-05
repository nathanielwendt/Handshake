# User API 

------------
##[POST] /v1/user##

Creates a new user.

#####Params#####
`email` email for user account purposes (email, required)

`phoneNumbers` phone numbers made available for route creation (num_list, required)

`name` name of the user (varchar, required)

`emails` emails made available for route creation (email_list, required)

#####Response#####

~~~~
{'email': '+',
 'emails': '+',
 'name': '+',
 'phoneNumbers': '+',
 'userId': '+'}
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
 'name': '+',
 'phoneNumbers': '+',
 'userId': '+'}
~~~~

