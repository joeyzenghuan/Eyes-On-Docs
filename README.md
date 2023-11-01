

**准备**

首先点击requirements 文件，查看并安装相关第三方包与支持环境。

接着创建.env文件 按照.env.example的示例，将your_xxxxxxxx 填入你自己的内容。

**运行**

如果需要测试效果，就不用更改代码中的starttime设定，测试时按照固定时间，爬取固定时间之后的commits事件。

如果需要正式开始监控，就将固定的starttime注释，将starttime下方的代码取消注释，则程序会从当前时间开始，监控并爬取更新的commits事件。

**时间间隔**

默认时间间隔为3600秒，也就是一小时，如果需要修改可以在MainDialog类的初始化方法中更改schedule变量。




祝您使用愉快。
Ryan pang