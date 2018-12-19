#! /usr/bin/env python


import os
import smtplib


from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage


def _sendmail(smtp_server,port,account,password,str_from,list_to,msg):
    smtp = smtplib.SMTP(smtp_server,port)
   # smtp.starttls()
   # smtp.ehlo()
    smtp.login(account, password)
    smtp.sendmail(str_from, list_to,msg)
    smtp.close()


def _get_pictures(image_dir):
    pictures = []
    for f in os.listdir(image_dir):
        pictures.append(f)
    return pictures


def _create_msg(screen_name,screens,image_dir,str_from,list_to):
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'Zabbix Screen Report: %s' % screen_name
    msgRoot['From'] = str_from
    msgRoot['To'] = ",".join(list_to)
    msgRoot.preamble = 'This is a multi-part message in MIME format.'


    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)


    msgText = MIMEText('This is the alternative plain text message.')
    msgAlternative.attach(msgText)
    contents = ""
    contents += "<h1>Screen %s</h1><br>" % screen_name
    _,_,hsize,vsize,_,_,_,_,= tuple(screens[0].split('.'))
    contents +="<table>"
    screens = sorted(screens)
    y= -1
    for f in screens:
        items = f.split('.')
        _,_,_,_,image_y,image_x,image_id,_ = tuple(items)
        image_name = "image-%s-%s" % (screen_name, image_id)
        fp = open('%s/%s' % (image_dir,f), 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', "<%s>" % image_name)
        msgRoot.attach(msgImage)
        if y != image_y:
            if y!= -1:
                contents +="</tr>"
            y = image_y
            contents +="<tr>"
        contents +="<td><img src='cid:%s'></td>" % image_name
    contents += "</table>"
    msgText = MIMEText(contents, 'html')
    msgAlternative.attach(msgText)
    msgRoot.attach(msgAlternative)
    return msgRoot


# Create the root message and fill in the from, to, and subject headers
def main(str_from,list_to,image_dir):
    pictures = _get_pictures(image_dir)
    for screen_name in list(set([x.split('.')[0] for x in pictures ])):
        screens = [x for x in pictures if x.startswith(str(screen_name) + '.') ]
        msgRoot = _create_msg(screen_name,screens,image_dir,str_from,list_to)
        _sendmail('smtp.126.com',25,'zabbix_report@126.com','password111',str_from,list_to,msgRoot.as_string())


if __name__ == '__main__':
   str_from = 'zabbix_report@126.com'
   list_to = [
                "test1@126.com","test2@126.com"
             ]
   image_dir = '/data/graph'
   main(str_from,list_to,image_dir)
