# ================================================= #
# @file serve.py
# @brief 媒体部OA服务端
# @author DDoS_LING & Wesley
# @date 2024-06-14
# @version 2.3.0
# @note 当前版本不兼容基于易语言编写的“媒体部设备管理系统”!!
# ================================================= #
##########################################
##      Made By DDoS_LING in 2021        #
##   Reconstruction By Wesley in 2024    #
##########################################

import os,sys,re
import time
import datetime
import json
import traceback
import flask
from flask import request,render_template,redirect
from flask_cors import CORS
import pymysql
import hashlib
import random 
from pymysql.converters import escape_string
import pymysql.cursors
from itertools import chain
import requests
import threading
import ast
from gevent import pywsgi
from urllib import parse
import base64
from io import BytesIO
# import uvicorn


VERSION = "v2_6_10" #20241214

URL_PREFIX = f"/v2"
REQ_METHODS = ["GET","POST"]

MysqlServer = "121.40.69.157"

# mysql config
mysql_config = {
    'host': MysqlServer,
    'user': 'sql_admin',
    'password': 'Admin@mtb_oa2024',
    'db': 'mtb-oa',
    'cursorclass': pymysql.cursors.DictCursor
}

# mysql_config = {
#     'host': '192.168.67.14',
#     'user': 'mtb-test',
#     'password': 'NbkTm44fcw2hJJnx',
#     'db': 'mtb-test',
#     'cursorclass': pymysql.cursors.DictCursor
# }
    
# 维护模式
maintain_reason = "停服维护中。请咨询管理员。"

# TOKEN数据存储
# TOKEN_GROUP = {}
# TOKENRenewalLimit = {}

# 获取当前时间
start_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
start_time = int(time.time())

## 通用类代码
def get_milliTimestamp():
    """获取毫秒级时间戳"""
    return int(round(time.time() * 1000))

def get_timestamp():
    """获取时间戳"""
    return int(round(time.time()))

def get_time():
    """获取YYYY-MM-DD hh:mm:ss"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

def get_dayOfWeek():
    """获取当前星期数"""
    return time.strftime("%w")

def get_weekOfYear():
    """获取当前周数"""
    return time.strftime("%W")

def writeLog(path,log):
    """写入日志"""
    with open(path, 'a') as file:
        file.write(f"{log}\n")

def log(type:str="SYSTEM",state:str="Normal",event:str="-",msg:str="-",url:str="-",ip:str="-",usercode:str="-"):
    """
    日志系统函数\n
    state: 
     - Normal：正常
     - Error：错误
     - Warning：告警
     - Info：记录
    """
    global WriteLogList
    state = 0 if state == "Normal" else 1 if state == "Error" else 2 if state == "Warning" else 3
    if not os.path.exists("./log/SYSTEM_LOG"):
        os.makedirs("./log/SYSTEM_LOG")
    if not os.path.exists("./log/USER_LOG"):
        os.makedirs("./log/USER_LOG")
    if not os.path.exists("./log/REQUEST_LOG"):
        os.makedirs("./log/REQUEST_LOG")
    try:
        times = get_milliTimestamp()
        # times = get_time()
        LOGSHA_SRT = str({"time":f"{get_time()}","randomNum1":f"{random.randint(1,9999999)}","randomNum2":f"{random.randint(2109,9999999999)}","randomNum3":f"{get_milliTimestamp()+random.randint(0,999999999999)}"})
        LOGSHA = sha256(LOGSHA_SRT).upper()
        if type == "USER":
            # 用户事件
            write_log = json.dumps({"id":LOGSHA,"time":times,"event":event,"log":msg,"status":state,"USER_ip":ip,"USER_code":usercode,"version":VERSION})
            path = f'./log/USER_LOG/{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.log'
            # with open(f'./log/USER_LOG/{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.log', 'a') as file:
            #     file.write(f"{write_log}\n")
        elif type == "REQUEST":
            # 请求事件
            write_log = json.dumps({"id":LOGSHA,"time":times,"event":event,"log":msg,"status":state,"url":url,"USER_ip":ip,"version":VERSION})
            path = f'./log/REQUEST_LOG/{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.log'
            # with open(f'./log/REQUEST_LOG/{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.log', 'a') as file:
            #     file.write(f"{write_log}\n")
        else:
            # 系统事件
            write_log = json.dumps({"id":LOGSHA,"time":times,"event":event,"log":msg,"status":state,"url":url,"USER_ip":ip,"USER_code":usercode,"version":VERSION})
            path = f'./log/SYSTEM_LOG/{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.log'
            # with open(f'./log/SYSTEM_LOG/{time.strftime("%Y-%m-%d", time.localtime(time.time()))}.log', 'a') as file:
            #     file.write(f"{write_log}\n")
        print("\033[0;32;40m"+write_log+"\033[0m")
        ls = threading.Thread(target=writeLog,args=(path, write_log))
        ls.start()
    except:
        print(f"Log Server Running Error\n{traceback.format_exc()}")

def getAllLogFileName(types="SYSTEM"):
    """获取全部日志文件名称（日期）"""
    if types == "USER":
        base_dir = './log/USER_LOG'
    elif types == "REQUEST":
        base_dir = './log/REQUEST_LOG'
    else:
        base_dir = './log/SYSTEM_LOG'
    # 遍历文件列表，获取文件日期
    files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
    lists = []
    try:
        if not files:
            return []
        for path in files:
            filedate = re.compile(r"\d{4}-\d{1,2}-\d{1,2}").search(path).group()
            RESS = {
                "date": filedate, 
            }
            lists.append(RESS)
    except:
        log(event="读取日志文件时出错",state="Error",msg=traceback.format_exc())
    lists.reverse()
    return lists

def getLog(types="SYSTEM",date=None):
    """获取日志内容"""
    if types == "USER":
        base_dir = './log/USER_LOG'
    elif types == "REQUEST":
        base_dir = './log/REQUEST_LOG'
    else:
        base_dir = './log/SYSTEM_LOG'
    # 遍历文件列表，获取文件日期
    files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
    lists = []
    try:
        if not date:
            return []
        # 读取目录下的时间，列出时间对应的文件列表
        for path in files:
            filedate = re.compile(r"\d{4}-\d{1,2}-\d{1,2}").search(path).group()
            if date == filedate:
                RESS = {
                    "date": filedate, 
                    "data": []
                }
                f = open(path)
                lines = f.read()
                lineslist = lines.split('\n')
                for item in lineslist:
                    try:
                        if item != "" and isinstance(eval(item),dict):
                            RESS["data"].append(eval(item))
                    except:
                        pass
                RESS["data"].reverse()
                f.close()
                return [RESS]
    except:
        log(event="读取日志文件时出错",state="Error",msg=traceback.format_exc())
    return lists

def sha256(data: str):
    """hash256加密"""
    hash256 = hashlib.sha256()
    hash256.update(data.encode('utf-8'))
    return(hash256.hexdigest())

def md5(data: str):
    """md5加密"""
    hashmd5 = hashlib.md5()
    hashmd5.update(data.encode('utf-8'))
    return(hashmd5.hexdigest())

def getIp(request):
    """获取访问者IP地址"""
    try:
        ip = request.headers["X-Real-IP"]
        if ip == "" or ip == None:
            ip = request.remote_addr
    except:
        ip = request.remote_addr
    return ip

def getOnlineNumber():
    """获取当前在线的人数"""
    cleanTimeoutToken()
    with pymysql.connect(**mysql_config) as conn:
        with conn.cursor() as cursor:
            sql = 'SELECT * FROM `login-status` WHERE 1'
            cursor.execute(sql)
            result = cursor.fetchall()
            return len(result)
    return 0
    

def escape(s):
    """防SQL注入"""
    return escape_string(s)

# ERROR CODE LIST

# 0 ok 正常返回内容
# -1 System Error 系统错误
# -2 Maintain Mode 维护模式
# -3 
# -1001 Invalid Result 无效的返回结果，无法合成返回数据
# -1002 Invalid Parameter 无效的参数，请求参数无效
# -1003 TokenTimeout Token失效
# -1005 No Permission 无权限
# -1006 Passwords need to be encrypted before transmission 密码需要加密后再进行传递
# -2001 The equipment cannot be found 找不到设备

# [START] MAIN FUNCTION CODE AREA

# Tools
def  synthesisReturnData(CODE:int,MSG:str="Invalid Result",DATA=None):
    """合成返回数据"""
    try:
        if DATA == None and (type(DATA) != str or (type(DATA) != list or type(DATA) != dict)):
            return ({"errcode":CODE,"errmsg":MSG},200)
        return ({"errcode":CODE,"errmsg":MSG,"data":DATA},200)
    except:
        log(event="合成返回数据时发生错误",state="Error",msg=traceback.format_exc())
        return ({"errcode":"-1001","errmsg":"Invalid Result"},200)

def getRequestToken(request):
    """获取请求是否携带Token"""
    try:
        token = request.headers["Token"]
        if token == "" or token == None:
            token = False
    except:
        token = False
    return token

def getMaintainStatus():
    """获取维护模式状态"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `system` where `name` = "maintain_mode"'
                cursor.execute(sql)
                result = cursor.fetchone()
                if not result:
                    return False
                if result["text"] == 1:
                    return True
                return False
    except:
        log(event="获取维护模式状态时发生错误",state="Error",msg=traceback.format_exc())
        return False


# 业务代码
def cleanTimeoutToken():
    """清除过期Token"""
    log(type="USER",event="用户触发清理过期Token",msg="-")
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'DELETE FROM `login-status` WHERE `timeout` < %s AND COALESCE(`remark`, "") != "_NoCleanToken"'
                cursor.execute(sql, (get_timestamp()))
                conn.commit()
    except:
        log(type="USER",event="清理过期Token失败",state="Error",msg=f"无法清理过期TOKEN，{traceback.format_exc()}")
    

def findTokenByUserCode(USER_code: str):
    """按照用户Code查找Token"""
    cleanTimeoutToken()
    with pymysql.connect(**mysql_config) as conn:
        with conn.cursor() as cursor:
            sql = 'SELECT * FROM `login-status` WHERE usercode = %s'
            cursor.execute(sql, (USER_code))
            result = cursor.fetchone()
            return result
    return False

def verifyTokenEffective(token:str):
    """校验token是否有效"""
    return tokenExists(token)

def tokenExists(Token:str):
    """查找Token是否在存在"""
    cleanTimeoutToken()
    with pymysql.connect(**mysql_config) as conn:
        with conn.cursor() as cursor:
            sql = 'SELECT * FROM `login-status` WHERE TOKEN = %s'
            cursor.execute(sql, (Token))
            result = cursor.fetchone()
            if result:
                return True
            return False

def getLoginUserInfo_ByToken(Token:str):
    """获取token对应的用户信息"""
    try:
        if tokenExists(Token):
            return getTokenInfo(Token)
        return False
    except Exception as err:
        print(err)
        return False

def getTokenInfo(Token:str):
    """获取Token信息"""
    with pymysql.connect(**mysql_config) as conn:
        with conn.cursor() as cursor:
            sql = 'SELECT * FROM `login-status` WHERE TOKEN = %s'
            cursor.execute(sql, (Token))
            result = cursor.fetchone()
            return result

def tokenRenewal(Token:str):
    """Token续期"""
    # 每小时只能续期一次，每次只能续期90分钟即5400秒
    cleanTimeoutToken()
    try:
        if tokenExists(Token):
            TOKENRenewalLimit = getTokenInfo(Token)["renewalLimit"]
            if TOKENRenewalLimit:
                if TOKENRenewalLimit < get_timestamp():
                    return False
            with pymysql.connect(**mysql_config) as conn:
                with conn.cursor() as cursor:
                    selectSql = "SELECT * FROM `login-status` WHERE TOKEN = %s"
                    cursor.execute(selectSql, (Token))
                    result = cursor.fetchone()
            with pymysql.connect(**mysql_config) as conn:
                with conn.cursor() as cursor:
                    sql = 'UPDATE `login-status` SET `timeout`=%s, `renewalLimit`=%s WHERE TOKEN = %s'
                    cursor.execute(sql, (result["timeout"] + 5400,get_timestamp() + 3600,Token))
                    conn.commit()
                    return True
    except:
        print(traceback.format_exc())

def getUserInfo(USER_CODE):
    """获取用户信息"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from user WHERE code = %s AND `type` = 0'
                cursor.execute(sql, (USER_CODE))
                result = cursor.fetchone()
                if not result:
                    return synthesisReturnData(-1004,"ok",{})
                return synthesisReturnData(0,"ok",{"id":result["id"],"name":result["name"],"code":result["code"],"class":result["class"],"password":None,"share_device":result["share_device"],"group":result["group"],"grade":result["grade"],"reg_time":result["reg_time"],"join_time":result["join_time"],"login_time":result["login_time"],"openid":result["openid"],"remark":result["remark"]})
    except:
        return synthesisReturnData(-1,traceback.format_exc())

def getUserInfo_ByID(USER_CODE):
    """获取用户信息"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from user where id = %s AND `type` = 0'  
                cursor.execute(sql, int(USER_CODE))
                result = cursor.fetchone()
                if not result:
                    return synthesisReturnData(-1004,"ok",{})
                return synthesisReturnData(0,"ok",{"id":result["id"],"name":result["name"],"code":result["code"],"class":result["class"],"password":None,"share_device":result["share_device"],"group":result["group"],"grade":result["grade"],"reg_time":result["reg_time"],"join_time":result["join_time"],"login_time":result["login_time"],"openid":result["openid"],"remark":result["remark"]})
    except:
        return synthesisReturnData(-1,traceback.format_exc())

def getUserInfo_ByName(NAME):
    """获取用户信息"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from user where name = %s AND `type` = 0'  
                cursor.execute(sql, (NAME))
                result = cursor.fetchone()
                if not result:
                    return synthesisReturnData(0,"ok",{})
                return synthesisReturnData(0,"ok",{"id":result["id"],"name":result["name"],"code":result["code"],"class":result["class"],"password":None,"share_device":result["share_device"],"group":result["group"],"grade":result["grade"],"reg_time":result["reg_time"],"join_time":result["join_time"],"login_time":result["login_time"],"openid":result["openid"],"remark":result["remark"]})
    except:
        return synthesisReturnData(-1,traceback.format_exc())

UP_Cache = {}
def getUserPermissions(USER_ID: int, GROUP_ID: int):
    """获取用户权限列表"""
    global UP_Cache
    try:
        a = []
        # if USER_ID in UP_Cache:
        #     return synthesisReturnData(0,"ok",UP_Cache[USER_ID])
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `permissions` where `type`= "userid" and `object` = %s and `open` = 1'
                cursor.execute(sql, int(USER_ID))
                result = cursor.fetchall()
                for i in result:
                    a.append(i["val"])
                sql2 = 'select * from `permissions` where `type`= "groupid" and `object` = %s'
                cursor.execute(sql2, int(GROUP_ID))
                result = cursor.fetchall()
                for i in result:
                    a.append(i["val"])
                # UP_Cache[USER_ID] = a
        return a
    except:
        print(traceback.format_exc())
        return []
    
def getPagePermissionsList():
    """获取页面权限列表"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `permissions` where `type`= "page"'
                cursor.execute(sql)
                result = cursor.fetchone()
                if not result:
                    return synthesisReturnData(0,"ok",{})
                return synthesisReturnData(0,"ok",result["val"])
    except:
        return synthesisReturnData(-1,traceback.format_exc())

def addUserPermissions(USER_ID:int, PERMISSIONS:str or list, remark:str=""):
    """添加用户权限"""
    try:
        if type(PERMISSIONS) != list:
            with pymysql.connect(**mysql_config) as conn:
                with conn.cursor() as cursor:
                    sql = 'insert into `permissions` (`type`,`object`,`val`,`remark`) values (%s,%s,%s,%s)'
                    cursor.execute(sql, ("userid",int(USER_ID),PERMISSIONS,remark))
                    conn.commit()
            return synthesisReturnData(0,"ok")
        for i in PERMISSIONS:
            with pymysql.connect(**mysql_config) as conn:
                with conn.cursor() as cursor:
                    sql = 'insert into `permissions` (`type`,`object`,`val`,`remark`) values (%s,%s,%s,%s)'
                    cursor.execute(sql, ("userid",int(USER_ID),i,remark))
                    conn.commit()
        return synthesisReturnData(0,"ok")
    except:
        return synthesisReturnData(-1,traceback.format_exc())

