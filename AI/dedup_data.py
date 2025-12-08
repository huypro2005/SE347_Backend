"""Deduplicate data_1.csv

Usage examples:
  python dedup_data.py                     # runs default exact dedupe, writes data_1.dedup.csv
  python dedup_data.py --method fuzzy --coord-scale 1000 --price-tol 0.1 --area-tol 0.15

This script supports two modes:
 - exact: drop exact duplicate rows
 - fuzzy: group by rounded coordinates (coord_scale) and within each group drop rows
          whose price and area are within relative tolerances of an earlier row.

Output: by default writes CSV next to input with suffix `.dedup.csv` and prints a short report.
"""
import argparse
import os
import sys
from typing import Optional

try:
    import pandas as pd
except Exception as e:
    print('This script requires pandas. Install with: python -m pip install pandas')
    raise


def parse_args():
    p = argparse.ArgumentParser(description='Deduplicate real-estate CSV')
    p.add_argument('--input', '-i', default='data_1.csv', help='Input CSV file path')
    p.add_argument('--output', '-o', help='Output CSV path (default: input.dedup.csv)')
    p.add_argument('--method', '-m', choices=['exact', 'fuzzy'], default='exact', help='Deduplication method')
    p.add_argument('--coord-scale', type=float, default=1000.0,
                   help='Scale used to round coordinates for fuzzy grouping (default 1000). Larger groups = more aggressive dedupe')
    p.add_argument('--price-tol', type=float, default=0.05, help='Relative tolerance for price in fuzzy dedupe (default 0.05 = 5%%)')
    p.add_argument('--area-tol', type=float, default=0.10, help='Relative tolerance for area in fuzzy dedupe (default 0.10 = 10%%)')
    p.add_argument('--keep', choices=['first', 'last', 'largest_area'], default='first', help='Which record to keep when duplicates found')
    return p.parse_args()


def read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    return df


def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)


def dedup_exact(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    out = df.drop_duplicates()
    after = len(out)
    print(f'Exact dedupe: {before - after} duplicates removed ({before} -> {after})')
    return out


def dedup_fuzzy(df: pd.DataFrame, coord_scale: float = 1000.0, price_tol: float = 0.05, area_tol: float = 0.10, keep: str = 'first') -> pd.DataFrame:
    """Fuzzy dedupe:
    - create groups by rounded coordinates: key = (round(x / coord_scale), round(y / coord_scale))
    - within each group, mark rows as duplicates when price and area are within tolerances of a kept row
    """
    before = len(df)

    # ensure coordinate columns exist
    x_col = 'tọa độ x' if 'tọa độ x' in df.columns else 'lat'
    y_col = 'tọa độ y' if 'tọa độ y' in df.columns else 'lon'

    if x_col not in df.columns or y_col not in df.columns:
        raise KeyError('Coordinate columns not found (expected "tọa độ x","tọa độ y")')

    # fillna to avoid errors
    df = df.copy()
    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    df['giá'] = pd.to_numeric(df['giá'], errors='coerce') if 'giá' in df.columns else pd.Series([None]*len(df))
    df['diện tích'] = pd.to_numeric(df['diện tích'], errors='coerce') if 'diện tích' in df.columns else pd.Series([None]*len(df))

    # group key
    df['_gx'] = (df[x_col] / coord_scale).round().astype('Int64')
    df['_gy'] = (df[y_col] / coord_scale).round().astype('Int64')
    df['_group'] = df['_gx'].astype(str) + '_' + df['_gy'].astype(str)

    keep_mask = pd.Series(False, index=df.index)

    for g, group_df in df.groupby('_group'):
        if group_df.shape[0] == 1:
            keep_mask[group_df.index] = True
            continue

        # within group, iterate and keep according to policy
        # sort by price (desc) if keep largest_area else keep first/last
        if keep == 'largest_area' and 'diện tích' in group_df.columns:
            order = group_df['diện tích'].fillna(-1).sort_values(ascending=False).index.tolist()
        elif keep == 'last':
            order = group_df.index.tolist()[::-1]
        else:
            order = group_df.index.tolist()

        kept = []
        for idx in order:
            if any(idx == k for k in kept):
                continue
            row = df.loc[idx]
            kept.append(idx)
            keep_mask.loc[idx] = True

            # compare to others in group and mark duplicates
            others = group_df.loc[~group_df.index.isin(kept)]
            if others.empty:
                continue
            # relative difference function
            def rel_diff(a, b):
                try:
                    if pd.isna(a) or pd.isna(b):
                        return float('inf')
                    denom = (abs(a) + abs(b)) / 2.0
                    if denom == 0:
                        return 0.0 if a == b else float('inf')
                    return abs(a - b) / denom
                except Exception:
                    return float('inf')

            for oidx, orow in others.iterrows():
                pdiff = rel_diff(row.get('giá'), orow.get('giá'))
                adiff = rel_diff(row.get('diện tích'), orow.get('diện tích'))
                if pdiff <= price_tol and adiff <= area_tol:
                    # mark duplicate
                    keep_mask.loc[oidx] = False
                    # add to kept to avoid rechecking
                    kept.append(oidx)

    out = df[keep_mask].drop(columns=['_gx', '_gy', '_group'])
    after = len(out)
    print(f'Fuzzy dedupe: {before - after} duplicates removed ({before} -> {after})')
    return out


def main():
    args = parse_args()
    df = read_csv(args.input)
    print(f'Read {len(df)} rows from {args.input}')

    if args.method == 'exact':
        out = dedup_exact(df)
    else:
        out = dedup_fuzzy(df, coord_scale=args.coord_scale, price_tol=args.price_tol, area_tol=args.area_tol, keep=args.keep)

    out_path = args.output or (os.path.splitext(args.input)[0] + '.dedup.csv')
    write_csv(out, out_path)
    print(f'Wrote {len(out)} rows to {out_path}')


if __name__ == '__main__':
    main()
