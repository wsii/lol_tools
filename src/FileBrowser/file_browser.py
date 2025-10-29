import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import (
    QApplication, QStyle, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QMenu, QFileDialog, QMessageBox,
    QPushButton, QProgressDialog, QAbstractItemView, QLineEdit, QRadioButton
)
from qfluentwidgets import (
    FluentWindow, MSFluentWindow, SubtitleLabel, TitleLabel,
    PrimaryPushButton, PushButton, ComboBox, LineEdit,
    ScrollArea, StateToolTip, ToolTipFilter, ToolTipPosition, InfoBar,
    Dialog, CheckBox, TreeWidget, RadioButton
)
from PySide6.QtGui import QPainter

from Core.paths import LOL_CLIENT_DIR, LOL_OUT_DIR

class CustomDelegate(QTreeWidgetItem):
    """自定义委托类，用于绘制带有勾选框的树项"""
    def paint(self, painter, option, index):
        try:
            # 检查是否为文件名列
            if index.column() == 0:
                # 获取项数据
                is_checked = self.checkState(0) == Qt.Checked
                
                # 计算勾选框位置（在文件名前面）
                check_box_rect = QRect(option.rect.left() + 5, option.rect.top() + 3, 16, 16)
                
                # 绘制勾选框
                if is_checked:
                    painter.fillRect(check_box_rect, Qt.blue)
                    painter.setPen(Qt.white)
                    painter.drawText(check_box_rect, Qt.AlignCenter, "✓")
                else:
                    painter.setPen(Qt.gray)
                    painter.drawRect(check_box_rect)
                
                # 调整文本位置，为勾选框留出空间
                text_rect = option.rect.adjusted(25, 0, 0, 0)
                painter.drawText(text_rect, Qt.AlignVCenter, option.text)
            else:
                # 对于目录，使用默认绘制
                super().paint(painter, option, index)
        except Exception as e:
            # 出错时使用默认绘制
            super().paint(painter, option, index)
    
    def sizeHint(self, option, index):
        """重写sizeHint方法，确保足够的空间"""
        size = super().sizeHint(option, index)
        # 增加高度，使勾选框更明显
        size.setHeight(max(size.height(), 24))
        return size

