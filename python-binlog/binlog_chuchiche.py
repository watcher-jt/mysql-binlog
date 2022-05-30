# -*- coding: utf-8 -*-

import MySQLdb
import logging
import os
import sys
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    UpdateRowsEvent,
    WriteRowsEvent
)

g_work_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(g_work_dir)
log_dir = os.path.join(g_work_dir, 'chu_zhi_log')
if os.path.isfile(log_dir):
    os.rename(log_dir, '%s_bak' % log_dir)
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, 'debug.log'),
                    level=logging.NOTSET,
                    format='[%(asctime)s] %(levelname)s %(filename)s '
                           '%(lineno)s %(funcName)s : %(message)s')


class Auth_Recharge(object):
    """
    通过park_schedule的上报进车监控binlog
    """
    def __init__(self, modify_balance, **kw):
        self.mysql_settings = kw
        self.modify_balance = modify_balance

    def recharge(self, plate):
        """
        充值逻辑判断
        """
        try:
            conn = MySQLdb.connect(host=self.mysql_settings['host'], user=self.mysql_settings['user'],
                                   passwd=self.mysql_settings['passwd'], db='irain_park', charset='utf8')
            cursor = conn.cursor()
            get_auth_no = "select a.auth_no from new_auth_share as a inner join new_auth_group as b on " \
                          "b.auth_type=14 and a.vpr_plate='%s' limit 1" % plate
            logging.debug(u"=====执行更新语句 %s " % get_auth_no)
            cursor.execute(get_auth_no)
            res = cursor.fetchone()
            if not res:
                return False
            auth_no = res[0]
            check_account = "select account from new_auth_account where auth_no='%s' and recharge>account " \
                            "and recharge!=0" % auth_no
            logging.debug(u"=====执行更新语句 %s " % check_account)
            cursor.execute(check_account)
            res = cursor.fetchone()
            if not res:
                return False
            logging.debug(u"监控到了,需要修改充值余额的授权编号:%s 车牌:%s" % (auth_no, plate))
            update_recharge = "update new_auth_account set account=%d,recharge=%d where auth_no='%s' " \
                              % (self.modify_balance, self.modify_balance, auth_no)
            print(update_recharge)
            logging.debug(u"=====执行更新语句 %s " % update_recharge)
            cursor.execute(update_recharge)
            conn.commit()
        except Exception as err:
            logging.debug("recharge error:%s"%str(err))
            return
        finally:
            cursor.close()
            conn.close()

    def run(self):
        """
        监控park_schedule表的写入和修改
        注：因为修改场内车不写park_schedule，所以下面监控update的逻辑实际上无法实现
        """
        logging.debug(u"=====start monitor=====")
        # 实例化binlog 流对象
        stream = BinLogStreamReader(
            connection_settings=self.mysql_settings,
            server_id=100,  # slave标识，唯一
            blocking=True,  # 阻塞等待后续事件
            # 设定只监控写操作：增、改
            only_events=[WriteRowsEvent, UpdateRowsEvent],
            only_tables=["park_schedule"]
        )

        for binlogevent in stream:
            for row in binlogevent.rows:
                event = {"schema": binlogevent.schema, "table": binlogevent.table}
                if isinstance(binlogevent, UpdateRowsEvent):
                    event["action"] = "update"
                    event["data"] = row["after_values"]  # 注意这里不是values
                    print(event["data"])
                elif isinstance(binlogevent, WriteRowsEvent):
                    event["action"] = "insert"
                    event["data"] = row["values"]
                if event["data"]["operate"] == 1:
                    print(event["data"]["vpr_plate"])
                    self.recharge(str(event["data"]["vpr_plate"]))


if __name__ == '__main__':
    """
    传入参数解释
    259200 :充值的时长（秒为单位）
    host=""：数据库ip地址
    port=3306：数据库端口
    user="root"：数据库用户名
    passwd=""：数据库密码
    """
    recharge = Auth_Recharge(259200, host="", port=3306, user="root", passwd="")
    recharge.run()
