# CyCIF selected TLS alignment — section 052 reference

The **25 slices and 196 selected TLS areas** of CRC01 have been unified to the XY coordinate system** of section **052**. The final 24 neighbor registrations, directly recallable transformation matrices, four-channel TLS data and interactive 3D/XY/XZ views are saved here. Contains 084; skips 045, 046, 047 (different channels).

![Aligned selected TLS: 3D, XY and XZ](figures/TLS_3D_aligned.png)

## 快速入口

| 内容 | 文件 |
| --- | --- |
| 主交互 3D／XY／XZ 视图 | [TLS_3D_XY_XZ_fixedZ.html](visualizations/TLS_3D_XY_XZ_fixedZ.html) |
| 独立 3D | [TLS_3D_filled_overlay.html](visualizations/TLS_3D_filled_overlay.html) |
| **24 个最终配对图及参数** | [最终配准图集](alignment/adjacent/README.md) |
| **相邻 transformation matrix CSV（24 行）** | [adjacent_transformation_matrices.csv](alignment/adjacent/adjacent_transformation_matrices.csv) |
| **各 section → 052 的 matrix CSV（25 行）** | [transformation_matrices_to_052.csv](alignment/to_section052/transformation_matrices_to_052.csv) |
| 每切片比例及换算依据 | [image_coordinate_scales.csv](alignment/to_section052/image_coordinate_scales.csv)、[image_to_global.json](alignment/to_section052/image_to_global.json) |
| TLS 中心与统计 | [TLS_aligned_regions.csv](alignment/to_section052/TLS_aligned_regions.csv) |
| 四通道共同画布 NPY | [raster](data/aligned_selected_tls/raster) |
| 精确坐标与原始标签 NPZ | [exact_points](data/aligned_selected_tls/exact_points) |

GitHub 文件页不直接运行交互 HTML。下载完整仓库和 LFS 数据后，在浏览器打开 HTML；Plotly 已内嵌，无需联网。点击 section 图例可同步显示／隐藏该切片的三个视图。

```bash
git clone https://github.com/SanJoe01/CycIF-TLS-segmentation.git
cd CycIF-TLS-segmentation
git lfs install
git lfs pull
```

## 简要方法

1. 按 `check.ipynb` 的结构将 cell CSV 转为 AnnData。配准使用全片 **Xt/Yt**，而非图块局部 X/Y；400 单位分箱，至少 5 个细胞。marker profile 为非负强度 `log1p` 后的均值。
2. 以 PASTE 计算相邻配对，拟合保持方向的刚性旋转和平移。最终保留已审核的 24 对：014→007、025→020 使用细胞数加权修正；044→039、049→044 使用部分空间 OT 刚性修正；其余保持已审核版本。
3. 各 section 的缩小图像分别转换到 Xt/Yt，再组合相邻变换，统一到 052，最后转换回 052 缩小图像坐标。各切片不共用固定的 6.5 或 5.876 倍比例。
4. selected TLS 的四通道应用同一个几何变换，保存逐像素精确坐标和最近邻重采样的共同画布 NPY。3D 展示通道 0 的 selected TLS。

这是对最终配准的应用与归档，没有重新拟合其余已核验配对，没有新增跨切片 TLS 身份匹配或局部非刚性变形。

## 坐标与矩阵变量

统一使用 **`[x,y,1]^T` 列向量**，x 向右、y 向下。CSV 矩阵字段下标是**零起始的行、列**，例如 `H_02` 为第一行第三列。矩阵保留浮点精度；section 按字符串读取以保留前导零。

### 相邻变换：source → target

```python
xy_target = (xy_source - source_center_xy) @ R.T + target_center_xy
# 等价形式
xy_target = xy_source @ H[:2, :2].T + H[:2, 2]
```

输入、输出均为**原始全片 Xt/Yt 单位**，不能直接作用于 resized-image TLS 坐标。

