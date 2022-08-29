import re
import requests
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@127.0.0.1:3306/video'
db = SQLAlchemy(app)


def download(shortcode):
    # instagram的url视频地址
    url = f'https://www.instagram.com/p/{shortcode}/'

    print('获取视频下载链接中......')

    obj = re.compile('"props":{"media_id":"(?P<pk>.*?)"')

    proxies = {
        "https": "http://127.0.0.1:7890"
    }
    headers = {
        'X-IG-App-ID': '936619743392459',
        'Cookie': 'csrftoken=UcTWfv2NroJABRj4dIWfe38eRpb1CXU1; mid=YZIUAwALAAHIMaHw27iWm4uRNhXm; ig_did=267B8A84-7E4C-4AE8-8310-89537C6AE002; ig_nrcb=1; ds_user_id=48282355544; sessionid=48282355544%3AuWW0eZDfR8CL3u%3A27; datr=ZWq4YgmzX9ZT1JWqg_JKOBhe; dpr=1.25; shbid="12194\05448282355544\0541688611539:01f75d3a60c811bfcd880e4e8f3baefa76a97af80c8452eb788f385d096964b8d7380896"; shbts="1657075539\05448282355544\0541688611539:01f790a0918bea636a217097bd7087021d8198bf00f019bb8c87e02a0a702e02d87c1d7e"; rur="NAO\05448282355544\0541688617994:01f7c149d91540dacf8374476beca35130e516943a12ed01f4c487859acfb14033ca7907'
    }
    resp = requests.get(url, proxies=proxies, headers=headers)
    pk = obj.search(resp.text).group('pk')
    resp = requests.get(f"https://i.instagram.com/api/v1/media/{pk}/info/", proxies=proxies, headers=headers)
    url = resp.json()['items'][0]['video_versions'][0]['url']
    title = resp.json()['items'][0]['clips_metadata']['original_sound_info']['original_audio_title']
    taken_at = datetime.fromtimestamp(resp.json()['items'][0]['taken_at'])
    caption = resp.json()['items'][0]['caption']['text']
    print(url)

    print('获取成功！开始下载......')

    content = requests.get(url, proxies=proxies).content
    with open(f'video/{pk}.mp4', mode='wb') as f:
        f.write(content)

    print('下载成功！')

    comment_url = f'https://i.instagram.com/api/v1/media/{pk}/comments/?can_support_threading=true&permalink_enabled=false'
    resp_comment = requests.get(comment_url, proxies=proxies, headers=headers)
    comments = resp_comment.json()['comments']
    for comment in comments:
        Comments(id=comment['pk'], video_id=pk, profile_pic=comment['user']['profile_pic_url'], username=comment['user']['username'], comment_like_count=comment['comment_like_count'], child_comment_count=comment['child_comment_count'], text=json.dumps(comment['text']), created_at=datetime.fromtimestamp(comment['created_at'])).add()

    print('评论存入数据库成功！')

    Video(id=pk, title=title, caption=json.dumps(caption), video=content, taken_at=taken_at, create_time=datetime.now(), update_time=datetime.now()).add()

    print('视频存入数据库成功！')


class Result:
    def __init__(self, code, msg, data):
        self.code = code
        self.msg = msg
        self.data = json.loads(data)

    def resp(self):
        result = {
            'code': self.code,
            'msg': self.msg,
            'data': self.data
        }
        result_json = json.dumps(result, ensure_ascii=False)
        print('--返回结果--' + result_json)
        return result_json


class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.BIGINT, primary_key=True)
    video_id = db.Column(db.BIGINT)
    profile_pic = db.Column(db.VARCHAR)
    username = db.Column(db.VARCHAR)
    comment_like_count = db.Column(db.INT)
    child_comment_count = db.Column(db.INT)
    text = db.Column(db.TEXT)
    created_at = db.Column(db.DateTime)

    def __init__(self, id, video_id, profile_pic, username, comment_like_count, child_comment_count, text, created_at):
        self.id = id
        self.video_id = video_id
        self.profile_pic = profile_pic
        self.username = username
        self.comment_like_count = comment_like_count
        self.child_comment_count = child_comment_count
        self.text = text
        self.created_at = created_at

    def add(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)


