#!/usr/bin/env python
# importing necessary libraries
import pika
import json
from pytemperature import k2f
import urllib.request, json

appid_key = "e125e10d5beec79d36fd71a90cdc590c"

# establishing connection to RabbitMQ server
credentials = pika.PlainCredentials( username = 'guest' , password = 'guest' )
connection = pika.BlockingConnection( pika.ConnectionParameters(
            host = 'message-broker' , port = 5672 , credentials = credentials ) )
channel = connection.channel()

# declaring sending queue
channel.queue_declare( queue = 'model_execution_2_post_processing' )

def forecasting( user_data ) :
    user_data_x = user_data[ "User" ]
    user_data_list = user_data_x.split( )
    # for forecasting weather
    user_url = "http://api.openweathermap.org/data/2.5/forecast?q=" + user_data_list[ 0 ] + "," + user_data_list[ 1 ] + "," + user_data_list[ 2 ] + "&appid=" + appid_key
    with urllib.request.urlopen( user_url ) as url:
        # load the website to dictionary
        data = json.loads( url.read( ).decode( ) )
    forecast = [  ]
    # filtering the forecast data got from the api call
    # 1 here implies every 3 hours data
    for i in range( 1 ) :
        # make a temporary dictionary
        # which stores all the important values as dictionary elements
        temp = { }
        curr_dir = data[ "list" ][ i ]
        temp[ "temp" ] = k2f( curr_dir[ "main" ][ "temp" ] )
        temp[ "temp_min" ] = k2f( curr_dir[ "main" ][ "temp_min" ] )
        temp[ "temp_max" ] = k2f( curr_dir[ "main" ][ "temp_max" ] )
        temp[ "humidity" ] = curr_dir[ "main" ][ "humidity" ]
        temp[ "weather" ] = curr_dir[ "weather" ][ 0 ][ "main" ]
        temp[ "wind_speed" ] = curr_dir[ "wind" ][ "speed" ]
        temp[ "date_time" ] = curr_dir[ "dt_txt" ]
        forecast.append( temp )
    # returning complete list of forecast which has all elements as dictionary
    return forecast

def callback( ch , method , properties , body ) :
    # making it dictionary
    body = json.loads( body )
    forecast_data = forecasting( body )
    # making dictionary with all elements from prevous and current to one dictionary
    all_data = { "Forecast" : forecast_data , "Processing" : body[ "Processing" ] }
    # calling the sending process
    channel.basic_publish( exchange = '' , routing_key = 'model_execution_2_post_processing' , body = json.dumps( all_data ) )
    connection.close( )

while True :
    channel.basic_consume(
        queue = 'data_retrieval_2_model_execution' , on_message_callback = callback , auto_ack = True )
    channel.start_consuming( )
    print( "Model Executed" )
    connection = pika.BlockingConnection( pika.ConnectionParameters(
                host = 'message-broker' , port = 5672 , credentials = credentials ) )
    channel = connection.channel( )
