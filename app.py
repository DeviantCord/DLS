import threading
from typing import Optional

from flask import Flask
from errite.tools.mis import fileExists
import errite.da.daParser as dp
import psycopg2.pool
import psycopg2
import json
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from errite.da.datools import getDLSUserInfo
import binascii
import uuid
import redis
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration

app = Flask(__name__)
print("Deviant Logic Server V1.6.1")
print("Developed by Errite Games LLC")
file = open('private.key', 'r')
external_key = file.read()
other_file = open('private-other.key', 'r')
other_ext_key = other_file.read()
key = RSA.import_key(external_key)
other_key = RSA.import_key(other_ext_key)
redisData = None
profileRedisData = None
shardData = None
configData = None
clientData = None
profile_pool = None
with open("client.json") as clientJson:
    clientData = json.load(clientJson)

if fileExists("db.json"):
    database_active = True
    with open("db.json", "r") as dbJson:
        dbInfo = json.load(dbJson)
        database_name = dbInfo["database-name"]
        database_host = dbInfo["database-host"]
        database_host2 = dbInfo["database-host2"]
        database_host3 = dbInfo["database-host3"]
        database_password = dbInfo["database-password"]
        database_user = dbInfo["database-username"]
        database_port = dbInfo["database-port"]
        stop_duplicaterecovery = False
        with open("config.json", "r") as configJson:
            configData = json.load(configJson)
            use_sentry = configData["sentry-enabled"]
            sentry_url = configData["sentry-url"]
        sentry_sdk.init(
            dsn=sentry_url,
            integrations=[FlaskIntegration()],

            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0
        )

        if database_host2 == "none":
            connect_str = "dbname='" + database_name + "' user='" + database_user \
                          + "'host='" + database_host + "' " + \
                          "'port='" + str(database_port) + "password='" + database_password + "'"
        elif database_host3 == "none":
            connect_str = "dbname='" + database_name + "' user='" + database_user \
                          + "'host='" + database_host + "," + database_host2 + "' " + \
                          "'port='" + str(database_port) + "password='" + database_password + "'"
        else:
            connect_str = "dbname='" + database_name + "' user='" + database_user \
                          + "'host='" + database_host + "," + database_host2 + "," + database_host3 + " " + \
                          "'port='" + str(database_port) + "'password='" + database_password + "'"
        print("Connecting to database")
        _connPool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        _poolSemaphore = threading.Semaphore(40)  # 10 is max no of connections in this case
        _connPool = psycopg2.pool.ThreadedConnectionPool(1, 40, connect_str)
        #db_connection = psycopg2.connect(connect_str)
        print("Preparing to connect to Redis")
        with open("redis.json", "r") as redisJson:
            redisData = json.load(redisJson)
            redisStr = redisData["url"]
            redisPassword = redisData["password"]
            print("Connecting to redis ")
            rpool = redis.ConnectionPool.from_url(url=redisStr, password=redisPassword, db=0)
            print("Connected to redis!")
            redisJson.close()
        with open("profile_redis.json", "r") as profileRedisJson:
            profileRedisData = json.load(profileRedisJson)
            profile_redisStr = profileRedisData["url"]
            profile_redisPassword = profileRedisData["password"]
            print("Connecting to profile redis ")
            profile_pool = redis.ConnectionPool.from_url(url=profile_redisStr, password=profile_redisPassword, db=0)
            print("Connected to profile redis!")
            profileRedisJson.close()
        print("Loading ShardData...")
        with open("shard.json","r") as shardJson:
            shardData = json.load(shardJson)
            print("ShardData loaded!")
            shardJson.close()

def getConnection():
    _poolSemaphore.acquire(blocking=True)
    print("Pool is delivering connection")
    return _connPool.getconn()

def putConnectionBack(conn: psycopg2):
    _connPool.putconn(conn, close=False)
    _poolSemaphore.release()
    print("Pool tool back a connection")



