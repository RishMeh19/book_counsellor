from elasticsearch import Elasticsearch

books_mapping = {
	    "settings" : {
	        "number_of_shards":2,
	        "number_of_replicas": 1
	    },

	    'mappings': {
	        'books': {
	            'properties': {
                    'name':{'index': 'analyzed', 'type': 'string'},
                    'author':{'index': 'analyzed', 'type': 'string'},
                    'genres':{'index': 'analyzed', 'type': 'string'},
                    'age':{'type':'object'}
                }}}}

requests_mapping = {
	    "settings" : {
	        "number_of_shards": 2,
	        "number_of_replicas": 1
	    },

	    'mappings': {
	        'requests': {
                'properties':{
                    'name':{'index': 'analyzed', 'type': 'string'},
                    'author':{'index': 'analyzed', 'type': 'string'},
                    'genres':{'index': 'analyzed', 'type': 'string'},
                    'age':{'type':'object'}
                }
            },
            '.percolator':{
                    'notification_token':{'index':'not_analyzed', 'type':'string'},
                    'sender_psid':{'index':'not_analyzed','type':'string'},
                    'query': {'type':'object','enabled': False}
            }
        }}
                

