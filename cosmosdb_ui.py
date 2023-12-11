import sys
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QPixmap
from io import BytesIO  
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDateTime, QUrl, QTimer
from PyQt5.QtGui import QDesktopServices
from ui_layout import Ui_DocsBot_CosmosDB
from cosmosdb_client import CosmosDBHandler
from threading import Thread


class MyApplication(QtWidgets.QMainWindow, CosmosDBHandler):
    def __init__(self):
        super(MyApplication, self).__init__()
        self.ui = Ui_DocsBot_CosmosDB()
        self.ui.setupUi(self)
        self.ui.clear_button.clicked.connect(self.clear_all)
        self.combo_box_list = [self.ui.topic, self.ui.language, self.ui.status, self.ui.tag, self.ui.post]
        self.date_list = [self.ui.start_time, self.ui.end_time]

        self.name_list = ["topic", "language", "status", "tag", "post"]
        self.topic = self.language = self.status = self.tag = self.post = "Select All"
        self.parameters = [self.topic, self.language, self.status, self.tag, self.post]
        self.data_list = ["gpt_title_tokens", "gpt_summary_tokens", "commit_time", "root_commits_url", "status", "language", "topic", "id", "log_time"]
        self.title_font = '<span style="font-size: 20px; font-weight: bold;font-family: "Microsoft JhengHei"">{}</span>'
        self.text_font = '<span style="font-size: 15px;font-family: "Microsoft JhengHei"">{}</span>'
        self.error_font = '<span style="color:red;font-size: 15px;font-family: "Microsoft JhengHei"">{}</span>'
        self.start_time = self.end_time = None
        self.ui.text_window.setOpenExternalLinks(False)
        self.ui.text_window.anchorClicked.connect(self.open_link)
        self.ui.checkBox.clicked.connect(self.call_cosmosdb)
        self.ui.number.valueChanged.connect(self.call_cosmosdb)

        self.fig, self.axs = plt.subplots(4,2)
        self.fig.set_size_inches(10, 5)
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False 


        self.db = self.initialize_cosmos_client()
        self.all_commit_time = self.db.get_commit_time_list()
        self.init_setting()
        self.show()
        self.call_cosmosdb()

    def open_link(self, url):  
        QDesktopServices.openUrl(url)  
        self.ui.text_window.setSource(QUrl()) 
        
    def add_html_link(self, url):
        self.ui.text_window.append(f"<a href='{url}'>{url}</a>")

    def add_title(self, title):
        title = self.title_format(title)
        self.ui.text_window.append(self.title_font.format(title))

    def add_summary(self, summary):
        if summary.startswith("https://"):
            new_line_index = summary.find("\n\n")
            self.add_html_link(summary[:new_line_index])
            self.ui.text_window.append(self.text_font.format(summary[new_line_index:]))
        else:
            self.ui.text_window.append(self.text_font.format(summary))
        
    def add_new_line(self):
        font = '<span style="color:orange;font-size: 15px; font-weight: bold;font-family: "Microsoft JhengHei"">{}</span>'
        self.ui.text_window.append(font.format("----------------------------------------------------------------------------------------------------------------------------"))

    def add_simple_data(self, data):
        if "gpt_title_response" in data.keys():
            self.add_title(data["gpt_title_response"])
        else:
            self.ui.text_window.append(self.error_font.format(f"gpt_title_response data could not be found"))
        if  "gpt_summary_response" in data.keys():
            self.add_summary(data["gpt_summary_response"])
        else:
            self.ui.text_window.append(self.error_font.format(f"gpt_summary_response data could not be found"))

    def add_other_data(self, key, value, data):
        if key in data.keys():
            if key in self.data_list:
                self.ui.text_window.append(self.text_font.format(str(key) + ": " + str(value)))
        else:
            self.ui.text_window.append(self.error_font.format(f"{key} data could not be found"))

    def add_all_data(self, data):
        self.add_simple_data(data)
        for k, v in data.items():
            self.add_other_data(k, v, data)
        self.ui.text_window.append("")

    def roll_to_top(self):
        self.ui.scrollArea.verticalScrollBar().setValue(10)
        
        # self.ui.scrollArea.verticalScrollBar().setValue()
        # vertical_scroll_bar = self.ui.scrollArea.verticalScrollBar()  
        # vertical_scroll_bar.setValue(0)
        # vertical_scroll_bar = self.ui.scrollArea.verticalScrollBar()
        # print(vertical_scroll_bar.minimum())
        # vertical_scroll_bar.setValue(vertical_scroll_bar.maximum()) 

    def init_setting(self):
        for i, edit in enumerate(self.date_list):
            edit.dateChanged.connect(self.date_edit_event)
            edit.setDateTime(QDateTime.fromString(self.all_commit_time[-i], "yyyy-MM-dd hh:mm:ss"))
        for i, combo_box in enumerate(self.combo_box_list):
            name, count = self.db.get_value_list(self.name_list[i])
            if self.name_list[i] == "post":
                name = ["Select All", "Weekly Summary"]
            self.draw_pie_subplot(i, name, count, self.name_list[i])
            # self.db.get_timestamp(self.name_list[i], self.start_time, self.end_time)
            combo_box.addItems(name)
            combo_box.currentTextChanged.connect(self.combo_box_event)
        self.draw_pie()
    def get_number_of_display(self):
        return self.ui.number.value()      

    def date_edit_event(self, text):
        sender = self.sender()
        if sender.objectName() == "start_time":
            self.start_time = text.toString("yyyy-MM-dd") + " 00:00:00"
        else:
            self.end_time = text.toString("yyyy-MM-dd") + " 23:59:59"
        if self.start_time and self.end_time:
            self.call_cosmosdb()
        # print(f"Selected text from {sender.objectName()}: {text}")
        # self.db.get_current_select()

    def combo_box_event(self, text):  
        sender = self.sender()
        try:  
            self.parameters[self.name_list.index(sender.objectName())] = text
        except ValueError:  
            print(f"can't find {sender.objectName()} in {self.name_list}") 
        self.call_cosmosdb()
        # print(f"Selected text from {sender.objectName()}: {text}")  
        # print(self.parameters)

    def call_cosmosdb(self):
        self.ui.text_window.clear()
        db_data, name, count = self.db.get_current_select(*self.parameters, self.start_time, self.end_time)
        if db_data:
            if len(db_data) > self.get_number_of_display():
                db_data = db_data[:self.get_number_of_display()]
            for data in db_data:
                if self.ui.checkBox.isChecked():
                    self.add_all_data(data)
                else:
                    self.add_simple_data(data)
                self.add_new_line()
        
        # [self.draw_pie_subplot(i, name, count, self.name_list[i]) for i, combo_box in enumerate(self.combo_box_list)]
        # time.sleep(1)
        # self.roll_to_top()


    def draw_pie(self):

        # 調整子圖之間的間隔和圖例的位置  
        plt.tight_layout()  
        self.fig.subplots_adjust(right=0.85)  # 調整右側邊距以留出空間顯示圖例  
  
        # 將繪製好的圖表保存到BytesIO對象中  
        img_data = BytesIO()  
        plt.savefig(img_data, format='png', bbox_inches='tight')  
        img_data.seek(0)  
  
        # 將BytesIO對象轉換為QPixmap並在QLabel中顯示  
        pixmap = QPixmap()  
        pixmap.loadFromData(img_data.read())  
        self.ui.vision.setPixmap(pixmap)  # 假設你有一個QLabel叫做analysis_label  
  
        # 清除當前圖表，以便繪製下一個圖表
        plt.close()

    def draw_pie_subplot(self, index, name, count, title):
        if index == 4:
            return
        ax = self.axs[index][0]
        ax.pie(count, startangle=140)  
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.  
        ax.set_title(f"{title}")
        ax.set_position([0.1, ax.get_position().y0, 0.5, ax.get_position().height])  
        new = []
        for n in name[1:4]:
            if len(n) > 8:
                new.append(n[:8] + "...")
            else:
                new.append(n)
        ax.legend(new, loc='lower right', fancybox=True, shadow=True)
        


    def draw_analysis(self, items, title):
        plt.figure()
        plt.hist(items, bins=len(set(items)), color='blue', alpha=0.7)  
        plt.title(title)  
        plt.xlabel('Categories')  
        plt.ylabel('Counts')
        img_data = BytesIO()  
        plt.savefig(img_data, format='png')  
        img_data.seek(0)  
  
        # 將BytesIO對象轉換為QPixmap並在QLabel中顯示  
        pixmap = QPixmap()  
        pixmap.loadFromData(img_data.read())  
        self.ui.vision.setPixmap(pixmap)  
  
        # 清除當前圖表，以便繪製下一個圖表  
        plt.close()

    def title_format(self, title):
        if title[0] == '"':
            return title[1:-1]
        elif title.find("[") < 3:
            return title[title.find("["):]
        else:
            return title

    def clear_all(self):
        for combo_box in self.combo_box_list:
            combo_box.setCurrentIndex(0)
        for i, edit in enumerate(self.date_list):
            edit.setDateTime(QDateTime.fromString(self.all_commit_time[-i], "yyyy-MM-dd hh:mm:ss"))
        self.call_cosmosdb()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApplication()
    # window.show()
    sys.exit(app.exec_())
