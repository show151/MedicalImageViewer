from pathlib import Path

import numpy as np
import pydicom


def load_dicom_series(folder_path):
    """
    DICOM画像群を読み込み、3次元CTデータに変換する。

    Returns:
        volume: CT値の3次元配列 (Z, Y, X)
        spacing: 画素間隔 (Z, Y, X) [mm]
    """

    folder = Path(folder_path)

    files = sorted(folder.rglob("*.dcm"))

    if not files:
        raise FileNotFoundError(
            "DICOMファイルが見つかりません。"
        )

    slices = []

    # DICOMファイルを読み込む
    for file in files:
        ds = pydicom.dcmread(file)
        slices.append(ds)

    # 複数シリーズの混在をチェック
    series_ids = {
        str(ds.SeriesInstanceUID)
        for ds in slices
        if hasattr(ds, "SeriesInstanceUID")
    }

    if len(series_ids) > 1:
        raise ValueError(
            "複数のDICOMシリーズが混在しています。"
        )

    # スライス位置を取得
    def get_slice_position(ds):
        if (
            hasattr(ds, "ImagePositionPatient")
            and hasattr(ds, "ImageOrientationPatient")
        ):
            position = np.asarray(
                ds.ImagePositionPatient, dtype=float
            )
            orientation = np.asarray(
                ds.ImageOrientationPatient, dtype=float
            )

            normal = np.cross(
                orientation[:3],
                orientation[3:]
            )

            return float(np.dot(position, normal))

        return float(getattr(ds, "InstanceNumber", 0))

    # 正しい順番に並べる
    slices.sort(key=get_slice_position)

    # 画像サイズの整合性を確認
    shapes = {
        (int(ds.Rows), int(ds.Columns))
        for ds in slices
    }

    if len(shapes) != 1:
        raise ValueError(
            "画像サイズが一致していません。"
        )

    # CT値に変換
    images = []

    for ds in slices:
        image = ds.pixel_array.astype(np.float32)

        slope = float(
            getattr(ds, "RescaleSlope", 1)
        )
        intercept = float(
            getattr(ds, "RescaleIntercept", 0)
        )

        image = image * slope + intercept
        images.append(image)

    # 3次元配列に変換
    volume = np.stack(images, axis=0)

    # 画素間隔
    first = slices[0]

    pixel_spacing = getattr(
        first, "PixelSpacing", [1.0, 1.0]
    )

    spacing_y = float(pixel_spacing[0])
    spacing_x = float(pixel_spacing[1])

    if (
        len(slices) > 1
        and all(
            hasattr(ds, "ImagePositionPatient")
            and hasattr(ds, "ImageOrientationPatient")
            for ds in slices
        )
    ):
        positions = [
            get_slice_position(ds)
            for ds in slices
        ]
        spacing_z = float(
            np.median(np.abs(np.diff(positions)))
        )
    else:
        spacing_z = float(
            getattr(first, "SliceThickness", 1.0)
        )

    spacing = (
        spacing_z,
        spacing_y,
        spacing_x
    )

    return volume, spacing


if __name__ == "__main__":

    folder = "data/LIDC-IDRI-0265_CT"

    volume, spacing = load_dicom_series(folder)

    print("DICOM読み込み成功！")
    print("画像サイズ:", volume.shape)
    print("画素間隔:", spacing)
    print("最小CT値:", volume.min())
    print("最大CT値:", volume.max())