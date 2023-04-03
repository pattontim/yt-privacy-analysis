import json
import datetime
import time
from pytube import Channel, YouTube, exceptions
import random
import socket
import argparse

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


def write_data_to_json(file_name, video_data):
    """Write video data to JSON file"""
    write_json_data(file_name, video_data)

def normal_video_data(video, video_url, max_retries=10):
    for i in range(max_retries):
        try:
            title = video.title
            publish_date = str(video.publish_date)
            keywords = video.keywords
            description = video.description
            length = video.length

            return {'title': title, 'upload_time': publish_date, 'keywords': keywords,
                    'description': description, 'length': length}
        except exceptions.PytubeError as e2:
            print(f'Failed to retrieve video data for {video_url}: {e2}')
            # Implement Gaussian step-back algorithm, 8, 8, 16, 16, 32, 32, 48 ...
            sleep_time = 4 + random.gauss(2, 0.5) * ((i+1)*2)
            time.sleep(sleep_time)
            video = YouTube(video_url)
    else:
        print(f'==== Completely failed to retrieve video data for {video_url} after {max_retries} retries. ====')
        return {}

video_errors = (exceptions.VideoPrivate, exceptions.VideoUnavailable, exceptions.VideoRegionBlocked, exceptions.AgeRestrictedError) 

# Define field names for video data
field_names = ['url', 'title', 'upload_time', 'keywords', 'privacystatus',
               'last_updated', 'timestamp', 'description', 'length']

def main(args):
    channel_data = load_json_data(args.input)

    if not args.ignore_new:
        new_channel_vidurls = {channel : { url:{} for url in Channel(channel).video_urls[:args.count]} for channel in args.channels}
        new_channels_urls_pairs = [(channel, key) for channel, value in new_channel_vidurls.items() for key in value.keys()]
    else:
        new_channels_urls_pairs = []

    channels_urls_pairs = [(channel, key) for channel, value in channel_data.items() for key in value.keys()]
    merged_channels_urls = set(channels_urls_pairs).union(set(new_channels_urls_pairs))

    failed = []

    for channel, video_url in merged_channels_urls:
        video = YouTube(video_url)
        video_data = channel_data.setdefault(channel, {})
        timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        privacystatus = None
        try:
            video.check_availability()
        except video_errors as e:
            privacystatus = type(e).__name__

            update_video_data(video_data, video_url, timestamp=timestamp, privacystatus=privacystatus)
        else:
            retrieved = normal_video_data(video, video_url, max_retries=args.max_retries)
            if retrieved:
                update_video_data(video_data, video_url, timestamp=timestamp, **retrieved)
                # OR
                # update_video_data(video_data, video_url, title=title,
                #             keywords=keywords, description=description, length=length,
                #             upload_time=str(publish_date))
            else:
                failed.append((channel, video_url))
                continue

        if privacystatus is not None and video_data[video_url].get('last_updated', None) is None:
            update_video_data(video_data, video_url, last_updated=timestamp)
        else:
            update_video_data(video_data, video_url, timestamp=timestamp)

    write_data_to_json(args.output, channel_data)

    if failed:
        # load failed data and append to it, if it exists
        failed_data = load_json_data('failed.json')
        failed_data.update(failed)
        write_data_to_json('failed.json', failed_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='YouTube privacy status checker')
    parser.add_argument('channels', nargs='+', help='YouTube channel URLs')
    parser.add_argument('--count', type=int, default=10, help='Number of videos to check (per channel)')
    parser.add_argument('--max-retries', type=int, default=10, help='Maximum number of retries for retrieving video data')
    parser.add_argument('--input', default='video_data.json', help='Input file name')
    parser.add_argument('--output', default='video_data.json', help='Output file name')
    parser.add_argument('--ignore-new', action='store_true', help='Ignore new videos and only check existing')
    args = parser.parse_args()

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

    main(args)
