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


def download():
    # instagram的url视频地址
    url = 'https://www.instagram.com/p/Chb-KVrohbb/'

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
    print(url)

    print('获取成功！开始下载......')

    content = requests.get(url, proxies=proxies).content
    with open(f'video/{pk}.mp4', mode='wb') as f:
        f.write(content)

    print('下载成功！')

    Video(pk, content, datetime.now(), datetime.now()).add()

    print('存入数据库成功！')


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


class Video(db.Model):
    __tablename__ = "resource"
    id = db.Column(db.INT, primary_key=True)
    video = db.Column(db.BLOB)
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)

    def __init__(self, id, video, create_time, update_time):
        self.id = id
        self.video = video
        self.create_time = create_time
        self.update_time = update_time

    def add(self):
        db.session.add(self)
        db.session.commit()


def convert(self):
    return {
        'id': self.id,
        'video': str(base64.b64encode(self.video)),
        'create_time': self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        'update_time': self.update_time.strftime("%Y-%m-%d %H:%M:%S")
    }


@app.route("/")
def find_video():
    # download()
    res = Video.query.filter_by().all()
    return Result(200, 'success', json.dumps(res, default=convert)).resp()


if __name__ == '__main__':
    app.run()
