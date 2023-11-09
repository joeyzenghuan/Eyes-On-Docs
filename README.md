##用户界面
用户可以在Teams Channel中看到以下推送。
![Message UI](/images/message_ui.jpg)
- 最上方是GPT4给出的标题
- 第二行是更新的UTC时间
- 主体内容是GPT4对这次更新涉及到的不同文档的总结。比如例子中涉及了三个文档的更新。
- 点击链接可以进入官方文档。
- 最下方的“Go to commit page”按钮，可以跳转到GitHub的commit页面。

##Commit Page
https://github.com/MicrosoftDocs/azure-docs/commit/4189b431df9d28d94f54661e223c318335bcb9f2 

可以看到这次更新涉及了三个文件的修改，和GPT4给出的总结一致。
左边是更新前的版本，右边是更新后的版本。
![Commit Page](/images/commit_page.jpg)

通过点击右上角的Preview按钮，可以更直观地看到更新的内容。
https://github.com/MicrosoftDocs/azure-docs/commit/4189b431df9d28d94f54661e223c318335bcb9f2

![preview_button](/images/preview_button.jpg)
![preview_ui](/images/preview_ui.jpg)

##原理：
- 以Azure OpenAI为例，文档的每次更新记录都会记录在 https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/ai-services/openai 这个页面。
- 爬取每一个commit的更新内容
- 提交给GPT4进行总结，生成标题
- 通过Teams Channel Webhook将GPT4的总结推送到Teams Channel



准备**

首先点击requirements 文件，查看并安装相关第三方包与支持环境。

接着创建.env文件 按照.env.example的示例，将your_xxxxxxxx 填入你自己的内容。

**运行**

如果需要测试效果，就不用更改代码中的starttime设定，测试时按照固定时间，爬取固定时间之后的commits事件。

如果需要正式开始监控，就将固定的starttime注释，将starttime下方的代码取消注释，则程序会从当前时间开始，监控并爬取更新的commits事件。

**时间间隔**

默认时间间隔为3600秒，也就是一小时，如果需要修改可以在MainDialog类的初始化方法中更改schedule变量。