def comments_convert(self):
    return {
        'id': str(self.id),
        'video_id': str(self.id),
        'profile_pic': self.profile_pic,
        'username': self.username,
        'comment_like_count': self.comment_like_count,
        'child_comment_count': self.child_comment_count,
        'text': json.loads(self.text),
        'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }


class Video(db.Model):
    __tablename__ = "resource"
    id = db.Column(db.BIGINT, primary_key=True)
    title = db.Column(db.VARCHAR)
    caption = db.Column(db.TEXT)
    video = db.Column(db.BLOB)
    taken_at = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)

    def __init__(self, id, title, caption, video, taken_at, create_time, update_time):
        self.id = id
        self.title = title
        self.caption = caption
        self.video = video
        self.taken_at = taken_at
        self.create_time = create_time
        self.update_time = update_time

    def add(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)

    def isExisted(self):
        video = Video.query.filter_by(id=self.id).first()
        if video is None:
            return 0
        else:
            return 1


def convert(self):
    return {
        'id': str(self.id),
        'title': self.title,
        'caption': json.loads(self.caption),
        'video': str(base64.b64encode(self.video)),
        'taken_at': self.taken_at.strftime("%Y-%m-%d %H:%M:%S"),
        'create_time': self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        'update_time': self.update_time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def caption_convert(self):
    return {
        'caption': json.loads(self.caption)
    }


@app.route("/")
def download_video():
    download('ChXhIAEj2Jt')
    return '<h1>Successfully Download!</h1>'


@app.route("/video")
def get_video():
    res = Video.query.filter_by().all()
    return Result(200, 'success', json.dumps(res, default=convert)).resp()


@app.route("/comments/<id>")
def get_comments(id):
    res = Comments.query.filter_by(video_id=id).all()
    return Result(200, 'success', json.dumps(res, default=comments_convert)).resp()


@app.route("/caption")
def get_caption():
    res = Video.query.filter_by(id=2853254463498529738).all()
    return Result(200, 'success', json.dumps(res, default=caption_convert)).resp()


@app.route("/latestVideo")
def get_latest_video():
    resp = requests.get('https://i.instagram.com/api/v1/users/web_profile_info/?username=alexandrmisko', headers={
        'X-IG-App-ID': '936619743392459',
        'Cookie': 'csrftoken=UcTWfv2NroJABRj4dIWfe38eRpb1CXU1; mid=YZIUAwALAAHIMaHw27iWm4uRNhXm; ig_did=267B8A84-7E4C-4AE8-8310-89537C6AE002; ig_nrcb=1; ds_user_id=48282355544; sessionid=48282355544%3AuWW0eZDfR8CL3u%3A27; datr=ZWq4YgmzX9ZT1JWqg_JKOBhe; dpr=1.25; shbid="12194\05448282355544\0541688611539:01f75d3a60c811bfcd880e4e8f3baefa76a97af80c8452eb788f385d096964b8d7380896"; shbts="1657075539\05448282355544\0541688611539:01f790a0918bea636a217097bd7087021d8198bf00f019bb8c87e02a0a702e02d87c1d7e"; rur="NAO\05448282355544\0541688617994:01f7c149d91540dacf8374476beca35130e516943a12ed01f4c487859acfb14033ca7907'
    }, proxies={
        "https": "http://127.0.0.1:7890"
    })
    typename = resp.json()['data']['user']['edge_owner_to_timeline_media']['edges'][3]['node']['__typename']
    shortcode = resp.json()['data']['user']['edge_owner_to_timeline_media']['edges'][3]['node']['shortcode']
    id = resp.json()['data']['user']['edge_owner_to_timeline_media']['edges'][3]['node']['id']
    if typename == 'GraphImage' or typename == 'GraphSidecar':
        return f'<h1>最新为图片或合集，视频无需更新</h1><a style="text-decoration:none;font-size:30px;color:orange" href="https://www.instagram.com/p/{shortcode}/">点此查看最新动态</a>'
    if Video(id, None, None, None, None, None, None).isExisted():
        return '<h1>视频已存在</h1>'
    else:
        download(shortcode)
        return f'<h1>视频更新完毕！</h1><h1 style="color:orange">typename: {typename}</h1><h1 style="color:#7FFFD4">shortcode: {shortcode}</h1>'


if __name__ == '__main__':
    app.run()
