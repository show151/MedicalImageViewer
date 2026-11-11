from pathlib import Path
import re

import numpy as np
import tifffile


def natural_key(path):
    """ファイル名内の数字を数値として並べる"""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def load_lung_volume(folder_path):
    """TIFF画像系列を3次元NumPy配列に変換する"""

    folder = Path(folder_path)

    files = sorted(
        (
            f for f in folder.rglob("*")
            if f.is_file()
            and f.suffix.lower() in (".tif", ".tiff")
        ),
        key=natural_key
    )

    if not files:
        raise FileNotFoundError("TIFF画像がありません")

    images = []

    for file in files:
        image = tifffile.imread(file)

        if image.ndim != 2:
            raise ValueError(
                f"グレースケール画像ではありません: {file.name}"
            )

        if images and image.shape != images[0].shape:
            raise ValueError(
                f"画像サイズが一致しません: {file.name}"
            )

        images.append(image)

    # (Z, Y, X) の3次元配列に変換
    volume = np.stack(images, axis=0)

    return volume, files


if __name__ == "__main__":

    folder = "data/LIDC-IDRI-0265_CT2"

    volume, files = load_lung_volume(folder)

    print("3Dデータ生成成功！")
    print("画像サイズ:", volume.shape)
    print("データ型:", volume.dtype)
    print("最小値:", volume.min())
    print("最大値:", volume.max())

    # スライスの並び順を確認
    print("\n先頭3ファイル:")
    for f in files[:3]:
        print(f.name)

    print("\n末尾3ファイル:")
    for f in files[-3:]:
        print(f.name)

    # 非ゼロ画素の割合
    nonzero_ratio = np.count_nonzero(volume) / volume.size

    print("\n非ゼロ画素率:", f"{nonzero_ratio:.2%}")

    # 中央スライスの非ゼロ画素率
    middle = volume[len(volume) // 2]
    middle_ratio = np.count_nonzero(middle) / middle.size

    print("中央スライスの非ゼロ画素率:", f"{middle_ratio:.2%}")

    # 3次元データを保存
    output = Path("data/lung_volume.npy")
    np.save(output, volume)

    print("\n保存完了:", output)