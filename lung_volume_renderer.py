
from pathlib import Path

import numpy as np
import pyvista as pv
from scipy import ndimage as ndi


def clean_lung_mask(volume):
    """肺以外の小さな領域を除去する"""

    mask = volume > 0

    print("除去前の画素数:", np.count_nonzero(mask))

    # 小さなノイズや細い接続部分を除去
    structure = ndi.generate_binary_structure(3, 1)

    mask = ndi.binary_opening(
        mask,
        structure=structure,
        iterations=1,
    )

    # 3D連結成分解析
    labels, count = ndi.label(
        mask,
        structure=structure,
    )

    print("連結成分数:", count)

    sizes = np.bincount(labels.ravel())
    sizes[0] = 0  # 背景を除外

    order = np.argsort(sizes)[::-1]

    print("大きい領域の画素数:")
    for label_id in order[:5]:
        if sizes[label_id] > 0:
            print(f"  ID {label_id}: {sizes[label_id]:,}")

    if count == 0:
        raise ValueError("領域が見つかりません")

    # 最大領域の15%以上の大きさを持つ領域から
    # 最大2つまでを肺の候補として残す
    min_size = max(10000, int(sizes[order[0]] * 0.15))

    keep_ids = [
        label_id
        for label_id in order[:2]
        if sizes[label_id] >= min_size
    ]

    cleaned = np.isin(labels, keep_ids)

    print("残した領域ID:", keep_ids)
    print("除去後の画素数:", np.count_nonzero(cleaned))

    return cleaned.astype(np.uint8)


def main():
    path = (
        Path(__file__).resolve().parent
        / "data"
        / "lung_volume.npy"
    )

    volume = np.load(path, allow_pickle=False)

    print("読み込み成功:", volume.shape)

    # 不要領域の除去
    mask = clean_lung_mask(volume)

    # 高解像度表示
    step = 1
    mask = mask[::step, ::step, ::step]

    # 元DICOMの画素間隔
    spacing_z = 2.5
    spacing_y = 0.78125
    spacing_x = 0.78125

    # PyVista用の軸順に変換
    mask_xyz = np.transpose(mask, (2, 1, 0))

    grid = pv.ImageData(
        dimensions=mask_xyz.shape,
        spacing=(
            spacing_x * step,
            spacing_y * step,
            spacing_z * step,
        ),
    )

    grid.point_data["lung"] = mask_xyz.ravel(order="F")

    plotter = pv.Plotter(window_size=(1100, 850))
    plotter.set_background("#101820")

    # 水色の肺を表示
    plotter.add_volume(
        grid,
        scalars="lung",
        clim=(0, 1),
        cmap="cool_r",
        opacity="foreground",
        shade=True,
        ambient=0.4,
        diffuse=0.7,
        show_scalar_bar=False,
    )

    plotter.add_axes()

    plotter.add_text(
        "3D Lung Volume",
        position="upper_left",
        font_size=12,
        color="white",
    )

    plotter.reset_camera()
    plotter.show()


if __name__ == "__main__":
    main()
