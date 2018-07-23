# -*- coding:utf-8 -*-
import Levenshtein
import requests
from bs4 import BeautifulSoup as bs
import re
from snownlp import SnowNLP
import json
import csv
import os
from gensim.models import word2vec
from gensim.models.word2vec import Word2Vec
import os
import logging
import sys

def word2vec_name(definite_dict,unsure_dict):
    #gensim 的 word2vec 词向量比对，准确率比较低，不做优化的情况下不推荐使用
    reload(sys)
    sys.setdefaultencoding('utf8')
    logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', level=logging.INFO)
    # sentences = word2vec.Text8Corpus(u"/home/hadoopnew/270万评论crf分词结果")
    # model = word2vec.Word2Vec(sentences, size=100)
    #  加载语料并训练模型
    model = Word2Vec.load('/home/hadoopnew/桌面/word2vec_270w_mymodel')
    # 直接使用已有模型
    print model
    actor_total_dict = {}
    for i in  unsure_dict:
        max = 0.0
        key = ''
        for j in definite_dict:
            try:
                value = model.similarity(i[5:].decode('utf-8'), j.decode('utf-8'))
            except KeyError:
                continue
            if max < value:
                max = value
                key = j
        if max > 0.7:
            print i[5:], definite_dict[key],key,max
            actor_total_dict.update({i[5:]: definite_dict[key]})
        # else :
        #     print i[5:]
    return actor_total_dict
def load_actor_role_dict():
    #fc = open('/home/hadoopnew/下载/douban_actor_data.txt', 'r')#原文件
    # fc = open('/home/hadoopnew/下载/展示电影演员角色对应.txt', 'r')#展示文件
    fc = open('/home/hadoopnew/下载/cbo_actor_role')#Seeing_future
    """
    文件格式如下：
    电影id,演员名，角色名
    641515,余男,龙小云,
    641515,吴京,冷锋,
    """
    movie_actor={}
    for line in fc.readlines():
        line = line.replace(',','\001')
        actor_role_dict = {}
        movie_name = line.split('\001')[0]
        # movie_name = line.split('\001')[1]源文件
        actor = line.split('\001')[1]
        role = line.split('\001')[2].strip()
        actor_role_dict.update({actor:actor})
        #if role != '\N':#原文件格式
        # if role != 'None':#展示文件格式
        if role != '':
            actor_role_dict.update({role: actor})
        if not movie_actor.has_key(movie_name):
            movie_actor.update({movie_name:actor_role_dict})
        else:
            movie_actor[movie_name].update(actor_role_dict)
    return movie_actor
def jaccard(p,q):
    #计算jaccard距离
    c = [i for i in p if i in q]
    return float(len(c))/(len(p)+len(q)-len(c))
def web_page(name,movie,actor_total_dict):
    #使用搜索引擎识别人名与演员对应关系，实际效果一般
    # print name
    relevant = {}
    str = '演艺圈谁叫'+name
    url = 'http://www.baidu.com/s?wd='+str.decode('utf-8')
    r = requests.get(url)
    soup = bs(r.content, "html.parser")
    main_content =  soup.find("div",id = "content_left").get_text()
    reg1 = re.compile("<[^>]*>")
    content = reg1.sub('', main_content)
    # urls = soup.find_all(name='a', attrs={'href': re.compile(('.'))})
    content =  content.replace("\n","").replace(" ","").replace("\t","")
    # print content
    array = re.findall(r"......."+name.decode('utf-8')+"........",content)
    for i in array:
        for aname in actor_total_dict:
            if aname in i.encode('utf-8') :
                relevant.update({name:aname})
    return relevant
def json_save(actor_total_dict,movie):
    fs = open("/home/hadoopnew/桌面/movie_actor_nick_2018/"+movie+".json", 'w')
    with open("/home/hadoopnew/桌面/movie_actor_nick_2018/"+movie+".json",'w') as f:
        json.dump(actor_total_dict,f)
def get_hanlp_result():
    fs = open("/home/hadoopnew/桌面/人名序列Seeing_future", 'r')
    """
    文件格式如下：
    电影id与人名序列以\t分隔，不同算法人名序列（此处有hmm，crf的专有名词序列hmmnz和crfnz以及hmm,crf的人名序列hmmnr和crfnr）以\002分隔，
    人名序列之间以\001分隔，电影与电影之间以\n分隔
    346818	hmmnr王大爷hmmnr吴秀波hmmnr米国crfnr吴修博
    346810  hmmnr李丽crfnr吴修博
    """
    movie_dict = {}
    for line in fs.readlines():
        m = line.strip("\n")
        movie = m.split("\t")[0]
        names = m.split("\t")[1].split("\002")
        hmmnr = names[0].split("\001")
        hmmnz = names[1].split("\001")
        crfnr = names[2].split("\001")
        crfnz = names[3].split("\001")
        list = [hmmnr,hmmnz,crfnr,crfnz]
        movie_dict.update({movie:list})
    return movie_dict
def Similarity(definite_dict,unsure_dict):
    actor_total_dict = {}
    for i in definite_dict:
        for j in unsure_dict:
            # 最小编辑距离
            print j
            if Levenshtein.distance(j[5:].decode('utf-8'), i.decode('utf-8')) <= 1:
                print j[5:]
                print Levenshtein.distance(j[5:].decode('utf-8'), i.decode('utf-8'))
                actor_total_dict.update({j[5:]: definite_dict[i]})
                # jaccard 距离，效果不是很好
            # else :
            #     if jaccard(j[5:], i) > 0.7:
            #         print j[5:]
            #         print jaccard(j[5:], i)
            #         actor_total_dict.update({j[5:]: definite_dict[i]})
    return actor_total_dict

if __name__ == '__main__':

    actor_role_dict = load_actor_role_dict()
    #加载演员名-角色名字典
    movie_dict = get_hanlp_result()
    #取得hanlp分词结果
    for i in movie_dict:
        #对每部电影进行人名识别
        print i
        if actor_role_dict.has_key(i):
            actor_total_dict = {}
            actor_total_dict = Similarity(actor_role_dict[i],movie_dict[i][2])
            actor_total_dict.update(Similarity(actor_role_dict[i], movie_dict[i][3]))
            actor_total_dict.update(actor_role_dict[i])
            # for j in actor_total_dict:
            #     print j,actor_total_dict[j]
            # print i
            json_save(actor_total_dict,i)
