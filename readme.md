# learning mall 下载小工具

使用示例：

```bash
python main.py -u myUsername -p myPassword -c 'https://www.learningmall.cn/course/view.php?id=3349' -t 5 -o 'myCourseFiles'
```

使用 username 与 password 登录 learningmall，把课程链接中的所有文件下载下来。`-t 5` 是多线程下载。文件下载到 `-o myCourseFiles` 文件夹。

可以用 3 中方式登录：

1. 复制浏览器中的 cookies 下来，通过 `-ck putYourCookiesHere` 放入 cookies；
2. 通过改变 `account.json` 里的用户名和密码，通过程序自动登录；
3. 通过 `-u YourUsername -p YourPassword` 通过命令行添加用户名密码；

同一个输出文件夹，可以不重复的补充文件，比如第一次下载了 10 个文件，之后这个课程中又添加了新的文件，再次启动程序可以把新文件补充进来。
