#!/usr/bin/env python3
"""장치를 세 번 돌려 결과가 같은지 확인하고 제출물/재현성_확인.md 를 다시 쓴다 (BRA-C09).

1차·2차: 이 폴더에서 build.py 두 번
3차   : 제출물/제출_문서와장치.zip 을 새 임시 폴더에 풀고, README 3단계대로 build.py 실행
        (ZIP에는 리추얼 원본이 없으므로 정제본만으로 재현되는지도 함께 확인된다)

사용법:  python 묶기.py → python 재현확인.py → python 묶기.py (갱신된 기록을 ZIP에 다시 담기)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

장치 = Path(__file__).resolve().parent
사업장 = 장치.parent
설정 = json.loads((사업장 / "본문" / "사이트설정.json").read_text(encoding="utf-8"))
사이트 = {"backend": "site-backend", "cloud": "site-cloud"}[설정["트랙"]]
꼬리 = {"backend": "백엔드", "cloud": "클라우드"}[설정["트랙"]]
대상 = [
    f"{사이트}/index.html",
    f"문서/{꼬리}_이력서.md",
    f"문서/{꼬리}_자기소개서.md",
    f"문서/{꼬리}_경력기술서.md",
    "장치/마지막결과/숫자.json",
    "장치/마지막결과/문단후보.md",
]


def 돌리기(뿌리: Path):
    subprocess.run([sys.executable, str(뿌리 / "장치" / "build.py")], cwd=뿌리 / "장치", capture_output=True, check=True)
    return {p: hashlib.md5((뿌리 / p).read_bytes()).hexdigest() for p in 대상}


def 확인():
    zip경로 = 사업장 / "제출물" / "제출_문서와장치.zip"
    if not zip경로.exists():
        raise SystemExit("[중단] 제출물/제출_문서와장치.zip 이 없습니다. 먼저 python 묶기.py 를 실행하세요.")

    첫째 = 돌리기(사업장)
    둘째 = 돌리기(사업장)
    with tempfile.TemporaryDirectory() as 임시:
        새폴더 = Path(임시)
        zipfile.ZipFile(zip경로).extractall(새폴더)
        원본없음 = not (새폴더 / "장치" / "입력" / "리추얼기록.json").exists()
        셋째 = 돌리기(새폴더)

    모두같음 = all(첫째[p] == 둘째[p] == 셋째[p] for p in 대상)
    줄 = [
        "# 장치 재현성 확인 (과제 5 \"남길 것\" — 두 번 실행한 결과 비교)",
        "",
        "BRA-C09(\"장치가 같은 입력에 같은 결과를 내고, README대로 새 폴더에서 돌아간다\")를 실제로 세 번 돌려",
        "파일 해시(MD5)로 비교한 기록입니다. 이 문서는 `python 장치/재현확인.py`가 실행 결과로 직접 씁니다.",
        "",
        "## 방법",
        "",
        "1. **1차 실행** — 프로젝트 폴더에서 `python 장치/build.py`",
        "2. **2차 실행** — 같은 폴더에서 다시 `python 장치/build.py`",
        "3. **3차 실행** — `제출물/제출_문서와장치.zip`을 새 임시 폴더에 풀고, README 3단계대로 `python 장치/build.py`"
        + (" (리추얼 원본 없이 정제본만 있는 상태)" if 원본없음 else ""),
        "",
        "## 결과 — MD5 해시",
        "",
        "| 파일 | 1차 실행 | 2차 실행 (같은 폴더) | 3차 실행 (새 폴더, ZIP에서 풀어서) | 같음 |",
        "|---|---|---|---|---|",
    ]
    for p in 대상:
        같음 = "O" if 첫째[p] == 둘째[p] == 셋째[p] else "X"
        줄.append(f"| `{p}` | `{첫째[p]}` | `{둘째[p]}` | `{셋째[p]}` | {같음} |")
    줄 += [
        "",
        f"**{'세 번 모두 ' + str(len(대상)) + '개 파일 전부 같은 해시가 나왔습니다.' if 모두같음 else '해시가 다른 파일이 있습니다 — 위 표의 X 항목을 확인하세요.'}**",
        "",
        "## 같은 결과가 나오는 이유",
        "",
        "- 실행 중 AI를 호출하지 않습니다(필요한 API 키·환경 변수가 없습니다).",
        "- 사이트에 들어가는 인용문은 `승인문장/능력별_장면.json`에서 `\"승인\": true`인 것만 읽습니다.",
        "- 숫자는 `입력/` 폴더의 파일에서만 셉니다.",
        "- 결과물에 실행 시각을 넣지 않습니다.",
        "- 리추얼 원본은 계산에 필요한 최소 정보만 남긴 정제본으로 저장되고, 정제본만으로도 같은 결과가 나옵니다.",
    ]
    (사업장 / "제출물" / "재현성_확인.md").write_text("\n".join(줄) + "\n", encoding="utf-8")
    print(f"[완료] 제출물/재현성_확인.md — {'모두 같음' if 모두같음 else '다른 파일 있음'}")
    return 0 if 모두같음 else 1


if __name__ == "__main__":
    sys.exit(확인())
