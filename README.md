# Medical Image Viewer

**知能情報実験実習2 — 医用画像処理実験 最終課題**

## 1. 概要

本アプリケーションは、Pythonで開発したDICOM形式のCT画像を表示・操作する医用画像Viewerです。

PySide6を使用したGUI上で、CT画像をAxial・Coronal・Sagittalの3方向から観察できます。

また、画像処理によって抽出した肺領域をPyVistaでボリュームレンダリングし、3次元形状を観察できます。

アプリケーションは「2D Viewer」と「3D Viewer」の2つのタブで構成されています。

### 1.1 主な機能

**2D Viewer**

- DICOMフォルダの選択と読み込み
- Axial（横断面）の表示
- Coronal（冠状断面）の表示
- Sagittal（矢状断面）の表示
- 各方向のスライス位置の変更
- WL（Window Level）の変更
- WW（Window Width）の変更
- 他の2方向のスライス位置を示す交差線
- スライダー操作と交差線の連動

**3D Viewer**

- 肺領域を抽出したTIFF画像系列の3次元データ化
- モルフォロジー処理による不要領域の除去
- 3次元連結成分解析
- 肺領域のボリュームレンダリング
- マウスによる回転・拡大・縮小

## 2. 動作環境

| 項目 | 内容 |
|---|---|
| OS | Windows |
| Python | 3.11.9 |
| GUI | PySide6 |
| DICOM処理 | pydicom |
| 数値・画像処理 | NumPy、SciPy |
| TIFF読み込み | tifffile |
| 3D描画 | PyVista、VTK |
| GUIへの3D描画統合 | PyVistaQt |

各ライブラリのバージョンは `requirements.txt` に記載しています。

インストールにはインターネット接続が必要です。

## 3. ファイル構成

```text
MedicalImageViewer/
├── main.py
├── dicom_loader.py
├── lung_volume_loader.py
├── lung_volume_renderer.py
├── requirements.txt
├── .python-version
├── .gitignore
├── README.md
└── data/
    ├── LIDC-IDRI-0265_CT/
    │   └── DICOM画像（133枚）
    └── LIDC-IDRI-0265_CT2/
        └── TIFF画像（133枚）
```

`lung_volume.npy` は提出ファイルに含めていません。後述のコマンドでTIFF画像から生成します。

### 3.1 Pythonファイルの説明

| ファイル | 役割 |
|---|---|
| `main.py` | GUIおよび2D・3D統合アプリのメインプログラム |
| `dicom_loader.py` | DICOM画像の読み込み・並べ替え・3次元配列化 |
| `lung_volume_loader.py` | TIFF画像系列から3次元NumPy配列を生成 |
| `lung_volume_renderer.py` | 肺領域の抽出結果の整理・3Dレンダリング |
| `requirements.txt` | 必要なライブラリとバージョン |
| `.python-version` | Pythonバージョンの指定 |
| `.gitignore` | Gitの管理対象外ファイルの指定 |

### 3.2 データファイルの説明

**LIDC-IDRI-0265_CT**

元のCT画像です。133枚のDICOMファイルが格納されています。2D Viewerで使用します。

**LIDC-IDRI-0265_CT2**

医用画像処理実験において肺領域を抽出したTIFF画像133枚です。3D表示用データの生成に使用します。

**lung_volume.npy（実行時に生成）**

TIFF画像133枚をNumPyの3次元配列として保存したファイルです。

3D Viewerタブで読み込むデータであり、`lung_volume_loader.py` によって生成できます。

## 4. インストール方法

### 4.1 Pythonの準備

Python 3.11.9をインストールしてください。

公式ダウンロードページ：

https://www.python.org/downloads/release/python-3119/

PowerShellで以下を実行し、Pythonのバージョンを確認します。

```powershell
py -3.11 --version
```

期待される出力：

```text
Python 3.11.9
```

### 4.2 アプリケーションのダウンロード

1. 提出されたGitHubリポジトリを開きます。
2. 「Code」→「Download ZIP」を選択します。
3. ZIPファイルをダウンロードします。
4. 任意の場所に展開します。
5. `main.py` があるフォルダでPowerShellを開きます。

