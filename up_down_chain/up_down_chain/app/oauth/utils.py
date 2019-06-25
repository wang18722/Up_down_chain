import hashlib
import random
import time
from urllib import parse
from xml.etree.ElementTree import fromstring

import requests

from up_down_chain import settings


class WechatAPI(object):
    def __init__(self):
        self.config = settings
        self._access_token = None
        self._openid = None
        self.config = settings
        self.dic = {}

    @staticmethod
    def process_response_login(rsp):
        """解析微信登录返回的json数据，返回相对应的dict, 错误信息"""
        if 200 != rsp.status_code:
            return None, {'code': rsp.status_code, 'msg': 'http error'}
        try:
            content = rsp.json()

        except Exception as e:
            return None, {'code': 9999, 'msg': e}
        if 'errcode' in content and content['errcode'] != 0:
            return None, {'code': content['errcode'], 'msg': content['errmsg']}

        return content, None

    def process_response_pay(self, rsp):
        """解析微信支付下单返回的json数据，返回相对应的dict, 错误信息"""
        rsp = self.xml_to_array(rsp)
        if 'SUCCESS' != rsp['return_code']:
            return None, {'code': '9999', 'msg': rsp['return_msg']}
        if 'prepay_id' in rsp:
            return {'prepay_id': rsp['prepay_id']}, None

        return rsp, None

    @staticmethod
    def create_time_stamp():
        """产生时间戳"""
        now = time.time()
        return int(now)

    @staticmethod
    def create_nonce_str(length=32):
        """产生随机字符串，不长于32位"""
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        strs = []
        for x in range(length):
            strs.append(chars[random.randrange(0, len(chars))])
        return "".join(strs)

    @staticmethod
    def xml_to_array(xml):
        """将xml转为array"""
        array_data = {}
        root = fromstring(xml)
        for child in root:
            value = child.text
            array_data[child.tag] = value
        return array_data

    def get_sign(self):
        """生成签名"""
        # 签名步骤一：按字典序排序参数
        key = sorted(self.dic.keys())
        buffer = []
        for k in key:
            buffer.append("{0}={1}".format(k, self.dic[k]))
        # self.dic["paySign"] = self.get_sign(jsApiObj)

        parm = "&".join(buffer)
        # 签名步骤二：在string后加入KEY
        parm = "{0}&key={1}".format(parm, self.config.API_KEY).encode('utf-8')
        # 签名步骤三：MD5加密
        signature = hashlib.md5(parm).hexdigest()
        # 签名步骤四：所有字符转为大写
        result_ = signature.upper()
        return result_

    def array_to_xml(self, sign_name=None):
        """array转xml"""
        if sign_name is not None:
            self.dic[sign_name] = self.get_sign()
        xml = ["<xml>"]
        for k in self.dic.keys():
            xml.append("<{0}>{1}</{0}>".format(k, self.dic[k]))
        xml.append("</xml>")
        return "".join(xml)


