import datetime
import polyline 
import folium
import pandas as pd
import numpy as np
from stravalib.client import Client
import os
import logging

from shapely import LineString
from shapely import frechet_distance
from shapely import geometry

log_directory = r'D:\Projects\Gar_to_Strav'
# log_file = os.path.join(log_directory, 'utils_log.log')
# logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')


gears_inverse={'Roubaix': 'b9512064'}
def create_name(strava_client,last_ride):
    day_limit=str(datetime.datetime.strptime(last_ride[0:10],"%Y-%m-%d")+datetime.timedelta(days=1))[0:10]
    logging.info(f'Day limit is {day_limit}')

    
    act_list=[]
    dist_lim=5
    elev_lim=20
    dist_buffer=0.02
    logging.info('We collect potential similar rides')
    for index,activity in enumerate(strava_client.get_activities(before=day_limit)): 
        activity=activity.dict()
        
        if activity['gear_id']==gears_inverse['Roubaix']:
            if index==0:
                NEW_RIDE=pd.json_normalize(activity)
                ROUTE=(NEW_RIDE['map.summary_polyline'].apply(polyline.decode)).apply(LineString)
                DISTANCE=NEW_RIDE['distance'][0]/1000
                ELEVATION=NEW_RIDE['total_elevation_gain'][0]
                # 
                logging.info(f'New ride distance is {DISTANCE} with {ELEVATION} meters of elevation')
                
                START=geometry.Point(NEW_RIDE['start_latlng'][0][0],NEW_RIDE['start_latlng'][0][1])
                RADIUS=START.buffer(dist_buffer)
                ID=NEW_RIDE['id'].values[0]
                # print(RADIUS)

            else: 
            
                if (DISTANCE-dist_lim < activity['distance']/1000 < DISTANCE+dist_lim) and (
                    ELEVATION-elev_lim < activity['total_elevation_gain'] < ELEVATION+elev_lim) and geometry.Point(
                        activity['start_latlng'][0],activity['start_latlng'][1]).within(RADIUS):
                    
                    logging.info(f"Activity called {activity['name']} with distance {activity['distance']/1000} could be similar")
                    act_list.append(activity)
        
                
                    

    act_df=pd.json_normalize(act_list)
    
    
    if act_df.empty:
        logging.info('This ride looks new!')
        return None
    else:
        logging.info(f"similar rides are : {act_df['name']}")

        #NEW VERSION
        act_df=act_df.sample(n=10,replace=True)
        act_df=act_df.drop_duplicates(subset=act_df.select_dtypes(exclude=object).columns)
        ###############
        #OLD VERSION
        # act_df=act_df.drop_duplicates(subset='name',keep='last')
        ############"
        
        act_df['ROUTE']=act_df['map.summary_polyline'].apply(polyline.decode)
        act_df['ROUTE_shp']=act_df['ROUTE'].apply(LineString)
        act_df=act_df[['name','ROUTE_shp']]
        act_df['distance']=act_df.apply(lambda x: frechet_distance(ROUTE[0],x['ROUTE_shp']),axis=1)
        
        #NEW VERSION
        act_df=act_df[act_df['distance']==act_df['distance'].min()]
        ###############
        
        if act_df['distance'].min()<=0.015:
            NAME=str(act_df[act_df['distance']==act_df['distance'].min()]['name'].values[0])
            logging.info(f'The ride will be named: {NAME}')

            # print(f'The ride will be named: {NAME}')
            return strava_client.update_activity(activity_id=ID,name=NAME)
        
        else :
            logging.info('This ride isn\'t quite like previous ones...')
            # print('This ride isn\'t quite like previous ones...')
            return None
            

