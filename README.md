binlog2sql
========================

从MySQL binlog解析出你要的SQL。根据不同选项，你可以得到原始SQL、回滚SQL、去除主键的INSERT SQL等。

用途
===========

* 数据快速回滚(闪回)
* 主从切换后新master丢数据的修复
* 从binlog生成标准SQL，带来的衍生功能


项目状态
===
正常维护。应用于部分公司线上环境。

* 已测试环境
    * Python 2.7, 3.4+
    * MySQL 5.6, 5.7


安装
==============

```
shell> pip install -r package.txt
```

使用
=========

### MySQL server必须设置以下参数:

    [mysqld]
    server_id = 1
    log_bin = /var/log/mysql/mysql-bin.log
    max_binlog_size = 1G
    binlog_format = row
    binlog_row_image = full

### user需要的最小权限集合：

    select, super/replication client, replication slave
    
    建议授权
    GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 

**权限说明**

* select：需要读取server端information_schema.COLUMNS表，获取表结构的元信息，拼接成可视化的sql语句
* super/replication client：两个权限都可以，需要执行'SHOW MASTER STATUS', 获取server端的binlog列表
* replication slave：通过BINLOG_DUMP协议获取binlog内容的权限


### 基本用法


**解析出标准SQL**

```bash
shell> python rollback_binlog.py -h127.0.0.1 -P3306 -uroot -padmin -drollback -tuser --start-file='mysql-bin.000004'

输出：
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (33, 'M', 3, 'marry'); #start 4 end 405 time 2019-03-01 10:12:18
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (23, 'F', 4, 'brank'); #start 436 end 687 time 2019-03-01 10:12:45
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (26, 'F', 5, 'Doc xiao'); #start 718 end 972 time 2019-03-01 10:13:20
DELETE FROM `rollback`.`user` WHERE `age`=12 AND `sex`='F' AND `id`=1 AND `name`='jack' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=22 AND `sex`='M' AND `id`=2 AND `name`='lucy' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=33 AND `sex`='M' AND `id`=3 AND `name`='marry' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=23 AND `sex`='F' AND `id`=4 AND `name`='brank' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=26 AND `sex`='F' AND `id`=5 AND `name`='Doc xiao' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (26, 'F', 5, 'Doc xiao'); #start 1354 end 1608 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (23, 'F', 4, 'brank'); #start 1639 end 1890 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (33, 'M', 3, 'marry'); #start 1921 end 2172 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (22, 'M', 2, 'lucy'); #start 2203 end 2453 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (12, 'F', 1, 'jack'); #start 2484 end 2734 time 2019-03-01 10:51:57
UPDATE `rollback`.`user` SET `age`=23, `sex`='F', `id`=4, `name`='jack ma' WHERE `age`=23 AND `sex`='F' AND `id`=4 AND `name`='brank' LIMIT 1; #start 2765 end 3036 time 2019-03-01 10:54:10
```

**解析出标准insert**
shell>python rollback_binlog.py -h127.0.0.1 -P3306 -uroot -padmin -drollback -tuser --start-file='mysql-bin.000004' --sql-type insert
输出：
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (33, 'M', 3, 'marry'); #start 4 end 405 time 2019-03-01 10:12:18
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (23, 'F', 4, 'brank'); #start 436 end 687 time 2019-03-01 10:12:45
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (26, 'F', 5, 'Doc xiao'); #start 718 end 972 time 2019-03-01 10:13:20
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (26, 'F', 5, 'Doc xiao'); #start 1354 end 1608 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (23, 'F', 4, 'brank'); #start 1639 end 1890 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (33, 'M', 3, 'marry'); #start 1921 end 2172 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (22, 'M', 2, 'lucy'); #start 2203 end 2453 time 2019-03-01 10:51:57
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (12, 'F', 1, 'jack'); #start 2484 end 2734 time 2019-03-01 10:51:57

解释：--sql-type   参数    -------->>>>对某一种操作类型进行标准解析






