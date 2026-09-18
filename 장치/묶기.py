#!/usr/bin/env python3
"""제출용 ZIP 한 개를 만든다 (문서 + 장치 + 본문 + 짧은 확인 방법·제출문·재현성 기록).

사용법:  python 묶기.py
결과:    제출물/제출_문서와장치.zip  — 비밀번호 없음
"""

from __future__ import annotations

import zipfile
from pathlib import Path

장치 = Path(__file__).resolve().parent
사업장 = 장치.parent
담을폴더 = ["문서", "장치", "본문"]
제외폴더 = {"__pycache__", ".git"}
# 개인 상세 텍스트가 담긴 원본. 계산에 필요한 정보만 남긴 "정제.json"만 ZIP에 담는다.
제외파일 = {장치 / "입력" / "리추얼기록.json"}
결과 = 사업장 / "제출물" / "제출_문서와장치.zip"


def 담기():
    결과.parent.mkdir(parents=True, exist_ok=True)
    파일들 = []
    for 이름 in 담을폴더:
        뿌리 = 사업장 / 이름
        for 경로 in sorted(뿌리.rglob("*")):
            if 경로.is_dir() or any(부분 in 제외폴더 for 부분 in 경로.parts):
                continue
            if 경로.suffix == ".pyc" or 경로 in 제외파일:
                continue
            파일들.append(경로)

    for 이름 in ("짧은_확인_방법.md", "제출문.md", "재현성_확인.md"):
        경로 = 사업장 / "제출물" / 이름
        if 경로.exists():
            파일들.append(경로)

    with zipfile.ZipFile(결과, "w", zipfile.ZIP_DEFLATED) as z:
        for 경로 in 파일들:
            z.write(경로, 경로.relative_to(사업장).as_posix())

    print(f"[완료] {결과.relative_to(사업장)} — 파일 {len(파일들)}개")
    for 경로 in 파일들:
        print(f"  {경로.relative_to(사업장).as_posix()}")


if __name__ == "__main__":
    담기()