def changeUserPermissions(USER_ID:int, PERMISSIONS:list):
    """变更用户权限列表"""
    # 逻辑是先查再删再加
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `permissions` where `type`= "userid" and `object` = %s'
                cursor.execute(sql, int(USER_ID))
                result = cursor.fetchall()
                if result:
                    for i in result:
                        # 不在新的权限列表内，则把该权限删除
                        if i["val"] not in PERMISSIONS:
                            sql = 'delete from `permissions` where `type`= "userid" and `object` = %s and `val` = %s'
                            cursor.execute(sql, (int(USER_ID),i["val"]))
                            conn.commit()
                        # 在数据库里，不进行操作，直接去掉
                        else:
                            PERMISSIONS.remove(i["val"])
                # 添加新的权限
                for j in PERMISSIONS:
                    sql = 'insert into `permissions` (`type`,`object`,`val`) values (%s,%s,%s)'
                    cursor.execute(sql, ("userid",int(USER_ID),j))
                    conn.commit()
                return synthesisReturnData(0,"ok")
    except:
        return synthesisReturnData(-1,traceback.format_exc())

def verifyPermissions(TOKEN: str, NP: str, NARP: bool = True) -> bool:
    """
    判断用户是否拥有权限（通过token）

    @param TOKEN: 用户TOKEN
    @param NP: 需要的权限
    @param NARP: 是否允许根权限
    """
    u = getTokenInfo(TOKEN)
    # 无实际操作权限
    if u["remark"]:
        if "_NoOperate" in u["remark"]:
             return False
    # 获取权限
    return verifyUserPermission(uid=u["uid"],Need=NP,AllowRoot=NARP)

def verifyUserPermission(uid: int,Need: str,AllowRoot: bool = True):
    """
    判断用户是否拥有权限

    @param uid: 用户id
    @param Need: 需要的权限
    @param AllowRoot: 是否允许根权限
    """
    # 用户信息
    UserInfo = getUserInfo_ByID(uid)[0]["data"]
    gid = UserInfo["group"]
    # 用户拥有的权限
    UserPermissionsList = []
    UserPermissionsList.extend(getUserOpenPermissions(uid))
    UserPermissionsList.extend(getGroupPermissionsList(gid))
    print(getGroupPermissionsList(gid),gid)
    UserClosePermissionsList = getUserClosePermissions(uid)
    # 是否直接拥有这个权限
    if Need in UserPermissionsList and not Need in UserClosePermissionsList:
        return True
    # 是否拥有Root权限，且允许Root权限
    if ("*.*" in UserPermissionsList or "*" in UserPermissionsList) and AllowRoot:
        return True
    # 是否拥有子权限
    Need = Need.split(".")
    IfPer = ""
    for i in Need:
        IfPer = IfPer + i + "."
        # 是否有父权限的根权限，且不是NotAllow状态，则为有权限
        if IfPer + "*" in UserPermissionsList and not IfPer + "*" in UserClosePermissionsList:
            return True
    return False
    
    

def getUserOpenPermissions(USER_ID: int):
    """获取用户开放权限列表"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `permissions` where `type`= "userid" and `object` = %s and `open` = 1'
                cursor.execute(sql, int(USER_ID))
                result = cursor.fetchall()
                if result:
                    data = []
                    for i in result:
                        data.append(i["val"])
                return data
    except:
        return []

def getUserClosePermissions(USER_ID: int):
    """获取用户关闭权限列表"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `permissions` where `type`= "userid" and `object` = %s and `open` = 0'
                cursor.execute(sql, int(USER_ID))
                result = cursor.fetchall()
                if result:
                    data = []
                    for i in result:
                        data.append(i["val"])
                return data
    except:
        return []

def getGroupPermissionsList(gid:int):
    """获取组权限列表"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `permissions` where `type`= "groupid" and `object` = %s'
                cursor.execute(sql, int(gid))
                result = cursor.fetchall()
                if result:
                    data = []
                    for i in result:
                        data.append(i["val"])
                return data
    except:
        return []


def getUserWithGroup():
    """获取组的用户列表"""
    data = {}
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `user` WHERE `type` = 0'
                cursor.execute(sql)
                result = cursor.fetchall()
                for i in result:
                    if i["group"] in data:
                        data[i["group"]].append(i)
                    else:
                        data[i["group"]] = [i]
                return synthesisReturnData(0,"ok",data)
    except:
        return synthesisReturnData(-1,traceback.format_exc())



# 初始化SSO服务
app = flask.Flask(__name__)
# 允许跨域
CORS(app)

# SSO-HTTP[404]
@app.errorhandler(404)
def not_found(error):
    log(type="REQUEST",ip=getIp(flask.request),url=flask.request.url,event=f"[{request.method}] Page-Not-Found",msg="Page Not Found",state="Warning")
    return synthesisReturnData(-1,"不支持的页面")

# SSO-HTTP[500]
@app.errorhandler(500)
def serve_error(error):
    print(error)
    log(type="REQUEST",ip=getIp(flask.request),url=flask.request.url,event=f"[{request.method}] Server-Error",msg=f"服务器错误，{traceback.format_exc()}",state="Warning")
    return synthesisReturnData(-3,"服务器错误")


# 路由开始
# 其他功能
@app.route(f'{URL_PREFIX}/maintain', methods=REQ_METHODS)
def Route_Maintain():
    """维护模式-路由"""
    try:
        return synthesisReturnData(0,"ok",{"maintain":getMaintainStatus()})
    except:
        log(event="维护模式时发生错误",state="Error",msg=traceback.format_exc())
        return synthesisReturnData(-1,"系统错误")

# 正牌功能
@app.route(f"{URL_PREFIX}/login", methods=REQ_METHODS)
def Route_Login():
    """登录-路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求登录接口",ip=getIp(flask.request),url=flask.request.url)
    POST_data = request.form
    try:
        try:
            account = str(POST_data.get("account"))
            password = str(POST_data.get("password"))
        except:
            return synthesisReturnData(-1001,"Invalid Parameter")
        return login(account,password)
    except:
        return synthesisReturnData(-1,"Running Function Error In Router",traceback.format_exc())

@app.route(f"{URL_PREFIX}/getLoginUserInfo", methods=REQ_METHODS)
def Route_GetLoginUserInfo():
    """获取登录用户信息-路由"""
    TOKEN = getRequestToken(flask.request)
    tokenData = getLoginUserInfo_ByToken(TOKEN)
    if not tokenData:
        return synthesisReturnData(0,"ok",{})
    return synthesisReturnData(0,"ok",tokenData)

@app.route(f"{URL_PREFIX}/checkToken", methods=REQ_METHODS)
def Route_CheckToken():
    """验证Token-路由"""
    try:
        return synthesisReturnData(0,"ok",{"token":getRequestToken(flask.request),"verify":verifyTokenEffective(getRequestToken(flask.request))})
    except:
        return synthesisReturnData(-1,"Running Function Error In Router",traceback.format_exc())

@app.route(f"{URL_PREFIX}/verifyPermissions", methods=REQ_METHODS)
def Route_VerifyPermissions():
    """验证权限-路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求验证权限接口",ip=getIp(flask.request),url=flask.request.url)
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        permissions = str(POST_data.get("permissions"))
    except:
        return synthesisReturnData(-1001,"Invalid Parameter")
    try:

        return synthesisReturnData(0,"ok",{"code":getTokenInfo(TOKEN)["usercode"],"verify":verifyPermissions(TOKEN,permissions)})
    except:
        return synthesisReturnData(-1,"Running Function Error In Router",traceback.format_exc())

@app.route(f"{URL_PREFIX}/changePassword", methods=REQ_METHODS)
def Route_ChangePassword():
    """更改密码-路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求更改密码接口",ip=getIp(flask.request),url=flask.request.url)
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        old_passwd = str(POST_data.get("oldpassword"))
        new_passwd = str(POST_data.get("newpassword"))
        if old_passwd == "" or new_passwd == "":
            return synthesisReturnData(-1001,"Invalid Parameter")
    except:
        return synthesisReturnData(-1001,"Invalid Parameter")
    tokenRenewal(TOKEN)

    old_passwd_hash = sha256(old_passwd)
    new_passwd_hash = sha256(new_passwd)

    if old_passwd_hash == "" or new_passwd_hash == "":
        return synthesisReturnData(-10001,"Cannot encrypt the password info")

    user_code = getTokenInfo(TOKEN)["usercode"]

    with pymysql.connect(**mysql_config) as conn:
        with conn.cursor() as cursor:
            sql = 'select * from user WHERE `type` = 0 AND `code` = %s'
            cursor.execute(sql, (escape_string(user_code)))
            result = cursor.fetchone()
            if not result:
                return synthesisReturnData(-10002,"Cannot find this user Account")
            if result["password"] != old_passwd_hash:
                return synthesisReturnData(-10003,"Old password is wrong")

        with conn.cursor() as cursor:
            sql = 'UPDATE user SET password = %s WHERE code = %s'
            cursor.execute(sql, (new_passwd_hash, escape_string(user_code)))
            conn.commit()
    return synthesisReturnData(0,"ok")

@app.route(f"{URL_PREFIX}/getServerTime", methods=REQ_METHODS)
def getServerTime():
    """获取服务器时间"""
    return synthesisReturnData(0,"ok",{"time":get_milliTimestamp()})


# @app.route(f"{URL_PREFIX}/permissions/userHasPermissions", methods=REQ_METHODS)
# def RuserHasPermissions():
#     """获取用户权限路由"""
#     log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取用户权限接口",ip=getIp(flask.request),url=flask.request.url)
#     TOKEN = getRequestToken(flask.request)
#     if not verifyTokenEffective(TOKEN):
#         # log(event="拒绝访问",ip=getIp(flask.request),url=flask.request.url,msg=f"无效的登录令牌 {key}")
#         RESULT = synthesisReturnData(-1003,"Token Timeout")
#         return RESULT
#     try:
#         RESULT =  A__GetUserPermissions(TOKEN_GROUP[TOKEN]["id"])
#     except:
#         RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
#     return RESULT

# @app.route(f"{URL_PREFIX}/permissions/pagePermissions", methods=REQ_METHODS)
# def RpagePermissions():
#     """获取页面权限路由"""
#     log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"获取请求页面权限接口",ip=getIp(flask.request),url=flask.request.url)
#     TOKEN = getRequestToken(flask.request)
#     if not verifyTokenEffective(TOKEN):
#         # log(event="拒绝访问",ip=getIp(flask.request),url=flask.request.url,msg=f"无效的登录令牌 {key}")
#         RESULT = synthesisReturnData(-1003,"Token Timeout")
#         return RESULT

#     try:
#         RESULT =  A__GetPageNeedPermissions()
#     except:
#         RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
#     return RESULT


## SSO 统一认证系统 代码结束 ##

















# OA代码区域

# [START] MAIN FUNCTION CODE AREA
# Tools

def GetMaintainStatus():
    """获取维护模式状态"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from system where name = "maintain_mode"'
                cursor.execute(sql)
                result = cursor.fetchone()
                if not result:
                    return False
                if result[1] == 1:
                    return True
                return False
    except:
        log(event="获取维护模式状态时发生错误",state="Error",msg=traceback.format_exc())
        return False
    
def GetWhichWeek():
    """获取今天是第几周"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from system where name = "start_date_of_semester"'
                cursor.execute(sql)
                result = cursor.fetchone()
                if not result:
                    weekth = -1
                else:
                    Start_date = time.strptime("2024-02-20","%Y-%m-%d")
                    Today = datetime.datetime.now().timetuple()
                    date1 = datetime.datetime(Start_date[0],Start_date[1],Start_date[2]-1)
                    date2 = datetime.datetime(Today[0],Today[1],Today[2])
                    #返回两个变量相差的值，就是相差天数
                    differ = date2 - date1
                    weekth = differ // datetime.timedelta(days=7) + 1
    except:
        log(event="获取第几周时发生错误",state="Error",msg=traceback.format_exc())
        weekth = -1
    return weekth

def GetDate_of_Weekth(date):
    """获取日期是星期几"""
    return datetime.datetime.strptime(date,'%Y-%m-%d').weekday()

def CheckDateIsThisWeek(WhatDays,Today=datetime.datetime.now()):
    """判断两个日期是不是同一周"""
    TodayWeek=Today.strftime('%W')
    WhatDaysWeek=datetime.datetime.strptime(WhatDays,'%Y-%m-%d').strftime('%W')
    if TodayWeek == WhatDaysWeek:
        return True
    return False

def GetLast7Days(NotNeedYear=False):
    data = []
    for i in range(7):
        current_date = datetime.date.today()
        delta = datetime.timedelta(days=i)
        seven_days_ago = current_date - delta
        if NotNeedYear:
            seven_days_ago = seven_days_ago.strftime("%m-%d")
        else:
            seven_days_ago = seven_days_ago.strftime("%Y-%m-%d")
        data.append(seven_days_ago)
    data.reverse()
    return data

def GetLendTotal():
    """获取借出总数"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from records'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    return len(result)
    except:
        log(event="获取借出总数时发生错误",state="Error",msg=traceback.format_exc())
    return 0

def GetNotReturnTotal():
    """获取未归还总数"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from records WHERE status = 1'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    return len(result)
    except:
        log(event="获取未归还总数时发生错误",state="Error",msg=traceback.format_exc())
    return 0

def GetEquipmentTotal():
    """获取设备总数"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from equipment'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    return len(result)
    except:
        log(event="获取设备总数时发生错误",state="Error",msg=traceback.format_exc())
    return 0

def GetDayLendDataTotal(date):
    """获取某天的借出数据量"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM `records` WHERE `lend_date` LIKE %s"
                cursor.execute(sql,(escape_string("%"+date+"%")))
                result = cursor.fetchall()
                if result:
                    return len(result)
    except:
        log(event="获取某天的借出数据量时发生错误",state="Error",msg=traceback.format_exc())
    return 0

