# Route API 

------------
##[POST] /v1/route##

Creates a route with 1 or more communication channels attached
:return:

#####Params#####
`slots` Access Slot items formatted as { "start": "+", "end": "+", "repeatInterval": "+", "cutoff": "+" } (slot_list, required)

`userId` Id for user that is creating the route (id, required)

`phoneNumbers` Phone numbers attached to the route (10 digit, not characters other than numbers) (phone_list, optional)

`emails` Emails attached to the route (email_list, optional)

#####Response#####

~~~~
{'displayName': '+',
 'emails': ['+', '*'],
 'id': '+',
 'open': '+',
 'phoneNumbers': ['+', '*'],
 'slots': [{'active': '+',
            'cutoff': '+',
            'end': '+',
            'repeatInterval': '+',
            'slotId': '+',
            'start': '+'},
           '*'],
 'userId': '+'}
~~~~

------------
##[GET] /v1/route/{id}/member/list##

Retrieves a list of members belonging to a specific route

#####Params#####
`userId` id of user that is requesting the list, only the route owner is allowed here (id, required)

#####Response#####

~~~~
{'members': [{'displayName': '+',
              'memberId': '+',
              'userId': '+'},
             '*']}
~~~~

------------
##[POST] /v1/route/{id}/member##

Joins a user to a specific route

#####Params#####
`userId` id of user to join route (id, required)

#####Response#####

~~~~
{'displayName': '+', 'memberId': '+', 'userId': '+'}
~~~~

------------
##[GET] /v1/route/list##

Retrieves all routes for a given user (both created and joined routes)

#####Params#####
`userId` Id for user for which to return routes (id, required)

#####Response#####

~~~~
{'routes': [{'displayName': '+',
             'emails': ['+', '*'],
             'id': '+',
             'open': '+',
             'phoneNumbers': ['+', '*'],
             'slots': '*',
             'userId': '+'},
            '*']}
~~~~

------------
##[PUT] /v1/route/{id}##

Updates route parameters.
Note: updating slots will wipe old slots and replace with new set.

#####Params#####
`slots` Access Slot items formatted as { "start": "+", "end": "+", "repeatInterval": "+", "cutoff": "+" } (slot_list, optional)

`phoneNumbers` Numbers attached to the route (phone_list, optional)

`emails` Emails attached to the route (email_list, optional)

#####Response#####

~~~~
{'displayName': '+',
 'emails': ['+', '*'],
 'id': '+',
 'open': '+',
 'phoneNumbers': ['+', '*'],
 'slots': [{'active': '+',
            'cutoff': '+',
            'end': '+',
            'repeatInterval': '+',
            'slotId': '+',
            'start': '+'},
           '*'],
 'userId': '+'}
~~~~

------------
##[GET] /v1/route/{id}##

Retrieves a route by route name

#####Params#####

None

#####Response#####

~~~~
{'displayName': '+',
 'emails': ['+', '*'],
 'id': '+',
 'open': '+',
 'phoneNumbers': ['+', '*'],
 'slots': [{'active': '+',
            'cutoff': '+',
            'end': '+',
            'repeatInterval': '+',
            'slotId': '+',
            'start': '+'},
           '*'],
 'userId': '+'}
~~~~

