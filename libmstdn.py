
import json
import requests


class MastodonAPIError(Exception):
    """ MastodonAPIのエラー """
    
    def __init__(self, message, http_status=None):
        """
        初期化
        
        Args:
            message (str): 例外メッセージ
            http_status (int): HTTPステータスコード
        """

        if http_status is not None:
            message = "http_status: {}, response: {}".format(
                http_status, message)
        else:
            message = "response: {}".format(message)

        super(MastodonAPIError, self).__init__(message)


class MastodonStream:
    """ Mastofonのストリームを受信するクラス """

    def __init__(self, url, access_token=None):
        """
        初期化
        
        Args:
            url (str): ストリームAPIのURL
            access_token (str): APIのアクセストークン
        """
        self.__url = url
        self.__access_token = access_token

    def __connect(self):
        """ ストリームに接続 """
        headers = {}
        if self.__access_token is not None:
            headers["Authorization"] = "Bearer " + self.__access_token

        self.__stream = requests.get(self.__url, headers=headers, stream=True)

        if self.__stream.status_code != 200:
            raise MastodonAPIError(
                self.__stream.text, self.__stream.status_code)

        self.__stream_gen = self.__stream.iter_lines()
        self.__event_type = ""

    def __iter__(self):
        """ ストリームデータを取得するイテレータを取得する """
        self.__connect()
        return self
    
    def __next__(self):
        """
        次のストリームデータを取得する
        
        この関数は，次のデータを受信するまで待機する．
        また，データは1行ごとに返される．
        
        Returns:
            str: 取得されたデータ
        """

        while True:
            try:
                line = next(self.__stream_gen).decode("utf-8").strip()
            except StopIteration:
                # 接続が切れたときは再接続する
                self.__connect()
                continue

            line_kv = [d.strip() for d in line.split(":", 1)]
            if len(line_kv) < 2:
                continue
            line_key = line_kv[0]
            line_value = line_kv[1]
            
            if line_key == "event":
                self.__event_type = line_value
            elif line_key == "data":
                if self.__event_type == "update":
                    return json.loads(line_value)
                elif self.__event_type == "notification":
                    return json.loads(line_value)["status"]
            else:
                pass


class MastodonAPI:
    """ MastodonのAPIを叩くクラス """

    def __init__(self, mastodon_host, access_token):
        """
        初期化
        
        Args:
            mastodon_host (str): Mastodonインスタンスのホスト名
            access_token (str): APIのアクセストークン
        """
        self.__host = mastodon_host
        self.__access_token = access_token
    
    def verify_account(self):
        """
        アカウント情報を取得
        
        Returns:
            dict: アカウント情報を格納したdict
        """
        url = "https://{}/api/v1/accounts/verify_credentials".format(self.__host)
        resp = requests.get(url, headers=self.__auth_header(), timeout=10)
        if resp.status_code != 200:
            raise MastodonAPIError(resp.text, resp.status_code)
        return resp.json()
    
    def toot(self, status, in_reply_to_id=None):
        """
        トゥートを送信
        
        Args:
            status (str): トゥートの内容
            in_reply_to_id (int): リプライするトゥートのID
        
        Returns:
            dict: 送信されたトゥート情報を格納したdict
        """
        url = "https://{}/api/v1/statuses".format(self.__host)

        data = {"status": status}
        if in_reply_to_id is not None:
            data["in_reply_to_id"] = in_reply_to_id

        resp = requests.post(
            url, headers=self.__auth_header(), data=data, timeout=10)
        if resp.status_code != 200:
            raise MastodonAPIError(resp.text, resp.status_code)
        return resp.json()
    
    def get_public_stream(self):
        """
        連合タイムラインのストリームを取得
        
        Returns:
            MastodonStream: ストリームクラス
        """
        return MastodonStream(
            url="https://{}/api/v1/streaming/public".format(self.__host))
    
    def get_user_stream(self):
        """
        ユーザタイムラインのストリームを取得
        
        Returns:
            MastodonStream: ストリームクラス
        """
        return MastodonStream(
            url="https://{}/api/v1/streaming/user".format(self.__host),
            access_token=self.__access_token)

    def __auth_header(self):
        """ OAuth2ヘッダを生成 """
        return {"Authorization": "Bearer " + self.__access_token}
