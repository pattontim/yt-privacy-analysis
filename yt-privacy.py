import json
import datetime
import time
from pytube import Channel, YouTube, exceptions
import random
import socket

ip_address = socket.gethostbyname('www.youtube.com')

while True:
    try:
        s = socket.create_connection((ip_address, 80), timeout=5)
        s.close()
        print("Connected to YouTube successfully.")
        break
    except OSError:
        print("Unable to connect to YouTube. Retrying in 10 seconds.")
        time.sleep(10)

channel = Channel('https://www.youtube.com/user/ANNnewsCH/videos')

def load_json_data(file_name):
    """Load JSON data from file"""
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def write_json_data(file_name, data):
    """Write JSON data to file"""
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=2)


def update_video_data(video_data, video_url, **kwargs):
    """Update video data"""
    if video_url not in video_data:
        video_data[video_url] = {}
    video_data[video_url].update(kwargs)


def write_video_data_to_json(file_name, video_data):
    """Write video data to JSON file"""
    write_json_data(file_name, video_data)

video_errors = (exceptions.VideoPrivate, exceptions.VideoUnavailable, exceptions.VideoRegionBlocked, exceptions.AgeRestrictedError) 

# Define field names for video data
field_names = ['url', 'title', 'upload_time', 'keywords', 'privacystatus',
               'last_updated', 'timestamp', 'description', 'length']

# Load video data from JSON file
video_data = load_json_data('video_data.json')

# Set max retries for retrieving video data
max_retries = 10

videos = set(channel.video_urls[:3])
videos.update(video_data.keys())

# private and non-private videos
# videos = ["https://www.youtube.com/watch?v=deULZrx1FxE", "https://www.youtube.com/watch?v=GddMUiqbx7s"]

for video_url in videos:
    video = YouTube(video_url)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    privacystatus = None
    try:
        video.check_availability()
    except video_errors as e:
        privacystatus = type(e).__name__

        update_video_data(video_data, video_url, timestamp=timestamp, privacystatus=privacystatus)
    else:
        for i in range(max_retries):
            try:
                video = YouTube(video_url)
                title = video.title
                publish_date = video.publish_date
                keywords = video.keywords
                description = video.description
                length = video.length
                update_video_data(video_data, video_url, title=title,
                                  keywords=keywords, description=description, length=length,
                                  upload_time=str(publish_date))
                break
            except exceptions.PytubeError as e2:
                print(f'Failed to retrieve video data for {video_url}: {e2}')
                # Implement Gaussian step-back algorithm, 8, 8, 16, 16, 32, 32, 48 ...
                sleep_time = 4 + random.gauss(2, 0.5) * ((i+1)*2)
                time.sleep(sleep_time)
        else:
            print(f'Failed to retrieve video data for {video_url} after {max_retries} retries.')
            continue

    if privacystatus is not None and video_data[video_url].get('last_updated', None) is None:
        update_video_data(video_data, video_url, last_updated=timestamp)
    else:
        update_video_data(video_data, video_url, timestamp=timestamp)

write_video_data_to_json('video_data.json', video_data)