class WechatLogin(WechatAPI):
    def get_code_url(self):
        """微信内置浏览器获取网页授权code的url"""
        url = self.config.defaults.get('wechat_browser_code') + (
            '?appid=%s&redirect_uri=%s&response_type=code&scope=%s&state=%s#wechat_redirect' %
            (self.config.APPID, parse.quote(self.config.REDIRECT_URI),
             self.config.SCOPE, self.config.STATE if self.config.STATE else ''))
        return url

    def get_code_url_pc(self):
        """pc浏览器获取网页授权code的url"""
        url = self.config.defaults.get('pc_QR_code') + (
            '?appid=%s&redirect_uri=%s&response_type=code&scope=%s&state=%s#wechat_redirect' %
            (self.config.APPID, parse.quote(self.config.REDIRECT_URI), self.config.PC_LOGIN_SCOPE,
             self.config.STATE if self.config.STATE else ''))
        return url

    def get_access_token(self, code):
        """获取access_token"""
        params = {
            'appid': self.config.APPID,
            'secret': self.config.APPSECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
        token, err = self.process_response_login(requests
                                                 .get(self.config.defaults.get('wechat_browser_access_token'),
                                                      params=params))
        if not err:
            self._access_token = token['access_token']
            self._openid = token['openid']
        return self._access_token, self._openid

    def get_user_info(self, access_token, openid):
        """获取用户信息"""
        params = {
            'access_token': access_token,
            'openid': openid,
            'lang': self.config.LANG
        }
        return self.process_response_login(requests
                                           .get(self.config.defaults.get('wechat_browser_user_info'), params=params))


class WechatTemplates(WechatAPI):
    def __init__(self):
        super().__init__()
        self.mp_access_token = None
        self.mp_expires_in = None

    def get_mp_access_token(self):
        """获取公众号的access_token"""
        # err_code = {
        #     '-1': '系统繁忙，请稍候再试',
        #     '0': '请求成功',
        #     '40001': 'AppSecret错误或者AppSecret不属于这个公众号，请开发者确认AppSecret的正确性',
        #     '40002': '请确保grant_type字段值为client_credential',
        #     '40164': '调用接口的IP地址不在白名单中，请在接口IP白名单中进行设置',
        # }
        url = self.config.defaults.get('mp_access_token') + (
            '?grant_type=%s&appid=%s&secret=%s' %
            (self.config.GRANT_TYPE,  self.config.APPID,
             self.config.APPSECRET))
        token_data = eval(requests.get(url).content)
        if 'access_token' not in token_data:
            return token_data['errcode'], token_data['errmsg'], False
        else:
            self.mp_access_token = token_data['access_token']
            self.mp_expires_in = token_data['expires_in']
            return self.mp_access_token, self.mp_expires_in, True

    # 以下功能暂不使用
    # def change_industry(self):
    #     """设置所属行业，每月可修改行业1次"""
    #     url = self.config.defaults.get('change_industry') + (
    #         '?access_token=%s' % self.mp_access_token)
    #     prams = {
    #         "industry_id1": "23",
    #         "industry_id2": "31"
    #     }
    #     data = requests.post(url, prams)
    #
    # def get_industry(self):
    #     """获取行业信息"""
    #     if self.mp_access_token is None:
    #         _, msg, success = self.get_mp_access_token()
    #         if not success:
    #             return msg, False
    #     url = self.config.defaults.get('get_industry') + (
    #         '?access_token=%s' % self.mp_access_token)
    #     industry_data = requests.get(url)
    #     if 'primary_industry' in industry_data:
    #         primary_industry = industry_data['primary_industry']
    #         secondary_industry = industry_data['secondary_industry']
    #         return primary_industry, secondary_industry, True
    #     else:
    #         return '', '获取行业信息错误', False
    #
    # def get_templates_id(self):
    #     pass
    #

    def send_templates_message(self, touser, template_id, data, url=None, miniprogram=None):
        post_data = {
            "touser": touser,
            "template_id": template_id,
            "data": data
        }
        if url is not None:
            post_data['url'] = url
        if miniprogram is not None:
            post_data['miniprogram'] = miniprogram
        url = self.config.defaults.get('send_templates_message') + (
            '?access_token=%s' % self.mp_access_token)
        back_data = requests.post(url, json=post_data)
        print(back_data)
        if "errcode" in back_data and back_data["errcode"] == 0:
            return True
        else:
            return False


class WechatPayAPI(WechatAPI):
    def __init__(self, package, sign_type=None):
        super().__init__()
        self.appId = self.config.APPID
        self.timeStamp = self.create_time_stamp()
        self.nonceStr = self.create_nonce_str()
        self.package = package
        self.signType = sign_type
        self.dic = {"appId": self.appId, "timeStamp": "{0}".format(self.create_time_stamp()),
                    "nonceStr": self.create_nonce_str(), "package": "prepay_id={0}".format(self.package)}
        if sign_type is not None:
            self.dic["signType"] = sign_type
        else:
            self.dic["signType"] = "MD5"

    def get_dic(self):
        self.dic['paySign'] = self.get_sign()
        return self.dic


class WechatOrder(WechatAPI):
    def __init__(self, body, trade_type, out_trade_no, total_fee, spbill_create_ip, notify_url, device_info=None,
                 sign_type=None, attach=None, fee_type=None, time_start=None, time_expire=None, goods_tag=None,
                 product_id=None, detail=None, limit_pay=None, openid=None, scene_info=None):
        super().__init__()
        self.device_info = device_info  #
        self.nonce_str = self.create_nonce_str()
        self.sign_type = sign_type  #
        self.detail = detail  #
        self.body = body
        self.attach = attach  #
        self.out_trade_no = out_trade_no
        self.fee_type = fee_type  #
        self.total_fee = total_fee
        self.spbill_create_ip = spbill_create_ip
        self.time_start = time_start  #
        self.time_expire = time_expire  #
        self.goods_tag = goods_tag  #
        self.notify_url = notify_url
        self.trade_type = trade_type
        self.product_id = product_id  #
        self.limit_pay = limit_pay  #
        self.openid = openid  #
        self.scene_info = scene_info  #
        self.dic = {"appid": self.config.APPID, "mch_id": self.config.MCH_ID,
                    "nonce_str": self.nonce_str, "body": self.body,
                    'out_trade_no': out_trade_no,
                    'openid': self.openid,
                    "total_fee": self.total_fee, "spbill_create_ip": self.spbill_create_ip,
                    "notify_url": self.notify_url,
                    "trade_type": self.trade_type}
        if self.device_info is not None:
            self.dic["device_info"] = self.device_info
        if self.sign_type is not None:
            self.dic["sign_type"] = self.sign_type
        if self.detail is not None:
            self.dic["detail"] = self.detail
        if self.attach is not None:
            self.dic["attach"] = self.attach
        if self.fee_type is not None:
            self.dic["fee_type"] = self.fee_type
        if self.time_start is not None:
            self.dic["time_start"] = self.time_start
        if self.time_expire is not None:
            self.dic["time_expire"] = self.time_expire
        if self.goods_tag is not None:
            self.dic["goods_tag"] = self.goods_tag
        if self.product_id is not None:
            self.dic["product_id"] = self.product_id
        if self.limit_pay is not None:
            self.dic["limit_pay"] = self.limit_pay
        if self.openid is not None:
            self.dic["openid"] = self.openid
        if self.scene_info is not None:
            self.dic["scene_info"] = self.scene_info

    def order_post(self):
        if self.config.APPID is None:
            return None, True
        xml_ = self.array_to_xml('sign')
        data = requests.post(self.config.defaults['order_url'], data=xml_.encode('utf-8'),
                             headers={'Content-Type': 'text/xml'})
        return self.process_response_pay(data.content)





# from itsdangerous import TimedJSONWebSignatureSerializer as TJSSerializer
# from oauth import constants
# from oauth.exceptions import WXAPIError
# from up_down_chain import settings
# from urllib.parse import urlencode, parse_qs
# from urllib.request import urlopen
# from django.conf import settings
# import json
# import logging
#
# logger = logging.getLogger('django')


# class OAuthWX(object):
#     """
#     WX认证辅助工具类
#     """
#     def __init__(self, appid=None, sercet=None, redirect_uri=None, response_type='code', scope='snsapi_userinfo', access_token=None, state=None):
#
#         self.appid = appid or settings.APPID
#         self.sercet =sercet or settings.APPSECRET
#         self.redirect_uri = redirect_uri or settings.REDIRECT_URI
#         self.response_type = response_type
#         self.scope = scope
#         self.access_token = access_token or settings.Token
#         self.state = state or settings.STATE  # 用于保存登录成功后的跳转页面路径
#
#     def get_wx_login_url(self):
#         """
#         获取微信登录的网址
#         :return: url网址
#         """
#         params = {
#             'appid': self.appid,
#             'redirect_uri': self.redirect_uri,
#             'response_type': 'code',
#             'scope': 'snsapi_userinfo',
#             'state': self.state,
#         }
#         url = 'https://open.weixin.qq.com/connect/oauth2/authorize?' + urlencode(params)
#         return url
#
#     def get_access_token(self, code):
#         """
#         获取access_token
#         """
#         params = {
#             'appid': self.appid,
#             'secret': self.sercet,
#             'response_type': code,
#             'grant_type': 'authorization_code',
#         }
#         url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' + urlencode(params)
#         response = urlopen(url)
#         response_data = response.read().decode()
#         try:
#             data = json.loads(response_data)
#         except Exception:
#             data = parse_qs(response_data)
#             access_token = data.get('access_token', None)
#             if not access_token:
#                 logger.error('errcode=%s errmsg=%s' % (data.get('errcode'), data.get('errmsg')))
#                 raise WXAPIError
#         access_token = data.get('access_token', None)
#         openid = data.get('openid', None)
#         return access_token, openid
#
#     def get_user_info(self, access_token, openid):
#         """
#         获取用户的个人信息
#         """
#         params = {
#             'access_token': access_token,
#             'openid': openid,
#         }
#         url = 'https://api.weixin.qq.com/sns/userinfo?' + urlencode(params)
#         response = urlopen(url)
#         response_data = response.read().decode()
#         try:
#             user_info = json.loads(response_data)
#         except Exception:
#             user_info = parse_qs(response_data)
#             logger.error('errcode=%s errmsg=%s' % (user_info.get('errcode'), user_info.get('errmsg')))
#             raise WXAPIError
#         return user_info
#
#
# def generate_save_token(self, openid):
#     """
#     生成保存用户数据的token
#     openid加密
#     """
#     serializer = TJSSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_WX_USER_TOKEN_EXPIRES)
#     # 加密openid
#     token = serializer.dumps({'openid': openid})
#
#     return token.decode()
#
#
# def check_save_user_openid(self, access_token):
#     serializer = TJSSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_WX_USER_TOKEN_EXPIRES)
#
#     # 解密openid
#     dict_data = serializer.loads(access_token)
#     return dict_data.get("openid")


# from urllib.parse import quote
#
# import requests
# from django.shortcuts import redirect
# from django.urls import reverse
# from django.views import View
#
# from up_down_chain.settings import WEICHAT_AUTH
#
#
# class DefaultAuthView(View):
#     """
#     静默授权，获取code
#     """
#
#     def get(self, request, *args, **kwargs):
#         # 静默授权
#         auth_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid={APPId}&' \
#                    'redirect_uri={redirect_url}&response_type=code&scope=snsapi_base&state=123#wechat_redirect'
#         # 回调函数
#         REDIRECT_URI = WEICHAT_AUTH['ROOT_URL'] + reverse('login:get_openid')
#         auth_url = auth_url.format(appId=WEICHAT_AUTH['APPId'], redirect_url=quote(REDIRECT_URI))
#         return redirect(auth_url)
#
#
# def get_user_token(code):
#     """
#     获取网页授权token
#     """
#     request_url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' \
#                   'appid={APPID}&secret={SECRET}&code={CODE}&grant_type=authorization_code'
#
#     request_url = request_url.format(APPID=WEICHAT_AUTH['APPId'], SECRET=WEICHAT_AUTH['SECRET'], CODE=code)
#     data = requests.get(request_url)
#     return data.json()
#
#
# class WeiChatAuthView(View):
#     """
#     微信用户授权，获取code
#     """
#     def get(self, request, *args, **kwargs):
#
#         auth_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid={APPID}&' \
#                    'redirect_uri= {redirect_url&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect'
#
#         REDIRECT_URI = WEICHAT_AUTH['ROOT_URL'] + reverse('login:get_info')
#         auth_url = auth_url.format(appId=WEICHAT_AUTH['APPId'], redirect_url=quote(REDIRECT_URI))
#         return redirect(auth_url)
#
#
# def get_user_info(a_token, open_id):
#     """
#     获取微信用户信息
#     """
#     info_url = 'https://api.weixin.qq.com/sns/userinfo?access_token={ACCESS_TOKEN}&openid＝{OPENID}&lang=zh_CN'
#     info_url = info_url.format(ACCESS_TOKEN=a_token, OPENID=open_id)
#
#     i = requests.get(info_url)
#     data = i.json()
#     return data
#
#
# def get_basics_token(open_id, secret):
#     """
#     获取基础token
#     """
#     info_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}'
#     info_url = info_url.format(APPID=open_id, SECRET=secret)
#     i = requests.get(info_url)
#     data = i.json()
#     return data
#
#
# def get_attention_info(a_token, open_id):
#     """
#     获取微信关注信息
#     """
#     info_url = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token={ACCESS_TOKEN}&openid＝{OPENID}&lang=zh_CN'
#     info_url = info_url.format(ACCESS_TOKEN=a_token, OPENID=open_id)
#     i = requests.get(info_url)
#     data = i.json()
#     return data


from itsdangerous import TimedJSONWebSignatureSerializer as TJSSerializer
from django.conf import settings
def generate_save_token(wx_openid):

    """
    openid加密,使用JWT加密token
    """
    serializer = TJSSerializer(settings.SECRET_KEY, expires_in=3600)

    # 加密openid
    token = serializer.dumps({'openid': wx_openid})

    return token.decode()

def check_save_user_openid(access_token):
    serializer = TJSSerializer(settings.SECRET_KEY, expires_in=300)

    # 解密openid
    dict_data = serializer.loads(access_token)


    return dict_data.get("openid")