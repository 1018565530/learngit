#! /usr/bin/env python
#coding=utf-8
# Andy_f
import time,os
import urllib
import urllib2
import cookielib
import MySQLdb
import smtplib
from email.mime.text import MIMEText

screens = ["xxx","xxx"]
#
save_graph_path = "/var/www/zabbix/reports/%s"%time.strftime("%Y-%m-%d")
if not os.path.exists(save_graph_path):
    os.makedirs(save_graph_path)
# zabbix host
zabbix_host = "zabbix.xxx.com"
# zabbix login username
username = "admin"
# zabbix login password
password = "zabbix"
# graph width
width = 600
# graph height
height = 100
# graph Time period, s
period = 86400
# zabbix DB
dbhost = "xxx.xxx.xxx.xxx"
dbport = 3306
dbuser = "zabbix"
dbpasswd = "xxxxx"
dbname = "zabbix"
# mail
to_list = ["xxx@xxx.com","aaa@xxx.com"]
smtp_server = "smtp.163.com"
mail_user = "xxxx"
mail_pass = "xxxxx"
domain  = "163.com"

def mysql_query(sql):
    try:
        conn = MySQLdb.connect(host=dbhost,user=dbuser,passwd=dbpasswd,port=dbport,connect_timeout=20)
        conn.select_db(dbname)
        cur = conn.cursor()
        count = cur.execute(sql)
        if count == 0:
            result = 0
        else:
            result = cur.fetchall()
        return result
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "mysql error:" ,e

def get_graph(zabbix_host,username,password,screen,width,height,period,save_graph_path):
    screenid_list = []
    global html
    html = ''
    for i in mysql_query("select screenid from screens where name='%s'"%(screen)):
                for screenid in i:
                    graphid_list = []
                    for c in mysql_query("select resourceid from screens_items where screenid='%s'"%(int(screenid))):
                        for d in c:
                            graphid_list.append(int(d))
                    for graphid in graphid_list:
                        login_opt = urllib.urlencode({
                        "name": username,
                        "password": password,
                        "autologin": 1,
                        "enter": "Sign in"})
                        get_graph_opt = urllib.urlencode({
                        "graphid": graphid,
                        "screenid": screenid,
                        "width": width,
                        "height": height,
                        "period": period})
                        cj = cookielib.CookieJar()
                        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                        login_url = r"http://%s/index.php"%zabbix_host
                        save_graph_url = r"http://%s/chart2.php"%zabbix_host
                        opener.open(login_url,login_opt).read()
                        data = opener.open(save_graph_url,get_graph_opt).read()
                        filename = "%s/%s.%s.png"%(save_graph_path,screenid,graphid)
                        html += '<img width="600" height="250" src="http://%s/%s/%s/%s.%s.png">'%(zabbix_host,save_graph_path.split("/")[len(save_graph_path.split("/"))-2],save_graph_path.split("/")[len(save_graph_path.split("/"))-1],screenid,graphid)
                        f = open(filename,"wb")
                        f.write(data)
                        f.close()


def send_mail(username,password,smtp_server,to_list,sub,content):
    print to_list
    me = "运维"+"<"+username+"@"+domain +">"
    msg = MIMEText(content,_subtype="html",_charset="utf8")
    msg["Subject"] = sub
    msg["From"] = me
    msg["To"] = ";".join(to_list)
    try:
        server = smtplib.SMTP()
        server.connect(smtp_server)
        server.login(username,password)
        server.sendmail(me,to_list,msg.as_string())
        server.close()
        print "send mail Ok!"
    except Exception, e:
        print e

if __name__ == '__main__':
    for screen in screens:
        get_graph(zabbix_host,username,password,screen,width,height,period,save_graph_path)
    send_mail(mail_user,mail_pass,smtp_server,to_list,"test email",html)
