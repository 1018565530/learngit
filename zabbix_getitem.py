#!/usr/bin/env pyhton
import urllib2
import json
import time
import datetime
import MySQLdb


now = int(time.time())
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
yesterday_start_time = int(time.mktime(time.strptime(str(yesterday), '%Y-%m-%d')))

print(now)
print(yesterday_start_time)


class ZabbixItem():
    def __init__(self):
        self.url = "http://xxx/api_jsonrpc.php"
        self.header = {"Content-Type": "application/json"}

        self.dbhost = "xxx"
        self.dbport = xxx
        self.dbuser = 'xxx'
        self.dbname = 'xxx'
        self.passwd = 'xxx'
        self.dbname = 'xxx'

        self.auth = self.login()

    def mysql(self,sql):
        try:
            self.conn = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpasswd, port=self.dbport, charset="utf8",connect_timeout=20)
            self.conn.select_db(dbname)
            self.cur = self.conn.cursor()
            self.count = self.cur.execute(sql)
            if self.count == 0:
                result = 0
            else:
                result = self.cur.fetchall()
            return  result
            self.cur.close()
            self.conn.close()
        except MySQLdb.Error, e:
            print "mysql error:", e



    def get_clock(self, value):
        clock = time.localtime(int(value))
        format = '%Y-%m-%d %H:%M'
        return time.strftime(format, clock)


    def login(self):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": "xxx",
                    "password": "xxx"
                },
                "id": 0
            })
        req = urllib2.Request(self.url, data)
        for key in self.header:
            req.add_header(key, self.header[key])
        try:
            result = urllib2.urlopen(req)
        except URLError as e:
            print("Auth Failed, Please Check Your Name AndPassword:", e.code)
        else:
            response = json.loads(result.read())
            auth = response['result']
            #print auth
            return auth


    def get_date(self, data):
        req = urllib2.Request(self.url, data)
        for key in self.header:
            req.add_header(key, self.header[key])
        try:
            result = urllib2.urlopen(req)
        except URLError as e:
            print("Auth Failed, Please Check Your Name AndPassword:", e.code)
        else:
            response = json.loads(result.read())
            result.close()
            return response

    def get_host(self):
        ips = ['xxx']
        for ip in ips:
            data = json.dumps({
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": "extend",
                    "filter": {
                        "host": ip
                    }
                },
                "auth": self.auth,
                "id": 2
            })
            result = self.get_date(data)['result']
            if result > 0:
                for host in result:
                    hostid = host['hostid']
                    data = json.dumps({
                        "jsonrpc": "2.0",
                        "method": "item.get",
                        "params": {
                            "output": "extend",
                            "hostids": hostid,
                            ##"search":{"key_":"portalias.inbytes[UPLINK_Huya]"},
                            #"filter":{"key_":"portalias.inbytes[UPLINK_Huya]"}
                        },
                        "auth": self.auth,
                        "id": 1
                    })
                    result = self.get_date(data)['result']
                    #print(result)

                    if result > 0:
                        print(result)
                        for itemid in result:
                            key_ = itemid['key_']

                            if key_ == 'portalias.outbytes[UPLINK_Huya]':
                                itemid_outbytes = itemid['itemid']
                                #print(itemid_outbytes)
                                sql = 'select min(value),avg(value),max(value) from history where itemid=itemid_outbytes and clock>=yesterday_start_time and clock<=now;'
                                for row in self.mysql(sql):
                                    print(row)
                            elif key_ == 'portalias.inbytes[UPLINK_Huya]':
                                itemid_inbytes = itemid['itemid']
                                #print(itemid_inbytes)

                                '''
                                data2 = json.dumps({
                                    "jsonrpc": "2.0",
                                    "method": "trend.get",
                                    "params":{
                                        "output":["itemid","clock","value_min","value_avg","value_max"],
                                        "time_from":yesterday_start_time,
                                        "time_till":now,
                                        "itemids": [itemid_inbytes]
                                    },

                                    "auth":self.login(),
                                    "id":2
                                })
                                result = self.get_date(data2)['result']
                                if result>0:
                                    #print(result)
                                    for val in result:
                                        value_avg = val['value_avg']
                                        value_min = val['value_min']
                                        value_max = val['value_max']
                                        print(value_max)

                                '''




                    #else:
                    #    print "Error host,check over!!!"
                    #print(hostid)

            #else:
                #print "Error host,check over!!!"




    #def main(self):
    #    zitem = ZabbixItem()
    #    print(zitem.get_host())
    #    print(zitem.login())
    #    #print(zitem.get_items())



if __name__ == '__main__':
    zitem = ZabbixItem()
    print(zitem.get_host())

