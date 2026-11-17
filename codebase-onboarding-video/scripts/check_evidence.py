#!/usr/bin/env python3
"""Offline, read-only validation of storyboard evidence IDs against claim register and repository lines."""
import argparse, json, sys
from pathlib import Path


def run(args):
    storyboard=json.loads(Path(args.storyboard).read_text(encoding='utf-8'))
    evidence=json.loads(Path(args.evidence).read_text(encoding='utf-8'))
    root=Path(args.repo).resolve()
    claims={c['id']:c for c in evidence.get('claims',[])}
    errors=[]
    demo=storyboard.get('example',False)
    for i,sc in enumerate(storyboard.get('scenes',[]),1):
        status=sc.get('status','UNKNOWN')
        ids=sc.get('evidence_ids',[])
        if not demo and status=='CONFIRMED' and not ids:
            errors.append(f'scene {i}: CONFIRMED 缺少證據 ID')
        for cid in ids:
            c=claims.get(cid)
            if not c:
                errors.append(f'scene {i}: 找不到證據 {cid}')
            elif c.get('status')!='CONFIRMED' and status=='CONFIRMED':
                errors.append(f'scene {i}: {cid} 不是 CONFIRMED')
    for cid,c in claims.items():
        if c.get('status')!='CONFIRMED': continue
        sources=c.get('sources') or []
        if not sources:
            errors.append(f'{cid}: 缺少來源路徑')
        for src in sources:
            name=src.get('path','')
            path=(root/name).resolve()
            if not path.is_relative_to(root):
                errors.append(f'{cid}: 路徑超出儲存庫範圍')
                continue
            if not path.is_file():
                errors.append(f'{cid}: 檔案不存在 {name}')
                continue
            start=src.get('line_start',0); end=src.get('line_end',0)
            if not (isinstance(start,int) and isinstance(end,int) and 1<=start<=end):
                errors.append(f'{cid}: 行數範圍無效 {name}:{start}-{end}')
                continue
            # Count lines; do not print or transmit content.
            with path.open('rb') as f:
                count=sum(1 for _ in f)
            if end>count:
                errors.append(f'{cid}: 行號超出實際檔案長度 {name}:{end} > {count}')
    if errors:
        print('\n'.join('ERROR: '+e for e in errors),file=sys.stderr)
        return 1
    print(f'PASS: {len(storyboard.get("scenes",[]))} scenes; {len(claims)} registered claims. 注意：此檢查只驗證引用存在與行號，不會判定解讀是否正確。')
    return 0

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--repo',required=True)
    p.add_argument('--storyboard',required=True)
    p.add_argument('--evidence',required=True)
    sys.exit(run(p.parse_args()))
