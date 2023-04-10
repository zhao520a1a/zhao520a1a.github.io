---
title: MySQL 使用指南
tags: [db]
categories: [效率工具]
date: 2021-07-11
cover: https://www.simplilearn.com/ice9/free_resources_article_thumb/difference_between_sql_and_mysql.jpg
---

整体思维脑图：https://www.processon.com/mindmap/5f154637e401fd2e0def5918
<img src="img.png" alt="img.png" />

### [安装 MySQL](
 (https://blog.csdn.net/vkingnew/article/details/80105323))

> 引言：[HomebrewCN：Homebrew的国内安装脚本，从此告别龟速更新](https://baijiahao.baidu.com/s?id=1668544039877443967&wfr=spider&for=pc)
```
brew install mysql

配置：/usr/local/etc/my.cnf
启动：/usr/local/bin/mysqld

后台启动 ：brew services start mysql
前台启动： mysql.server start
![89aad1d0bfa0761664628ff5757badd5.png](evernotecid://CD3082B6-03A3-4D41-80AB-E48CAD259C0B/appyinxiangcom/17782910/ENResource/p269)

重要！！ MySQL配置data目录为/usr/local/var/mysql
注：偏好设置就没mysql图标

```

采坑记录：
> Failed to find valid data directory.
1. 先清除原来data目录
2. 执行命令mysqld --initialize-insecure，重新创建data文件夹以及对应的文件。
3.重启mysql服务


>ERROR 1819 (HY000): Your password does not satisfy the current policy requirements
解决方案：[修改密码验证策略](https://blog.csdn.net/hello_world_qwp/article/details/79551789)  

>error 2059: Authentication plugin 'caching_sha2_password' cannot be loaded
解决方案：
[改密码认证方式]
思路：将验证方式修改为上一版的，
1.使用mysql，输入ALTER USER root@localhost IDENTIFIED WITH mysql_native_password BY '111111';
2.刷新权限：FLUSH PRIVILEGES;
运行截图：![5691eeff65aba4040b3260a7942fa35d.png](evernotecid://CD3082B6-03A3-4D41-80AB-E48CAD259C0B/appyinxiangcom/17782910/ENResource/p270)


### 重置密码


**跳过MySQL的密码认证过程**
1. vim etc/my.cnf
2. 注：windows下修改的是my.ini
3. 定位到[mysqld]文本段; 
4. 在[mysqld]后面任意一行添加“skip-grant-tables”;


**重启MySQL**
/etc/init.d/mysql restart(有些用户可能需要使用/etc/init.d/mysqld restart)


**进入并修改root密码** 
输入 mysql即可进入,无须指定用户密码
```
mysql> use mysql;

# 老版本MySQL
mysql> update user set password=password("你的新密码") where user="root";
# 新版本MySQL eg：mysql5.7.21
mysql> update user set authentication_string = password("123456") where user='root' and Host = 'localhost';

mysql> flush privileges;
mysql> quit
```

**恢复配置**
将etc/my.cnf中的“skip-grant-tables”配置去除



### SQL 使用技巧

####  HQL 
select 后面非聚合列必须出现在gruopby中

#### 字符串拆分
 SUBSTRING_INDEX（str, delim, count）

<img src="MySQL%20%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/D09AEE98-4E69-4120-923A-54CCD5D647D3.png" alt="D09AEE98-4E69-4120-923A-54CCD5D647D3" style="zoom:50%;" />

#### 日期格式
  date_format(add_date, '%Y-%m-%d') add_date,

 - 近30天数据
 DATE_SUB(CURDATE(), INTERVAL 30 DAY) <= date(时间字段名)


#### 字段值判断
```
  case
      f.flow_type
      when 3 then '系统'
      when 2 then '自定义'
      else f.flow_type
    end
```

#### 获取分组取组内特定数据
可分为两种情况：
- 获取组内前几条条数据
- 获取组内第几条条数据

 

##### 获取组内前几条条数据
eg: 获取组内前2条数据
``` sql
SELECT
	*
FROM
	(
		SELECT
			g.id ,
			g.kemu ,
			g.score ,
			count(*) AS rank
		FROM
			grade g
		LEFT JOIN grade g1 ON g.kemu = g1.kemu
		AND g.score <= g1.score
		GROUP BY
			g.id ,
			g.kemu ,
			g.score
		ORDER BY
			g.id ,
			g.kemu ,
			g.score DESC
	) n
WHERE
	rank <= 2
ORDER BY
	kemu ,
	rank 
```


##### 获取组内第几条条数据

- 子查询 -  mysql
 eg: 获取组内第二条数据
``` sql
SELECT
	fr.id ,
	fr.bug_id ,
	fr.creator first_follow_name
FROM
	iwork_feedback_remark fr
WHERE
	fr.id =(
		SELECT
			id
		FROM
			iwork_feedback_remark
		WHERE
			bug_id = fr.bug_id
		LIMIT 1 , 1
	)
```


​      

- ROW_NUMBER()  - hive
`语法：ROW_NUMBER() OVER(PARTITION BY COLUMN ORDER BY COLUMN)`
> 简单的说row_number()从1开始，为每一条分组记录返回一个数字，这里的ROW_NUMBER() OVER (ORDER BY xlh DESC) 是先把xlh列降序，再为降序以后的没条xlh记录返回一个序号
 eg: 获取组内第二条数据
 ``` sql
SELECT
	id ,
	bug_id ,
	creator ,
	add_date
FROM
	(
		SELECT
			id ,
			bug_id ,
			creator ,
			add_date ,
			row_number() over(PARTITION BY bug_id ORDER BY id) row_num
		FROM hdp_teg_feedback_remark
	) fr
WHERE
	row_num == 2
 ```

 


 #### 将多个列中内容合成一个字段

 #####  GROUP_CONCAT  - mysql
 eg： 将id降序后的列表中name数据已‘/’拼接起来

 ``` sql
 SELECT
	bf.id ,
     GROUP_CONCAT(name order by id desc separator '/') NAME
FROM
	iwork_bugs_feedback bf
LEFT JOIN iwork_feedback_ranks fr ON(
	fr.id = bf.filed1
	OR fr.id = bf.filed2
	OR fr.id = bf.filed3
)
WHERE
	kefu_org_id = 2104
GROUP BY
	bf.id
 ```

 ##### concat_ws -hive
 concat_ws('/', collect_set( fr.name))  name 


#### 将分组中的某列转为一个数组
Hive中collect相关的函数有collect_list和collect_set。
它们都是将分组中的某列转为一个数组返回，不同的是collect_list不去重而collect_set去重。


#### 按时间区间统计数据
使用使用`时间格式函数` + ·Group by· 的方式来获取数据

##### 按月维度统计
eg: 需求平均完成周期
 注：排除了需求完成周期超过90天异常数据
``` sql
SELECT
	DATE_FORMAT(add_date , '%Y-%m') AS time ,
	avg(
		timestampdiff(DAY , add_date , real_end_date)
	) AS avg_finish_time
FROM
	iwork_issue
WHERE
	add_date BETWEEN '2017-01-01 00:00:00'
AND '2019-01-01 00:00:00'
AND real_end_date IS NOT NULL
AND state = 3
AND timestampdiff(DAY , add_date , real_end_date) <= 90
GROUP BY
	time
```


##### 按周维度统计
 eg: 迭代完成周期分布,按每7天维度统计 【时间分隔 [0,7)  [7-14)  [14,21) 】
``` sql
SELECT
	floor(
		timestampdiff(DAY , start_time , online_time) / 7 + 1
	) * 7 AS t ,
	count(*)
FROM
	iwork_project b
WHERE
	start_time BETWEEN '2018-01-01 00:00:00'
AND '2019-01-01 00:00:00'
AND online_time IS NOT NULL
GROUP BY
	t
HAVING
	t > 0
```


##### 按天维度统计
eg: bug解决周期分布
``` sql
SELECT
	timestampdiff(DAY , add_date , solve_date) AS t ,
	count(*)
FROM
	iwork_bug
WHERE
	add_date BETWEEN '2018-01-01 00:00:00'
AND '2019-01-01 00:00:00'
AND state IN(2 , 4)
GROUP BY
	t
HAVING
	t > 0
```

##### 按小时维度统计
eg: 需求录入时间分布图（0-24h）
``` sql
SELECT
	DATE_FORMAT(add_date , '%H') hours ,
	COUNT(add_date)
FROM
	iwork_issue b
WHERE
	add_date BETWEEN '2018-01-01'
AND '2019-01-01'
GROUP BY
	hours;
```

##### 按分钟维度统计
eg：3天内bugfix最快(Top1-3)的业务线
``` sql
SELECT
	avg(timestampdiff(MINUTE , add_date , solve_date)) AS t ,
	bg.id ,
	bg.bg_name
FROM
	iwork_bug b
LEFT JOIN iwork_product p ON(p.id = b.org_id)
LEFT JOIN iwork_business_group bg ON(bg.id = p.bg_id)
WHERE
	add_date BETWEEN '2018-01-01 00:00:00'
AND '2019-01-01 00:00:00'
AND b.state IN(2 , 4)
AND timestampdiff(DAY , add_date , solve_date) < 3
GROUP BY
	p.bg_id
ORDER BY
	t ASC
LIMIT 0 ,
 3
```


### 索引调优
1. 查询是在单个表上。
2. GROUP BY仅命名构成索引最左前缀的列，而没有命名其他列。（如果查询具有DISTINCT子句，而不是GROUP BY，则所有不同的属性都引用构成索引最左前缀的列。）
eg: 
- 如果表t1在（c1，c2，c3）上具有索引，如果查询具有GROUP BY c1，c2，则松散索引扫描适用。
- 如果查询具有GROUP BY c2，c3（列不是最左边的前缀）或GROUP BY c1，c2，c4（c4不在索引中），则不适用。

3. 选择列表中使用的唯一聚合函数（如果有）是MIN（）和MAX（），它们全部引用同一列。该列必须在索引中，并且必须紧随GROUP BY中的列。除MIN（）或MAX（）函数的参数外，查询中所引用的索引中除GROUP BY以外的任何其他部分都必须为常量（即，必须与常量相等地引用）。对于索引中的列，必须索引完整的列值，而不仅是前缀。例如，对于c1 VARCHAR（20）和INDEX（c1（10）），索引仅使用c1值的前缀，而不能用于宽松索引扫描。
