# mysql_table_meta
查询一些基础的表空间信息

![例子](/assets/sample.jpg)

# 前提条件
1. 安装依赖
```
pip3 install -r requirement.txt
```
2. 执行代码的服务器需要和目标数据库网络打通


# 代码中需要修改的部分
```python
# 需要根据情况修改
## 数据库主节点地址
HOST = 'tx-db.cbore8wpy3mc.us-east-2.rds.amazonaws.com'
## 访问端口
PORT = 3306
## 用户名
USER = 'demo'
## 数据库名称
DBName = 'business'

# 更新meta表，获取更准确的信息。由于meta 表的信息需要手动调用analyze table命令才能更新，但是analyze 命令会对表进行上锁
# 所以不能频繁执行analyze table命令。所以需要有个间隔时间,不建议设置的太小。单位分钟
UPDATE_META_INTERVAL_MINUTES = 60
###############################################
```

# 强烈注意
```
由于程序启动后就会调用 analyze table <table name> 命令，并且会根据

UPDATE_META_INTERVAL_MINUTES，再定期调用analyze table命令，而analyze table命令会对对应的表进行

锁表（只读锁），造成缩表期间无法修改表，也不能对表写入。analyze table命令 运行的时长依赖 具体表的大

小，比较块，都是毫秒级
```

# 执行
以下命令会直接在本地生成一个Html文件，呈现表空间基础信息
```
python3 app.py  --pwd password123
```

或者
```
 python3 app.py  --pwd password123 --mode web
```
上述命令将启动一个简单的flask服务器，运行在5016端口,可以通过浏览器访问