def GetDayReturnDataTotal(date):
    """获取某天的归还数据量"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM `records` WHERE `return_date` LIKE %s"
                cursor.execute(sql,(escape_string("%"+date+"%")))
                result = cursor.fetchall()
                if result:
                    return len(result)
    except:
        log(event="获取某天的归还数据量时发生错误",state="Error",msg=traceback.format_exc())
    return 0

def GetTodayLendAndReturnPrecent():
    """获取当天借还数据百分比"""
    try:
        current_date = datetime.date.today()
        date = current_date.strftime("%Y-%m-%d")
        LENDTOTAL = GetDayLendDataTotal(date)
        RETURNTOTAL = 0
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM `records` WHERE `return_date` LIKE %s AND `lend_date` LIKE %s"
                cursor.execute(sql,(escape_string("%"+date+"%"),escape_string("%"+date+"%")))
                returnResult = cursor.fetchall()
                if returnResult:
                    RETURNTOTAL = len(returnResult)
    except:
        log(event="获取当天借还数据百分比时发生错误",state="Error",msg=traceback.format_exc())
    return {
        "returnTotal" : RETURNTOTAL,
        "lendTotal" : LENDTOTAL
    }
    

def GetLoginTotal():
    """获取当天登录人次"""
    Today = datetime.datetime.now()
    N = 0
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `user` where `type` = 0'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        # 判断日期是不是一天
                        if (i["login_time"]):
                            if i["login_time"].date() == Today.date():
                                N += 1
                return N
    except:
        log(event="获取登录人次数据时发生错误",state="Error",msg=traceback.format_exc())
    return 0

def SortFunction(elm):
    return elm["lend_total"]

def GetLendRanking():
    """获取借出排行"""
    EquipmentList_ex = {}
    LendTotalList_ex = {}
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM `records` WHERE `equipment_code`"
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    # 获取用户表，后面设置使用人用户名需要用到
                    sql = "SELECT * FROM `user`"
                    cursor.execute(sql)
                    UsersList = cursor.fetchall()
                    # 第一次遍历，初步归类
                    for i in result:
                        # 设备
                        if i["equipment_code"] in EquipmentList_ex:
                            EquipmentList_ex[i["equipment_code"]]["lend_total"] += 1
                            if not i["lend_operater"] in EquipmentList_ex[i["equipment_code"]]["user_name"]:
                                EquipmentList_ex[i["equipment_code"]]["user_name"].append(i["lend_operater"])
                            if not EquipmentList_ex[i["equipment_code"]]["equipment_name"] and i["equipment_name"]:
                                EquipmentList_ex[i["equipment_code"]]["equipment_name"] = i["equipment_name"]
                        else:
                            EquipmentList_ex[i["equipment_code"]] = {
                                "lend_total": 1,
                                "user_name": [i["lend_operater"]],
                                "equipment_code": i["equipment_code"],
                                "equipment_name": i["equipment_name"],
                            }
                        # 用户
                        if i["lend_userid"] in LendTotalList_ex:
                            LendTotalList_ex[i["lend_userid"]]["lend_total"] += 1
                            if not i["equipment_code"] in LendTotalList_ex[i["lend_userid"]]["lend_equipment"]:
                                LendTotalList_ex[i["lend_userid"]]["lend_equipment"].append(i["equipment_code"])
                        else:
                            LendTotalList_ex[i["lend_userid"]] = {
                                "lend_total": 1,
                                "lend_equipment": [i["equipment_code"]],
                                "operater_username": i["lend_operater"],
                                "lend_userid": i["lend_userid"],
                            }
        # 二次遍历
        # finally_equipment = {}
        # finally_user = {}
        finally_equipments = []
        finally_equipment = []
        finally_users = []
        finally_user = []
        # 设备
        i = 1
        for eq in EquipmentList_ex.keys():
            key = EquipmentList_ex[eq]
            finally_equipments.append(key)
        finally_equipments.sort(key=SortFunction,reverse=True)
        for a in finally_equipments:
            a["id"] = i
            finally_equipment.append(a)
            i += 1
        # for eq in EquipmentList_ex.keys():
        #     key = EquipmentList_ex[eq]
        #     if str(key["lend_total"]) in finally_equipment:
        #         finally_equipment[str(key["lend_total"])]["items"].append(key)
        #     else:
        #         finally_equipment[str(key["lend_total"])] = {
        #             "items": [key],
        #         }
        # 用户
        i = 1
        for us in LendTotalList_ex.keys():
            key = LendTotalList_ex[us]
            finally_users.append(key)
        finally_users.sort(key=SortFunction,reverse=True)
        for a in finally_users:
            a["id"] = i
            # 排除访客数据
            if not "guest:" in a["lend_userid"]:
                # 借出的人（使用人）用户名
                LenderName = a["lend_userid"]
                for j in UsersList:
                    if j["id"] == a["lend_userid"]:
                        LenderName = j["name"]
                a["lend_userid"] = LenderName
                finally_user.append(a)
                i += 1
        # for us in LendTotalList_ex.keys():
        #     key = LendTotalList_ex[us]
        #     if str(key["lend_total"]) in finally_user:
        #         finally_user[str(key["lend_total"])]["items"].append(key)
        #     else:
        #         finally_user[str(key["lend_total"])] = {
        #             "items": [key],
        #         }
        return {"equipment": finally_equipment, "user": finally_user}
    except:
        log(event="获取某天的借出数据量时发生错误",state="Error",msg=traceback.format_exc())
    return {"equipment": {}, "user": {}}

# B_Start
def B__GetEquimentInfo(EQUIMENT_CODE):
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from equipment where code = %s'
                cursor.execute(sql, escape_string(EQUIMENT_CODE))
                result = cursor.fetchone()
                if not result:
                    return synthesisReturnData(0,"ok",{})
                return synthesisReturnData(0,"ok",{"id":result["id"], "name":result["name"]})
    except:
        return synthesisReturnData(-1,traceback.format_exc())

def B__UserExist(USER_CODE,type="code"):
    """判断用户是否存在"""
    try:
        if type == "id":
            a = getUserInfo_ByID(USER_CODE)
        else:
            a = getUserInfo(USER_CODE)
        b = True
        if a[0]["errcode"] != 0:
            b = False 
        return { "has": b, "data": a }
    except:
        return { "has": False, "data": synthesisReturnData(0,"ok",{}) }

def B__EquimentExist(EQUIMENT_CODE):
    """判断设备是否存在"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from equipment where code = %s and type = 0'
                cursor.execute(sql, escape_string(EQUIMENT_CODE))
                result = cursor.fetchone()
                if not result:
                    return synthesisReturnData(-1004,"ok",{})
                return synthesisReturnData(0,"ok",{"id":result["id"],"name":result["name"],"code":result["code"],"ascription":result["ascription"], "model":result["model"], "sn":result["sn"], "type":result["type"], "status":result["status"], "record_sha":result["record_sha"]})
    except:
        return synthesisReturnData(0,"ok",{})
# B_End
# [END] MAIN FUNCTION CODE AREA


# E_Start 免鉴权类功能
def UnPermissions_GetUserList():
    """免鉴权-获取用户列表（不包含display组）"""
    data = []

    # 排除的组id
    ExceptGroupId = []
    
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from `group`"
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        if i["type"] == "display":
                            ExceptGroupId.append(i["id"])
                sql = 'select * from user WHERE `type` = 0'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        if not i["group"] in ExceptGroupId:
                            data.append({"id":i["id"],"name":i["name"],"code":i["code"],"class":i["class"],"group":i["group"],"grade":i["grade"],"remark":i["remark"]})
                
                return synthesisReturnData(0,"ok",data)
    except:
        return synthesisReturnData(-1,traceback.format_exc())

# E_End


# [START]ERROR HANDLING CODE ARE
# HTTP[404]
@app.errorhandler(404)
def not_found(error):
    log(type="REQUEST",ip=getIp(flask.request),url=flask.request.url,event=f"[{request.method}] Page-Not-Found",msg="触发了404",state="Warning")
    return flask.render_template("404.html"), 404

# HTTP[500]
@app.errorhandler(500)
def serve_error(error):
    log(type="REQUEST",ip=getIp(flask.request),url=flask.request.url,event=f"[{request.method}] Server-Error",msg="触发了500",state="Warning")
    return flask.render_template("500.html"), 500
# [END]ERROR HANDLING CODE AREA

# [START]ROUTE CODE AREA
@app.route(f"{URL_PREFIX}/LatestVersion", methods=["GET","POST"])
def __RETURN_VERSION__():
    """返回最新版本号"""
    RESULT = synthesisReturnData(0,"ok",{"version":VERSION})
    log(type="REQUEST",event=f"Request Version Info at {getIp(flask.request)}",state="Info",msg=f"IP: {getIp(flask.request)} 请求了版本号,返回值:{RESULT[1]}",ip=getIp(flask.request),url=flask.request.url)
    return RESULT

@app.route(f"{URL_PREFIX}/redirect/<path:url>", methods=["GET"])
def Rredirect(url):
    return redirect(url)

# @app.route(f"{URL_PREFIX}/InternetAuthentication/loginBack", methods=REQ_METHODS)
# def RIAloginBack():
#     """上网认证-返回认证URL"""
#     log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"上网认证-返回认证URL",ip=getIp(flask.request),url=flask.request.url)
#     POST_data = request.form
#     TOKEN = getRequestToken(flask.request)
#     try:
#         user_ip = str(POST_data.get("u_ip"))
#         timestamp = str(POST_data.get("timestamp"))
#         mac = str(POST_data.get("mac"))
#         user_name = str(POST_data.get("u_name"))
#         user_id = str(POST_data.get("u_id"))
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
    
#     if not verifyPermissions(TOKEN,"internet.verify"):
#         RESULT = synthesisReturnData(-1005,"No Permission")
#         return RESULT
#     tokenRenewal(TOKEN)
    
#     key = "e4edc10319111938a705d8766077754b"
#     Token = md5(f"user_ip={user_ip}&timestamp={timestamp}&mac={mac}&upload=0&download=0&key={key}")
#     RESULT =  synthesisReturnData(0, "ok", {"url":f"https://portal.ikuai8-wifi.com/Action/webauth-up?type=20&user_id={user_id}&custom_name={user_name}&user_ip={user_ip}&timestamp={timestamp}&mac={mac}&token={Token}&release_type=1"})
#     return RESULT

@app.route(URL_PREFIX, methods=["GET"])
def __API_DEFAULT__():
    """默认路由"""
    return flask.render_template("403.html"),200

@app.route(f"{URL_PREFIX}/Dashboard/ContentData", methods=["GET"])
def __API_Dashboard_ContentData__():
    """获取Dashboard文字数据"""
    # log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取Dashboard文字数据接口",ip=getIp(flask.request),url=flask.request.url)
    try:
        __7Days_LR_Chart_DateData = GetLast7Days(NotNeedYear=True)
        __Lend_Total = GetLendTotal()
        __NotReturn_Total = GetNotReturnTotal()
        __Equipment_Total = GetEquipmentTotal()
        __Login_Total = GetLoginTotal()
        TopItems_Data = {
            "LendTotal": __Lend_Total,
            "NotReturnTotal": __NotReturn_Total,
            "EquipmentTotal": __Equipment_Total,
            "LoginTotal": __Login_Total,
        }
        RESULT = synthesisReturnData(0,"ok",{ "TopItemsData": TopItems_Data, "Days_LR_Text": __7Days_LR_Chart_DateData })
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/Dashboard/ChartData", methods=["GET"])
def __API_Dashboard_ChartData__():
    """获取Dashboard图表数据"""
    
    # log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取Dashboard图表数据接口",ip=getIp(flask.request),url=flask.request.url)
    try:
        __7Days_LR_Chart_DateData = GetLast7Days()
        index = 0
        __DATA_Charts_Days_LR = {}
        __DATA_LEND = []
        __DATA_RETURN = []
        __DATA_TOTAL_L = 0
        __DATA_TOTAL_R = 0
        for i in __7Days_LR_Chart_DateData:
            try:
                if not __DATA_Charts_Days_LR[i]:
                    __DATA_Charts_Days_LR[i] = {}
            except:
                __DATA_Charts_Days_LR[i] = {}
            __DATA_Charts_Days_LR[i]["LendTotal"] = GetDayLendDataTotal(i)
            __DATA_Charts_Days_LR[i]["ReturnTotal"] = GetDayReturnDataTotal(i)
            # BUG：每日归还率：若借出日期不是当天但归还日期是当天，则计算的归还率会超出100%
            # 所以需要获取限定日期的数据，即 归还日期等于借出日期 的数据才纳入统计
            if index == 6:
                __DATA_TOTAL_L = __DATA_Charts_Days_LR[i]["LendTotal"]
                __DATA_TOTAL_R = __DATA_Charts_Days_LR[i]["ReturnTotal"]
            __DATA_LEND.append(__DATA_Charts_Days_LR[i]["LendTotal"])
            __DATA_RETURN.append(__DATA_Charts_Days_LR[i]["ReturnTotal"])
            index += 1
        try:
            # abc = (__DATA_TOTAL_R / __DATA_TOTAL_L) * 100
            # if abc != 0:
            #     percent = '%.1f'%(abc)
            LR = GetTodayLendAndReturnPrecent()
            returnTotal = LR["returnTotal"]
            lendTotal = LR["lendTotal"]
            percent = (returnTotal / lendTotal) * 100
            if percent != 0:
                percent = '%.1f'%(percent)
        except ZeroDivisionError:
            percent = 0
        __DATA = {
            "LendTotal": __DATA_LEND,
            "ReturnTotal": __DATA_RETURN,
            "Source_LR": __DATA_Charts_Days_LR,
            "TodayTotal": {
                "lend": __DATA_TOTAL_L,
                "return": __DATA_TOTAL_R,
                "percent": percent
            },
        }
        RESULT = synthesisReturnData(0,"ok",__DATA)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/Dashboard/TableData", methods=["GET"])