@app.route('/get_da_profile/<artist>/<token>/<da_token>')
def get_da_profile(artist=None, token=None, da_token=None):
    ttconnection = redis.Redis(connection_pool=rpool)
    token_result = ttconnection.get(token)
    ttconnection.close()
    if not token_result is None:
        decryptor = PKCS1_OAEP.new(other_key)
        obt_password_unhexed = binascii.unhexlify(da_token)
        decrypted_token = decryptor.decrypt(obt_password_unhexed)
        db_connection = getConnection()
        pscursor = db_connection.cursor()
        sql = """SELECT * FROM deviantcord.artist_info WHERE artist = %s"""
        pscursor.execute(sql, (artist,))
        obt_results = pscursor.fetchall()
        if not len(obt_results) == 0:
            jsonResponse = {}
            jsonResponse["result"] = "pass"
            jsonResponse["artist-name"] = obt_results [0][0]
            jsonResponse["artist-icon"] = obt_results[0][1]
            jsresponse = json.dumps(jsonResponse)
            pscursor.close()
            putConnectionBack(db_connection)
            return jsresponse
        else:
            str_pass = decrypted_token.decode('utf-8')
            obt_da_resp = dp.userInfoResponse(artist, str_pass, False)
            validUser = True
            if obt_da_resp["response"].status == 500 or obt_da_resp["response"].status == 400:
                validUser = False
            if validUser:
                userInfo = getDLSUserInfo(obt_da_resp["data"])
                redis_connection = redis.Redis(connection_pool=profile_pool)
                redis_connection.set(artist.upper() + "-icon", userInfo["user_pic"])
                redis_connection.expire(artist.upper() + "-icon", 259200)
                sql = """INSERT INTO deviantcord.artist_info(artist, artist_picture_url) VALUES(%s, %s);"""
                artist_cursor = db_connection.cursor()
                artist_cursor.execute(sql, (artist, userInfo["user_pic"],))
                db_connection.commit()
                artist_cursor.close()
                jsonResponse = {}
                jsonResponse["result"] = "pass"
                jsonResponse["artist-name"] = artist.upper()
                jsonResponse["artist-icon"] = userInfo["user_pic"]
                jsresponse = json.dumps(jsonResponse)
                pscursor.close()
                putConnectionBack(db_connection)
                return jsresponse
            else:
                jsonResponse = {}
                jsonResponse["result"] = "no-artist-change"
                jsresponse = json.dumps(jsonResponse)
                pscursor.close()
                putConnectionBack(db_connection)
                return jsresponse

    else:
        jsonResponse = {}
        jsonResponse["result"] = "fail"
        jsresponse = json.dumps(jsonResponse)
        return jsresponse


@app.route('/get_token/<username>/<password>/<node_name>')
def get_token(username=None, password=None, node_name=None):
    db_connection = getConnection()
    login_cursor = db_connection.cursor()
    login_cursor.execute("SELECT * FROM deviantcord.deviant_accounts WHERE username = %s",(username,))
    results = login_cursor.fetchall()
    obt_password = results[0][1]
    obt_password_unhexed = binascii.unhexlify(obt_password)
    decryptor = PKCS1_OAEP.new(key)
    decrypted_given = decryptor.decrypt(obt_password_unhexed)
    decrypted = decryptor.decrypt(binascii.unhexlify(password))
    login_cursor.close()
    putConnectionBack(db_connection)
    if decrypted == decrypted_given:
        login_token = str(uuid.uuid1())
        rtokenconnection = redis.Redis(connection_pool=rpool, retry_on_timeout=True)
        rtokenconnection.set(login_token, node_name)
        rtokenconnection.expire(login_token,3600)
        rtokenconnection.close()

        jsonResponse = {}
        jsonResponse["result"] = "pass"
        jsonResponse["token"] = login_token
        jsresponse = json.dumps(jsonResponse)
        return jsresponse
    else:
        jsonResponse = {}
        jsonResponse["result"] = "fail"
        jsresponse = json.dumps(jsonResponse)
        return jsresponse

    login_cursor.close()




@app.route('/get_shard/<token>/<shard_type>')
def findNextShardID(token=None, shard_type=None):
    ttconnection = redis.Redis(connection_pool=rpool)
    token_result = ttconnection.get(token)
    ttconnection.close()
    if not token_result is None:
        max = shardData[shard_type][shard_type + "-max"]
        index = 0
        chosenid = 0
        lowest = 0
        while not index == max:
            index = index + 1
            if index == 1:
                lowest = shardData[shard_type][shard_type + "-1"]
                chosenid = index
            elif shardData[shard_type][shard_type + "-" + str(index)] < lowest:
                lowest = shardData[shard_type][shard_type + "-" + str(index)]
                chosenid = index
        responseData = {}
        responseData["results"] = "pass"
        responseData["chosen-id"] = chosenid
        response = json.dumps(responseData)
        shardData[shard_type][shard_type + "-" + str(chosenid)] = shardData[shard_type][shard_type + "-" + str(chosenid)] + 1
        saveFile = open("shard.json", "w+")
        saveFile.write(json.dumps(shardData, indent=4, sort_keys=True))
        saveFile.close()
    else:
        responseData = {}
        responseData["results"] = "fail"
        response = json.dumps(responseData)
    return response




if __name__ == '__main__':
    app.run(host="0.0.0.0")