以降のコマンドは、すべてプロジェクトのルートフォルダで実行してください。

### 4.3 仮想環境の作成

```powershell
py -3.11 -m venv .venv
```

仮想環境を有効化します。

```powershell
.\.venv\Scripts\Activate.ps1
```

PowerShellの実行ポリシーにより有効化できない場合は、次のコマンドを実行してから再試行してください。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

成功すると、PowerShellの先頭に `(.venv)` が表示されます。

### 4.4 ライブラリのインストール

以下のコマンドを実行してください。

```powershell
python -m pip install -r requirements.txt
```

インストール後、依存関係を確認します。

```powershell
python -m pip check
```

`No broken requirements found.` と表示されれば、ライブラリ間の依存関係に問題が検出されなかったことを意味します。

## 5. アプリケーションの起動

次のコマンドを実行します。

```powershell
python main.py
```

「Medical Image Viewer」のウィンドウが開きます。

画面上部に以下の2つのタブが表示されます。

- 2D Viewer
- 3D Viewer

## 6. 2D Viewerの使用方法

### 6.1 DICOM画像の読み込み

1. 「2D Viewer」タブを開きます。
2. メニューバーの「File」を選択します。
3. 「Open DICOM Folder...」をクリックします。
4. `data/LIDC-IDRI-0265_CT` を選択します。
5. DICOM画像が読み込まれ、3方向の断面画像が表示されます。

ショートカットキー `Ctrl + O` でもフォルダを選択できます。

### 6.2 スライス位置の変更

各画像の下部に配置されたスライダーで、表示する断面位置を変更できます。

| 表示方向 | 操作対象 |
|---|---|
| Axial | Z方向のスライス |
| Coronal | Y方向のスライス |
| Sagittal | X方向のスライス |

スライダーを移動すると、対応するCT画像が更新されます。

### 6.3 WL・WWの調整

各画像には、WLとWWを調整するスライダーが配置されています。

**WL（Window Level）**

表示するCT値の中心を指定します。

**WW（Window Width）**

表示するCT値の範囲を指定します。

初期値は以下のとおりです。

- WL：-600
- WW：1500

WLとWWは3方向それぞれ独立して変更できます。

### 6.4 交差線の表示

各画像上には、他の2方向のスライス位置を示す交差線が描画されています。

| 表示画像 | 縦線 | 横線 |
|---|---|---|
| Axial | X方向（赤） | Y方向（緑） |
| Coronal | X方向（赤） | Z方向（水色） |
| Sagittal | Y方向（緑） | Z方向（水色） |

スライス位置スライダーを変更すると、他の画像上の交差線も連動して更新されます。

## 7. 3D Viewerの使用方法

### 7.1 3D表示用データの生成

3D Viewerでは `lung_volume.npy` を使用します。

このファイルはGitHubに含まれていないため、初回利用時に以下のコマンドを実行してください。

```powershell
python lung_volume_loader.py
```

プログラムは、`data/LIDC-IDRI-0265_CT2/` に格納されているTIFF画像を読み込みます。

画像をファイル名の番号順に並べ、3次元のNumPy配列に変換し、以下のファイルを生成します。

```text
data/lung_volume.npy
```

生成後は、再度生成する必要はありません。

**注意：現在のアプリケーションでは、3D表示用NPYファイルの自動生成は実装していません。初回の3D表示前に上記コマンドを実行してください。**

### 7.2 肺領域の3D表示

データ生成後、アプリケーションを起動します。

```powershell
python main.py
```

次の手順で操作してください。

1. 「3D Viewer」タブを選択します。
2. 「Open 3D Viewer Volume...」をクリックします。
3. `data/lung_volume.npy` を選択します。
4. 肺領域の3Dモデルが表示されます。

3D表示にはPyVistaを使用しています。

肺領域以外の小さな不要領域を減らすため、モルフォロジー処理と3次元連結成分解析を行っています。

### 7.3 3Dモデルの操作

| マウス操作 | 動作 |
|---|---|
| 左ドラッグ | 3Dモデルの回転 |
| ホイール | 拡大・縮小 |
| 中ドラッグ | 表示位置の移動 |

