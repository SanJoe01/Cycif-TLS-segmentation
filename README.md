# CyCIF TLS Segmentation Results

This repository contains CRC01 CyCIF TLS contour outputs and review figures.

## Folder Layout

- `data/raw_tlscontour_npy/`
  - Original or intermediate `CRC01_*_TLScontour.npy` outputs from `D:\cycif_segmentation\results`.
  - Also includes relabeled helper arrays such as `CRC01_050_TLScontour_relabeled_regions.npy` and `CRC01_091_TLScontour_relabeled_regions.npy`.
- `data/selected_tlscontour_npy/`
  - Final manually selected TLS contour arrays, one file per section.
  - Filenames use `CRC01_{section}_selected_TLScontour.npy`.
- `figures/`
  - `CRC01_selected_TLS_contours_CD20_5x5.png`: final selected TLS contours over CD20 background.
  - `tls-3x3-comparison-side-by-side.png`: 3x3 comparison figure.
- `visualizations/`
  - `TLS_3D_XY_XZ_fixedZ.html`: interactive 3D / XY / XZ TLS visualization.
- `metadata/`
  - `CRC01_selected_TLS_contours_manifest.csv`: selected region manifest and source labels.

## NPY File Contents

### Raw TLS contour files

Files named `CRC01_{section}_TLScontour.npy` are 3D NumPy arrays:

```python
arr = np.load("data/raw_tlscontour_npy/CRC01_091_TLScontour.npy")
print(arr.shape)  # usually (height, width, 3)
```

Channel convention:

- `arr[..., 0]`: threshold / mask intermediate
- `arr[..., 1]`: B-cell core or intermediate contour channel
- `arr[..., 2]`: final TLS contour mask

The final TLS mask is usually read as:

```python
tls_mask = arr[..., 2] > 0
```

### Selected TLS contour files

Files named `CRC01_{section}_selected_TLScontour.npy` are final curated outputs:

```python
selected = np.load("data/selected_tlscontour_npy/CRC01_091_selected_TLScontour.npy")
print(selected.shape)  # (height, width, 2)

selected_mask = selected[..., 0] > 0
selected_labels = selected[..., 1]
```

Channel convention:

- `selected[..., 0]`: binary mask for manually retained TLS regions
- `selected[..., 1]`: integer TLS region label map

Labels are main TLS region IDs. When a region was manually subdivided during review, only the retained pixels were kept, but the final saved label remains the main region ID.

Example:

```python
import numpy as np

path = "data/selected_tlscontour_npy/CRC01_050_selected_TLScontour.npy"
arr = np.load(path)

mask = arr[..., 0] > 0
labels = arr[..., 1]
region_ids = sorted(int(x) for x in np.unique(labels) if x != 0)

print(region_ids)
print(mask.sum())
```

## ROI And Naming

The working ROI used during curation was:

```python
x0, x1 = 500, 2200
y0, y1 = 1200, 2400
```

Section IDs are encoded in filenames, for example:

- `CRC01_002_selected_TLScontour.npy`
- `CRC01_091_TLScontour.npy`

Section `002` was rotated clockwise by 90 degrees during the image-processing workflow before ROI operations.

## Notes

Large `.npy` files are tracked with Git LFS.
