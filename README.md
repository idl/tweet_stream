Tweet_stream
============

Twitter Streaming API Flask Server. A REST API server for Twitter spitzer hose streaming. 


## Requirements
1. Tweepy
2. Multiprocessing
3. Flask
4. MongoDB (For storage)

## Utilization

Start Server:
```
python twt_server.py
```

REST Endpoints:

Start Streaming:
```
curl http://localhost:5000/start_streaming/<stream/client_id> -d "terms=<fire,water>" -X POST
```

Get Stream:
```
curl http://localhost:5000/start_streaming/<stream/client_id> -X GET
```

Delete Stream:
```
curl http://localhost:5000/update_streaming/<stream/client_id> -X DELETE
```

Update Streaming:
```
curl http://localhost:5000/update_streaming/<stream/client_id> -d "terms=<test,program>" -X POST
```
