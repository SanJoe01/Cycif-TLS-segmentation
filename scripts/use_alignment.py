"""Read/export/apply the published transforms; validate the saved package.

Usage: python scripts/use_alignment.py --validate
       python scripts/use_alignment.py --section 049 --points xy.npy --output xy_052.npy
Only NumPy is required. No alignment is re-fitted.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def matrix(row,prefix='H'):
    """CSV matrix suffixes use zero-based row/column indices."""
    return np.array([[float(row[f'{prefix}_{i}{j}']) for j in range(3)] for i in range(3)])


def read_rows(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def to_reference(section,points):
    rows=read_rows(ROOT/'alignment/to_section052/transformation_matrices_to_052.csv')
    row=next(r for r in rows if r['section']==str(section).zfill(3))
    h=matrix(row)
    xy=np.asarray(points,dtype=float)
    if xy.ndim!=2 or xy.shape[1]!=2 or not np.isfinite(xy).all():
        raise ValueError('points must be a finite N x 2 array in original selected-NPY (x,y) coordinates')
    return xy@h[:2,:2].T+h[:2,2]


def restore_source(section):
    """Recover the current four-channel source canvas from the lossless point package."""
    p=ROOT/'data/aligned_selected_tls/exact_points'/f'CRC01_{str(section).zfill(3)}_selected_TLS_aligned.npz'
    with np.load(p) as data:
        arr=np.zeros(tuple(data['source_shape']),dtype=np.int16)
        x,y=data['source_xy'].T
        arr[y,x]=data['channel_values']
        return arr


def validate():
    adj=ROOT/'alignment/adjacent'
    rows=read_rows(adj/'adjacent_transformation_matrices.csv')
    refs=read_rows(ROOT/'alignment/to_section052/transformation_matrices_to_052.csv')
    reference={r['section']:r for r in refs}
    assert len(rows)==24 and len(refs)==25
    assert not ({'045','046','047'}&set(reference))
    for r in rows:
        src,dst=r['source_section'],r['target_section']
        original=json.loads((adj/r['transform_json']).read_text())
        h=matrix(r)
        np.testing.assert_allclose(h,original['homogeneous_matrix_source_to_target'],rtol=0,atol=1e-12)
        np.testing.assert_allclose(h@matrix(r,'Hinv'),np.eye(3),rtol=0,atol=1e-8)
        a_s=matrix(reference[src],'A');a_t=matrix(reference[dst],'A')
        np.testing.assert_allclose(matrix(reference[dst])@np.linalg.inv(a_t)@h@a_s,
            matrix(reference[src]),rtol=0,atol=1e-8)
        assert (adj/r['qc_image']).is_file()
    total=0
    for r in refs:
        s=r['section'];h=matrix(r)
        with np.load(ROOT/'data/aligned_selected_tls/exact_points'/f'CRC01_{s}_selected_TLS_aligned.npz') as data:
            xy=data['source_xy'];out=to_reference(s,xy)
            np.testing.assert_allclose(out,data['aligned_xy'],rtol=0,atol=1e-8)
            assert len(xy)==int(r['exact_point_count'])
            assert data['channel_values'].shape==(len(xy),4)
            total+=len(xy)
        np.testing.assert_allclose(matrix(r,'C')[:2,2],h[:2,2]-[float(r['canvas_origin_x']),float(r['canvas_origin_y'])],rtol=0,atol=1e-8)
    np.testing.assert_allclose(matrix(reference['052']),np.eye(3),rtol=0,atol=1e-10)
    for item in json.loads((ROOT/'alignment/artifact_manifest.json').read_text()):
        with (ROOT/item['path']).open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        assert digest==item['sha256'],item['path']
    print(f'PASS: 24 adjacent pairs, 25 sections, {total:,} exact selected pixels; matrices, points, images and file hashes consistent.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--validate',action='store_true')
    parser.add_argument('--section')
    parser.add_argument('--points',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.validate:validate()
    elif args.section and args.points and args.output:
        np.save(args.output,to_reference(args.section,np.load(args.points)))
    else:parser.error('use --validate or --section NNN --points xy.npy --output xy_052.npy')