| 相邻 CSV 变量 | 含义 |
| --- | --- |
| `source_section`, `target_section`, `pair` | 方向，例如 `049_to_044` |
| `section_number_gap` | 源编号减目标编号 |
| `rotation_angle_deg` | `atan2(R[1,0],R[0,0])`；y 向下时正角视觉上为顺时针 |
| `source_center_x/y`, `target_center_x/y` | 拟合源／目标中心，Xt/Yt 单位 |
| `affine_offset_x/y` | `target_center - R @ source_center`，即 `H[:2,2]`，不是两中心之差 |
| `R_00` … `R_11` | 2×2 正旋转矩阵 |
| `H_00` … `H_22` | 3×3 source → target 齐次变换 |
| `Hinv_00` … `Hinv_22` | target → source 逆变换 |
| `method`, `qc_status` | 保存的拟合方法及全片 QC 状态 |
| `raw_transport_mass` | 拟合 transport 质量；044→039 为 0.85，049→044 为 0.90，**不是真实组织重叠率** |
| `after_nn_median`, `after_nn_p95` | 对齐后双向最近邻距离中位数／95 分位，Xt/Yt 单位 |
| `after_fraction_within_400` | 双向最近邻距离 ≤400 的比例 |
| `transform_json`, `qc_image` | 相对于相邻变换目录的参数与最终配对图路径 |

每对 `transform.json` 保留完整来源参数。图集原样复制正式 `pairs/*/qc.png`；[final_pair_images.csv](alignment/adjacent/final_pair_images.csv) 记录图像 SHA-256，未混入历史候选图。原配准图和来源 JSON 中的 `px` 字样沿用旧输出，数值按原 CSV Xt/Yt 单位理解。

### 每切片缩放与 002 方向校正

从 CSV 图块布局恢复全幅范围，再使用每张 TIFF 的 H×W：

```text
Xt - X = (COL - 1) * pitch_x
Yt - Y = (ROW - 1) * pitch_y
Lx = max(COL) * pitch_x       Ly = max(ROW) * pitch_y
sx = Lx / W                  sy = Ly / H
Xt = x * sx                  Yt = y * sy
```

`X/Y` 是图块局部坐标；`COL/ROW` 从 1 开始；`frame` 为图块编号；`pitch_x/y` 是相邻图块坐标跨度。`Lx/Ly` 使用图块覆盖范围，而非最外侧细胞坐标。049 的 `Ly=18322.2, sy=6.1074`；052 的 `sx≈6.330603, sy=6.3336`。图块偏移等式和 frame 布局均已检查。

002 在 TLS 分割前曾顺时针旋转 90°，已撤销：原 TIFF `(x,y)=(selected_y,2826-selected_x)`。其余切片保持 TIFF 方向。selected NPY 是完整画布，**不重复添加**筛选 ROI 原点 `(500,1200)`。

比例根据提供的 TIFF 尺寸和 CSV 图块范围估算，不是直接读取原始拼接 TIFF 的尺寸元数据。Xt/Yt 沿用数据单位，**没有再乘 0.65**；最终 XY 单位为 052 resized-image pixel，未声称是微米。

### 所有 section → 052

```text
A_s : selected 图像 → 原 Xt/Yt，含 002 方向校正
G_s : 原 Xt/Yt → 052 的 Xt/Yt，组合已保存的相邻变换
H_s = inverse(A_052) @ G_s @ A_s
C_s = Translate(-662, -1538) @ H_s
```

| 052 CSV 变量 | 含义 |
| --- | --- |
| `section`, `reference_section` | 当前切片、固定基准 `052` |
| `A_ij`, `G_ij`, `H_ij`, `C_ij` | 上述 3×3 矩阵；**原 selected NPY 的点转到 052 时用 H** |
| `Hinv_ij` | 052 完整 resized-image → 原 selected 图像 |
| `composed_global_rotation_angle_deg` | G 的旋转角；H 还含比例与方向校正，不能只用此角替代 H |
| `source_center_x/y`, `aligned_center_x/y` | selected 像素原始／对齐中心，各自图像坐标单位 |
| `source_height/width` | 原 selected NPY 画布尺寸 |
| `canvas_origin_x/y` | 共同画布原点在 052 完整图像的位置 `(662,1538)` |
| `canvas_height/width` | 共同画布 `865×1219` |
| `exact_point_count` | 精确保留的源 selected 像素个数 |
| `z` | 沿用 selected TLS 3D notebook 的 `(section-2)*5` |