3Dモデルは水色系で描画され、自由な視点から観察できます。

### 7.4 単独での3D表示

統合アプリを起動せず、3D表示だけを確認する場合は、NPYファイルを生成した後に以下を実行してください。

```powershell
python lung_volume_renderer.py
```

独立した3D表示ウィンドウが開きます。

## 8. 各プログラムの実行方法

| 目的 | コマンド |
|---|---|
| 統合アプリを起動 | `python main.py` |
| DICOM読み込みの確認 | `python dicom_loader.py` |
| TIFFから3Dデータを生成 | `python lung_volume_loader.py` |
| 3D表示のみを実行 | `python lung_volume_renderer.py` |

通常の操作では `main.py` を実行します。

3D表示用データを初めて使用する場合のみ、事前に `lung_volume_loader.py` の実行が必要です。

## 9. 使用データの仕様

本アプリケーションで使用したCT画像の情報は以下のとおりです。

| 項目 | 値 |
|---|---|
| データセット | LIDC-IDRI-0265 |
| DICOM枚数 | 133枚 |
| TIFF枚数 | 133枚 |
| 画像サイズ | 512 × 512 |
| スライス間隔 | 2.5 mm |
| Y方向画素間隔 | 0.78125 mm |
| X方向画素間隔 | 0.78125 mm |
| 3D配列の形状 | (133, 512, 512) |
| 3D配列のデータ型 | uint8 |

Coronal・Sagittalの表示および3Dレンダリングでは、画素間隔の違いを考慮して表示しています。

## 10. 実装方法

### 10.1 DICOM読み込み

pydicomを使用してDICOMデータを読み込みます。

スライスの位置情報を参照して画像を並べ、NumPyの3次元配列を作成します。

画像の画素値は、DICOMのRescaleSlopeとRescaleInterceptを使って変換します。

### 10.2 3方向の画像表示

3次元配列を `(Z, Y, X)` として扱い、各方向の断面を取得します。

```python
axial = volume[z, :, :]
coronal = volume[:, y, :]
sagittal = volume[:, :, x]
```

WL・WWを適用してグレースケール画像へ変換し、PySide6上に表示します。

### 10.3 スライス位置と交差線

3つの座標 `x`、`y`、`z` を共有することで、各断面位置と交差線を管理します。

スライダーの値が変更されると、各画像と交差線を再描画します。

### 10.4 肺領域の3D表示

肺領域を抽出したTIFF画像から3次元配列を生成します。

その後、以下の処理を行います。

1. 0より大きい画素を肺領域の候補とする
2. 3次元のモルフォロジー処理を実施
3. 3次元連結成分解析によって小さな不要領域を削減
4. PyVistaのImageDataに変換
5. ボリュームレンダリングで3D表示

## 11. 注意事項・制限事項

- 本アプリケーションは教育・実習目的で開発したものであり、医療診断には使用できません。
- DICOM読み込みは、主に同一シリーズのCT画像を対象としています。
- 2D断面の生成は通常の軸に沿ったCT画像を想定しています。
- 斜め方向で撮影されたDICOMデータに対する汎用的な再構成処理は実装していません。
- 3D表示時の画素間隔は今回のCTシリーズに合わせて設定しています。
- 3D表示用TIFF画像と元DICOMのスライス方向・順序の対応は、データ作成時の管理に依存します。
- 肺領域の不要部分を完全に除去できるとは限りません。
- 3DレンダリングはPCのグラフィック環境によって表示速度が変化します。

## 12. 最短実行手順

PowerShellでプロジェクトのルートフォルダを開き、以下を順番に実行してください。

```powershell
# 仮想環境の作成
py -3.11 -m venv .venv

# 仮想環境の有効化
.\.venv\Scripts\Activate.ps1

# 必要ライブラリのインストール
python -m pip install -r requirements.txt

# 3D表示用データの生成
python lung_volume_loader.py

# アプリの起動
python main.py
```

起動後、2D Viewerでは `data/LIDC-IDRI-0265_CT` を選択してください。

3D Viewerでは、生成された `data/lung_volume.npy` を選択してください。

以上の操作により、2D断面表示と3D肺領域表示の両方を確認できます。
