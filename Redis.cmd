Update 

New entry : updated state of the order add to redis list

order_history:{order_uuid}  : Act as version history for the order, each entry in this
list represent the state of the order at a certain point in time
Every time you update the order, you push the new state to the list using `lpush`
This command adds a new entry to the head of the list, so the latest state is always at the beginning.


REtrieving the Order History : Get the entire history of the order, retrieve the entire list
using lrange

LRANGE order_history:ab83d806-b08e-4904-b726-1e5e31f3f7ae 0 -1



f you want to fetch a specific version (e.g., the third version since the order was created), you can use the index when calling lrange
LINDEX order_history:ab83d806-b08e-4904-b726-1e5e31f3f7ae 2

