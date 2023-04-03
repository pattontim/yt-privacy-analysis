# yt-privacy-analysis
Observe a youtube channel for video privacy status. The script will write and update a csv file with the privacy status of the videos, with a timestamp of when the status was checked and when it last changed.

## Usage
```
py yt-privacy.py --help
```

```
py .\yt-privacy.py "https://www.youtube.com/user/ANNnewsCH/videos" "--count" "2" "--ignore-new" 
```

## Requirements
- python
- pytube (in maintenance mode as of this writing, currently using [pytube-saguaro]( https://github.com/sluggish-yard/pytube-saguaro.git) fork