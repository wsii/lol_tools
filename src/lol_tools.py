from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, NavigationItemPosition
from FileBrowser.file_browser import FileBrowserApp as BrowserApp
from Core.setting_view import SettingView
from Core.paths import LOL_OUT_DIR
import os

class MainView(FluentWindow):
    def __init__(
            self
    ):
        super().__init__()
        self.navigationInterface.setAcrylicEnabled(True)
        self.setAcceptDrops(True)
        self.navigationInterface.panel.expandWidth = 150

        # create sub interface
        self.browse_interface = BrowserApp()
        self.setting_interface = SettingView()

        self.browse_interface.setObjectName("browser")
        self.setting_interface.setObjectName("setting")


        self._init_navigation()
        self._init_window()

    def dragEnterEvent(self, event):
        # Handle drag enter for the current active interface
        pass

    def _init_navigation(self):
        self.addSubInterface(self.browse_interface, FIF.MOVE, "文件浏览")
        self.addSubInterface(self.setting_interface, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)


    def _init_window(self):
        self.resize(1100, 750)
        # 设置窗口的最小尺寸
        self.setMinimumSize(1100, 750)

        self.setWindowTitle("LOL Tools")

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)


def create_necessary_directories():
    """创建应用程序运行所需的所有目录"""
    # 确保目录存在
    for directory in [LOL_OUT_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

if __name__ == "__main__":
    # 创建必要的目录
    create_necessary_directories()
    
    app = QApplication([])
    w = MainView()
    w.show()
    app.exec()
