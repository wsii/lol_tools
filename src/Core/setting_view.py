from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QFileDialog, QMessageBox
from pathlib import Path
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    Icon,
    SettingCardGroup,
    ToolTipFilter,
)
from qfluentwidgets.components import (
    ExpandLayout,
    LargeTitleLabel,
    SmoothScrollArea,
    ComboBoxSettingCard,
    PushSettingCard,
    SwitchSettingCard
)

from .config import cfg
from .version import __version__

class SettingView(QWidget):
    def __init__(self, parent=None):

        super().__init__(parent=parent)
        self.setObjectName("setting_view")
        
        # 先初始化UI组件
        self.main_layout = QVBoxLayout()
        self.smooth_scroll_area = SmoothScrollArea()
        self.scroll_widget = QWidget()
        self.expand_layout = ExpandLayout(self.scroll_widget)
        self.setting_title = LargeTitleLabel()
        self.version_lb: BodyLabel = BodyLabel()
        
        self.is_state_tooltip_running: bool = False
        
        # 创建UI元素
        self._create_card_group()
        self._create_card()
        self._set_up_layout()
        self._initialize()
        
        # 设置工具提示
        self._set_up_tooltip()
        
        # 绑定信号
        self.bind()
        
        # 更新视图
        self.update_view()

    def _create_card_group(self):
        self.general_group = SettingCardGroup("通用", self.scroll_widget)
        self.hash_group = SettingCardGroup("哈希表设置", self.scroll_widget)

    def _create_card(self):
        # 全局设置
        self.lol_card = PushSettingCard(
            "LOL客户端资产路径",
            Icon(FluentIcon.CHEVRON_RIGHT),
            "设置LOL客户端资产路径",
            "选择LOL客户端资产路径",    
            self.general_group,
        )

        self.out_dir_card = PushSettingCard(
            "导出资产路径",
            Icon(FluentIcon.CHEVRON_RIGHT),
            "设置导出资产路径",
            "选择导出资产路径", 
            self.general_group,
        )
        
        # 哈希表设置
        self.cdtb_hash_card = PushSettingCard(
            "CDTB哈希路径",
            Icon(FluentIcon.CHEVRON_RIGHT),
            "设置CDTB哈希保存路径",
            "选择CDTB哈希保存路径",
            self.hash_group,
        )
        
        self.extracted_hash_card = PushSettingCard(
            "提取哈希路径",
            Icon(FluentIcon.CHEVRON_RIGHT),
            "设置提取哈希保存路径",
            "选择提取哈希保存路径",
            self.hash_group,
        )
        
        self.custom_hash_card = PushSettingCard(
            "自定义哈希路径",
            Icon(FluentIcon.CHEVRON_RIGHT),
            "设置自定义哈希保存路径",
            "选择自定义哈希保存路径",
            self.hash_group,
        )
        
    def _set_up_tooltip(self):
        self.lol_card.setToolTip("选择LOL客户端资产路径")
        self.out_dir_card.setToolTip("选择导出资产路径")
        self.cdtb_hash_card.setToolTip("选择CDTB哈希保存路径")
        self.extracted_hash_card.setToolTip("选择提取哈希保存路径")
        self.custom_hash_card.setToolTip("选择自定义哈希保存路径")


    def _set_up_layout(self):
        """设置布局"""
        self.smooth_scroll_area.setWidget(self.scroll_widget)

        self.expand_layout.addWidget(self.general_group)
        self.expand_layout.addWidget(self.hash_group)
        self.scroll_widget.setLayout(self.expand_layout)
        self.expand_layout.setSpacing(28)
        self.expand_layout.setContentsMargins(60, 10, 60, 0)

        # 给卡片组添加卡片
        self.general_group.addSettingCards(
            [
                self.lol_card,
                self.out_dir_card,
            ]
        )
        
        self.hash_group.addSettingCards(
            [
                self.cdtb_hash_card,
                self.extracted_hash_card,
                self.custom_hash_card,
            ]
        )

    def _initialize(self) -> None:
        """初始化窗体"""
        self.setWindowTitle("设置")
        self.setObjectName("setting_view")
        self.resize(1100, 800)
        self.smooth_scroll_area.setWidgetResizable(True)
        self.smooth_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.setting_title.setText("设置")
        self.setting_title.setMargin(30)
        self.setting_title.setFixedWidth(200)
        self.version_lb.setText(f"当前软件版本: {__version__}")
        self.version_lb.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.setting_title)
        self.main_layout.addWidget(self.smooth_scroll_area)
        self.main_layout.addWidget(self.version_lb)
        self.setLayout(self.main_layout)

        # 这里因为背景色不一样,我手动打个补丁
        self.setStyleSheet("background-color: #f9f9f9")
        self.smooth_scroll_area.setStyleSheet("background-color: #f9f9f9")

        for each in self.findChildren(QWidget):
            each.installEventFilter(ToolTipFilter(each, 200))

    def _lol_card_clicked(self):
        """让用户选择LOL客户端资产路径"""
        file_path = QFileDialog.getExistingDirectory(self, "选择LOL客户端资产路径", cfg.lol_client_dir.value)
        if file_path:
            # 保存配置
            cfg.lol_client_dir.value = file_path
            cfg.save()
            self.lol_card.setToolTip(file_path)
            QMessageBox.information(self, "提示", f"LOL客户端资产路径已设置为: {file_path}")

    def _out_dir_card_clicked(self):
        """让用户选择导出的文件目录"""
        file_path = QFileDialog.getExistingDirectory(self, "选择导出的文件目录", cfg.lol_out_dir.value)
        if file_path:
            # 保存配置
            cfg.lol_out_dir.value = file_path
            cfg.save()
            self.out_dir_card.setToolTip(file_path)
            QMessageBox.information(self, "提示", f"导出文件目录已设置为: {file_path}")
    
    def _cdtb_hash_card_clicked(self):
        """让用户选择CDTB哈希保存路径"""
        file_path = QFileDialog.getExistingDirectory(self, "选择CDTB哈希保存路径", cfg.cdtb_hashes_dir.value)
        if file_path:
            # 保存配置
            cfg.cdtb_hashes_dir.value = file_path
            cfg.save()
            self.cdtb_hash_card.setToolTip(file_path)
            QMessageBox.information(self, "提示", f"CDTB哈希保存路径已设置为: {file_path}")
    
    def _extracted_hash_card_clicked(self):
        """让用户选择提取哈希保存路径"""
        file_path = QFileDialog.getExistingDirectory(self, "选择提取哈希保存路径", cfg.extracted_hashes_dir.value)
        if file_path:
            # 保存配置
            cfg.extracted_hashes_dir.value = file_path
            cfg.save()
            self.extracted_hash_card.setToolTip(file_path)
            QMessageBox.information(self, "提示", f"提取哈希保存路径已设置为: {file_path}")
    
    def _custom_hash_card_clicked(self):
        """让用户选择自定义哈希保存路径"""
        file_path = QFileDialog.getExistingDirectory(self, "选择自定义哈希保存路径", cfg.custom_hashes_dir.value)
        if file_path:
            # 保存配置
            cfg.custom_hashes_dir.value = file_path
            cfg.save()
            self.custom_hash_card.setToolTip(file_path)
            QMessageBox.information(self, "提示", f"自定义哈希保存路径已设置为: {file_path}")


    def update_view(self):
        self.lol_card.setToolTip(cfg.lol_client_dir.value)
        self.out_dir_card.setToolTip(cfg.lol_out_dir.value)
        self.cdtb_hash_card.setToolTip(cfg.cdtb_hashes_dir.value)
        self.extracted_hash_card.setToolTip(cfg.extracted_hashes_dir.value)
        self.custom_hash_card.setToolTip(cfg.custom_hashes_dir.value)


    def bind(self):
        self.lol_card.clicked.connect(self._lol_card_clicked)
        self.out_dir_card.clicked.connect(self._out_dir_card_clicked)
        self.cdtb_hash_card.clicked.connect(self._cdtb_hash_card_clicked)
        self.extracted_hash_card.clicked.connect(self._extracted_hash_card_clicked)
        self.custom_hash_card.clicked.connect(self._custom_hash_card_clicked)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    s = SettingView()
    s.show()
    app.exec()
