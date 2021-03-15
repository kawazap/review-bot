# review-bot

ここでは、プログラムの実行手順を紹介しておきます。実際の動作画面は、Wikiに掲載しておきます。
Mastodon上で行うことに注意してください。(私は、大学の先生が用意したサーバ上で建てられたMastodonで行ったため、他の環境ではうまくいかない可能性もあります。予めご了承ください。)

## Tutorial
+ 実行環境
 - [x] Python 3.7.3 64-bit(conda) 

+ Mastdonの設定
```
bot用に用意したアカウントのアクセストークンと、ユーザ名を確認しておく。
```

+ Build
```
$ git clone git@github.com:kawazap/review-bot.git
$ cd review-bot
```

+ プログラムの変更
```
#mastodon ホスト
#注意 "https://"をつけずホスト名のみを記述する
HOST = "***"
***には、使用するMastodonのURLをhttps://を抜かして記載する。

#Mastodon APIアクセストークンを取得して以下のTOKENに代入する
#Mastodon のサイトで登録を行う.ログイン後[設定]->[開発]->[新規アプリ]
TOKEN = "***"
***には、APIアクセストークンを記載．
```
+ プログラムの実行
```
python3 bot_review.py
```
