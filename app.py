from flask import Flask, request, render_template, send_file
import os
import googleapiclient.errors
from googleapiclient.discovery import build
from pytube import YouTube
import isodate
import pymongo

key = 'AIzaSyCCJ9m6UdyVio4tpTXBLteCouvdoxZkcso'

# link = "youtube.com/watch?v=JPHS10dt_CY&t=2s"

client = pymongo.MongoClient("mongodb+srv://ankushch997:A1dgjmptw@youtubecluster.affwkef.mongodb.net/?retryWrites=true&w=majority")
mydb = client.test

channel_info_col = mydb["Channel Database"]
video_col = mydb['Videos Collection']

ch_info = []

api_service_name = "youtube"
api_version = "v3"

youtube = build(api_service_name, api_version, developerKey=key)

app= Flask(__name__)

@app.route('/', methods= ['GET'])
def home():
  return render_template('index.html')

@app.route("/channel-info", methods=['POST'])
def chennel_info(): #Extracting channel details
  
  pyobj = YouTube(request.form['link'])
  global ch_id
  ch_id = pyobj.channel_id
  
  request1 = youtube.channels().list(
      part="snippet,contentDetails,statistics",
      id= ch_id,
      maxResults=50
  )
  response_channel = request1.execute() 

  for item in response_channel['items']:
    channel_name = item['snippet']['title']
    about = item['snippet']['description']
    subs = item['statistics']['subscriberCount']
    channel_thumb = item['snippet']['thumbnails']['medium']['url']
    ch_info.append({'channel_name': channel_name, 'about': about, 'subs': subs, 'channel_thumb': channel_thumb})
  
  channel_info_col.insert_many(ch_info)

  return render_template('Channel_info.html', ch_info = ch_info)

@app.route("/latest-videos", methods=['POST','GET'])
def video_list(): # Exctrating data of latest 50 videos

  request2 = youtube.activities().list(
      part="snippet,contentDetails",
      channelId= ch_id,
      maxResults=50
  )
  response_acvtivities = request2.execute()
  
  vid_list = []

  for item in response_acvtivities['items']:
    if 'playlistItem' in item['contentDetails']:
      videoID = item['contentDetails']['playlistItem']['resourceId']['videoId']
    else:
      videoID = item['contentDetails']['upload']['videoId']
    video_link = 'https://www.youtube.com/watch?v=' + videoID
    title = item['snippet']['title']

    vid_list.append({'videoID': videoID, 'video_link': video_link, 'title': title})

  vid_detail = []

  for item in vid_list:
    ID = item['videoID']
    request3 = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=ID
        )
    response_videos = request3.execute()

    views = response_videos['items'][0]['statistics']['viewCount']
    comment_count = response_videos['items'][0]['statistics']['commentCount']
    like_count = response_videos['items'][0]['statistics']['likeCount']
    dur = response_videos['items'][0]['contentDetails']['duration']
    duration = isodate.parse_duration(dur)
    thumb_url = response_videos['items'][0]['snippet']['thumbnails']['default']['url']
    vid_detail.append({'views': views, 'comment_count': comment_count, 'like_count': like_count, 'duration': str(duration), 'thumb_url': thumb_url})
  
  for i in range(0,len(vid_list)):
    vid_list[i].update(vid_detail[i])

  video_col.insert_many(vid_list)

  return render_template('Videos.html', vid_list= vid_list, vid_detail= vid_detail)

@app.route('/download/<vid>')
def download(vid):
  yt = YouTube('youtube.com/watch?v=' + vid) 

  mp4files = yt.streams.filter(file_extension='mp4') 

  d_video = yt.streams.get_highest_resolution() 
  path = d_video.download()
  return send_file(path, as_attachment=True)

@app.route('/comments/<com>')
def comments(com):
  request4 = youtube.commentThreads().list(
    part="snippet,replies",
    videoId= com
  )
  response_comment = request4.execute()

  comment_list = []

  for item in response_comment['items']:
    username = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
    comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
    comment_list.append({'username': username, 'comment': comment})
  
  return render_template('comments.html', comment_list = comment_list)


if __name__ == "__main__":
  app.run(debug= True, port= '5001')