052 的 H 为单位矩阵。**XY 基准为 052，Z 零点仍为 002**；Z 保留 section 编号间隔，不把所有层压成等间距，也不插值生成缺失切片。3D 纵横比例属于显示设置。

## 四通道结果及使用

NPY 为 `(865,1219,4)`、`int16`；每个 NPY 有对应 metadata JSON。

| 通道（零起始） | 含义 |
| --- | --- |
| 0 | selected TLS 二值 mask |
| 1 | section 内的原有 TLS region ID |
| 2 | 最强 Otsu 类别，值为 3，其余为 0 |
| 3 | 原始 signed true B-core instance ID，限制在 selected TLS 内 |

ID 不重编号；不同 section 的相同数字不表示同一个 TLS。B-core 正负号沿用原始定义，不代表新的选择或配准置信度。

```python
import numpy as np
from scripts.use_alignment import to_reference, restore_source

# 原 selected 图像坐标 → 052 完整 resized-image 坐标
xy_052 = to_reference('049', np.array([[1200., 1800.]]))

# 精确数据，不经过栅格插值
d = np.load('data/aligned_selected_tls/exact_points/CRC01_049_selected_TLS_aligned.npz')
xy_052 = d['aligned_xy']       # N×2, float64
values = d['channel_values']   # N×4, int16；每行与 source_xy / aligned_xy 对应
original_four_channels = restore_source('049')

# 共同画布像素 → 052 完整图像坐标
a = np.load('data/aligned_selected_tls/raster/CRC01_049_selected_TLScontour_aligned.npy')
yy, xx = np.nonzero(a[..., 0])
xy_052_raster = np.column_stack([xx + 662, yy + 1538])
```

NPZ 还含 `source_xy`、`source_shape`、`z`、`channel_names` 及坐标矩阵，可恢复当前四通道 source canvas。`TLS_aligned_regions.csv` 保存 section、region_id、原始像素数、原始／对齐中心、z、Otsu／B-core 像素数；统计来自原始选择。

历史 `data/selected_tlscontour_npy/` 是之前提交的三通道版本，通道 2 使用旧的 Otsu-derived 解释；本次最终四通道结果以 **`data/aligned_selected_tls/`** 为准。旧 raw 数据和分析 notebooks 保留供追溯；[原 README](docs/README_before_alignment.md) 也保留。

## 验证与适用范围

- 25 张切片、196 个 TLS、**1,753,172** 个源 selected 像素，四通道精确对应。
- 共同画布无 TLS 裁切，全部 TLS／signed B-core ID 保留；052 四通道与原图对应裁剪完全一致。
- 逆变换最大误差约 `9.09e-13` 像素；矩阵组合最大误差约 `8.24e-13`。这是坐标传递数值精度，**不是组织配准的生物学误差**。
- 浏览器渲染包含 25 个 section、75 条图层，JavaScript 错误 0。
- NPY 最近邻重采样会改变部分边缘像素及面积；交互图用 3×3 占用块近似填充。定量处理优先使用 NPZ。
- 044→039、049→044 部分匹配范围及连续配准累积误差仍需考虑；全片 QC 通过不代表所有 TLS 局部地标都经过独立验证。

详细记录：[坐标验证](alignment/to_section052/validation.json)、[渲染验证](alignment/to_section052/render_validation.json)、[文件校验清单](alignment/artifact_manifest.json)。完整下载 LFS 后运行：

```bash
python -m pip install numpy
python scripts/use_alignment.py --validate
python scripts/use_alignment.py --section 049 --points xy.npy --output xy_052.npy
```

辅助脚本读取／应用最终矩阵并检查结果，不重新拟合 PASTE。NPY、NPZ、交互 HTML 和 figures 中的 PNG 使用 Git LFS；CSV、参数 JSON 和 24 张配对图可直接浏览。
