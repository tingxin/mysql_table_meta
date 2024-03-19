# mysql_table_meta
查询一些基础的表空间信息

# 前提条件
```
pip3 install -r requirement.txt
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