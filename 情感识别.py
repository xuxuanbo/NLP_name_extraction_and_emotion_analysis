# -*- coding: utf-8 -*-
from snownlp import SnowNLP
import MySQLdb
import json
import os
from snownlp import sentiment
import re
def get_train_data_from_database():
    conn = MySQLdb.connect(host='localhost', user='root', passwd='1601', db='TEST', charset="utf8")
    cur = conn.cursor()
    cur.execute("select DISTINCT content from douban_comment where score = 50")
    fs = open("/home/hadoopnew/pos.txt", 'a')
    items = cur.fetchall()
    for item in items:
        fs.write(item[0].strip()+'\n')
    cur.execute("select DISTINCT content from douban_comment where score = 10")
    fs = open("/home/hadoopnew/neg.txt", 'a')
    items = cur.fetchall()
    for item in items:
        fs.write(item[0].strip()+'\n')

def test_train_data():
    conn = MySQLdb.connect(host='localhost', user='root', passwd='1601', db='TEST', charset="utf8")
    cur = conn.cursor()
    cur.execute("select DISTINCT content from douban_comment where score = 50 ")
    # fs = open("/home/hadoopnew/pos.txt", 'a')
    items = cur.fetchall()
    total = 0
    correct = 0
    for item in items:
        if item[0].strip() == '':
            continue
        total += 1

        s = SnowNLP(item[0].strip())
        if s.sentiments > 0.5 :
            # print item[0].strip() ,s.sentiments
            correct += 1
    cur.execute("select DISTINCT content from douban_comment where score = 10 ")
    fs = open("/home/hadoopnew/neg.txt", 'a')
    items = cur.fetchall()
    for item in items:
        if item[0].strip() == '':
            continue
        total += 1
        # print item[0].strip(),'!!'
        s = SnowNLP(item[0].strip())
        if s.sentiments < 0.5:
            # print item[0].strip(), s.sentiments
            correct+=1
    accuracy = float(correct)/float(total)
    print accuracy
    #此处为打印准确率

def get_data_from_h32_db():
    conn = MySQLdb.connect(host='192.168.1.102', user='root', passwd='hadoop', db='movie', charset="utf8")
    cur = conn.cursor()
    cur.execute("select DISTINCT * from douban_comment where movie_id = 26698897 or movie_id = 26861685")
    items = cur.fetchall()
    return items

def get_data_from_iiip_db():
    conn = MySQLdb.connect(host='192.168.235.55', user='root', passwd='iiip', db='Seeing_future', charset="utf8")
    cur = conn.cursor()
    cur.execute("select * from douban_comment")
    items = cur.fetchall()
    return items

def train_model():
    #自行百度如何训练snownlp模型，实验室的同学请自己在实验室电脑里拿数据，github上没有
    from snownlp import sentiment
    sentiment.train('/home/hadoopnew/neg.txt', '/home/hadoopnew/pos.txt')
    sentiment.save('sentiment.marshal_knee')

def get_movie_name(movie_id):
    if not os.path.exists("/home/hadoopnew/桌面/movie_actor_nick_2018/"+movie_id+".json"):
        return None,None
    with open("/home/hadoopnew/桌面/movie_actor_nick_2018/"+movie_id+".json",'r') as f:
        # 这个以电影id为名称的json文件中存储着有关该部电影的演员与人名的对应关系，如唐人街探案 {“刘昊然”：“然然”，“刘昊然”：“老秦”}
        actor_total_dict =json.load(f)
    actor_score = {}
    for i in actor_total_dict:
        if not actor_score.has_key(actor_total_dict[i]):
            actor_score.update({actor_total_dict[i]:0})
    return actor_total_dict,actor_score

def comment_emotion_recogize(str):
    # print str
    try:
        s = SnowNLP(str.decode('utf-8'))
    except:
        print str
        return 0
    return s.sentiments-0.5
    #主要为了直观体现评论是正向还是负向，这样做分数范围是（-0.5,0.5）

if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    items = get_data_from_iiip_db()
    movie_actor_dict = {}
    movie_score_dict = {}
    for i in items:
        # print i[5]
        movie_id = str(i[0])
        short_sentence = re.split(r'，|。|；|？|…|！',str(i[5]).strip())
        #将长句切割为短句
        tmp = {}
        if not movie_actor_dict.has_key(movie_id):
            actor_total_dict,actor_score = get_movie_name(movie_id)
            movie_actor_dict.update({movie_id:actor_total_dict})
            movie_score_dict.update({movie_id:actor_score})
        else :
            actor_total_dict = movie_actor_dict[movie_id]
            actor_score = movie_score_dict[movie_id]
        if actor_total_dict == None:
            continue
        total_score = comment_emotion_recogize(str(i[5]))
        #对一整个句子进行情感识别
        for ss in short_sentence:
            if ss == '':
                continue
            ss_score = comment_emotion_recogize(ss)
            #对短句进行情感识别

            for actor_name in actor_total_dict:
                if actor_name in ss:
                    if not tmp.has_key(actor_total_dict[actor_name]):
                        tmp[actor_total_dict[actor_name]] = ss_score
                    else :
                        if tmp[actor_total_dict[actor_name]] < ss_score:
                            tmp[actor_total_dict[actor_name]] = ss_score

        for j in tmp:
            j_actor_score = tmp[j]*0.8 + total_score*0.2
            #得分加和
            if movie_score_dict[movie_id].has_key(j):
                #演员已有得分情况，则将分数与原有分数相加
                movie_score_dict[movie_id][j] += j_actor_score
            else:
                #演员未有得分情况，赋给演员此评论得分
                movie_score_dict[movie_id][j] = j_actor_score
            #将评分赋给演员
    for i in movie_score_dict:

        if movie_score_dict[i] == None:
            continue
        fs = open("/home/hadoopnew/桌面/movie_actor_score_2018/" + i + ".json", 'w')

        with open("/home/hadoopnew/桌面/movie_actor_score_2018/" + i + ".json", 'w') as f:
            #将得分情况以字典形式存入json
            json.dump(movie_score_dict[i], f)
        for j in movie_score_dict[i]:
            print j,movie_score_dict[i][j]
            # comment_emotion_recogize(ss)
