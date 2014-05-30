from flask import Flask, jsonify, render_template, request
from flask.ext.restful import Resource, Api, abort, reqparse
import sys
import tweepy
import json
from pymongo import MongoClient
import time
from multiprocessing import Process, Queue, Pool, cpu_count
from multiprocessing.pool import ThreadPool

app = Flask(__name__)
api = Api(app)

#multiprocessing
pool = ThreadPool(processes = cpu_count())

#global stuff conn_client = {'client_id' : {'conn_obj': object, 'bot_id':bot1/2}, 'collect' = 0/1}
conn_client = {}

#database storage
client = MongoClient()
db = client.twitter

#tweepy stuff
def get_access_bots(bot_id = None):
	access_creds = {}

	access_creds['bot1'] = {
			'consumer_key' : "BpkCXkd6KYSxc0WetI3jpw",
		    'consumer_secret': "sT3qkQk0lMbD9YFi2nGLbdpoAHeSWS2xfhu0wvFGYZU",
		    'access_key' : "616747288-ARmQaB5E2s3HHKlXsK6ZFelsLeM3Phva53T1CrOU",
		    'access_secret' : "GWJdsPF1jLJkmSQIFZm0qyXtTVj7DeLBD1V6bLpNj9g" ,
		}
	access_creds['bot2'] = {
			'consumer_key' : "n1ZwDvpk2igEzT3mrxxLU4bJx",
		    'consumer_secret': "kXJy1K8Pll3GuzMmttS3ku5SYT1rp78C2ADFB5Xtak3UieIL1A",
		    'access_key' : "616747288-WmUQANsIVTHJoVI9Gtnm8k03Y34iUElEfwkCbdIZ",
		    'access_secret' : "WODzLHUh31rxv6RwgQsAmcaYN9WyKeg4CS3USTLppSbtC" ,
		}

	if bot_id == 1:
		return 2, access_creds['bot2']
	else:
		return 1, access_creds['bot1']


class CustomStreamListener(tweepy.StreamListener):
	def __init__(self, collection, *args, **kwargs):
		super(CustomStreamListener, self).__init__(*args, **kwargs)
		self.collection = collection

	def on_data(self, data):
		tweet = json.loads(data)
		# print tweet['text'], self.collection
		collection = db[self.collection]
		collection.insert(tweet)

	def on_error(self, status_code):
		print >> sys.stderr, 'Encountered error with status code:', status_code
		return False # Don't kill the stream

	def on_timeout(self):
		print >> sys.stderr, 'Timeout...'
		return True # Don't kill the stream

def streaming_twitter(client_id, terms, access, bot_id, update):
	restart_flag = 1
	while True:
		try:
			if restart_flag == 1: 
				auth = tweepy.OAuthHandler(access['consumer_key'], access['consumer_secret'])
				auth.set_access_token(access['access_key'], access['access_secret'])
				api = tweepy.API(auth)

				sapi = tweepy.streaming.Stream(auth, CustomStreamListener(collection=client_id))

				stream = sapi.filter(track=terms, async=True)

				if update == True and sapi.running is True:
					conn_client[client_id]['conn_obj'].disconnect()

				conn_client[client_id]['conn_obj'] = sapi
				conn_client[client_id]['bot_id'] = bot_id

				if conn_client[client_id]['collect'] == 0:
					print "Collection Terminated", conn_client[client_id]
					return None

				restart_flag = 0

				if sapi.running is True:
					time.sleep(180)
				else:
					time.sleep(180)
					restart_flag = 1
					print "Trying to re-start"
		except Exception, e:
			time.sleep(180)
			restart_flag = 1
			print "Trying to re-start"
			pass

	return None

#flask stuff
def abort_if_client_conn_doesnt_exist(client_id):
	if client_id not in conn_client:
		abort(404, message="Client Connection {} doesn't exist".format(client_id))

class init_stream_db(Resource):
	pass

class start_streaming(Resource):
	def get(self, client_id):
		abort_if_client_conn_doesnt_exist(client_id)
		return client_id, conn_client[client_id]

	def post(self, client_id):
		track_terms = request.form['terms']
		track_terms = track_terms.split(',')

		print track_terms

		if client_id in conn_client:
			abort(400, message="Stream for client {} already up. Use update to change terms.".format(client_id))
		else:
			conn_client[client_id] = {'collect' : 1}
			bot_id, access = get_access_bots()
			pool.apply_async(streaming_twitter, args = (client_id,track_terms,access, bot_id, False))
			return "Client Started", 200

class update_streaming(Resource):
	def delete(self,client_id):
		abort_if_client_conn_doesnt_exist(client_id)
		conn_client[client_id]['collect'] = 0
		conn_client[client_id]['conn_obj'].disconnect()
		conn_client.pop(client_id, None)
		return "Connection Terminated", 200

	def post(self,client_id):
		track_terms = request.form['terms']
		track_terms = track_terms.split(',')

		abort_if_client_conn_doesnt_exist(client_id)
		
		if 'bot_id' in conn_client[client_id]:
			bot_id, access = get_access_bots(conn_client[client_id]['bot_id'])
		else:
			bot_id, access = get_access_bots()

		pool.apply_async(streaming_twitter, args = (client_id,track_terms,access, bot_id, True))

		return "Client Updated", 200

api.add_resource(start_streaming, '/start_streaming/<string:client_id>')
api.add_resource(update_streaming, '/update_streaming/<string:client_id>')

if __name__ == "__main__":
    app.run(debug=True)