**解析出回滚SQL**
'''
对标准操作的回滚解析说明：

标准操作insert  ------>>  回滚解析delete
标准操作update  ------>>  回滚解析update
标准操作delete  ------>>  回滚解析insert
'''
```bash

shell> python rollback_binlog.py --flashback -h127.0.0.1 -P3306 -uroot -padmin -drollback -tuser --start-file='mysql-bin.000004' --start-position=1003 --stop-position=1323

输出：
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (26, 'F', 5, 'Doc xiao'); #start 1003 end 1323 time 2019-03-01 10:30:55
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (23, 'F', 4, 'brank'); #start 1003 end 1323 time 2019-03-01 10:30:55
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (33, 'M', 3, 'marry'); #start 1003 end 1323 time 2019-03-01 10:30:55
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (22, 'M', 2, 'lucy'); #start 1003 end 1323 time 2019-03-01 10:30:55
INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (12, 'F', 1, 'jack'); #start 1003 end 1323 time 2019-03-01 10:30:55

```

**对标准insert的解析回滚**
shell> python rollback_binlog.py --flashback -h127.0.0.1 -P3306 -uroot -padmin -drollback -tuser --start-file='mysql-bin.000004' --start-position=1003 --stop-position=3036 --sql-type insert
输出：
DELETE FROM `rollback`.`user` WHERE `age`=12 AND `sex`='F' AND `id`=1 AND `name`='jack' LIMIT 1; #start 2484 end 2734 time 2019-03-01 10:51:57
DELETE FROM `rollback`.`user` WHERE `age`=22 AND `sex`='M' AND `id`=2 AND `name`='lucy' LIMIT 1; #start 2203 end 2453 time 2019-03-01 10:51:57
DELETE FROM `rollback`.`user` WHERE `age`=33 AND `sex`='M' AND `id`=3 AND `name`='marry' LIMIT 1; #start 1921 end 2172 time 2019-03-01 10:51:57
DELETE FROM `rollback`.`user` WHERE `age`=23 AND `sex`='F' AND `id`=4 AND `name`='brank' LIMIT 1; #start 1639 end 1890 time 2019-03-01 10:51:57
DELETE FROM `rollback`.`user` WHERE `age`=26 AND `sex`='F' AND `id`=5 AND `name`='Doc xiao' LIMIT 1; #start 1354 end 1608 time 2019-03-01 10:51:57
DELETE FROM `rollback`.`user` WHERE `age`=26 AND `sex`='F' AND `id`=5 AND `name`='Doc xiao' LIMIT 1; #start 718 end 972 time 2019-03-01 10:13:20
DELETE FROM `rollback`.`user` WHERE `age`=23 AND `sex`='F' AND `id`=4 AND `name`='brank' LIMIT 1; #start 436 end 687 time 2019-03-01 10:12:45


### 选项

**mysql连接配置**

-h host; -P port; -u user; -p password

**解析模式**

--stop-never 持续解析binlog。可选。默认False，同步至执行命令时最新的binlog位置。

-K, --no-primary-key 对INSERT语句去除主键。可选。默认False

-B, --flashback 生成回滚SQL，可解析大文件，不受内存限制。可选。默认False。与stop-never或no-primary-key不能同时添加。

--back-interval -B模式下，每打印一千行回滚SQL，加一句SLEEP多少秒，如不想加SLEEP，请设为0。可选。默认1.0。

**解析范围控制**

--start-file 起始解析文件，只需文件名，无需全路径 。必须。

--start-position/--start-pos 起始解析位置。可选。默认为start-file的起始位置。

--stop-file/--end-file 终止解析文件。可选。默认为start-file同一个文件。若解析模式为stop-never，此选项失效。

--stop-position/--end-pos 终止解析位置。可选。默认为stop-file的最末位置；若解析模式为stop-never，此选项失效。

--start-datetime 起始解析时间，格式'%Y-%m-%d %H:%M:%S'。可选。默认不过滤。

--stop-datetime 终止解析时间，格式'%Y-%m-%d %H:%M:%S'。可选。默认不过滤。

**对象过滤**

-d, --databases 只解析目标db的sql，多个库用空格隔开，如-d db1 db2。可选。默认为空。

-t, --tables 只解析目标table的sql，多张表用空格隔开，如-t tbl1 tbl2。可选。默认为空。

--only-dml 只解析dml，忽略ddl。可选。默认False。

--sql-type 只解析指定类型，支持INSERT, UPDATE, DELETE。多个类型用空格隔开，如--sql-type INSERT DELETE。可选。默认为增删改都解析。用了此参数但没填任何类型，则三者都不解析。

### 应用案例

#### **误删整张表数据，需要紧急回滚**

闪回详细介绍可参见example目录下《闪回原理与实战》[example/mysql-flashback-priciple-and-practice.md](./example/mysql-flashback-priciple-and-practice.md)

