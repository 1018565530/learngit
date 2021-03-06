#!/usr/bin/python
#coding:utf-8

import MySQLdb
import time,datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import string


#zabbix数据库信息：
zdbhost = ''
zdbuser = ''
zdbpass = ''
zdbport = 
zdbname = 'z'

#需要查询的key列表
keys = {
    'trends_uint':[
        'net.if.in[eth0]',
        'net.if.out[eth0]',
        'vfs.fs.size[/,used]',
        'vm.memory.size[available]',
        ],
    'trends':[
        'system.cpu.load[percpu,avg5]',
        'system.cpu.util[,idle]',
        ],
    }


class ReportForm:

    def __init__(self):
        '''打开数据库连接'''
        self.conn = MySQLdb.connect(host=zdbhost,user=zdbuser,passwd=zdbpass,port=zdbport,db=zdbname)
        self.cursor = self.conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        #生成zabbix哪个分组报表
        self.groupname = 'Test_Server'

        #获取IP信息：
        self.IpInfoList = self.__getHostList()

    def __getHostList(self):
        '''根据zabbix组名获取该组所有IP'''

        #查询组ID:
        sql = '''select groupid from groups where name = '%s' ''' % self.groupname
        self.cursor.execute(sql)
        groupid = self.cursor.fetchone()['groupid']

        #根据groupid查询该分组下面的所有主机ID（hostid）：
        sql = '''select hostid from hosts_groups where groupid = %s''' % groupid
        self.cursor.execute(sql)
        hostlist = self.cursor.fetchall()

        #生成IP信息字典：结构为{'112.111.222.55':{'hostid':10086L,},}
        IpInfoList = {}
        for i in hostlist:
            hostid = i['hostid']
            sql = '''select host from hosts where status = 0 and hostid = %s''' % hostid
            ret = self.cursor.execute(sql)
            if ret:
                IpInfoList[self.cursor.fetchone()['host']] = {'hostid':hostid}
        return IpInfoList

    def __getItemid(self,hostid,itemname):
        '''获取itemid'''
        sql = '''select itemid from items where hostid = %s and key_ = '%s' ''' % (hostid, itemname)
        if self.cursor.execute(sql):
            itemid = self.cursor.fetchone()['itemid']
        else:
            itemid = None
        return itemid

    def getTrendsValue(self,itemid, start_time, stop_time):
        '''查询trends_uint表的值,type的值为min,max,avg三种'''
        resultlist = {}
        for type in ['min','max','avg']:
            sql = '''select %s(value_%s) as result from trends where itemid = %s and clock >= %s and clock <= %s''' % (type, type, itemid, start_time, stop_time)
            self.cursor.execute(sql)
            result = self.cursor.fetchone()['result']
            if result == None:
                result = 0
            resultlist[type] = result
        return resultlist

    def getTrends_uintValue(self,itemid, start_time, stop_time):
        '''查询trends_uint表的值,type的值为min,max,avg三种'''
        resultlist = {}
        for type in ['min','max','avg']:
            sql = '''select %s(value_%s) as result from trends_uint where itemid = %s and clock >= %s and clock <= %s''' % (type, type, itemid, start_time, stop_time)
            self.cursor.execute(sql)
            result = self.cursor.fetchone()['result']
            if result:
                resultlist[type] = int(result)
            else:
                resultlist[type] = 0
        return resultlist


    def getLastMonthData(self,hostid,table,itemname):
        '''根据hostid,itemname获取该监控项的值'''
        #获取上个月的第一天和最后一天
        ts_first = int(time.mktime(datetime.date(datetime.date.today().year,datetime.date.today().month-1,1).timetuple()))
        lst_last = datetime.date(datetime.date.today().year,datetime.date.today().month,1)-datetime.timedelta(1)
        ts_last = int(time.mktime(lst_last.timetuple()))

        itemid = self.__getItemid(hostid, itemname)

        function = getattr(self,'get%sValue' % table.capitalize())

        return  function(itemid, ts_first, ts_last)

    def getInfo(self):
        #循环读取IP列表信息
        for ip,resultdict in  zabbix.IpInfoList.items():
            print "正在查询 IP:%-15s hostid:%5d 的信息！" % (ip, resultdict['hostid'])
            #循环读取keys，逐个key统计数据：
            for table, keylists in keys.items():
                for key in keylists:
                    print "\t正在统计 key_:%s" % key
                    data =  zabbix.getLastMonthData(resultdict['hostid'],table,key)
                    zabbix.IpInfoList[ip][key] = data

    def writeToXls(self):
        '''生成xls文件'''
        try:
            import xlsxwriter
            #创建文件
            workbook = xlsxwriter.Workbook('damo.xls')
            #创建工作薄
            worksheet = workbook.add_worksheet()
            #写入标题（第一行）
            i = 0
            for value in ["主机","CPU平均空闲值","CPU最小空闲值","可用平均内存(单位M)","可用最小内存(单位M)","CPU5分钟负载","进入最大流量（单位Kbps）","进入平均流量（单位Kbps）","出去最大流量（单位Kbps）","出去平均流量（单位Kbps）"]:
                worksheet.write(0,i, value.decode('utf-8'))
                i = i + 1
                #写入内容：
            j = 1
            for ip,value in self.IpInfoList.items():
                worksheet.write(j,0, ip)
                worksheet.write(j,1, '%.2f' % value['system.cpu.util[,idle]']['avg'])
                worksheet.write(j,2, '%.2f' % value['system.cpu.util[,idle]']['min'])
                worksheet.write(j,3, '%dM' % int(value['vm.memory.size[available]']['avg'] / 1024 / 1024))
                worksheet.write(j,4, '%dM' % int(value['vm.memory.size[available]']['min'] / 1024 / 1024))
                worksheet.write(j,5, '%.2f' % value['system.cpu.load[percpu,avg5]']['avg'])
                worksheet.write(j,6, value['net.if.in[eth0]']['max']/1000)
                worksheet.write(j,7, value['net.if.in[eth0]']['avg']/1000)
                worksheet.write(j,8, value['net.if.out[eth0]']['max']/1000)
                worksheet.write(j,9, value['net.if.out[eth0]']['avg']/1000)
                j = j + 1
            workbook.close()
        except Exception,e:
            print e



    def __del__(self):
        '''关闭数据库连接'''
        self.cursor.close()
        self.conn.close()

    def sendEmail(self):

    # 创建一个带附件的实例
        msg = MIMEMultipart()

    # 构造附件1
        xlsxpart = MIMEApplication(open('damo.xls', 'rb').read())
        xlsxpart.add_header('Content-Disposition', 'attachment', filename='damo.xlsx')
        msg.attach(xlsxpart)

    # 写入邮件正文
        text=" 附件为运维监控报表，请查收！"
    # 邮件正文乱码,所以在这里指定编码
        part1 = MIMEText(text, 'plain', _charset='utf-8')
        msg.attach(part1)

    # 加邮件

        to="xxxxx@qq.com,xxxxx@163.com"
        to=string.splitfields(to,",")

        msg['from'] = 'xxxxxx@163.com'
        msg['subject'] = '运维部门监控统计报表'.decode('utf-8')

    # 发送邮件
        try:
            server = smtplib.SMTP()

        # 数据中心测试时
            server.connect('smtp.163.com')
        # 用户名,密码
            server.login('xxxxx@163.com', '123456')
            server.sendmail(msg['from'], to, msg.as_string())
            server.quit()
            print 'sucessfule'.decode("utf-8")
        except Exception, e:
            print str(e)



if __name__ == "__main__":
    zabbix = ReportForm()
    zabbix.getInfo()
    zabbix.writeToXls()
    zabbix.sendEmail()
