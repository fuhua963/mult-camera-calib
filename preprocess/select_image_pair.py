import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QListWidget, 
                            QMessageBox, QProgressBar, QShortcut)
from PyQt5.QtGui import QPixmap, QImage, QKeySequence
from PyQt5.QtCore import Qt, QSize

class ImagePairSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_folder = None
        self.current_index = 0
        self.selected_pairs = set()  # 记录已选择的图像对
        self.setup_shortcuts()  # 添加这行
        
    def setup_shortcuts(self):
        """设置快捷键"""
        # 左箭头：上一对
        self.shortcut_prev = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut_prev.activated.connect(self.show_previous)
        
        # 右箭头：下一对
        self.shortcut_next = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut_next.activated.connect(self.show_next)
        
        # 空格：选择/取消选择
        self.shortcut_select = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.shortcut_select.activated.connect(self.select_current)
        
        # S键：保存
        self.shortcut_save = QShortcut(QKeySequence('S'), self)
        self.shortcut_save.activated.connect(self.save_selected_pairs)
        
        # 添加文件夹导航快捷键
        self.shortcut_prev_folder = QShortcut(QKeySequence('A'), self)
        self.shortcut_prev_folder.activated.connect(self.previous_folder)
        
        self.shortcut_next_folder = QShortcut(QKeySequence('D'), self)
        self.shortcut_next_folder.activated.connect(self.next_folder)
        
    def initUI(self):
        self.setWindowTitle('图像对选择器')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 创建顶部按钮布局
        top_layout = QHBoxLayout()
        
        # 添加文件夹选择按钮
        self.folder_btn = QPushButton('选择文件夹', self)
        self.folder_btn.clicked.connect(self.load_folders)
        top_layout.addWidget(self.folder_btn)
        
        # 添加保存按钮
        self.save_btn = QPushButton('保存选中的图像对', self)
        self.save_btn.clicked.connect(self.save_selected_pairs)
        self.save_btn.setEnabled(False)
        top_layout.addWidget(self.save_btn)
        
        layout.addLayout(top_layout)
        
        # 创建图像显示区域
        image_layout = QHBoxLayout()
        
        # RGB图像显示
        rgb_layout = QVBoxLayout()
        self.rgb_label = QLabel('RGB图像')
        self.rgb_image = QLabel()
        self.rgb_image.setFixedSize(500, 500)
        rgb_layout.addWidget(self.rgb_label)
        rgb_layout.addWidget(self.rgb_image)
        image_layout.addLayout(rgb_layout)
        
        # 重建图像显示
        recon_layout = QVBoxLayout()
        self.recon_label = QLabel('重建图像')
        self.recon_image = QLabel()
        self.recon_image.setFixedSize(500, 500)
        recon_layout.addWidget(self.recon_label)
        recon_layout.addWidget(self.recon_image)
        image_layout.addLayout(recon_layout)
        
        layout.addLayout(image_layout)
        
        # 创建底部控制按钮
        control_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton('上一对', self)
        self.prev_btn.clicked.connect(self.show_previous)
        self.prev_btn.setEnabled(False)
        control_layout.addWidget(self.prev_btn)
        
        self.select_btn = QPushButton('选择此对', self)
        self.select_btn.clicked.connect(self.select_current)
        self.select_btn.setEnabled(False)
        control_layout.addWidget(self.select_btn)
        
        self.next_btn = QPushButton('下一对', self)
        self.next_btn.clicked.connect(self.show_next)
        self.next_btn.setEnabled(False)
        control_layout.addWidget(self.next_btn)
        
        layout.addLayout(control_layout)
        
        # 添加进度显示
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        self.progress_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_label)
        
        # 添加文件夹导航按钮
        folder_nav_layout = QHBoxLayout()
        
        self.prev_folder_btn = QPushButton('上一个文件夹', self)
        self.prev_folder_btn.clicked.connect(self.previous_folder)
        self.prev_folder_btn.setEnabled(False)
        folder_nav_layout.addWidget(self.prev_folder_btn)
        
        self.next_folder_btn = QPushButton('下一个文件夹', self)
        self.next_folder_btn.clicked.connect(self.next_folder)
        self.next_folder_btn.setEnabled(False)
        folder_nav_layout.addWidget(self.next_folder_btn)
        
        layout.addLayout(folder_nav_layout)
        
        # 初始化数据
        self.folders = []
        self.current_pairs = []
        
    def load_folders(self):
        """加载文件夹"""
        base_dir = "./image_pairs"
        if not os.path.exists(base_dir):
            QMessageBox.warning(self, '错误', 'image_pairs文件夹不存在！')
            return
            
        self.folders = []
        for main_folder in ['1.10', '1.11']:
            folder_path = os.path.join(base_dir, main_folder)
            if os.path.exists(folder_path):
                subfolders = sorted([f for f in os.listdir(folder_path) 
                                   if os.path.isdir(os.path.join(folder_path, f))],
                                  key=lambda x: int(x))
                for subfolder in subfolders:
                    full_path = os.path.join(folder_path, subfolder)
                    self.folders.append(full_path)
        
        if self.folders:
            self.current_folder = 0
            self.load_current_folder()
            self.save_btn.setEnabled(True)
            print(f"已加载 {len(self.folders)} 个文件夹")
            
            # 启用文件夹导航按钮
            self.prev_folder_btn.setEnabled(True)
            self.next_folder_btn.setEnabled(True)
        else:
            print("未找到任何文件夹")
        
    def load_current_folder(self):
        folder = self.folders[self.current_folder]
        rgb_path = os.path.join(folder, 'rgb')
        recon_path = os.path.join(folder, 'event')
        
        rgb_images = sorted([f for f in os.listdir(rgb_path) if f.endswith('.png')],
                          key=lambda x: int(x.split('.')[0]))
        recon_images = sorted([f for f in os.listdir(recon_path) if f.endswith('.png')],
                            key=lambda x: int(x.split('.')[0]))
        
        self.current_pairs = list(zip(
            [os.path.join(rgb_path, img) for img in rgb_images],
            [os.path.join(recon_path, img) for img in recon_images]
        ))
        
        self.current_index = 0
        self.update_display()
        self.update_controls()
        
    def update_display(self):
        if not self.current_pairs:
            return
            
        rgb_path, recon_path = self.current_pairs[self.current_index]
        
        # 显示RGB图像
        pixmap = QPixmap(rgb_path)
        pixmap = pixmap.scaled(500, 500, Qt.KeepAspectRatio)
        self.rgb_image.setPixmap(pixmap)
        
        # 显示重建图像
        pixmap = QPixmap(recon_path)
        pixmap = pixmap.scaled(500, 500, Qt.KeepAspectRatio)
        self.recon_image.setPixmap(pixmap)
        
        # 更新进度显示，添加更详细的文件夹信息
        folder_path = os.path.dirname(os.path.dirname(rgb_path))
        main_folder = os.path.basename(os.path.dirname(folder_path))  # 1.10 或 1.11
        sub_folder = os.path.basename(folder_path)  # 子文件夹编号
        
        self.progress_label.setText(
            f'当前位置: {main_folder}/{sub_folder}\n'
            f'图像进度: {self.current_index + 1}/{len(self.current_pairs)}\n'
            f'文件夹进度: {self.current_folder + 1}/{len(self.folders)}'
        )
        
        # 更新选择按钮状态
        pair_key = (rgb_path, recon_path)
        self.select_btn.setText('取消选择' if pair_key in self.selected_pairs else '选择此对')
        
    def update_controls(self):
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.current_pairs) - 1)
        self.select_btn.setEnabled(bool(self.current_pairs))
        
    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()
            self.update_controls()
            
    def show_next(self):
        if self.current_index < len(self.current_pairs) - 1:
            self.current_index += 1
            self.update_display()
            self.update_controls()
            
    def select_current(self):
        if not self.current_pairs:
            return
            
        pair_key = self.current_pairs[self.current_index]
        if pair_key in self.selected_pairs:
            self.selected_pairs.remove(pair_key)
        else:
            self.selected_pairs.add(pair_key)
        self.update_display()
        
    def save_selected_pairs(self):
        if not self.selected_pairs:
            QMessageBox.warning(self, '警告', '请先选择要保存的图像对！')
            return
            
        # 创建保存目录
        output_dir = "./pair2calib"
        event_dir = os.path.join(output_dir, "event")
        flir_dir = os.path.join(output_dir, "flir")
        os.makedirs(event_dir, exist_ok=True)
        os.makedirs(flir_dir, exist_ok=True)
        
        # 获取已存在的最大编号
        existing_numbers = []
        if os.path.exists(event_dir):
            existing_numbers.extend([
                int(f.split('.')[0]) for f in os.listdir(event_dir)
                if f.endswith('.png') and f.split('.')[0].isdigit()
            ])
        if os.path.exists(flir_dir):
            existing_numbers.extend([
                int(f.split('.')[0]) for f in os.listdir(flir_dir)
                if f.endswith('.png') and f.split('.')[0].isdigit()
            ])
        
        # 确定起始编号
        start_number = max(existing_numbers, default=0) + 1
        
        # 保存选中的图像对
        for i, (rgb_path, recon_path) in enumerate(sorted(self.selected_pairs), start_number):
            # 复制RGB图像到flir文件夹
            dst_rgb = os.path.join(flir_dir, f"{i}.png")
            shutil.copy2(rgb_path, dst_rgb)
            
            # 复制重建图像到event文件夹
            dst_recon = os.path.join(event_dir, f"{i}.png")
            shutil.copy2(recon_path, dst_recon)
        
        QMessageBox.information(
            self, 
            '成功', 
            f'已保存 {len(self.selected_pairs)} 对图像！\n'
            f'编号范围: {start_number} - {start_number + len(self.selected_pairs) - 1}'
        )
        
        # 保存完成后清空选择
        self.selected_pairs.clear()
        self.update_display()

    def previous_folder(self):
        """切换到上一个文件夹"""
        if self.current_folder > 0:
            self.current_folder -= 1
            self.load_current_folder()
            self.update_folder_controls()

    def next_folder(self):
        """切换到下一个文件夹"""
        if self.current_folder < len(self.folders) - 1:
            self.current_folder += 1
            self.load_current_folder()
            self.update_folder_controls()

    def update_folder_controls(self):
        """更新文件夹导航按钮状态"""
        self.prev_folder_btn.setEnabled(self.current_folder > 0)
        self.next_folder_btn.setEnabled(self.current_folder < len(self.folders) - 1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImagePairSelector()
    window.show()
    sys.exit(app.exec_()) 