```bash
rollback库user表原有数据
mysql> select * from user;
+----+----------+------+------+
| id | name     | age  | sex  |
+----+----------+------+------+
|  1 | jack     |   12 | F    |
|  2 | lucy     |   22 | M    |
|  3 | marry    |   33 | M    |
|  4 | brank    |   23 | F    |
|  5 | Doc xiao |   26 | F    |
+----+----------+------+------+
5 rows in set (0.01 sec)

mysql> delete from user;
Query OK, 5 rows affected (0.06 sec)

10:28时,user表误操作被清空
mysql> select * from user;
Empty set (0.00 sec)
```

**恢复数据步骤**：

1. 登录mysql，查看目前的binlog文件

	```bash
	mysql> show master status;
+------------------+----------+--------------+------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+------------------+----------+--------------+------------------+-------------------+
| mysql-bin.000004 |      154 |              |                  |                   |
+------------------+----------+--------------+------------------+-------------------+
	```

2. 最新的binlog文件是mysql-bin.000004，我们再定位误操作SQL的binlog位置。误操作人只能知道大致的误操作时间，我们根据大致时间过滤数据。

	```bash
	shell> python rollback_binlog.py -h127.0.0.1 -P3306 -uroot -padmin -drollback -tuser --start-file='mysql-bin.000004' --start-datetime='2019-03-01 10:25:00' --stop-datetime='2019-03-01 10:32:00'

	输出：
DELETE FROM `rollback`.`user` WHERE `age`=12 AND `sex`='F' AND `id`=1 AND `name`='jack' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=22 AND `sex`='M' AND `id`=2 AND `name`='lucy' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=33 AND `sex`='M' AND `id`=3 AND `name`='marry' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=23 AND `sex`='F' AND `id`=4 AND `name`='brank' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
DELETE FROM `rollback`.`user` WHERE `age`=26 AND `sex`='F' AND `id`=5 AND `name`='Doc xiao' LIMIT 1; #start 1003 end 1323 time 2019-03-01 10:30:55
	```

3. 我们得到了误操作sql的准确位置在1003-1323之间，再根据位置进一步过滤，使用flashback模式生成回滚sql，检查回滚sql是否正确(注：真实环境下，此步经常会进一步筛选出需要的sql。结合grep、编辑器等)

	```bash
	shell> python rollback_binlog.py -h127.0.0.1 -P3306 -uroot -padmin -drollback -tuser --start-file='mysql-bin.000004' --start-position=1003 --stop-position=1323 -B > back.sql | cat back.sql
	输出：
    INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (26, 'F', 5, 'Doc xiao'); #start 1003 end 1323 time 2019-03-01 10:30:55
    INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (23, 'F', 4, 'brank'); #start 1003 end 1323 time 2019-03-01 10:30:55
    INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (33, 'M', 3, 'marry'); #start 1003 end 1323 time 2019-03-01 10:30:55
    INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (22, 'M', 2, 'lucy'); #start 1003 end 1323 time 2019-03-01 10:30:55
    INSERT INTO `rollback`.`user`(`age`, `sex`, `id`, `name`) VALUES (12, 'F', 1, 'jack'); #start 1003 end 1323 time 2019-03-01 10:30:55
	```

4. 确认回滚sql正确，执行回滚语句。登录mysql确认，数据回滚成功。

	```bash
	shell> mysql -h127.0.0.1 -P3306 -uroot -padmin rollback < back.sql

	mysql> select * from user;
    +----+----------+------+------+
    | id | name     | age  | sex  |
    +----+----------+------+------+
    |  1 | jack     |   12 | F    |
    |  2 | lucy     |   22 | M    |
    |  3 | marry    |   33 | M    |
    |  4 | brank    |   23 | F    |
    |  5 | Doc xiao |   26 | F    |
    +----+----------+------+------+
	```

### 限制（对比mysqlbinlog）

* mysql server必须开启，离线模式下不能解析
* 参数 _binlog\_row\_image_ 必须为FULL，暂不支持MINIMAL
* 解析速度不如mysqlbinlog

### 优点（对比mysqlbinlog）

* 纯Python开发，安装与使用都很简单
* 自带flashback、no-primary-key解析模式，无需再装补丁
* flashback模式下，更适合[闪回实战](./example/mysql-flashback-priciple-and-practice.md)
* 解析为标准SQL，方便理解、筛选
* 代码容易改造，可以支持更多个性化解析