class FileBrowserApp(QWidget):
    """文件浏览器工具主应用窗口"""
    
    def __init__(self):
        super().__init__()
        # 设置当前选择的路径
        self.current_path = ""
        
        try:
            # 尝试从配置中读取路径
            from Core.config import cfg
            # 从配置中获取LOL客户端资产路径（默认为空）
            if hasattr(cfg, 'lol_client_dir') and cfg.lol_client_dir.value and os.path.isdir(str(cfg.lol_client_dir.value)):
                self.current_path = str(cfg.lol_client_dir.value)
        except Exception:
            # 如果读取配置出错，保持路径为空
            pass
        
        # 如果没有有效的路径，回退到用户主目录
        if not self.current_path or not os.path.exists(self.current_path) or not os.path.isdir(self.current_path):
            self.current_path = os.path.expanduser("~")
        
        # 存储文件勾选状态的字典
        self.checked_files = {}
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 直接设置布局到QWidget
        main_layout = QVBoxLayout(self)
        
        # 上部按钮区域
        buttons_layout = QHBoxLayout()
        
        # 路径显示框
        self.path_edit = LineEdit()
        self.path_edit.setText(self.current_path)
        self.path_edit.setReadOnly(True)
        buttons_layout.addWidget(self.path_edit, 1)
        
        # 选择路径按钮
        self.select_path_btn = PrimaryPushButton("选择路径")
        self.select_path_btn.clicked.connect(self.select_path)
        buttons_layout.addWidget(self.select_path_btn)
        
        # 保存为默认路径按钮
        self.save_default_btn = PushButton("保存为默认路径")
        self.save_default_btn.clicked.connect(self.save_default_path)
        buttons_layout.addWidget(self.save_default_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # 文件统计标签
        self.stats_label = QLabel("文件统计: 0 个文件")
        main_layout.addWidget(self.stats_label)
        
        # 移除文件操作区域
        
        # 创建TreeWidget (使用qfluentwidgets的TreeWidget)
        self.file_tree_view = TreeWidget()
        # 只设置两列：文件名和大小
        self.file_tree_view.setHeaderLabels(["文件名", "大小"])
        self.file_tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.file_tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 启用复选框功能
        self.file_tree_view.setSelectionMode(TreeWidget.SingleSelection)
        
        # 连接复选框状态变化信号
        self.file_tree_view.itemChanged.connect(self.on_item_changed)
        
        # 连接点击事件，让文件夹可以单击展开
        self.file_tree_view.itemClicked.connect(self.on_item_clicked)
        
        # 设置为单击展开模式
        self.file_tree_view.setItemsExpandable(True)
        main_layout.addWidget(self.file_tree_view, 1)
        
        # 设置列宽比例
        self.set_column_widths()
        
        # 连接窗口大小变化事件，以便在窗口大小改变时重新调整列宽比例
        self.file_tree_view.resizeEvent = lambda event: (super(type(self.file_tree_view), self.file_tree_view).resizeEvent(event), self.set_column_widths())
        
        # 设置根路径
        self.set_root_path(self.current_path)
        
        # 导出路径配置区域
        export_path_layout = QHBoxLayout()
        export_path_layout.setContentsMargins(0, 10, 0, 10)
        
        # 导出路径标签
        export_label = QLabel("导出路径:")
        export_path_layout.addWidget(export_label)
        
        # 导出路径显示框
        self.export_path_edit = LineEdit()
        # 从配置中获取默认导出路径
        try:
            from Core.config import cfg
            if hasattr(cfg, 'lol_out_dir') and cfg.lol_out_dir.value:
                self.export_path_edit.setText(str(cfg.lol_out_dir.value))
        except Exception:
            # 如果读取配置出错，保持为空
            pass
        self.export_path_edit.setReadOnly(True)
        export_path_layout.addWidget(self.export_path_edit, 1)
        
        # 导出路径选择按钮
        self.select_export_path_btn = PushButton("选择")
        self.select_export_path_btn.clicked.connect(self.select_export_path)
        export_path_layout.addWidget(self.select_export_path_btn)
        
        main_layout.addLayout(export_path_layout)
        
        # 独立的导出按钮区域（最底层）
        export_button_layout = QHBoxLayout()
        export_button_layout.setContentsMargins(0, 5, 0, 15)
        
        # 导出按钮 - 增大尺寸
        self.export_btn = PrimaryPushButton("导出")
        self.export_btn.setMinimumHeight(40)  # 增大按钮高度
        self.export_btn.setFixedWidth(150)    # 设置固定宽度
        self.export_btn.clicked.connect(self.export_files)
        
        # 将按钮居中显示
        export_button_layout.addStretch()
        export_button_layout.addWidget(self.export_btn)
        export_button_layout.addStretch()
        
        main_layout.addLayout(export_button_layout)
    
    def update_file_stats(self):
        """更新文件统计信息"""
        selected_files = self.get_selected_files()
        self.stats_label.setText(f"文件统计: {len(selected_files)} 个文件")
    
    def select_export_path(self):
        """选择导出路径"""
        # 获取当前显示的路径作为默认目录
        default_path = self.export_path_edit.text() if self.export_path_edit.text() else os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "选择导出文件夹", default_path)
        if path:
            self.export_path_edit.setText(path)
            # 同时更新配置
            try:
                from Core.config import cfg
                if hasattr(cfg, 'lol_out_dir'):
                    cfg.lol_out_dir.value = path
                    cfg.save()
            except Exception:
                # 如果保存配置出错，不影响用户操作
                pass
    
    def export_files(self):
        """导出选中的文件"""
        try:
            # 获取选中的文件
            selected_files = self.get_selected_files()
            if not selected_files:
                QMessageBox.information(self, "提示", "请先选择要导出的文件")
                return
            
            # 获取导出路径
            export_path = self.export_path_edit.text()
            if not export_path:
                QMessageBox.warning(self, "警告", "请先选择导出路径")
                return
            
            # 确保导出路径存在
            os.makedirs(export_path, exist_ok=True)
            
            # 复制文件到导出路径
            import shutil
            success_count = 0
            error_count = 0
            error_files = []
            
            for file_path in selected_files:
                try:
                    # 目标文件路径
                    file_name = os.path.basename(file_path)
                    dest_path = os.path.join(export_path, file_name)
                    
                    # 复制文件
                    shutil.copy2(file_path, dest_path)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    error_files.append(f"{file_path}: {str(e)}")
            
            # 显示导出结果
            if error_count == 0:
                QMessageBox.information(self, "成功", f"全部 {success_count} 个文件导出成功")
            else:
                message = f"成功导出 {success_count} 个文件\n导出失败 {error_count} 个文件\n\n"
                if error_files:
                    message += "失败的文件:\n" + "\n".join(error_files[:10])  # 只显示前10个失败的文件
                    if len(error_files) > 10:
                        message += f"\n...以及 {len(error_files) - 10} 个其他文件"
                QMessageBox.warning(self, "部分成功", message)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出过程中发生错误: {str(e)}")
    
    def set_root_path(self, path):
        """设置文件树的根路径并完全重建TreeWidget"""
        if os.path.exists(path) and os.path.isdir(path):
            self.current_path = path
            self.path_edit.setText(path)
            
            # 清除勾选状态记录
            self.checked_files.clear()
            
            # 清空TreeWidget
            self.file_tree_view.clear()
            
            # 创建根节点
            root_item = QTreeWidgetItem([os.path.basename(path), ""])
            root_item.setData(0, Qt.UserRole, path)
            root_item.setCheckState(0, Qt.Checked)  # 为根节点添加勾选框
            self.file_tree_view.addTopLevelItem(root_item)
            
            # 递归填充树结构
            self._populate_tree_widget(root_item, path)
            
            # 展开根节点
            self.file_tree_view.expandItem(root_item)
            
            # 设置列宽
            self.set_column_widths()
            
            # 更新文件统计
            self.update_file_stats()
            
    def _populate_tree_widget(self, parent_item, parent_path):
        """递归填充TreeWidget，移除空文件夹并保持展开状态"""
        try:
            # 获取目录内容
            items = os.listdir(parent_path)
            
            # 分离文件夹和文件
            folders = []
            files = []
            
            for item in items:
                item_path = os.path.join(parent_path, item)
                
                if os.path.isdir(item_path):
                    folders.append((item, item_path))
                else:
                    files.append((item, item_path))
            
            # 先添加文件夹并递归处理
            folders_to_keep = []
            for folder, folder_path in sorted(folders, key=lambda x: x[0]):
                # 创建文件夹项并添加勾选框
                folder_item = QTreeWidgetItem([folder, ""])
                folder_item.setData(0, Qt.UserRole, folder_path)
                folder_item.setCheckState(0, Qt.Checked)  # 默认勾选文件夹
                parent_item.addChild(folder_item)
                
                # 递归填充子文件夹
                self._populate_tree_widget(folder_item, folder_path)
                
                # 检查子文件夹是否为空（没有子项）
                if folder_item.childCount() == 0:
                    # 移除空文件夹
                    parent_item.removeChild(folder_item)
                else:
                    # 保留非空文件夹并设置为展开状态
                    folders_to_keep.append(folder_item)
                    folder_item.setExpanded(True)
            
            # 添加文件
            for file, file_path in sorted(files, key=lambda x: x[0]):
                try:
                    # 获取文件信息
                    file_size = os.path.getsize(file_path)
                    
                    # 创建文件项
                    file_item = QTreeWidgetItem([file, self.format_size(file_size)])
                    file_item.setData(0, Qt.UserRole, file_path)  # 存储完整路径
                    file_item.setCheckState(0, Qt.Checked)  # 默认勾选
                    parent_item.addChild(file_item)
                    
                    # 更新勾选状态记录
                    if hasattr(self, 'checked_files'):
                        self.checked_files[file_path] = True
                except Exception as e:
                    # 静默处理文件错误
                    pass
        except Exception as e:
            # 静默处理目录错误
            pass
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def select_path(self):
        """选择路径"""
        path = QFileDialog.getExistingDirectory(self, "选择文件夹", self.current_path)
        if path:
            self.set_root_path(path)
            
    def save_default_path(self):
        """将当前路径保存为默认路径"""
        try:
            from Core.config import cfg
            
            # 保存当前路径到配置
            cfg.lol_client_dir.value = self.current_path
            cfg.save()
            
            # 显示成功消息
            QMessageBox.information(self, "成功", "路径已保存为默认路径")
            
        except Exception as e:
            # 显示错误消息
            QMessageBox.critical(self, "错误", f"保存默认路径失败: {str(e)}")
    
    def get_selected_files(self):
        """获取所有勾选的文件路径列表
        
        修复: 不再依赖checked_files字典，而是直接从当前TreeWidget中递归收集所有勾选的文件
        确保统计的文件数量与实际显示的文件数量完全一致
        """
        selected_files = []
        
        def collect_checked_files(parent_item):
            """递归收集所有勾选的文件"""
            for i in range(parent_item.childCount()):
                item = parent_item.child(i)
                file_path = item.data(0, Qt.UserRole)
                
                if file_path and os.path.isfile(file_path) and item.checkState(0) == Qt.Checked:
                    # 如果是文件且被勾选，添加到列表
                    selected_files.append(file_path)
                elif file_path and os.path.isdir(file_path):
                    # 如果是目录，递归处理
                    collect_checked_files(item)
        
        # 从根节点开始递归收集
        collect_checked_files(self.file_tree_view.invisibleRootItem())
        
        # 收集完成，返回结果
        return selected_files
        
    def check_all_filtered_files(self):
        """勾选所有过滤后的文件"""
        try:
            # 遍历TreeWidget中的所有文件项
            self._check_items_recursively(self.file_tree_view.invisibleRootItem())
        except Exception as e:
            # 静默处理错误
            pass
            
    def _check_items_recursively(self, parent_item):
        """递归检查所有文件项"""
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            file_path = item.data(0, Qt.UserRole)
            
            if file_path and os.path.isfile(file_path):
                # 设置为勾选状态
                item.setCheckState(0, Qt.Checked)
                if hasattr(self, 'checked_files'):
                    self.checked_files[file_path] = True
            else:
                # 递归检查子项
                self._check_items_recursively(item)
        
    def on_item_clicked(self, item, column):
        """处理树项点击事件，展开/折叠文件夹"""
        # 检查是否是文件夹
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isdir(file_path):
                        # 获取鼠标位置
            pos = self.file_tree_view.mapFromGlobal(QApplication.mousePosition())
            
            # 获取项的矩形区域
            rect = self.file_tree_view.visualItemRect(item)
            
            # 计算箭头区域的宽度（通常约为20像素）
            arrow_width = 20
            
            # 只有当点击位置不在箭头区域时，才手动切换展开/折叠状态
            if pos.x() > arrow_width:
            # 切换展开/折叠状态
                if item.isExpanded():
                    item.setExpanded(False)
                else:
                    # 确保子内容已经加载
                    if item.childCount() == 0:
                        self._populate_tree_widget(item, file_path)
                    item.setExpanded(True)

    def on_item_changed(self, item, column):
        """当TreeWidget项的状态改变时的处理函数"""
        # 只有第一列的状态变化需要处理
        if column == 0:
            file_path = item.data(0, Qt.UserRole)
            check_state = item.checkState(0)
            is_checked = (check_state == Qt.Checked)
            
            # 添加标志防止递归调用时的无限循环
            if hasattr(item, '_updating') and item._updating:
                return
            item._updating = True
            
            try:
                # 如果是文件夹，递归设置所有子节点的勾选状态
                if file_path and os.path.isdir(file_path):
                    self._update_child_items_check_state(item, check_state)
                # 如果是文件，更新单个文件的勾选状态
                elif file_path and os.path.isfile(file_path):
                    # 更新勾选状态记录
                    if hasattr(self, 'checked_files'):
                        if is_checked:
                            self.checked_files[file_path] = True
                        elif file_path in self.checked_files:
                            del self.checked_files[file_path]

                # 更新父节点的勾选状态
                if item.parent():
                    self._update_parent_check_state(item.parent())
                    
                # 更新文件统计
                self.update_file_stats()

            finally:
                # 确保无论如何都移除标志
                delattr(item, '_updating')
            
            
    
    def _update_child_items_check_state(self, parent_item, check_state):
        """递归更新子节点的勾选状态"""
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            file_path = item.data(0, Qt.UserRole)
            
            # 设置子项的勾选状态
            if hasattr(item, '_updating') and item._updating:
                continue
            item._updating = True
            try:
                item.setCheckState(0, check_state)
                
                # 更新文件勾选状态记录
                if file_path and os.path.isfile(file_path) and hasattr(self, 'checked_files'):
                    if check_state == Qt.Checked:
                        self.checked_files[file_path] = True
                    elif file_path in self.checked_files:
                        del self.checked_files[file_path]
                        
                # 如果是文件夹，递归更新其子项
                if file_path and os.path.isdir(file_path):
                    self._update_child_items_check_state(item, check_state)
            finally:
                # 移除标志
                item._updating = False
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取鼠标位置下的项
        item = self.file_tree_view.itemAt(position)
        
        # 创建菜单
        menu = QMenu()
        
        # 如果有选中项，添加相关操作
        if item:
            # 检查项类型（文件或文件夹）
            file_path = item.data(0, Qt.UserRole)
            
            # 添加勾选/取消勾选操作
            if item.checkState(0) == Qt.Checked:
                menu.addAction("取消勾选", lambda: item.setCheckState(0, Qt.Unchecked))
            else:
                menu.addAction("勾选", lambda: item.setCheckState(0, Qt.Checked))
            
            # 添加分隔线
            menu.addSeparator()
            
            # 如果是文件夹，添加展开/折叠操作
            if file_path and os.path.isdir(file_path):
                if item.isExpanded():
                    menu.addAction("折叠", lambda: item.setExpanded(False))
                else:
                    menu.addAction("展开", lambda: item.setExpanded(True))
        
        # 添加全选操作
        menu.addAction("全选", lambda: self.check_all_files())
        
        # 显示菜单
        menu.exec_(self.file_tree_view.mapToGlobal(position))
    
    def check_all_files(self):
        """勾选所有文件"""
        # 从根节点开始递归勾选所有文件
        self._check_items_recursively(self.file_tree_view.invisibleRootItem())
        
        # 更新文件统计
        self.update_file_stats()
    
    def set_column_widths(self):
        """设置列宽比例"""
        # 确保有足够的宽度
        total_width = self.file_tree_view.width()
        if total_width > 0:
            # 文件名占70%，大小占30%
            self.file_tree_view.setColumnWidth(0, int(total_width * 0.7))
            self.file_tree_view.setColumnWidth(1, int(total_width * 0.3))

    def delete_files_to_folder(self):
        """删除选中的文件到指定文件夹"""
        # 获取选中的文件
        selected_files = self.get_selected_files()
        
        if not selected_files:
            QMessageBox.information(self, "提示", "没有选中的文件")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_files)} 个文件到DeleteFiles文件夹吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # 确保删除文件夹存在
            if not os.path.exists(DELETE_DIR):
                os.makedirs(DELETE_DIR)
            
            # 创建进度对话框
            progress = QProgressDialog("正在删除文件...", "取消", 0, len(selected_files), self)
            progress.setWindowTitle("删除文件")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            # 执行删除操作
            for i, file_path in enumerate(selected_files):
                if progress.wasCanceled():
                    break
                
                try:
                    # 获取目标路径
                    file_name = os.path.basename(file_path)
                    target_path = os.path.join(DELETE_DIR, file_name)
                    
                    # 如果目标文件已存在，添加时间戳
                    if os.path.exists(target_path):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        name, ext = os.path.splitext(file_name)
                        target_path = os.path.join(DELETE_DIR, f"{name}_{timestamp}{ext}")
                    
                    # 移动文件到删除文件夹
                    shutil.move(file_path, target_path)
                    
                    # 更新进度
                    progress.setValue(i + 1)
                    
                except Exception as e:
                    # 单个文件删除失败不影响整体操作
                    pass
            
            if progress.wasCanceled():
                QMessageBox.information(self, "提示", "删除操作已取消")
            else:
                QMessageBox.information(self, "提示", f"成功删除 {progress.value()} 个文件")
                
                # 重新加载当前目录，更新文件列表
                self.set_root_path(self.current_path)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除文件时出错: {str(e)}")

    def move_or_copy_files(self):
        """移动或复制选中的文件"""
        # 获取选中的文件
        selected_files = self.get_selected_files()
        
        if not selected_files:
            QMessageBox.information(self, "提示", "没有选中的文件")
            return
        
        # 选择目标文件夹
        target_dir = QFileDialog.getExistingDirectory(self, "选择目标文件夹", self.current_path)
        
        if not target_dir:
            return
        
        # 判断是复制还是移动
        is_copy = self.copy_radio.isChecked()
        operation_name = "复制" if is_copy else "移动"
        
        # 确认操作
        reply = QMessageBox.question(
            self, f"确认{operation_name}", 
            f"确定要{operation_name}选中的 {len(selected_files)} 个文件吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # 创建进度对话框
            progress = QProgressDialog(f"正在{operation_name}文件...", "取消", 0, len(selected_files), self)
            progress.setWindowTitle(f"{operation_name}进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            # 是否保持相对路径
            preserve_paths = self.preserve_paths_check.isChecked()
            
            # 执行操作
            success_count = 0
            for i, file_path in enumerate(selected_files):
                if progress.wasCanceled():
                    break
                
                try:
                    # 计算目标路径
                    if preserve_paths:
                        # 计算相对于当前路径的相对路径
                        root_path = self.current_path
                        rel_path = os.path.relpath(os.path.dirname(file_path), root_path)
                        target_path = os.path.join(target_dir, rel_path)
                        
                        # 确保目标目录存在
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    else:
                        # 直接使用文件名
                        file_name = os.path.basename(file_path)
                        target_path = os.path.join(target_dir, file_name)
                        
                        # 如果目标文件已存在，添加时间戳
                        if os.path.exists(target_path):
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            name, ext = os.path.splitext(file_name)
                            target_path = os.path.join(target_dir, f"{name}_{timestamp}{ext}")
                    
                    # 执行复制或移动
                    if is_copy:
                        shutil.copy2(file_path, target_path)
                    else:
                        shutil.move(file_path, target_path)
                    
                    success_count += 1
                    
                except Exception as e:
                    # 单个文件操作失败不影响整体操作
                    pass
                finally:
                    # 更新进度
                    progress.setValue(i + 1)
            
            if progress.wasCanceled():
                QMessageBox.information(self, "提示", f"{operation_name}操作已取消")
            else:
                QMessageBox.information(self, "提示", f"成功{operation_name} {success_count} 个文件")
                
                # 如果是移动操作，重新加载当前目录
                if not is_copy:
                    self.set_root_path(self.current_path)
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"{operation_name}文件时出错: {str(e)}")

if __name__ == "__main__":
    import sys
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建窗口实例
    window = FileBrowserApp()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())