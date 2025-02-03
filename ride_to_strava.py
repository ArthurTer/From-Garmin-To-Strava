
import os
import logging
import sys
import subprocess
import glob
import re
import subprocess
import win32api
import win32file
from datetime import datetime
from stravalib.client import Client
from urllib.parse import urlparse,urlsplit
from datetime import datetime
import shutil
import time
import pickle as pkl
from dotenv import load_dotenv
from utils import create_name
load_dotenv()


# Configure logging
log_directory = r'D:\Projects\Gar_to_Strav'
log_file = os.path.join(log_directory, 'usb_device_event.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')


def main():
    logging.info('USB device connected')


if __name__ == "__main__":
    main()


# subprocess.call([sys.executable,r"D:\Projects\Gar_to_Strav\ride_to_strava.py"])



bike_activities=r"C:\Users\terli\Desktop\Tours de vélos\activités"

GARMIN=('', -1130943919, 255, 131590, 'FAT32')
drives=[f'{letter}:\\' for letter in 'EFGHIJKL']

CODE=os.getenv('CODE')
CLIENT_ID=os.getenv('CLIENT_ID')
CLIENT_SECRET=os.getenv('CLIENT_SECRET')
REFRESH_TOKEN=os.getenv('REFRESH_TOKEN')

redirect_url="https://localhost"
scope=['read_all','profile:read_all','activity:read_all','activity:write']
gears_inverse={'Roubaix': 'b9512064'}

def sorted_directory(dir):
    directory=(glob.glob(os.path.join(dir, '*.fit')))
    directory.sort(key=os.path.getmtime)
    return [f.split('\\')[-1] for f in directory]





logging.info('About to read in devices')

for drive in (win32api.GetLogicalDriveStrings()).split('\000')[:-1]:

    if win32api.GetVolumeInformation(drive)==GARMIN:
        logging.info(f'The drive is {drive}. Garmin has been found ')


        with open(r'D:\Projects\Gar_to_Strav\access_token.pkl', 'rb') as f:
            access_token = pkl.load(f)

        client=Client()

        if time.time() > access_token['expires_at']:

            refresh_response = client.refresh_access_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, refresh_token=access_token['refresh_token'])
            access_token = refresh_response
            with open(r'D:\Projects\Gar_to_Strav\access_token.pkl', 'wb') as f:
                pkl.dump(refresh_response, f)

            client.access_token = refresh_response['access_token']
            client.refresh_token = refresh_response['refresh_token']
            client.token_expires_at = refresh_response['expires_at']
            logging.info('refresh token is expired')

                
        else:
            client.access_token = access_token['access_token']
            client.refresh_token = access_token['refresh_token']
            client.token_expires_at = access_token['expires_at']
            logging.info('Token up to date')

        
        logging.info(f'Client connected')

        last_ride_file=open(r'D:\Projects\Gar_to_Strav\Last_ride.txt','r')
        last_ride=last_ride_file.read()+'.fit'
        last_ride_file.close()

        logging.info('The last ride occured on:')
        logging.info(str(last_ride.split('.')[0]))
        dir=(os.path.join(drive,'\Garmin\Activities'))


        sorted_dir=sorted_directory(dir)
        new_rides=sorted_dir[sorted_dir.index(last_ride)+1::]

        if len(new_rides)==0:
            logging.info('No new rides')
        else: 
            
            logging.info(f'New rides are {str(new_rides)}')


            for new_file in new_rides:
                last_ride_file=open(r'D:\Projects\Gar_to_Strav\Last_ride.txt','r')
                last_ride=last_ride_file.read()+'.fit'
                last_ride_file.close()

                logging.info(f'most recent to be uploaded is {new_file}')

                new_ride=datetime(*map(int,(((new_file.split('.'))[0]).split('-'))))

                past_ride=datetime(*map(int,(((last_ride.split('.'))[0]).split('-'))))

                if past_ride.date()<new_ride.date():
                    logging.info(f'{new_file} is more recent than {past_ride}')

                    shutil.copyfile(os.path.join(dir,new_file),os.path.join(bike_activities,new_file))
                    with open(r'D:\Projects\Gar_to_Strav\Last_ride.txt','w') as text_file:
                        text_file.write(new_file.split('.')[0])


                    activity_file=open((os.path.join(dir,new_file)), 'rb')
                    logging.info('The upload will start')
                    upload=client.upload_activity(activity_file=activity_file,data_type='fit',name=None,activity_type='ride')
                    
                    
                    time.sleep(5)
                    logging.info(upload.status)
                    logging.info('Naming starts')
                    last_ride_file=open(r'D:\Projects\Gar_to_Strav\Last_ride.txt','r')
                    last_ride=last_ride_file.read()+'.fit'
                    last_ride_file.close()
                    
                    create_name(strava_client=client,last_ride=last_ride)
                    
                    text_file.close()
                    activity_file.close()
                else: 
                    last_ride_file.close()
                    logging.info('No recent rides encountered')
    else: 
        logging.info(f'Drive {drive}. The Garmin hasn\'t been found')