def __API_Dashboard_TableData__():
    """获取Dashboard表格数据"""
    try:
        _ = GetLendRanking()
        _Data = {
            "equipment": _["equipment"],
            "user": _["user"],
        }
        RESULT = synthesisReturnData(0,"ok",_Data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT













# 免鉴权功能
@app.route(f"{URL_PREFIX}/get/userlist", methods=REQ_METHODS)      
def R_GetUserList_Up():
    """获取用户列表（免鉴权）"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取用户列表（免鉴权）接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    try:
        return UnPermissions_GetUserList()
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT












@app.route(f"{URL_PREFIX}/log/user", methods=REQ_METHODS)      
def RlogUser():
    """获取用户操作日志"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取用户操作日志接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    try:
        
        if not verifyPermissions(TOKEN,"log.manage.user"):
            RESULT = synthesisReturnData(-1005,"No Permission")
            return RESULT
        tokenRenewal(TOKEN)

        POST_data = request.form
        try:
            date = str(POST_data.get("date")) or None
        except:
            RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        RESULT = synthesisReturnData(0,"ok",getLog("USER",date))
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/log/request", methods=REQ_METHODS)      
def RlogRequest():
    """获取请求日志"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取请求日志接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    try:
        if not verifyPermissions(TOKEN,"log.manage.request"):
            RESULT = synthesisReturnData(-1005,"No Permission")
            return RESULT
        tokenRenewal(TOKEN)
        POST_data = request.form
        try:
            date = str(POST_data.get("date")) or None
        except:
            RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        RESULT = synthesisReturnData(0,"ok",getLog("REQUEST",date))
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/log/system", methods=REQ_METHODS)      
def RlogSystem():
    """获取系统日志"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取系统日志接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    try:
        if not verifyPermissions(TOKEN,"log.manage.system"):
            RESULT = synthesisReturnData(-1005,"No Permission")
            return RESULT
        tokenRenewal(TOKEN)
        POST_data = request.form
        try:
            date = str(POST_data.get("date")) or None
        except:
            RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        RESULT = synthesisReturnData(0,"ok",getLog("SYSTEM",date))
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/log/getFileDate", methods=REQ_METHODS)
def RlogGetDate():
    """获取日志文件列表"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取日志文件列表接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    try:
        if not verifyPermissions(TOKEN,"log.manage.getdate"):
            RESULT = synthesisReturnData(-1005,"No Permission")
            return RESULT
        tokenRenewal(TOKEN)
        POST_data = request.form
        try:
            types = str(POST_data.get("type")) or None
        except:
            RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        RESULT = synthesisReturnData(0,"ok",getAllLogFileName(types))
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/verifyPermissions", methods=REQ_METHODS)
def RverifyPermissions():
    """验证权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求验证权限接口",ip=getIp(flask.request),url=flask.request.url)
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        permissions = str(POST_data.get("permissions"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
    try:
        RESULT = synthesisReturnData(0,"ok",{"code":getLoginUserInfo_ByToken(TOKEN)["usercode"],"verify":verifyPermissions(TOKEN,permissions)})
    except:
        RESULT = synthesisReturnData(-1,"Running Function Error In Router",traceback.format_exc())
    return RESULT 

@app.route(f"{URL_PREFIX}/equipment/lend", methods=REQ_METHODS)
def Rlend():
    """设备借出路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求设备借出接口",ip=getIp(flask.request),url=flask.request.url)
    data = {}
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        tokenData = getLoginUserInfo_ByToken(TOKEN)
        try:
            user_code = str(POST_data.get("user_code"))
            if not user_code:
                user_code = tokenData["usercode"]
            eq_code = str(POST_data.get("equipment_code"))
            guest = POST_data.get("guest", False, str)
        except:
            RESULT = synthesisReturnData(-1001,"Invalid Parameter")
            return RESULT
        tokenRenewal(TOKEN)
        # 操作人
        data["operator"] = tokenData["name"]

        # 非管理员且非本人借出
        if tokenData["usercode"] != user_code and not verifyPermissions(TOKEN,"equipment.lend.helpothers"):
            # log(type=1,event="借出设备-JSON",ip=getIp(flask.request),msg=f"操作无法完成：没有权限为其他用户({user_code})借出设备({code})",username=username)
            RESULT = synthesisReturnData(-30001,"This user can't help others lend the equipment")
            return RESULT
        
        # 不是访客借出时
        if not guest:
            # 查找借出设备用户名称，然后记录到lend_info中
            if B__UserExist(user_code)["has"] == False:
                # log(type=1,event="借出设备-JSON",ip=getIp(flask.request),msg=f"操作无法完成：指派了一个不存在的用户({user_code})用于借出设备({code})",username=username)
                data["lend_user"] = "未知用户"
                RESULT = synthesisReturnData(-30002,"借出失败：找不到借出用户",data)
                return RESULT
            else:
                # 使用人
                afdskohfju = getUserInfo(user_code)[0]["data"]
                data["lend_user"] = afdskohfju["name"]
                # BREAKING CHANGE: 不再使用user_id，改用user_name
                user_id = afdskohfju["name"]
        # 是访客借出
        else:
            data["lend_user"] = guest
            user_id = f"guest:{guest}"

        # 查找借出设备名称，然后记录到lend_info中
        if B__EquimentExist(eq_code)[0]["errcode"] != 0:
            # log(type=1,event="借出设备-JSON",ip=getIp(flask.request),msg=f"操作无法完成：找不到该设备：{code}",username=username)
            data["eq_code"] = eq_code
            data["eq_name"] = "未知设备"
            RESULT = synthesisReturnData(-30003,"借出失败：找不到设备",data)
            return RESULT
        else:
            data["eq_code"] = eq_code
            aedgvpiklhn = B__GetEquimentInfo(eq_code)[0]["data"]
            eq_id = aedgvpiklhn["id"]
            data["eq_name"] = aedgvpiklhn["name"]

        # 1. 基本内容验证完毕，借出流程开始
        # 2. 验证设备是否已经借出，如果已经借出了则归还后再次借出
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from records where equipment_code = %s and status = 1'
                cursor.execute(sql, (escape_string(eq_code)))
                result = cursor.fetchone()
                if result:
                    # if not verifyPermissions(TOKEN,"equipment.lend.helpothers"):
                    #     # log(type=1,event="借出设备",ip=getIp(flask.request),msg=f"操作无法完成：设备({code})已在用户({user_code})登记过借出",username=username)
                    #     RESULT = synthesisReturnData(-30004,"The equipment has been lend out",data)
                    #     return RESULT
                    # 先归还，再借出
                    rlResult = Return_Operation(None,eq_code,TOKEN,True,"在借出时归还")
                    if rlResult[0]["errcode"] != 0:
                        RESULT = synthesisReturnData(-30005,f"Error Was Happend When Return this equipment. It Said{rlResult[0]['errmsg']}",data)
                        return RESULT
            # 借出
            if tokenData["usercode"] != user_code:
                data["remark"] = "以他人身份借出设备"
            sha = sha256(eq_code+TOKEN+str(get_milliTimestamp())+str(random.randint(1,99999999)))
            data["SHA"] = sha
            timer_S5364fdg = get_time()
            with conn.cursor() as cursor:
                sql = 'INSERT INTO records (equipment_id, equipment_name, equipment_code, lend_userid, lend_operater, lend_date, status, record_sha) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
                cursor.execute(sql, (int(eq_id), data["eq_name"], escape_string(eq_code), user_id, tokenData["name"], escape_string(timer_S5364fdg), 1, sha))
                lendId = cursor.lastrowid
                sql = 'UPDATE equipment SET status = %s,record_sha = %s WHERE code = %s'
                cursor.execute(sql, (2, sha, escape_string(eq_code)))
                data["lend_id"] = lendId
                conn.commit()
            data["lend_time"] = timer_S5364fdg
            RESULT = synthesisReturnData(0,"ok",data)
        # log(type=1,event="借出设备-JSON",ip=getIp(flask.request),msg=f"设备({code})已在用户({user_code})借出成功",username=username)
    except:
        # log(event="RouteError",ip=getIp(flask.request),url=flask.request.url,msg=traceback.format_exc())
        RESULT = synthesisReturnData(-1,"Lending Error",traceback.format_exc())
    return RESULT

def Return_Operation(user_code,eq_code,TOKEN,NeedRemark=False,remark=""):
    """归还操作函数"""
    data = {}
    tokenData = getLoginUserInfo_ByToken(TOKEN)
    # 操作人
    data["operator"] = tokenData["name"]

    try:
        # 本人归还（系统归还）
        if B__UserExist(tokenData["usercode"])["has"] == False:
            # log(type=1,event="借出设备-JSON",ip=getIp(flask.request),msg=f"操作无法完成：指派了一个不存在的用户({user_code})用于借出设备({code})",username=username)
            data["return_user"] = "未知用户"
            RESULT = synthesisReturnData(-40003,"Can't find this user account",data)
            return RESULT
        else:
            # 归还人
            afdskohfju = getUserInfo(tokenData["usercode"])[0]["data"]
            data["return_user"] = afdskohfju["name"]
            # BREAKING CHANGE: 不再使用user_id，改用user_name
            user_id = afdskohfju["name"]

        # 获取设备信息
        if B__EquimentExist(eq_code)[0]["errcode"] != 0:
            # log(type=1,event="归还设备-JSON",ip=getIp(flask.request),msg=f"操作无法完成：找不到该设备：{code}",username=username)
            data["eq_code"] = eq_code
            data["eq_name"] = "未知设备"
            RESULT = synthesisReturnData(-40001,"The equipment cannot be found",data)
            return RESULT
        else:
            data["eq_code"] = eq_code
            data["eq_name"] = B__GetEquimentInfo(eq_code)[0]["data"]["name"]
        
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from records where equipment_code = %s and status = 1'
                cursor.execute(sql, (escape_string(eq_code)))
                result = cursor.fetchone()
                # 如果没有数据
                if not result:
                    # log(type=1,event="归还设备-JSON",ip=getIp(flask.request),msg=f"操作无法完成：设备({code})已登记过归还",username=username)
                    RESULT = synthesisReturnData(-40004,"The equipment has been return in",data)
                    return RESULT
                # ↓ 保留代码！原本帮还需要权限认证的，现在不需要了。
                # elif getLoginUserInfo_ByToken(TOKEN)["usercode"] != user_code and not verifyPermissions(TOKEN,"equipment.return.helpothers"):
                #     # log(type=1,event="归还设备-JSON",ip=getIp(flask.request),msg=f"操作无法完成：没有权限为其他用户({user_code})归还设备({code})",username=username)
                #     RESULT = synthesisReturnData(-40002,"This user can't help others return the equipment",data)
                #     return RESULT

                try:
                    if int(result["lend_userid"]) != tokenData["uid"]:
                        data["remark"] = "归还他人借出设备"
                except:
                    # 只有一种情况下，无法将lend_userid格式化为int，说明是访客借出
                    # 2025.02 BreakingChange: lend_userid变更为借出人名字，所以需要判断是否本人名字再决定
                    if not result["lend_userid"] == tokenData["name"]:
                        data["remark"] = "归还访客借出设备"
                # 有权限帮还或是借出人归还
                with conn.cursor() as cursor:
                    if not NeedRemark:
                        sql = 'UPDATE records SET status = 0,return_date = %s,return_userid = %s,return_operater = %s WHERE equipment_code = %s and status = 1'
                        cursor.execute(sql, (get_time(), user_id, escape_string(tokenData["name"]), escape_string(eq_code)))
                    else:
                        sql = 'UPDATE records SET status = 0,return_date = %s,return_userid = %s,return_operater = %s,remark = %s WHERE equipment_code = %s and status = 1'
                        cursor.execute(sql, (get_time(), user_id, escape_string(tokenData["name"]), escape_string(remark), escape_string(eq_code)))
                    sql = 'UPDATE equipment SET status = 0 WHERE code = %s'
                    cursor.execute(sql, (escape_string(eq_code)))
                    conn.commit()
                    # log(type=1,event="归还设备-JSON",ip=getIp(flask.request),msg=f"设备({code})已在用户({user_code})归还成功",username=username)
                data["return_time"] = get_time()
                RESULT = synthesisReturnData(0,"ok",data)
    except:
        # log(event="RouteError",ip=getIp(flask.request),url=flask.request.url,msg=traceback.format_exc())
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/equipment/return", methods=REQ_METHODS)
def Rreturn():
    """设备归还路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求设备归还接口",ip=getIp(flask.request),url=flask.request.url)
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        user_code = str(POST_data.get("user_code"))
        eq_code = str(POST_data.get("equipment_code"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    tokenRenewal(TOKEN)
    # 给代理了
    return Return_Operation(user_code,eq_code,TOKEN)
    

# @app.route(f"{URL_PREFIX}/record_list", methods=REQ_METHODS)
# def RrecordList():
#     """借出记录路由"""
#     log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求借出记录接口",ip=getIp(flask.request),url=flask.request.url)
#     data = {}
#     try:
#         A__CleanTimeoutToken()
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from records where status = 1 ORDER BY id;'
#                 cursor.execute(sql)
#                 result = cursor.fetchall()
#                 if not result:
#                     index = 0
#                     for i in result:
#                         user_code = i[1]
#                         eq_code = i[2]
#                         user_name = getUserInfo(user_code)[0]["data"]["name"]
#                         if user_name == False:
#                             user_name = "Error：找不到用户"
#                         eq_name = B__GetEquimentInfo(eq_code)[0]["data"]["name"]
#                         if eq_name == False:
#                             eq_name = "Error：找不到设备"
#                         data[index]={"record_id":i[0],"user_name":user_name,"user_code":user_code,"eq_name":eq_name,"eq_code":eq_code,"date":i[3]}
#                         index += 1
#                     RESULT = synthesisReturnData(0,"ok",data)
#     except Exception as err:
#         RESULT = synthesisReturnData(-1,"Running Function Error In Router",traceback.format_exc())
#     return RESULT

def convertParamerter_SQLmode(data:dict):
    """转换数据，变成sql格式"""
    """{'a':'b'} to `a` = `b`"""
    res = []
    for i in data.keys():
        di = f"'{data[i]}'"
        if data[i] == None:
            break
        if data[i] == "":
            di = 'NULL'
        res.append(f"`{i}` = {di} ")
    return ",".join(res)


@app.route(f"{URL_PREFIX}/equipment/list", methods=REQ_METHODS)
def RequipmentList():
    """设备列表路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求设备列表接口",ip=getIp(flask.request),url=flask.request.url)
    data = []
    TOKEN = getRequestToken(flask.request)
    try:

        if not verifyPermissions(TOKEN,"equipment.manage.getlist"):
            RESULT = synthesisReturnData(-1005,"No Permission")
            return RESULT
        tokenRenewal(TOKEN)

        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from equipment'
                cursor.execute(sql)
                result = cursor.fetchall()
                # data["lenght"] = len(result)
                index = 0  
                for i in result:
                    data.append({"id":i["id"],"eq_name":i["name"],"eq_code":i["code"],"ascription":i["ascription"],"model":i["model"],"sn":i["sn"],"type":i["type"],"status":i["status"],"record_sha":i["record_sha"]})
                    index += 1
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/equipment/add", methods=REQ_METHODS)
def RequipmentAdd():
    """设备添加路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求设备添加接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    try:
        name = str(POST_data.get("eqname"))
        code = str(POST_data.get("eqcode"))
        ascription = str(POST_data.get("ascription")) or ""
        sn = str(POST_data.get("sn")) or ""
        model = str(POST_data.get("model")) or ""
        types = str(POST_data.get("type")) or ""
        status = str(POST_data.get("status")) or ""
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"equipment.manage.add"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO equipment (name, code, ascription, model, sn, type, status) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (escape_string(name),escape_string(code),escape_string(ascription),escape_string(model),escape_string(sn),escape_string(types),escape_string(status)))
                conn.commit()
                data["id"] = cursor.lastrowid
                
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/equipment/edit", methods=REQ_METHODS)
def RequipmentEdit():
    """设备编辑路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求设备编辑接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    
    try:
        ids = POST_data.get("id",None)
        name = POST_data.get("eqname",None)
        code = POST_data.get("eqcode",None)
        ascription = POST_data.get("ascription",None)
        sn = POST_data.get("sn",None)
        model = POST_data.get("model",None)
        types = POST_data.get("type",None)
        status = POST_data.get("status",None)
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"equipment.manage.edit"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = f'UPDATE equipment SET {convertParamerter_SQLmode({"name":name,"code":code,"ascription":ascription,"model":model,"sn":sn,"type":types,"status":status})} WHERE id = {ids}'
                cursor.execute(sql)
                conn.commit()
            data["id"] = ids
            RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/equipment/del", methods=REQ_METHODS)
def RequipmentDel():
    """设备删除路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求设备删除接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form

    try:
        ids = str(POST_data.get("id"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if  not verifyPermissions(TOKEN,"equipment.manage.del"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "DELETE FROM equipment WHERE id=%s"
                cursor.execute(sql, int(ids))
                conn.commit()
        data["id"] = ids
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/equipment/info", methods=REQ_METHODS)
def RequipmentInfo():
    """设备信息路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求设备信息接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    try:
        code = str(POST_data.get("code"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"equipment.get"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)
    try:
        RESULT = B__EquimentExist(code)
        return RESULT
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/user/list", methods=REQ_METHODS)
def RuserList():
    """账号列表路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求账号列表接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    
    if not verifyPermissions(TOKEN,"account.manage.getlist"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from user WHERE `type` = 0'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        data.append({"id":i["id"],"name":i["name"],"code":i["code"],"class":i["class"],"password":None,"share_device":i["share_device"],"group":i["group"],"grade":i["grade"],"reg_time":i["reg_time"],"join_time":i["join_time"],"login_time":i["login_time"],"openid":i["openid"],"remark":i["remark"]})
                    RESULT = synthesisReturnData(0,"ok",data)
                else:
                    RESULT = synthesisReturnData(-1001,"Null Data")
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

def letUserPermissionClose(uid: int,permissionName: str):
    """关闭账号权限"""
    # 判断权限是否存在，不存在则添加，存在则将open设置为False
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from permissions WHERE `type` = 'userid' AND `object` = %s AND `val` = %s"
                cursor.execute(sql,(uid,permissionName))
                result = cursor.fetchone()
                if not result:
                    sql = "insert into permissions(`type`,`object`,`val`,`open`) VALUES ('userid',%s,%s,%s)"
                    cursor.execute(sql,(uid,permissionName,False))
                    conn.commit()
                else:
                    sql = "UPDATE `permissions` SET `open` = %s WHERE `id` = %s"
                    cursor.execute(sql,(False,result["id"]))
                    conn.commit()
        return True
    except:
        log(type="USER",event=f"Let Permission to close Error",state="Error",msg=f"关闭权限({permissionName})失败",ip=getIp(flask.request),url=flask.request.url)
        return False

def letUserPermissionOpen(uid:int, permissionName:str):
    """开启账号权限"""
    # 判断权限是否存在，不存在则添加，存在则将open设置为True
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from permissions WHERE `type` = 'userid' AND `object` = %s AND `val` = %s"
                cursor.execute(sql,(uid,permissionName))
                result = cursor.fetchone()
                if not result:
                    sql = "insert into permissions(`type`,`object`,`val`,`open`) VALUES ('userid',%s,%s,%s)"
                    cursor.execute(sql,(uid,permissionName,True))
                    conn.commit()
                else:
                    sql = "UPDATE `permissions` SET `open` = %s WHERE `id` = %s"
                    cursor.execute(sql,(True,result["id"]))
                    conn.commit()
        return True
    except:
        return False
        
def besidesUserPermission(uid: int, permissionList: list):
    """筛选账号权限，移除"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from permissions WHERE `type` = 'userid' AND `object` = %s"
                cursor.execute(sql,(uid))
                result = cursor.fetchall()
                for i in result:
                    if i["val"] not in permissionList:
                        sql = "DELETE FROM `permissions` WHERE `id` = %s"
                        cursor.execute(sql,i["id"])
                        conn.commit()
        return True
    except:
        return False

def delUserAllPermission(uid: int):
    """删除账号所有权限"""
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "DELETE FROM `permissions` WHERE `type` = 'userid' AND `object` = %s"
                cursor.execute(sql,(uid))
                conn.commit()
        return True
    except:
        return False

@app.route(f"{URL_PREFIX}/user/add", methods=REQ_METHODS)
def RuserAdd():
    """账号添加路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求账号添加接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    
    try:
        name = POST_data.get("name",None)
        code = POST_data.get("code",None)
        cla = POST_data.get("class",None)
        grade = POST_data.get("grade",None)
        if grade == "":
            grade = None
        password = POST_data.get("password",None)
        permissions_open = POST_data.get("permissions_open",None)
        permissions_close = POST_data.get("permissions_close",None)
        group = int(POST_data.get("group",0,type=int) or 0)
        # reg_time = POST_data.get("reg_time",get_time())
        reg_time = None
        share_device = int(POST_data.get("share_device",2))
        join_time = POST_data.get("join_time",get_time())
        remark = POST_data.get("remark",None)
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"account.manage.add"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO user (`name`, `code`, `class`, `password`, `group`, `grade`, `share_device`, `reg_time`, `join_time`, `remark`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (name,code,cla,password,group,grade,share_device,reg_time,join_time,remark))
                conn.commit()
                data["id"] = cursor.lastrowid
                ids = data["id"]
                # 用户权限
                if permissions_close or permissions_open:
                    permissions_list = []
                    permissions_list.extend(permissions_close.split(","))
                    permissions_list.extend(permissions_open.split(","))
                    besidesUserPermission(ids,permissions_list)
                    # 关闭用户某权限
                    if len(permissions_close.split(",")) > 0:
                        for i in permissions_close.split(","):
                            letUserPermissionClose(ids,i)
                    # 开启用户某权限
                    if len(permissions_open.split(",")) > 0:
                        for i in permissions_open.split(","):
                            letUserPermissionOpen(ids,i)
        # if permissions and len(permissions.split(",")) > 0:
        #     AAP = addUserPermissions(data["id"],permissions.split(","))
        #     if AAP[0]["errcode"] != 0:
        #         return synthesisReturnData(-1,"Cannot Add User's Permissions. " + AAP[0]["errmsg"],data)
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/user/edit", methods=REQ_METHODS)
def RuserEdit():
    """账号编辑路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求账号编辑接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    try:
        ids = POST_data.get("id",None)
        name = POST_data.get("name",None)
        code = POST_data.get("code",None)
        cla = POST_data.get("class",None)
        grade = POST_data.get("grade",None)
        password = POST_data.get("password",None)
        permissions_open = POST_data.get("permissions_open",None)
        permissions_close = POST_data.get("permissions_close",None)
        share_device = POST_data.get("share_device",2)
        group = POST_data.get("group",None)
        reg_time = POST_data.get("reg_time",None)
        join_time = POST_data.get("join_time",None)
        remark = POST_data.get("remark",None)
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"account.manage.edit"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                a = {"name":name,"code":code,"class":cla,"group":group,"grade":grade,"share_device":share_device,"reg_time":reg_time,"join_time":join_time,"remark":remark}
                if password:
                    a = {"name":name,"code":code,"class":cla,"group":group,"password":password,"grade":grade,"share_device":share_device,"reg_time":reg_time,"join_time":join_time,"remark":remark}
                sql = f'UPDATE `user` SET {convertParamerter_SQLmode(a)} WHERE id = {int(ids)}'
                cursor.execute(sql)
                conn.commit()
        data["id"] = ids
        # 用户权限
        if permissions_close or permissions_open:
            permissions_list = []
            permissions_list.extend(permissions_close.split(","))
            permissions_list.extend(permissions_open.split(","))
            besidesUserPermission(ids,permissions_list)
            # 关闭用户某权限
            if len(permissions_close.split(",")) > 0:
                for i in permissions_close.split(","):
                    letUserPermissionClose(ids,i)
            # 开启用户某权限
            if len(permissions_open.split(",")) > 0:
                for i in permissions_open.split(","):
                    letUserPermissionOpen(ids,i)
        else:
            # 确认permissions_close和permissions_open都为空后，删除该用户全部权限
            delUserAllPermission(ids)
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/user/del", methods=REQ_METHODS)
def RuserDel():
    """账号删除路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求账号删除接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)

    data = {}
    POST_data = request.form

    try:
        ids = str(POST_data.get("id"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"account.manage.del"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "DELETE FROM user WHERE id=%s"
                # 假删
                # sql = "update user set type=-1 where id=%s"
                cursor.execute(sql, int(ids))
                conn.commit()
                # 删除用户所有权限
                delUserAllPermission(int(ids))
        data["id"] = ids
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/user/info", methods=REQ_METHODS)
def Ruserinfo():
    """查询用户信息路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求查询用户信息接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    
    if not verifyPermissions(TOKEN,"account.manage.get"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)
    tokenData = getLoginUserInfo_ByToken(TOKEN)
    RESULT = synthesisReturnData(0,"ok",{"name":tokenData["name"],"code":tokenData["usercode"],"class":tokenData["class"],"password":None,"share_device":tokenData["share_device"]})
    return RESULT

@app.route(f"{URL_PREFIX}/user/random_GetUserList", methods=REQ_METHODS)
def RrandomGetUserList():
    """随机抽取-账号列表路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求随机抽取-账号列表路由接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    ug = []
    gg = []
    
    if not verifyPermissions(TOKEN,"account.random"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    # 排除的组id
    ExceptGroupId = []
    
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from `group`"
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        if not i["type"] == "display":
                            gg.append({"id":i["id"],"name":i["name"],"type":i["type"],"desc":i["desc"]})
                        else:
                            ExceptGroupId.append(i["id"])
                        
                sql = 'select * from user WHERE `type` = 0'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        if not i["group"] in ExceptGroupId:
                            ug.append({"id":i["id"],"name":i["name"],"code":i["code"],"class":i["class"],"group":i["group"],"share_device":i["share_device"],"grade":i["grade"],"reg_time":i["reg_time"],"join_time":i["join_time"],"login_time":i["login_time"],"remark":i["remark"]})
                
                RESULT = synthesisReturnData(0,"ok",{"user":ug,"group":gg})
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/group/list", methods=REQ_METHODS)
def RgroupList():
    """组列表路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求账号列表接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    
    if not verifyPermissions(TOKEN,"group.manage.getlist"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `group`'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        data.append({"id":i["id"],"type":i["type"],"name":i["name"],"desc":i["desc"]})
                    RESULT = synthesisReturnData(0,"ok",data)
                else:
                    RESULT = synthesisReturnData(-1001,"Null Data")
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/group/info", methods=REQ_METHODS)
def RgroupInfo():
    """组信息路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求查询组信息接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    try:
        gid = str(POST_data.get("gid"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"account.manage.get"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)
    
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `group` where id = %s'
                cursor.execute(sql, escape_string(gid))
                result = cursor.fetchall()
                if result:
                    for i in result:
                        data.append({"id":i["id"],"type":i["type"],"name":i["name"],"desc":i["desc"]})
                    RESULT = synthesisReturnData(0,"ok",data)
                else:
                    RESULT = synthesisReturnData(-1001,"Null Data")
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/group/user", methods=REQ_METHODS)
def RgroupUser():
    """组用户路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求组用户接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    if not verifyPermissions(TOKEN,"account.manage.edit"):
        return synthesisReturnData(-1005,"No Permission")
    tokenRenewal(TOKEN)
    try:
        return getUserWithGroup()
    except:
        return synthesisReturnData(-1,"System Error",traceback.format_exc())

@app.route(f"{URL_PREFIX}/group/add", methods=REQ_METHODS)
def Rgroupadd():
    """组添加路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求组添加接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    
    try:
        name = str(POST_data.get("name"))
        types = str(POST_data.get("type"))
        desc = str(POST_data.get("desc"))
        push = str(POST_data.get("push",""))
        permission = str(POST_data.get("permission",""))
        permissions = permission.split(",")
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"account.manage.edit"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO `group` (`name`, `type`, `desc`) VALUES (%s, %s, %s)"
                cursor.execute(sql, (escape_string(name),escape_string(types),escape_string(desc)))
                conn.commit()
                data["id"] = cursor.lastrowid
        useri = push.split(",")
        if useri:
            for i in useri:
                with pymysql.connect(**mysql_config) as conn:
                    with conn.cursor() as cursor:
                        a = {"group":data["id"]}
                        sql = f"UPDATE `user` SET {convertParamerter_SQLmode(a)} WHERE `code` = '{i}'"
                        cursor.execute(sql)
                        conn.commit()
        # 添加权限
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                for p in permissions:
                    sql = f"INSERT INTO `permissions` (`object`, `type`, `val`) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (escape_string(data["id"]),"groupid",escape_string(p)))
                    conn.commit()
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1, traceback.format_exc())
    return RESULT

def EditGroupPermissions(gid:int,permissions:list):
    """编辑组权限"""
    try:
        DelList = []
        AddList = []
        # 排除空项
        permissions = [i for i in permissions if i]
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * from `permissions` WHERE `object` = %s AND `type` = 'groupid'"
                cursor.execute(sql, escape_string(gid))
                GroupPermissions = cursor.fetchall()
                GroupPermissionsList = []
                for i in GroupPermissions:
                    GroupPermissionsList.append(i["val"])
                    if i["val"] not in permissions:
                        sql = f"DELETE FROM `permissions` WHERE `object` = %s AND `type` = 'groupid' AND `val` = %s"
                        cursor.execute(sql, (escape_string(gid),escape_string(i["val"])))
                        conn.commit()
                        DelList.append(i["id"])
                for j in permissions:
                    if j not in GroupPermissionsList:
                        sql = f"INSERT INTO `permissions` (`object`, `type`, `val`) VALUES (%s, 'groupid', %s)"
                        cursor.execute(sql, (escape_string(gid),escape_string(j)))
                        conn.commit()
                        AddList.append(cursor.lastrowid)
                return {
                    "del": DelList,
                    "add": AddList
                }
    except:
        return {
            "del": [],
            "add": []
        }

@app.route(f"{URL_PREFIX}/group/edit", methods=REQ_METHODS)
def Rgroupedit():
    """组编辑路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求组编辑接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    try:
        ids = str(POST_data.get("id"))
        name = str(POST_data.get("name"))
        types = str(POST_data.get("type",""))
        desc = str(POST_data.get("desc",""))
        permission = str(POST_data.get("permission",""))
        permissions = permission.split(",")
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"account.manage.edit"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        GPE = EditGroupPermissions(ids,permissions)
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "UPDATE `group` SET `name` = %s,`desc` = %s, `type` = %s WHERE `id` = %s"
                cursor.execute(sql, (escape_string(name),escape_string(desc),escape_string(types),int(ids)))
                conn.commit()
        data["id"] = ids
        data["permissions"] = GPE
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/group/del", methods=REQ_METHODS)
def Rgroupdel():
    """组删除路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求组删除接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)

    data = {}
    POST_data = request.form

    try:
        ids = str(POST_data.get("id"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"account.manage.edit"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                # 设置用户组为默认组
                sql1 = "UPDATE `user` SET `group` = 1 WHERE `group` = %s"
                cursor.execute(sql1, int(ids))
                sql = "DELETE FROM `group` WHERE id=%s"
                cursor.execute(sql, int(ids))
                conn.commit()
        data["id"] = ids
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/systemlist", methods=REQ_METHODS)
def RpermissionsList():
    """获取权限列表路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取权限列表接口",ip=getIp(flask.request),url=flask.request.url)
    data = []
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from `permissions` where  type = 'system'"
                cursor.execute(sql)
                result = cursor.fetchall()
                if not result:
                    RESULT = synthesisReturnData(-1001,"Null Data")
                for i in result:
                    data.append({"id":i["id"],"val":i["val"],"object":i["object"],"remark":i["remark"],"type":"system"})
                RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/userHasPermissions", methods=REQ_METHODS)
def RuserHasPermissions():
    """获取用户权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取用户权限接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    try:
        userinfo = getLoginUserInfo_ByToken(TOKEN)
        RESULT =  synthesisReturnData(0,"ok",getUserPermissions(userinfo["uid"],userinfo["group"]))
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/userlist", methods=REQ_METHODS)
def RpermissionsUserList():
    """获取全部用户权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取全部用户权限接口",ip=getIp(flask.request),url=flask.request.url)
    data = {}
    users = {}
    group = {}
    TOKEN = getRequestToken(flask.request)
    if not verifyPermissions(TOKEN,"permissions.manage"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from `permissions` where `type` = 'userid'"
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        i["mode"] = "user"
                        if i["object"] in users:
                            users[i["object"]].append(i)
                        else:
                            users[i["object"]] = [i]
                sql = "select * from `permissions` where `type` = 'groupid'"
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    for i in result:
                        i["mode"] = "group"
                        if i["object"] in group:
                            group[i["object"]].append(i)
                        else:
                            group[i["object"]] = [i]
                RESULT = synthesisReturnData(0,"ok",{"users":users,"group":group})
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/Allgrouplist", methods=REQ_METHODS)
def RpermissionsAllGroupList():
    """获取全部用户组权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取全部用户组权限接口",ip=getIp(flask.request),url=flask.request.url)
    data = []
    TOKEN = getRequestToken(flask.request)
    if not verifyPermissions(TOKEN,"account.manage.edit"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from `permissions` where type = 'groupid'"
                cursor.execute(sql)
                result = cursor.fetchall()
                GroupPermissionsList = {}
                if result:
                    for i in result:
                        if i["object"] in GroupPermissionsList:
                            GroupPermissionsList[i["object"]].append(i)
                        else:
                            GroupPermissionsList[i["object"]] = [i]
                sql = "select * from `group`"
                cursor.execute(sql)
                group = cursor.fetchall()
                if group:
                    for i in group:
                        if str(i["id"]) in GroupPermissionsList:
                            groupPermissions = GroupPermissionsList[str(i["id"])]
                        else:
                            groupPermissions = []
                        data.append({
                            "id": i["id"],
                            "name": i["name"],
                            "permissionsList": groupPermissions,
                        })
                RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/groupEdit", methods=REQ_METHODS)
def RpermissionsGroupEdit():
    """编辑用户组权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求编辑用户组权限接口",ip=getIp(flask.request),url=flask.request.url)
    data = {}
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        gid = POST_data.get("gid",None)
        val = POST_data.get("val","")
        val = val.split(",")
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"account.manage.edit"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)
    
    try:
        alreadyAppend = []
        appendId = []
        removeId = []
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from `permissions` where object = %s and type = 'groupid'"
                cursor.execute(sql,(gid))
                result = cursor.fetchall()
                if result:
                    for i in result:
                        # 不在，移除
                        if not i["val"] in val:
                            sql = "delete from `permissions` where object = %s and type = 'groupid' and val = %s"
                            cursor.execute(sql,(gid,i["val"]))
                            conn.commit()
                            removeId.append(i["val"])
                        else:
                            alreadyAppend.append(i["val"])
                        # 查看是否有新增
                        for j in val:
                            if not j in alreadyAppend:
                                sql = "insert into `permissions` (object,type,val) values (%s,'groupid',%s)"
                                cursor.execute(sql,(gid,j))
                                conn.commit()
                                alreadyAppend.append(j)
                                appendId.append(j)
                # 权限列表中没有这个组的数据，全部添加
                else:
                    for i in val:
                        if not i in alreadyAppend:
                            sql = "insert into `permissions` (object,type,val) values (%s,'groupid',%s)"
                            cursor.execute(sql,(gid,i))
                            conn.commit()
                            alreadyAppend.append(i)
                            appendId.append(i)
                RESULT = synthesisReturnData(0,"ok")
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())


@app.route(f"{URL_PREFIX}/permissions/pagePermissions", methods=REQ_METHODS)
def RpagePermissions():
    """获取页面权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"获取请求页面权限接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)

    try:
        RESULT =  getPagePermissionsList()
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/systemadd", methods=REQ_METHODS)
def RpermissionsSystemAdd():
    """添加系统权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求添加系统权限接口",ip=getIp(flask.request),url=flask.request.url)
    data = {}
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        val = str(POST_data.get("val"))
        object = str(POST_data.get("object",""))
        remark = str(POST_data.get("remark",""))
        push = POST_data.get("push","")
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"permissions.manage"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO `permissions` (`type`, `val`, `object`, `remark`) VALUES ('system', %s, %s, %s)"
                cursor.execute(sql, (val,object,remark))
                conn.commit()
                data["id"] = cursor.lastrowid
        # 不需要推送到用户
        if push == "":
            RESULT = synthesisReturnData(0,"ok",data)
        elif push == "all":
            a1 = UnPermissions_GetUserList()
            if a1[0]["errcode"] != 0:
                return synthesisReturnData(-10010,"GetUsersListError",traceback.format_exc())
            for j in a1[0]["data"]:
                AAP = addUserPermissions(j["id"],val,"ByAddPermission")
                if AAP[0]["errcode"] != 0:
                    return synthesisReturnData(-1,"Cannot Add User's Permissions: " + AAP[0]["errmsg"],user)
            return synthesisReturnData(0,"ok",data)
        else:
            # 需要推送的用户组列表
            GroupList = push.split(",")
            # 用户组列表
            UserGroupList = getUserWithGroup()[0]
            if UserGroupList["errcode"] != 0:
                return synthesisReturnData(-10010,"GetUsersGroupListError",traceback.format_exc())
            # 找对应
            for i in list(UserGroupList["data"]):
                if i in GroupList:
                    user = UserGroupList["data"][i]
                    user_id = user["id"]
                    AAP = addUserPermissions(user_id,val,"ByAddPermission")
                    if AAP[0]["errcode"] != 0:
                        return synthesisReturnData(-1,"Cannot Add User's Permissions: " + AAP[0]["errmsg"],user)
                    return synthesisReturnData(0,"ok",data)
                else:
                    return synthesisReturnData(-1,"Cannot Add User's Permissions: Group Error.")
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/systemremove", methods=REQ_METHODS)
def RpermissionsSystemRemove():
    """删除系统权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求删除系统权限接口",ip=getIp(flask.request),url=flask.request.url)
    data = {}
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        pid = str(POST_data.get("pid"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"permissions.manage"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "select * from `permissions` where id = %s"
                cursor.execute(sql, pid)
                result = cursor.fetchone()
                if not result:
                    RESULT = synthesisReturnData(-1001,"Null Data")
                    return RESULT
                val = result["val"]
                sql = "DELETE FROM `permissions` WHERE val=%s"
                cursor.execute(sql, val)
                conn.commit()
        data["id"] = pid
        data["val"] = val
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/permissions/systemedit", methods=REQ_METHODS)
def RpermissionsSystemEdit():
    """编辑系统权限路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求编辑系统权限接口",ip=getIp(flask.request),url=flask.request.url)
    data = {}
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        val = POST_data.get("val",None)
        pid = POST_data.get("pid","")
        remark = POST_data.get("remark","")
        object = POST_data.get("object","")
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"permissions.manage"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        if not val:
            a = {"val":val,"remark":remark,"object":object}
        else:
            a = {"remark":remark,"object":object}
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                ######
                sql0 = "select * from `permissions` where id = %s"
                cursor.execute(sql0, pid)
                result = cursor.fetchone()
                if not result:
                    RESULT = synthesisReturnData(-1001,"Null Data")
                    return RESULT
                val_o = result["val"]

                sql1 = f"UPDATE `permissions` SET {convertParamerter_SQLmode(a)} WHERE `id`={pid}"
                cursor.execute(sql1)
                # 减少数据库操作
                if val_o != val:
                    sql2 = f"UPDATE `permissions` SET {convertParamerter_SQLmode({'val': val})} WHERE `val`={val_o} AND `type`='userid'"
                    cursor.execute(sql2)
                conn.commit()
                data["val"] = val
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())

@app.route(f"{URL_PREFIX}/permissions/init", methods=REQ_METHODS)
def RpermissionsSystemInit():
    """系统权限初始化路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求系统权限初始化接口",ip=getIp(flask.request),url=flask.request.url)
    data = []
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        arr = str(POST_data.get("arr"))
        arr = json.loads(arr)
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"permissions.manage"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        for i in list(arr.keys()):
            val = i
            object = arr[i]["o"]
            try:
                with pymysql.connect(**mysql_config) as conn:
                    with conn.cursor() as cursor:
                        sql = "select * from `permissions` where val = %s"
                        cursor.execute(sql, val)
                        result = cursor.fetchone()
                        if not result:
                            sql = "INSERT INTO `permissions` (`type`, `val`, `object`, `remark`) VALUES ('system', %s, %s, %s)"
                            cursor.execute(sql, (val,object,"用户-初始化系统权限"))
                            conn.commit()
                            data.append(cursor.lastrowid)
            except:
                return synthesisReturnData(-1,f"init val: {i} has been error",traceback.format_exc())
        return synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT


@app.route(f"{URL_PREFIX}/record/list", methods=REQ_METHODS)
def RrecordList():
    """记录列表路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求记录列表接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    
    if not verifyPermissions(TOKEN,"equipment.record.getlist"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `records`'
                cursor.execute(sql)
                result = cursor.fetchall()
                for i in result:
                    LEND_USERNAME = i["lend_userid"]
                    RETURN_USERNAME = i["return_userid"]
                    # 使用人应是借出用户的id对应的人
                    a = B__UserExist(i["lend_userid"],"id")
                    if a["has"] == True:
                        LEND_USERNAME = a["data"][0]["data"]["name"]
                    elif "guest:" in i["lend_userid"]:
                        LEND_USERNAME = i["lend_userid"]
                    # 归还人应是归还用户的id对应的人
                    b = B__UserExist(i["return_userid"],"id")
                    if b["has"] == True:
                        RETURN_USERNAME = b["data"][0]["data"]["name"]
                    Equipment_name = i["equipment_name"]
                    c = B__EquimentExist(i["equipment_code"])
                    if c[0]["errcode"] == 0:
                        Equipment_name = c[0]["data"]["name"]
                    data.append({"id":i["id"],"eqname":Equipment_name,"eqcode":i["equipment_code"],"lendtime":i["lend_date"],"user":LEND_USERNAME,"lender":i["lend_operater"],"returntime":i["return_date"],"returner":RETURN_USERNAME,"status":i["status"],"record_sha":i["record_sha"],"remark":i["remark"]})
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/record/count", methods=REQ_METHODS)
def RrecordCount():
    """记录列表计数路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求记录数据数量接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'SELECT COUNT(*) FROM `records` WHERE 1'
                cursor.execute(sql)
                result = cursor.fetchall()
                data["total"] = result[0]['COUNT(*)']
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/record/listV2", methods=REQ_METHODS)
def RrecordListV2():
    """记录列表路由v2(支持分表)"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求记录列表v2接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    POST_data = request.form
    data = []
    try:
        limit = int(str(POST_data.get("limit"))) or 25
        offset = int(str(POST_data.get("offset"))) or 0
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"equipment.record.getlist"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `records` ORDER BY id DESC LIMIT %s, %s'
                cursor.execute(sql,(offset,limit))
                result = cursor.fetchall()
                for i in result:
                    LEND_USERNAME = i["lend_userid"]
                    RETURN_USERNAME = i["return_userid"]
                    # 使用人应是借出用户的id对应的人
                    a = B__UserExist(i["lend_userid"],"id")
                    if a["has"] == True:
                        LEND_USERNAME = a["data"][0]["data"]["name"]
                    elif "guest:" in i["lend_userid"]:
                        LEND_USERNAME = i["lend_userid"]
                    # 归还人应是归还用户的id对应的人
                    b = B__UserExist(i["return_userid"],"id")
                    if b["has"] == True:
                        RETURN_USERNAME = b["data"][0]["data"]["name"]
                    Equipment_name = i["equipment_name"]
                    c = B__EquimentExist(i["equipment_code"])
                    if c[0]["errcode"] == 0:
                        Equipment_name = c[0]["data"]["name"]
                    data.append({"id":i["id"],"eqname":Equipment_name,"eqcode":i["equipment_code"],"lendtime":i["lend_date"],"user":LEND_USERNAME,"lender":i["lend_operater"],"returntime":i["return_date"],"returner":RETURN_USERNAME,"status":i["status"],"record_sha":i["record_sha"],"remark":i["remark"]})
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT


@app.route(f"{URL_PREFIX}/record/add", methods=REQ_METHODS)
def RrecordListRrecordAdd():
    """新增借出记录路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求新增借出记录接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    TOKEN = getRequestToken(flask.request)
    try:
        equipment_code = POST_data.get("equipment_code",None)
        lend_usercode = POST_data.get("lend_usercode",None)
        return_usercode = POST_data.get("return_usercode",None)
        lend_date = POST_data.get("lend_date",None)
        return_date = POST_data.get("return_date",None)
        isMeLend = POST_data.get("isMeLend",None)
        isMeReturn = POST_data.get("isMeReturn",None) 
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"equipment.lend"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        # 借出用户
        if isMeLend == 'true':
            lend_userid = getTokenInfo(TOKEN)["uid"]
        else:
            a = B__UserExist(lend_usercode,"code")
            if a["has"] == True:
                lend_userid = a["data"][0]["data"]["id"]
            else:
                return synthesisReturnData(-8001,"The lend user does not exist")
        lend_operater = getTokenInfo(TOKEN)["name"]

        # 归还用户
        if isMeReturn == 'true':
            return_userid = getTokenInfo(TOKEN)["uid"]
        else:
            b = B__UserExist(return_usercode,"code")
            if b["has"] == True:
                return_userid = b["data"][0]["data"]["id"]
            else:
                return synthesisReturnData(-8001,"The return user does not exist")
        return_operater = getTokenInfo(TOKEN)["name"]

        # 设备
        c = B__EquimentExist(equipment_code)
        if c[0]["errcode"] == 0:
            equipment_id = c[0]["data"]["id"]
            equipment_name = c[0]["data"]["name"]
        else:
            return synthesisReturnData(-8002,"The equipment does not exist")
        # 借出SHA
        record_sha = sha256(equipment_code+TOKEN+str(get_milliTimestamp())+str(random.randint(1,99999999)))
        # 数据库操作
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'INSERT INTO `records` (equipment_id, equipment_code, equipment_name, lend_date, lend_userid, lend_operater, return_date, return_userid, return_operater, status, record_sha, remark) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                cursor.execute(sql, (equipment_id,equipment_code,equipment_name,lend_date,lend_userid,lend_operater,return_date,return_userid,return_operater,0,record_sha,"后补记录"))
                conn.commit()
                data["id"] = cursor.lastrowid
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/record/item", methods=REQ_METHODS)
def RrecordItem():
    """查询借出记录路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求查询借出记录接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    try:
        ids = POST_data.get("id", type=int)
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"equipment.record.get"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from records WHERE id = %s'
                cursor.execute(sql,(ids))
                result = cursor.fetchone()
                if result:
                    LEND_USERNAME = "未知"
                    RETURN_USERNAME = ""
                    # 使用人应是借出用户的id对应的人
                    a = B__UserExist(result["lend_userid"],"id")
                    if a["has"] == True:
                        LEND_USERNAME = a["data"][0]["data"]["name"]
                    elif "guest:" in result["lend_userid"]:
                        LEND_USERNAME = result["lend_userid"]
                    # 归还人应是归还用户的id对应的人
                    b = B__UserExist(result["return_userid"],"id")
                    if b["has"] == True:
                        RETURN_USERNAME = b["data"][0]["data"]["name"]
                    Equipment_name = result["equipment_name"]
                    c = B__EquimentExist(result["equipment_code"])
                    if c[0]["errcode"] == 0:
                        Equipment_name = c[0]["data"]["name"]
                    data = {"id":result["id"],"eqname":Equipment_name,"eqcode":result["equipment_code"],"lendtime":result["lend_date"],"user":LEND_USERNAME,"lender":result["lend_operater"],"returntime":result["return_date"],"returner":RETURN_USERNAME,"status":result["status"],"record_sha":result["record_sha"],"remark":result["remark"]}
                    RESULT = synthesisReturnData(0,"ok",data)
                else:
                    RESULT = synthesisReturnData(0,"ok",{})
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/task/list", methods=REQ_METHODS)
def RtaskList():
    """任务列表路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求任务列表接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `task`'
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    data = result
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

def SendMessage(MessageTitle: str, TaskId:int, MessageDesc: str, MessageContent: str, SendTo: list, MessageType: int = 0):
    if not MessageDesc:
        MessageDesc = f"{MessageContent[0:13]}..."
    post_time = get_time()
    data = {}
    # 发送
    try:
        for i in SendTo:
            ui = getUserInfo_ByName(i)
            if ui[0]["errcode"] != 0:
                print(f"[Message] Try to Find UserId {i} Failed.So this User Not Send this message.")
                break
            userid = ui[0]["data"]["id"]
            with pymysql.connect(**mysql_config) as conn:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO `message` (`tid`,`title`, `d`, `content`, `type`, `object`, `post_time`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, (TaskId,MessageTitle,MessageDesc,MessageContent,MessageType,userid,post_time))
                    conn.commit()
                    data[str(i)] = {}
                    data[str(i)]["id"] = cursor.lastrowid
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        print(traceback.format_exc())
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

def DelTaskMeassage(TaskId:int,UserList: list = []):
    try:
        if UserList == []:
            with pymysql.connect(**mysql_config) as conn:
                with conn.cursor() as cursor:
                    sql = "DELETE FROM `message` WHERE tid=%s"
                    cursor.execute(sql, TaskId)
                    conn.commit()
        else:
            for i in UserList:
                ui = getUserInfo_ByName(i)
                if ui[0]["errcode"] != 0:
                    print(f"[Message] Try to Find UserId {i} Failed.So this User Not Send this message.")
                    break
                userid = ui[0]["data"]["id"]
                with pymysql.connect(**mysql_config) as conn:
                    with conn.cursor() as cursor:
                        sql = "DELETE FROM `message` WHERE tid=%s AND object=%s"
                        cursor.execute(sql, (TaskId,userid))
                        conn.commit()
        return synthesisReturnData(0,"ok",{"taskId": TaskId})
    except:
        return synthesisReturnData(-1,"System Error",traceback.format_exc())

@app.route(f"{URL_PREFIX}/message/MyMessage", methods=REQ_METHODS)
def RmyMessage():
    """我的消息路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求我的消息接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []

    tokenRenewal(TOKEN)

    uid = getTokenInfo(TOKEN)["uid"]

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = 'select * from `message` WHERE object = %s'
                cursor.execute(sql,(uid))
                result = cursor.fetchall()
                if result:
                    data = result
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/message/ReadMessage", methods=REQ_METHODS)
def RreadMessage():
    """读消息路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求读消息接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    POST_data = request.form
    
    try:
        id = int(POST_data.get("id",None))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT

    tokenRenewal(TOKEN)

    uid = getTokenInfo(TOKEN)["uid"]

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = f'UPDATE `message` SET `onread` = 1 WHERE id = {id} AND object = {uid}'
                cursor.execute(sql)
                conn.commit()
        RESULT = synthesisReturnData(0,"ok",{"id": id})
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/task/add", methods=REQ_METHODS)
def RtaskAdd():
    """添加任务路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求添加任务接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    
    try:
        work_time = POST_data.get("work_time",None)
        finally_time = POST_data.get("finally_time",None)
        content = POST_data.get("content",None)
        place = POST_data.get("place",None)
        types = POST_data.get("type",None)
        user = POST_data.get("user",None)
        equipment = POST_data.get("equipment",None)
        create_user = POST_data.get("create_user",None)
        change_time = str(get_time())
        weight = POST_data.get("weight",None)
        status = POST_data.get("status",None)
        remark = POST_data.get("remark",None)
        name = POST_data.get("name",None)
        if not create_user:
            create_user = getTokenInfo(TOKEN)["name"]
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"task.post"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO `task` (`name`, `work_time`, `finally_time`, `content`, `place`, `type`, `status`, `user`, `equipment`, `create_user`, `change_time`, `weight`, `remark`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (name,work_time,finally_time,content,place,types,status,user,equipment,create_user,change_time,weight,remark))
                conn.commit()
                data["id"] = cursor.lastrowid
        if user and len(user.split(",")) > 0:
            # 添加信息
            ac = SendMessage("新任务通知",data["id"],"你有新的任务安排，请到任务面板查阅详情",f"任务名称：{name},工作时间：{work_time},工作内容：{content},工作地点：{place}",user.split(","),0)
            if ac[0]["errcode"] != 0:
                return synthesisReturnData(-1,"SendMessageError",ac[0])
            data["message"] = ac[0]["data"]
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/task/edit", methods=REQ_METHODS)
def RtaskEdit():
    """编辑任务路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求编辑任务接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = {}
    POST_data = request.form
    
    try:
        id = int(POST_data.get("id",None))
        work_time = POST_data.get("work_time",None)
        finally_time = POST_data.get("finally_time",None)
        content = POST_data.get("content",None)
        place = POST_data.get("place",None)
        types = POST_data.get("type",None)
        status = POST_data.get("status",None)
        user = POST_data.get("user",None)
        equipment = POST_data.get("equipment",None)
        change_time = str(get_time())
        weight = POST_data.get("weight",None)
        remark = POST_data.get("remark",None)
        name = POST_data.get("name",None)

        Ndata = {
            "name": name,
            "work_time":work_time,
            "finally_time":finally_time,
            "content":content,
            "place":place,
            "type":types,
            "status":status,
            "user":user,
            "equipment":equipment,
            "change_time":change_time,
            "weight":weight,
            "remark":remark
        }
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    if not verifyPermissions(TOKEN,"task.post"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        NeedUpdateData = {}
        NeedDelMessage = []
        NeedPushMessage = []
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = sql = f'select * from `task` where `id` = {id}'
                cursor.execute(sql)
                result = cursor.fetchone()
                if result:
                    # 比对数据是否有变化
                    for i in result.keys():
                        if i in Ndata.keys():
                            if Ndata[i] != result[i]:
                                NeedUpdateData[i] = Ndata[i]
                        # 消息，判断user的内容有没有改变
                        if i == "user":
                            # result[i] 原来的名单
                            # Ndata[i] 新的名单
                            if result[i] != Ndata[i]:
                                for j in result[i].split(","):
                                    # 如果原来名单中的人不在新的名单中,表示移除了这个用户,NeedDelMessage
                                    if j not in Ndata[i].split(","):
                                        NeedDelMessage.append(j)
                                for k in Ndata[i].split(","):
                                    # 如果新名单中的人不在原来名单中,表示添加了这个用户,NeedPushMessage
                                    if k not in result[i].split(","):
                                        NeedPushMessage.append(k)
                    sql = f'UPDATE `task` SET {convertParamerter_SQLmode(NeedUpdateData)} WHERE id = {id}'
                    cursor.execute(sql)
                    conn.commit()
                    data["id"] = id
        if NeedDelMessage != []:
            DelTaskMeassage(id,NeedDelMessage)
        if NeedPushMessage != []:
            # 添加信息
            ac = SendMessage("新任务通知",id,"你有新的任务安排，请到任务面板查阅详情",f"任务名称：{name},工作时间：{work_time},工作内容：{content},工作地点：{place}",NeedPushMessage,0)
            if ac[0]["errcode"] != 0:
                return synthesisReturnData(-1,"SendMessageError",ac[0])
            data["message"] = ac[0]["data"]
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/task/del", methods=REQ_METHODS)
def RtaskDel():
    """删除任务路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求删除任务接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)

    data = {}
    POST_data = request.form

    try:
        ids = str(POST_data.get("id"))
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    
    if not verifyPermissions(TOKEN,"task.post"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = "DELETE FROM `task` WHERE id=%s"
                cursor.execute(sql, int(ids))
                conn.commit()
        data["id"] = ids
        DelTaskMeassage(ids)
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

@app.route(f"{URL_PREFIX}/task/myTask", methods=REQ_METHODS)
def RtaskMyTask():
    """获取我的任务路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取我的任务接口",ip=getIp(flask.request),url=flask.request.url)
    TOKEN = getRequestToken(flask.request)
    data = []
    POST_data = request.form
    try:
        name = POST_data.get("name","")
        if name == "":
            name = getTokenInfo(TOKEN)["name"]
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                sql = f"select * from `task` WHERE `user` LIKE '%{name}%'"
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    data = result
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT


EQUIPMENT_CHECK_DATA = {
    "STATUS": False,
    "THIS_OPERATION_SHA": None,
    "START_USER": None,
    "NC_ERROR_LIST": [],
    "TOTAL": 0,
    "NCN": 0,
    "Done": False,
}

@app.route(f"{URL_PREFIX}/eqcheck/start", methods=REQ_METHODS)
def ReqcheckStart():
    global EQUIPMENT_CHECK_DATA
    """开始清点设备路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求开始清点设备接口",ip=getIp(flask.request),url=flask.request.url)

    if EQUIPMENT_CHECK_DATA["STATUS"]:
        RESULT = synthesisReturnData(-6000,"Count Equipment Has Been Start")
        return RESULT
    EQUIPMENT_CHECK_DATA["STATUS"] = True
    TOKEN = getRequestToken(flask.request)
    data = {}
    EQUIPMENT_CHECK_DATA["START_USER"] = getUserInfo(getLoginUserInfo_ByToken(TOKEN)["usercode"])[0]["data"]["name"]
    EQUIPMENT_CHECK_DATA["THIS_OPERATION_SHA"] = sha256(str(get_time())+TOKEN+start_date+str(random.randint(1,99999999))+str(get_time()+random.randint(0,123456))).upper()

    if not verifyPermissions(TOKEN,"equipment.check.start"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    # 开始清点
    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                # 不是晚修管理组设备，而且设备状态正常
                sql = 'select * from equipment WHERE type = 0 and status = 0'
                cursor.execute(sql)
                result = cursor.fetchall()
                if not result:
                    # 有设备
                    EQUIPMENT_CHECK_DATA["TOTAL"] = len(result) # 设置设备总数
                    result = [result]
                    td = threading.Thread(target=CHECK_EQ_SON,args=(result))
                    td.start()
                    RESULT = synthesisReturnData(0,"ok",{"operation_sha":EQUIPMENT_CHECK_DATA["THIS_OPERATION_SHA"]})
                else:
                    RESULT = synthesisReturnData(-6001,"Equipment List Length Is 0")
    except:
        RESULT = synthesisReturnData(-6002,"Try Get Equipment List Error ：",traceback.format_exc())
    return RESULT

def CHECK_EQ_SON(result):
    global EQUIPMENT_CHECK_DATA
    print(f"\033[0;33;40m【设备清点】第{ EQUIPMENT_CHECK_DATA['NCN'] }项\033[0m")
    try:
        for i in result:
            EQ_ID = i[0]
            EQ_NAME = i[1]
            EQ_CODE = i[2]
            try:
                with pymysql.connect(**mysql_config) as conn:
                    with conn.cursor() as cursor:
                        sql = 'UPDATE equipment SET status = 4 WHERE id = %s'
                        cursor.execute(sql, (EQ_ID))
                        conn.commit()
            except:
                erritem = {
                    "id": EQ_ID,
                    "name": EQ_NAME,
                    "code": EQ_CODE,
                    "msg": traceback.format_exc()
                }
                EQUIPMENT_CHECK_DATA["NC_ERROR_LIST"].append(erritem)
            EQUIPMENT_CHECK_DATA["NCN"] += 1
    except:
        erritem = {
            "id": None,
            "name": None,
            "code": None,
            "msg": "循环执行时失败，"+traceback.format_exc()
        }
        EQUIPMENT_CHECK_DATA["NC_ERROR_LIST"].append(erritem)
        print("\033[0;32;40m"+"#【设备清点】错误："+traceback.format_exc()+"\033[0m")
    print("\033[0;33;40m"+"【设备清点】完成！"+"\033[0m")
    EQUIPMENT_CHECK_DATA["Done"] = True
    print(EQUIPMENT_CHECK_DATA["Done"])

@app.route(f"{URL_PREFIX}/eqcheck/status", methods=REQ_METHODS)
def ReqcheckStatus():
    global EQUIPMENT_CHECK_DATA
    """获取清点设备状态路由"""
    log(type="REQUEST",event=f"Request form {getIp(flask.request)}",state="Info",msg=f"请求获取清点设备状态接口",ip=getIp(flask.request),url=flask.request.url)

    if not EQUIPMENT_CHECK_DATA["STATUS"]:
        RESULT = synthesisReturnData(-6003,"Count Equipment Not Start")
        return RESULT
    TOKEN = getRequestToken(flask.request)
    data = {}
    if not verifyPermissions(TOKEN,"equipemnt.check.status"):
        RESULT = synthesisReturnData(-1005,"No Permission")
        return RESULT
    tokenRenewal(TOKEN)

    try:
        if EQUIPMENT_CHECK_DATA["Done"]:
            if len(EQUIPMENT_CHECK_DATA["NC_ERROR_LIST"]) == 0:
                RESULT = synthesisReturnData(0,"ok",{"operation_sha":EQUIPMENT_CHECK_DATA["THIS_OPERATION_SHA"],"START_USER":EQUIPMENT_CHECK_DATA["START_USER"],"progressing":False})
                EQUIPMENT_CHECK_DATA = {
                    "STATUS": False,
                    "THIS_OPERATION_SHA": None,
                    "START_USER": None,
                    "NC_ERROR_LIST": [],
                    "TOTAL": 0,
                    "NCN": 0,
                    "Done": False,
                }
            else:
                RESULT = synthesisReturnData(-2,"Done,but has error opertion",{"operation_sha":EQUIPMENT_CHECK_DATA["THIS_OPERATION_SHA"],"START_USER":EQUIPMENT_CHECK_DATA["START_USER"],"NC_ERROR_LIST":EQUIPMENT_CHECK_DATA["NC_ERROR_LIST"],"progressing":False})
        else:
            PROGRESS = ((EQUIPMENT_CHECK_DATA["NCN"]/EQUIPMENT_CHECK_DATA["TOTAL"])*100)
            PROGRESS = '{:.2f}'.format(PROGRESS)
            if PROGRESS == 100:
                PROGRESS = 99
            RESULT = synthesisReturnData(0,"ok",{"operation_sha":EQUIPMENT_CHECK_DATA["THIS_OPERATION_SHA"], "START_USER":EQUIPMENT_CHECK_DATA["START_USER"], "progress":PROGRESS, "progressing":True})
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT

# [END]ROUTE CODE AREA



# 借出记录查询JSON
# @app.route('/json/record/date/<query_date>')
# def json_record(query_date):
#     log(type=2,ip=getIp(flask.request),url=flask.request.url,event=request.method)
#     return_json = {}
#     status = 0
#     data_len = 0
#     error=""
#     try:
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from records where date like %s"%%"'
#                 cursor.execute(sql, escape_string(query_date))
#                 result = cursor.fetchall()
#                 table_list = ""
#                 if not result:
#                     data_len = len(result)
#                     data_no = 0
#                     for i in result:
#                         user_code = i[1]
#                         eq_code = i[2]
#                         sql = 'select * from user where code = %s'
#                         cursor.execute(sql, escape_string(user_code))
#                         result_s = cursor.fetchone()
#                         if result_s is not None:
#                             user_name = result_s[3]
#                             user_name = name_waf(user_name,user_code)
#                         else:
#                             user_name = "Error:UserCode不存在"
                        
#                         return_user_code = i[6]
#                         if return_user_code is not None:
#                             sql = 'select * from user where code = %s'
#                             cursor.execute(sql, escape_string(return_user_code))
#                             result_s = cursor.fetchone()
#                             if result_s is not None:
#                                 return_user_name = result_s[3]
#                                 return_user_name = name_waf(user_name,return_user_code)
#                             else:
#                                 return_user_name = "Error:UserCode不存在"
#                         else:
#                             return_user_name = "None"
                        
#                         sql = 'select * from equipment where code = %s'
#                         cursor.execute(sql, escape_string(eq_code))
#                         result_s = cursor.fetchone()
#                         if result_s is not None:
#                             eq_name = result_s[3]
#                             eq_name = name_waf(eq_name,eq_code)
#                         else:
#                             eq_name = "Error:设备Code不存在"
#                         return_json[data_no]={"id":i[0],"user_name":user_name,"user_code":user_code,"eq_name":eq_name,"eq_code":eq_code,"lend_date":i[3],"return_date":i[5],"return_user_name":return_user_name,"return_user_code":return_user_code}
#                         data_no += 1
#     except Exception as err:
#         traceback.print_exc()
#         log(event="RouteError",ip=getIp(flask.request),url=flask.request.url,msg=traceback.format_exc())
#         status = -1
#         error = "未知的错误"
#     return flask.jsonify(errcode=status,errmsg=error,data=return_json,data_len=data_len)


# 小程序业务
# @app.route(f"{URL_PREFIX}/wx/bindAccount",methods=['GET','POST'])
# def Route_WxBindAccount():
#     """绑定"""
#     POST_data = request.get_json()
#     try:
#         usercode = POST_data["usercode"]
#         password = POST_data["password"]
#         openid = POST_data["openid"]
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT
#     data = {}
#     try:
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from `user` where code = %s and password = %s and type = 0'
#                 cursor.execute(sql, (escape_string(usercode),
#                             escape_string(sha256(password))))
#                 result = cursor.fetchone()
#                 sqlo = 'select * from `user` where openid = %s AND type = 0'
#                 cursor.execute(sqlo, (str(openid)))
#                 result_openid = cursor.fetchone()
#                 if result:
#                     if result["openid"]:
#                         return synthesisReturnData(21,"该账号已绑定其他微信账号，请在统一认证系统解绑后再次尝试！")
#                     if result_openid:
#                         return synthesisReturnData(22,"该微信账号已绑定其他账号，请在小程序解绑后再次尝试！")
#                     with pymysql.connect(**mysql_config) as conn:
#                         with conn.cursor() as cursor:
#                             sql = "UPDATE `user` SET `openid` = %s WHERE id = %s"
#                             cursor.execute(sql, (str(openid),int(result["id"])))
#                             conn.commit()
#                     log(type="USER",state="Info",event=f"用户({result['name']})绑定微信",msg=f"{result['name']}绑定微信成功，openid：{openid}，方式：Miniprogram")
#                     return synthesisReturnData(0,"ok",{ "name": result["name"], "code": result["code"], "id": result["id"], "openid": openid })
#         return synthesisReturnData(20,"账号或密码错误")
#     except Exception as err:
#         log(event="系统错误",ip=getIp(flask.request),url=flask.request.url,msg=traceback.format_exc())
#         log(type="USER",state="Error",event=f"用户({result['name']})绑定微信",msg=f"{result['name']}绑定微信失败，因为 {err}，具体错误请查看系统日志。")
#         return synthesisReturnData(-1,f"System Error: {traceback.format_exc()}")

# @app.route(f"{URL_PREFIX}/wx/bindByWeb",methods=['GET','POST'])
# def Route_WxWebBind():
#     """统一认证 绑定微信"""
#     POST_data = request.get_json()
#     try:
#         uid = POST_data["uid"]
#         openid = POST_data["openid"]
#         code = POST_data["code"]
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT
#     data = {}
#     try:
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from `user` where openid = %s type = 0'
#                 cursor.execute(sql, (str(openid)))
#                 result = cursor.fetchone()
#                 if result:
#                     return synthesisReturnData(22,"该微信账号已绑定其他账号，请在小程序解绑后再次尝试！")
#                 sql_u = 'select * from `user` where id = %s type = 0'
#                 cursor.execute(sql_u, (str(uid)))
#                 result = cursor.fetchone()
#                 if result:
#                     with pymysql.connect(**mysql_config) as conn:
#                         with conn.cursor() as cursor:
#                             sql = "UPDATE `user` SET `openid` = %s WHERE id = %s"
#                             cursor.execute(sql, (str(openid),int(uid)))
#                             conn.commit()
#                     # 直接设置小程序码为已确认状态
#                     cleanWxCode()
#                     if code in CodeGroup:
#                         if CodeGroup[code]["status"] == 402:
#                             CodeGroup[code]["status"] = 404
#                     log(type="USER",state="Info",event=f"用户({result['name']})绑定微信",msg=f"{result['name']}绑定微信成功，openid：{openid}，方式：Web")
#                     return synthesisReturnData(0,"ok",{ "name": result["name"], "code": result["code"], "id": result["id"], "openid": openid })
#         return synthesisReturnData(25,"账号不存在")
#     except Exception as err:
#         log(event="系统错误",ip=getIp(flask.request),url=flask.request.url,msg=traceback.format_exc())
#         log(type="USER",state="Error",event=f"用户({result['name']})绑定微信",msg=f"{result['name']}绑定微信失败，因为 {err}，具体错误请查看系统日志。")
#         return synthesisReturnData(-1,f"System Error: {traceback.format_exc()}")
    
# @app.route(f"{URL_PREFIX}/wx/unbind",methods=['GET','POST'])
# def Route_WxUnbind():
#     """解绑"""
#     POST_data = request.get_json()
#     try:
#         openid = POST_data["openid"]
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT
#     data = {}
#     try:
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = "select * from `user` where openid = %s AND type = 0"
#                 cursor.execute(sql, (str(openid)))
#                 result = cursor.fetchone()
#                 if not result:
#                     # 找不到账号
#                     return synthesisReturnData(-90,"Unable to find the account corresponding to openid")
#                 sql = "UPDATE `user` SET `openid` = %s WHERE openid = %s"
#                 cursor.execute(sql, (None,str(openid)))
#                 conn.commit()
#                 # 清除登录数据中的openid
#                 for i in TOKEN_GROUP.keys():
#                     if TOKEN_GROUP[i]["openid"] == openid:
#                         TOKEN_GROUP[i]["openid"] = ""
#                 log(type="USER",state="Info",event=f"用户({result['name']})解绑微信",msg=f"{result['name']}解绑微信成功。")
#                 return synthesisReturnData(0,"ok")
#     except Exception as err:
#         log(event="系统错误",ip=getIp(flask.request),url=flask.request.url,msg=traceback.format_exc())
#         log(type="USER",state="Error",event=f"用户({result['name']})解绑微信",msg=f"{result['name']}解绑微信失败，因为 {err}，具体错误请查看系统日志。")
#         return synthesisReturnData(-1,f"System Error: {traceback.format_exc()}")

# @app.route(f"{URL_PREFIX}/wx/login",methods=['GET','POST'])
# def Route_WxLogin():
#     global CodeGroup
#     POST_data = request.get_json()
#     try:
#         code = POST_data["code"]
#         openid = POST_data["openid"]
#         renewalWxCode(code)
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT
#     try:
#         cleanWxCode()
#         if not code in CodeGroup:
#             return synthesisReturnData(24,"小程序码已过期")
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from `user` where openid = %s'
#                 cursor.execute(sql, (escape_string(openid)))
#                 result = cursor.fetchone()
#                 if not result:
#                     return synthesisReturnData(11,"找不到用户：未绑定")
#                 else:
#                     # 更新登录时间
#                     with pymysql.connect(**mysql_config) as conn:
#                         with conn.cursor() as cursor:
#                             sql = "UPDATE `user` SET `login_time` = %s WHERE id = %s"
#                             cursor.execute(sql, (str(get_time()),int(result["id"])))
#                             conn.commit()
#                     # 注册TOKEN
#                     TOKEN_CONSTITUTE = str({"login_time":f"{get_milliTimestamp()}","usercode":f"{result['code']}","passowrd":f"{result['password']}","KEY":f"{random.randint(1,100000)}"})
#                     TOKEN = sha256(TOKEN_CONSTITUTE).upper()
#                     TOKEN_GROUP[TOKEN] = {
#                         "login_time": get_time(),
#                         "timeout": get_timestamp(),
#                         "usercode": result["code"],
#                         "password": None,
#                         "name": result["name"],
#                         "id": result["id"],
#                         "class": result["class"],
#                         "share_device": result["share_device"],
#                         "reg_time": result["reg_time"],
#                         "join_time": result["join_time"],
#                         "grade": result["grade"],
#                         "openid": openid,
#                         "remark": result["remark"],
#                         "login_type": "miniprogram",
#                     }
#                     tokenRenewal(TOKEN)
#                     log(type="USER",event=f"用户({result['name']})登录成功",state="Info",msg=f"本次分发Token:{TOKEN},登录方式：{TOKEN_GROUP[TOKEN]['login_type']}",usercode=result["code"])
#                     CodeGroup[code]["status"] = 404
#                     CodeGroup[code]["raw"] = TOKEN_GROUP[TOKEN]
#                     CodeGroup[code]["token"] = TOKEN
#                     log(type="USER",event=f"用户({result['name']})登录",msg=f"{result['name']} 于 {get_time()} 使用(平台) {TOKEN_GROUP[TOKEN]['login_type']} 登录成功，登录有效期5400秒。",state="Info",ip=getIp(flask.request),url=flask.request.url,usercode=result["code"])
#                     return synthesisReturnData(0,"ok",{"token":TOKEN,"raw":TOKEN_GROUP[TOKEN]})
#     except Exception as e:
#         return synthesisReturnData(-1,f"获取数据失败：{e}")

# @app.route(f"{URL_PREFIX}/wx/task/list", methods=REQ_METHODS)
# def Route_WxTaskList():
#     """微信-任务列表路由"""
#     data = []
#     POST_data = request.get_json()
#     try:
#         openid = POST_data["openid"]
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT
#     try:
#         if not Wx_CheckOpenid(openid):
#             return synthesisReturnData(13,"用户未绑定")
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from `task`'
#                 cursor.execute(sql)
#                 result = cursor.fetchall()
#                 if result:
#                     data = result
#         RESULT = synthesisReturnData(0,"ok",data)
#     except:
#         RESULT = synthesisReturnData(-1,f"系统错误：{traceback.format_exc()}")
#     return RESULT

# @app.route(f"{URL_PREFIX}/wx/task/detail", methods=REQ_METHODS)
# def Route_WxTaskDetail():
#     """微信-任务详情路由"""
#     data = {}
#     POST_data = request.get_json()
#     try:
#         openid = POST_data["openid"]
#         tid = POST_data["tid"]
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT
#     try:
#         if not Wx_CheckOpenid(openid):
#             return synthesisReturnData(13,"用户未绑定")
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from `task` WHERE id = %s'
#                 cursor.execute(sql,(tid))
#                 result = cursor.fetchone()
#                 if result:
#                     data = result
#         RESULT = synthesisReturnData(0,"ok",data)
#     except:
#         RESULT = synthesisReturnData(-1,f"系统错误：{traceback.format_exc()}")
#     return RESULT

# @app.route(f"{URL_PREFIX}/wx/task/myTask", methods=REQ_METHODS)
# def Route_WxTaskMyTask():
#     """微信-获取我的任务路由"""
#     data = []
#     POST_data = request.get_json()
#     try:
#         openid = POST_data["openid"]
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT

#     try:
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 sql = 'select * from `user` WHERE openid = %s'
#                 cursor.execute(sql,(openid))
#                 result = cursor.fetchone()
#                 if not result:
#                     return synthesisReturnData(13,"用户未绑定")
#                 name = result["name"]
#                 sql = f"select * from `task` WHERE `user` LIKE '%{name}%'"
#                 cursor.execute(sql)
#                 result = cursor.fetchall()
#                 if result:
#                     data = result
#         RESULT = synthesisReturnData(0,"ok",data)
#     except:
#         RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
#     return RESULT

# @app.route(f"{URL_PREFIX}/wx/task/add", methods=REQ_METHODS)
# def Route_WxTaskAdd():
#     """添加任务路由"""
#     data = {}
#     POST_data = request.get_json()
#     try:
#         openid = POST_data["openid"]
#         work_time = POST_data["work_time"]
#         finally_time = POST_data["finally_time"]
#         content = POST_data["content"]
#         place = POST_data["place"]
#         types = POST_data["type"]
#         user = POST_data["user"]
#         create_user = POST_data["create_user"]
#         weight = POST_data["weight"]
#         equipment = POST_data["equipment"]
#         status = POST_data["status"]
#         remark = POST_data["remark"]
#         name = POST_data["name"]
#         change_time = str(get_time())
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT

#     try:
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 # 先找用户，再判断权限
#                 sql = 'select * from `user` where openid = %s'
#                 cursor.execute(sql, (escape_string(openid)))
#                 result = cursor.fetchone()
#                 if not result:
#                     return synthesisReturnData(13,"用户未绑定")
#                 # 判断权限
#                 if not verifyUserPermission(result["id"],"task.post"):
#                     return synthesisReturnData(-1005,"No Permission")
#                 # 有权限就可以新增
#                 sql = "INSERT INTO `task` (`name`, `work_time`, `finally_time`, `content`, `place`, `type`, `status`, `user`, `equipment`, `create_user`, `change_time`, `weight`, `remark`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
#                 cursor.execute(sql, (name,work_time,finally_time,content,place,types,status,user,equipment,create_user,change_time,weight,remark))
#                 conn.commit()
#                 data["id"] = cursor.lastrowid
#         if user and len(user.split(",")) > 0:
#             # 添加信息
#             ac = SendMessage("新任务通知",data["id"],"你有新的任务安排，请到任务面板查阅详情",f"任务名称：{name},工作时间：{work_time},工作内容：{content},工作地点：{place}",user.split(","),0)
#             if ac[0]["errcode"] != 0:
#                 return synthesisReturnData(-1,"SendMessageError",ac[0])
#             data["message"] = ac[0]["data"]
#         RESULT = synthesisReturnData(0,"ok",data)
#     except:
#         RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
#     return RESULT

# @app.route(f"{URL_PREFIX}/wx/task/edit", methods=REQ_METHODS)
# def Route_WxTaskEdit():
#     """微信-编辑任务路由"""
#     data = {}
    
#     POST_data = request.get_json()
#     try:
#         openid = POST_data["openid"]
#         id = POST_data["id"]
#         work_time = POST_data["work_time"]
#         finally_time = POST_data["finally_time"]
#         content = POST_data["content"]
#         place = POST_data["place"]
#         types = POST_data["type"]
#         user = POST_data["user"]
#         weight = POST_data["weight"]
#         equipment = POST_data["equipment"]
#         status = POST_data["status"]
#         remark = POST_data["remark"]
#         name = POST_data["name"]
#         change_time = str(get_time())
#         Ndata = {
#             "name": name,
#             "work_time":work_time,
#             "finally_time":finally_time,
#             "content":content,
#             "place":place,
#             "type":types,
#             "status":status,
#             "user":user,
#             "equipment":equipment,
#             "change_time":change_time,
#             "weight":weight,
#             "remark":remark
#         }
#     except:
#         RESULT = synthesisReturnData(-1001,"Invalid Parameter")
#         return RESULT

#     try:
#         NeedUpdateData = {}
#         NeedDelMessage = []
#         NeedPushMessage = []
#         with pymysql.connect(**mysql_config) as conn:
#             with conn.cursor() as cursor:
#                 # 先找用户，再判断权限
#                 sql = 'select * from `user` where openid = %s'
#                 cursor.execute(sql, (escape_string(openid)))
#                 result = cursor.fetchone()
#                 if not result:
#                     return synthesisReturnData(13,"用户未绑定")
#                 # 判断权限
#                 if not verifyUserPermission(result["id"],"task.post"):
#                     return synthesisReturnData(-1005,"No Permission")
#                 sql = sql = f'select * from `task` where `id` = {id}'
#                 cursor.execute(sql)
#                 result = cursor.fetchone()
#                 if result:
#                     # 比对数据是否有变化
#                     for i in result.keys():
#                         if i in Ndata.keys():
#                             if Ndata[i] != result[i]:
#                                 NeedUpdateData[i] = Ndata[i]
#                         # 消息，判断user的内容有没有改变
#                         if i == "user":
#                             # result[i] 原来的名单
#                             # Ndata[i] 新的名单
#                             if result[i] != Ndata[i]:
#                                 for j in result[i].split(","):
#                                     # 如果原来名单中的人不在新的名单中,表示移除了这个用户,NeedDelMessage
#                                     if j not in Ndata[i].split(","):
#                                         NeedDelMessage.append(j)
#                                 for k in Ndata[i].split(","):
#                                     # 如果新名单中的人不在原来名单中,表示添加了这个用户,NeedPushMessage
#                                     if k not in result[i].split(","):
#                                         NeedPushMessage.append(k)
#                     sql = f'UPDATE `task` SET {convertParamerter_SQLmode(NeedUpdateData)} WHERE id = {id}'
#                     cursor.execute(sql)
#                     conn.commit()
#                     data["id"] = id
#         if NeedDelMessage != []:
#             DelTaskMeassage(id,NeedDelMessage)
#         if NeedPushMessage != []:
#             # 添加信息
#             ac = SendMessage("新任务通知",id,"你有新的任务安排，请到任务面板查阅详情",f"任务名称：{name},工作时间：{work_time},工作内容：{content},工作地点：{place}",NeedPushMessage,0)
#             if ac[0]["errcode"] != 0:
#                 return synthesisReturnData(-1,"SendMessageError",ac[0])
#             data["message"] = ac[0]["data"]
#         RESULT = synthesisReturnData(0,"ok",data)
#     except:
#         RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
#     return RESULT

# @app.route(f"{URL_PREFIX}/wx/task/del", methods=REQ_METHODS)
# def Route_WxTaskDel():
    """微信-删除任务路由"""
    data = {}
    POST_data = request.get_json()
    try:
        openid = POST_data["openid"]
        ids = POST_data["id"]
    except:
        RESULT = synthesisReturnData(-1001,"Invalid Parameter")
        return RESULT

    try:
        with pymysql.connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                # 先找用户，再判断权限
                sql = 'select * from `user` where openid = %s'
                cursor.execute(sql, (escape_string(openid)))
                result = cursor.fetchone()
                if not result:
                    return synthesisReturnData(13,"用户未绑定")
                # 判断权限
                if not verifyUserPermission(result["id"],"task.post"):
                    return synthesisReturnData(-1005,"No Permission")
                # 有权限就可以新增
                sql = "DELETE FROM `task` WHERE id=%s"
                cursor.execute(sql, int(ids))
                conn.commit()
        data["id"] = ids
        DelTaskMeassage(ids)
        RESULT = synthesisReturnData(0,"ok",data)
    except:
        RESULT = synthesisReturnData(-1,"System Error",traceback.format_exc())
    return RESULT




# 
@app.before_request
def before_request():
    url = request.path
    Other_Page = [
        f"{URL_PREFIX}/get/userlist",
        f"{URL_PREFIX}/permissions/pagePermissions",
        f"{URL_PREFIX}/permissions/systemlist",
        f"{URL_PREFIX}/Dashboard/ContentData",
        f"{URL_PREFIX}/Dashboard/ChartData",
        f"{URL_PREFIX}/Dashboard/TableData",
    ]
    # 如果是不检测token的页面，直接跳过
    if url in Other_Page:
        pass
    else:
        # 放行OPTIONS
        if request.method == "OPTIONS":
            return synthesisReturnData(0,"ok",{"methods":"OPTIONS"})
        TOKEN = getRequestToken(flask.request)
        if not TOKEN:
            RESULT = synthesisReturnData(-1000,"Invalid Token")
            return RESULT
        if not verifyTokenEffective(TOKEN):
            RESULT = synthesisReturnData(-1003,"Token Timeout")
            return RESULT
        else:
            pass


# 运行
if __name__ == '__main__':
    log(event="服务启动",msg="代码加载完成，运行服务")
    print(f"后端版本：{VERSION}")
    app.run(host='0.0.0.0', port=51001, debug=False)

    # uvicorn.run(app,port=30000)