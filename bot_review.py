import re
import libmstdn
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import time
import MeCab
import itertools
import collections


#mastodon ホスト
#注意 "https://"をつけずホスト名のみを記述する
HOST = "***"

#Mastodon APIアクセストークンを取得して以下のTOKENに代入する
#Mastodon のサイトで登録を行う.ログイン後[設定]->[開発]->[新規アプリ]
TOKEN = "***"

def remove_html_tags(content):
    return re.sub("<[^>]*>", "", content).strip()

def is_to_me(status, my_id):
    for mention in status["mentions"]:
        if mention["id"] == my_id:
            return True
        return False

#青空文庫から文書の取得
def get_text(id_num):
    time.sleep(1) #HPへのDos対策
    res = requests.get("http://pubserver2.herokuapp.com/api/v0.1/books/"+ str(id_num) +"/content?format=html")
    soup = BeautifulSoup(res.content,"html.parser")
    title = soup.find("title").text
    doc = soup.find("div",{"class":"main_text"}).text
    return title,doc


#文書の品詞分類
def word_analysis(doc):
    m = MeCab.Tagger("-Ochasen")
    node = m.parseToNode(doc)
    meishi_list = []
    doshi_list = []
    keiyoshi_list = []
    while node:
        hinshi = node.feature.split(",")[0]
        if hinshi == "名詞":
            meishi_list.append(node.surface)
        elif hinshi == "動詞":
            doshi_list.append(node.feature.split(",")[6])        
        elif hinshi == "形容詞":
            keiyoshi_list.append(node.feature.split(",")[6])        
        node = node.next
    return pd.Series([list(set(meishi_list)), list(set(doshi_list)), list(set(keiyoshi_list))])

#レビューのわかち書き
def review_list(num):
    tagger = MeCab.Tagger("-Owakati")
    str_output = tagger.parse(num)
    list_output = str_output.split(' ')
    return list_output

def generate_reply(status, my_name):
    received_text = remove_html_tags(status["content"])
    toot_from = status["account"]["username"]
    if "こんにちは" in received_text:
        return toot_from + "さんこんにちは! \n 研究で忙しくなる前に，のんびり芥川龍之介の作品を読んでみるのはいかがですか？ "
    elif "こんばんは" in received_text:
        return toot_from + "さんこんばんは!\nこんな夜には「春の夜」がお勧めですよ！"
    elif "はじめまして" in received_text:
        return toot_from + "さん,はじめまして!\n私は"+ my_name +"です！\n 芥川龍之介の本のタイトルとレビューを呟いてくれたら，レビューに対してのアドバイスを行います"
    else:
        received_context = received_text.replace("***","")

        if " 「" in received_text:
            
            checktitle = re.findall('「(.*)」', received_context) #本のタイトルを取得
            checktitle = "".join(checktitle)
            res = requests.get("https://www.aozora.gr.jp/index_pages/person879.html")
            soup = BeautifulSoup(res.content,"html.parser")
            ol_data = soup.find("ol").text

            id_list = re.findall("新字新仮名、作品ID：[0-9]+",ol_data)
            id_list = [i.split("：")[1] for i in id_list]
            #print(id_list)
            doc_list = []
            for i in id_list:
                title,doc = get_text(i)
                doc_list.append([title,doc])
            df_doc = pd.DataFrame(doc_list,columns=["作品名","本文"])
            m = MeCab.Tagger("-Ochasen")
            df_doc[["名詞","動詞","形容詞"]] = df_doc["本文"].apply(word_analysis)
            df_select = df_doc[df_doc.作品名.str.contains(checktitle, na=False)]

            #ランキング
            words = list(itertools.chain.from_iterable(df_select["名詞"]))
            #print(words)
            words_double = [] #2文字以上の単語を保存
            for w in words:
                    if len(w) > 1:
                            words_double.append(w)

            c = collections.Counter(words_double)
            print(c.most_common(10))
            
            word, counts = zip(*c.most_common(10))
            review = re.findall('」(.*)', received_context) #本のレビューを取得
            review = "".join(review)
            print(review)
            tagger = MeCab.Tagger("-Owakati")
            str_output = tagger.parse(review)
            list_output = str_output.split(' ')
            print(list_output)
            
            #if   len(set(book_sort) - set(review)) == 0:
            if len(set(word)- set(list_output)) == 0:
                return  "いい作品ですよね〜。\n私もいい感じのレビューだと思いますよ！"
            else:
                return  "いい作品ですよね〜。\nもしよかったら、以下のことについて触れてみるのはいかがですか？\n「"+ '・'.join(set(word) - set(list_output))+ "」"
        else:
            return "ごめんなさい。そのタイトルでは、よくわかりません.「」で囲んでもらえたらできるかもしれません。c"
        
#main

api = libmstdn.MastodonAPI(mastodon_host=HOST,access_token=TOKEN)

account_info = api.verify_account()
my_id =account_info["id"]
my_name = account_info["username"]
print("Started bot, name: {}, id: {}".format(my_name,my_id))

stream = api.get_user_stream()
for status in stream:
    if is_to_me(status,my_id):
        received_text = remove_html_tags(status["content"])
        toot_id = status["id"]
        toot_from = status["account"]["username"]
        print("received from {}: {}".format(toot_from,received_text))

        reply_text = "@{} {}".format(toot_from,generate_reply(status,my_name))
        api.toot(reply_text,toot_id)
        print("post to {}: {}".format(toot_from,reply_text))
