import sys
from pathlib import Path

import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QImage, 
    QPixmap, 
    QAction,
    QPainter,
    QColor,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
    QSlider,
    QGridLayout,
    QFrame,
    QPushButton,
    QTabWidget,
)

from dicom_loader import load_dicom_series

import pyvista as pv
from pyvistaqt import QtInteractor
from lung_volume_renderer import clean_lung_mask

from PySide6.QtCore import QTimer

class MedicalImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Medical Image Viewer")
        self.resize(1200, 600)

        # タブを作成
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 2Dタブ
        self.tab_2d = QWidget()
        self.tabs.addTab(self.tab_2d, "2D Viewer")

        # 3Dタブ
        self.tab_3d = QWidget()
        self.tabs.addTab(self.tab_3d, "3D Viewer")

        # 2D側は3方向を横並び
        layout = QHBoxLayout(self.tab_2d)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 3D側は全画面表示
        self.tab_3d_layout = QVBoxLayout(self.tab_3d)
        self.tab_3d_layout.setContentsMargins(12, 12, 12, 12)

        self.image_labels = {}
        self.pixmaps = {}
        self.aspect_ratios = {}
        self.sliders = {}

        # 各方向のWL・WWを管理
        self.window_settings = {
            "Axial": {"wl": -600, "ww": 1500},
            "Coronal": {"wl": -600, "ww": 1500},
            "Sagittal": {"wl": -600, "ww": 1500},
        }

        # WL・WWスライダーを管理
        self.window_controls = {}

        # 3方向の表示領域
        for name in ["Axial", "Coronal", "Sagittal"]:
            view_panel = QFrame()
            view_panel.setObjectName("viewPanel")

            column = QVBoxLayout(view_panel)
            column.setContentsMargins(12, 12, 12, 12)
            column.setSpacing(6)

            title = QLabel(name)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)

            image_label = QLabel("No Image")
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet(
                "background-color: black; color: white;"
            )
            image_label.setMinimumSize(200, 150)

            self.image_labels[name] = image_label

            # スライス位置スライダー
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setEnabled(False)  # 読み込み前は操作不可
            slider.setSingleStep(1)

            # スライス番号表示
            position_label = QLabel("Slice: -")
            position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # スライダー操作時に画像を更新
            slider.valueChanged.connect(
                self.on_slice_position_changed
            )

            self.sliders[name] = slider

            # 画面に配置
            column.addWidget(title)
            column.addWidget(image_label, stretch=1)
            column.addWidget(position_label)
            column.addWidget(slider)

            # WLスライダー
            wl_label = QLabel("WL: -600")

            wl_slider = QSlider(Qt.Orientation.Horizontal)
            wl_slider.setRange(-2000, 2000)
            wl_slider.setValue(-600)

            # WWスライダー
            ww_label = QLabel("WW: 1500")

            ww_slider = QSlider(Qt.Orientation.Horizontal)
            ww_slider.setRange(1, 4000)
            ww_slider.setValue(1500)

            # 管理用辞書に保存
            self.window_controls[name] = {
                "wl_slider": wl_slider,
                "ww_slider": ww_slider,
                "wl_label": wl_label,
                "ww_label": ww_label,
            }

            # スライダー操作時のイベント
            wl_slider.valueChanged.connect(
                lambda _value, view=name: self.on_window_changed(view)
            )

            ww_slider.valueChanged.connect(
                lambda _value, view=name: self.on_window_changed(view)
            )

            # 画面に追加
            column.addWidget(wl_label)
            column.addWidget(wl_slider)

            column.addWidget(ww_label)
            column.addWidget(ww_slider)

            # 3方向を均等な幅で横並びにする
            layout.addWidget(view_panel, 1)

            # 番号表示用ラベルを保存
            if not hasattr(self, "position_labels"):
                self.position_labels = {}

            self.position_labels[name] = position_label

        # 3Dタブの作成（1回のみ）
        self.setup_3d_tab()

        # Fileメニュー
        file_menu = self.menuBar().addMenu("File")

        # DICOMフォルダを開くアクション
        open_action = QAction("Open DICOM Folder...", self)
        open_action.setShortcut("Ctrl+O")

        open_action.triggered.connect(
            self.open_dicom_folder
        )

        file_menu.addAction(open_action)

        # 初期状態
        self.volume = None
        self.spacing = None

        self.statusBar().showMessage(
            "File > Open DICOM Folder... to load images"
        )

        self.setStyleSheet("""
            QMainWindow {
                background-color: #111827;
            }

            QFrame#viewPanel {
                background-color: #1f2937;
                border: 1px solid #334155;
                border-radius: 10px;
            }

            QLabel {
                color: #e5e7eb;
            }

            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #3b82f6;
            }

            QMenuBar, QMenu, QStatusBar {
                background-color: #111827;
                color: #e5e7eb;
            }
        """)

        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #475569;
                background-color: #111827;
            }

            QTabBar::tab {
                background-color: #334155;
                color: #cbd5e1;
                padding: 12px 28px;
                margin-right: 6px;
                min-width: 130px;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #475569;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            QTabBar::tab:selected {
                background-color: #2563eb;
                color: #ffffff;
                border-color: #60a5fa;
            }

            QTabBar::tab:hover:!selected {
                background-color: #475569;
                color: #ffffff;
            }
        """)

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def apply_window_level(self, image, name):
        """方向ごとのWL・WWを使用して画像を変換"""

        wl = self.window_settings[name]["wl"]
        ww = max(1, self.window_settings[name]["ww"])

        # 表示するCT値の範囲
        lower = wl - ww / 2

        # グレースケールに変換
        processed = np.clip(
            (image - lower) * 255.0 / ww,
            0,
            255
        ).astype(np.uint8)

        return np.ascontiguousarray(processed)

    def numpy_to_pixmap(self, image):
        """NumPy配列をQPixmapに変換"""

        height, width = image.shape

        qimage = QImage(
            image.data,
            width,
            height,
            image.strides[0],
            QImage.Format.Format_Grayscale8
        ).copy()

        return QPixmap.fromImage(qimage)

    def update_all_views(self):
        """3方向の断面画像を作成"""

        # Axial: Z軸を固定
        axial = self.volume[self.z, :, :]

        # Coronal: Y軸を固定
        coronal = self.volume[:, self.y, :]

        # Sagittal: X軸を固定
        sagittal = self.volume[:, :, self.x]

        images = {
            "Axial": axial,
            "Coronal": coronal,
            "Sagittal": sagittal,
        }

        spacing_z, spacing_y, spacing_x = self.spacing

        # 画素の実際の間隔（縦・横）
        spacings = {
            "Axial": (spacing_y, spacing_x),
            "Coronal": (spacing_z, spacing_x),
            "Sagittal": (spacing_z, spacing_y),
        }

        for name, image in images.items():

            processed = self.apply_window_level(image, name)

            # NumPy画像をQPixmapに変換
            pixmap = self.numpy_to_pixmap(processed)

            # 交差線を描画
            self.draw_crosshair(pixmap, name)

            # 表示用画像を保存
            self.pixmaps[name] = pixmap

            vertical_spacing, horizontal_spacing = spacings[name]

            height, width = image.shape

            # 実際の長さに基づく縦横比
            self.aspect_ratios[name] = (
                width * horizontal_spacing
            ) / (
                height * vertical_spacing
            )

        self.refresh_display()

    def refresh_display(self):
        """表示領域に合わせて画像サイズを調整"""

        for name, pixmap in self.pixmaps.items():
            label = self.image_labels[name]

            available_width = label.width()
            available_height = label.height()

            if available_width <= 0 or available_height <= 0:
                continue

            ratio = self.aspect_ratios[name]

            target_width = available_width
            target_height = int(target_width / ratio)

            if target_height > available_height:
                target_height = available_height
                target_width = int(target_height * ratio)

            if target_width <= 0 or target_height <= 0:
                continue

            scaled = pixmap.scaled(
                target_width,
                target_height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, "pixmaps") and self.pixmaps:
            self.refresh_display()

    def open_dicom_folder(self):
        """フォルダを選択してDICOMシリーズを読み込む"""

        # フォルダ選択ダイアログ
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select DICOM Folder",
            str(Path.home())
        )

        # キャンセルされた場合
        if not folder:
            return

        try:
            # DICOMデータを読み込む
            volume, spacing = load_dicom_series(folder)

            # 読み込み成功後にデータを更新
            self.volume = volume
            self.spacing = spacing

            # 3方向の中央位置を設定
            z_size, y_size, x_size = self.volume.shape

            self.z = z_size // 2
            self.y = y_size // 2
            self.x = x_size // 2

            # スライダーの範囲と初期値
            positions = {
                "Axial": (self.z, z_size),
                "Coronal": (self.y, y_size),
                "Sagittal": (self.x, x_size),
            }

            for name, (position, size) in positions.items():
                slider = self.sliders[name]

                # 初期設定中はイベントを発生させない
                slider.blockSignals(True)

                slider.setRange(0, size - 1)
                slider.setValue(position)
                slider.setEnabled(True)

                slider.blockSignals(False)

            # スライス番号表示
            self.update_position_labels()

            # 3方向の画像を更新
            self.update_all_views()

            # ステータスバーに表示
            self.statusBar().showMessage(
                f"Loaded: {folder} | Shape: {self.volume.shape}"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "DICOM Load Error",
                f"Failed to load DICOM series:\n{error}"
            )

    def on_slice_position_changed(self, _value):
        """スライダー操作時に3方向の画像を更新"""

        if self.volume is None:
            return

        # 各スライダーの値を取得
        self.z = self.sliders["Axial"].value()
        self.y = self.sliders["Coronal"].value()
        self.x = self.sliders["Sagittal"].value()

        self.update_position_labels()

        # 3方向の画像を更新
        self.update_all_views()


    def update_position_labels(self):
        """スライス番号を更新"""

        if self.volume is None:
            return

        z_size, y_size, x_size = self.volume.shape

        positions = {
            "Axial": (self.z, z_size),
            "Coronal": (self.y, y_size),
            "Sagittal": (self.x, x_size),
        }

        for name, (position, total) in positions.items():
            self.position_labels[name].setText(
                f"Slice: {position + 1} / {total}"
            )

    def on_window_changed(self, name):
        """WL・WWスライダーの変更を反映"""

        controls = self.window_controls[name]

        wl = controls["wl_slider"].value()
        ww = controls["ww_slider"].value()

        # パラメータを更新
        self.window_settings[name]["wl"] = wl
        self.window_settings[name]["ww"] = ww

        # 数値表示を更新
        controls["wl_label"].setText(f"WL: {wl}")
        controls["ww_label"].setText(f"WW: {ww}")

        # DICOM読み込み済みなら再描画
        if self.volume is not None:
            self.update_all_views()

    def draw_crosshair(self, pixmap, name):
        """各断面に他の2方向のスライス位置を描画する"""

        # 軸ごとの色
        color_x = QColor(255, 70, 70)    # 赤
        color_y = QColor(80, 255, 80)    # 緑
        color_z = QColor(50, 220, 255)   # 水色

        # 各画像に描く線
        # (方向, 座標, 色)
        lines = {
            "Axial": [
                ("vertical", self.x, color_x),
                ("horizontal", self.y, color_y),
            ],
            "Coronal": [
                ("vertical", self.x, color_x),
                ("horizontal", self.z, color_z),
            ],
            "Sagittal": [
                ("vertical", self.y, color_y),
                ("horizontal", self.z, color_z),
            ],
        }

        painter = QPainter(pixmap)

        width = pixmap.width()
        height = pixmap.height()

        for direction, position, color in lines[name]:

            # 線の設定
            pen = QPen(color)
            pen.setWidth(2)

            painter.setPen(pen)

            if direction == "vertical":
                # 縦線
                painter.drawLine(
                    position, 0,
                    position, height - 1
                )

            elif direction == "horizontal":
                # 横線
                painter.drawLine(
                    0, position,
                    width - 1, position
                )

        painter.end()
    
    def open_lung_volume(self):
        """肺領域の3Dデータを読み込んで表示"""

        default_folder = (
            Path(__file__).resolve().parent / "data"
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Lung Volume",
            str(default_folder),
            "NumPy Volume (*.npy)",
        )

        if not file_path:
            return

        try:
            self.statusBar().showMessage(
                "Loading 3D Viewer volume..."
            )

            volume = np.load(
                file_path,
                allow_pickle=False
            )

            if volume.ndim != 3:
                raise ValueError(
                    "3次元のNumPy配列が必要です"
                )

            # 以前作成した肺領域の除去処理を再利用
            mask = clean_lung_mask(volume)

            if not np.any(mask):
                raise ValueError(
                    "表示可能な肺領域がありません"
                )

            # (Z, Y, X) → (X, Y, Z)
            mask_xyz = np.transpose(
                mask, (2, 1, 0)
            )

            # 今回のLIDC-IDRI-0265_CT用画素間隔
            spacing = (
                0.78125,
                0.78125,
                2.5,
            )

            grid = pv.ImageData(
                dimensions=mask_xyz.shape,
                spacing=spacing,
            )

            grid.point_data["lung"] = (
                mask_xyz.ravel(order="F")
            )

            # 現在の3D表示を削除
            self.plotter.clear()
            self.plotter.set_background("#101820")

            # 水色系のボリュームレンダリング
            self.plotter.add_volume(
                grid,
                scalars="lung",
                clim=(0, 1),
                cmap=["#000000", "#7dd3fc"],
                n_colors=2,
                opacity=[0.0, 1.0],
                shade=False,
                show_scalar_bar=False,
            )

            surface = grid.contour(
                isosurfaces=[0.5],
                scalars="lung"
            )

            self.plotter.add_mesh(
                surface,
                color="#7dd3fc",
                opacity=0.50,
                smooth_shading=True,
                show_scalar_bar=False,
            )

            self.plotter.add_axes()
            self.plotter.reset_camera()
            self.plotter.render()

            self.statusBar().showMessage(
                f"3D Viewer Loaded: {volume.shape}"
            )

        except Exception as error:
            self.statusBar().showMessage(
                "3D Viewer loading failed"
            )

            QMessageBox.critical(
                self,
                "3D Viewer Error",
                str(error),
            )

    def on_tab_changed(self, index):
        """タブ切り替え時に表示を更新"""

        if index == 0:
            # 2D画像を現在の表示サイズに合わせる
            QTimer.singleShot(0, self.refresh_display)

        elif index == 1:
            # 3D描画を更新
            QTimer.singleShot(0, self.plotter.render)
    
    def setup_3d_tab(self):
        """3Dタブを1回だけ構築する"""

        lung_panel = QFrame()
        lung_panel.setObjectName("viewPanel")

        lung_layout = QVBoxLayout(lung_panel)
        lung_layout.setContentsMargins(12, 12, 12, 12)
        lung_layout.setSpacing(10)

        # タイトル
        lung_title = QLabel("3D Viewer Volume")
        lung_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 3D表示領域
        self.plotter = QtInteractor(lung_panel)
        self.plotter.set_background("#101820")

        self.plotter.add_text(
            "Open Lung Volume to display 3D",
            position="upper_left",
            font_size=10,
            color="white",
        )

        # 読み込みボタン
        self.load_lung_button = QPushButton(
            "Open 3D Viewer Volume..."
        )

        self.load_lung_button.clicked.connect(
            self.open_lung_volume
        )

        lung_layout.addWidget(lung_title)
        lung_layout.addWidget(self.plotter, stretch=1)
        lung_layout.addWidget(self.load_lung_button)

        # 3Dタブに追加
        self.tab_3d_layout.addWidget(lung_panel)




if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MedicalImageViewer()
    window.show()

    sys.exit(app.exec())