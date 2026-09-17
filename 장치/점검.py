#!/usr/bin/env python3
"""과제 통과 기준(BRA-C01~C21)을 파일에서 직접 확인한다.

사용법:  python 점검.py
결과:    항목마다 통과 / 실패 / 대기 를 출력하고, 마지막에 요약을 적는다.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

장치 = Path(__file__).resolve().parent
사업장 = 장치.parent
사이트 = {"backend": 사업장 / "site-backend", "cloud": 사업장 / "site-cloud"}
문서폴더 = 사업장 / "문서"
제출물 = 사업장 / "제출물"

결과 = []


def 적기(코드, 설명, 상태, 근거):
    결과.append((코드, 설명, 상태, 근거))


def 읽기(경로: Path) -> str:
    return 경로.read_text(encoding="utf-8")


def 해시(경로: Path) -> str:
    return hashlib.md5(경로.read_bytes()).hexdigest()


def 사이트글(키) -> str:
    return 읽기(사이트[키] / "index.html")


def 본문만(html글: str) -> str:
    return re.sub(r"<[^>]+>", " ", html글)


def c01():
    통과 = []
    for 키 in 사이트:
        글 = 본문만(사이트글(키))
        고난 = "2022년" in 글 or "GOP" in 글
        회복 = "2026년 8월" in 글 or "2026-08" in 글
        지금 = "목표로 하고 있습니다" in 글
        통과.append(고난 and 회복 and 지금)
    적기(
        "BRA-C01",
        "이야기가 고난에서 시작해 다시 일어난 날을 지나 지금으로 이어진다",
        "통과" if all(통과) else "실패",
        "두 사이트 모두 2022년(고난)·2026년 8월(회복)·현재 목표 문장이 모두 있음",
    )


def c02():
    능력 = ["자기조절력", "대인관계력", "자기동기력"]
    문제 = []
    for 키 in 사이트:
        글 = 사이트글(키)
        칸들 = re.findall(r'<article class="ability">(.*?)</article>', 글, re.S)
        보유 = {}
        for 칸 in 칸들:
            제목 = re.search(r"<h3>(.*?)</h3>", 칸)
            인용수 = len(re.findall(r'class="quote"', 칸))
            날짜수 = len(re.findall(r"\d{4}-\d{2}-\d{2}", 칸))
            if 제목:
                보유[제목.group(1)] = (인용수, 날짜수)
        for 이름 in 능력:
            if 보유.get(이름, (0, 0))[0] < 1 or 보유.get(이름, (0, 0))[1] < 1:
                문제.append(f"{키}:{이름}")
    적기(
        "BRA-C02",
        "세 능력이 각각 날짜가 붙은 장면과 함께 드러난다",
        "통과" if not 문제 else "실패",
        "부족: " + ", ".join(문제) if 문제 else "능력 3칸 × 사이트 2개 모두 날짜 있는 인용 보유",
    )


def c03():
    문제 = []
    for 키 in 사이트:
        글 = 사이트글(키)
        이름 = re.search(r"<h1>(.*?)</h1>", 글)
        한줄 = re.search(r'<p class="oneline">(.*?)</p>', 글)
        if not 이름 or not 한줄 or not 한줄.group(1).strip().endswith("사람"):
            문제.append(키)
    적기(
        "BRA-C03",
        '첫 화면에 이름과 "…한 사람"으로 끝나는 한 줄 소개가 있다',
        "통과" if not 문제 else "실패",
        "문제: " + ", ".join(문제) if 문제 else "두 사이트 모두 h1 이름 + 한 줄 소개가 '사람'으로 끝남",
    )


def c04():
    문제 = []
    for 키 in 사이트:
        글 = 사이트글(키)
        이야기 = re.search(r'<section id="story">(.*?)</section>', 글, re.S)
        본 = 본문만(이야기.group(1)) if 이야기 else ""
        if not re.search(r"\d{4}년 \d{1,2}월", 본):
            문제.append(키)
    적기(
        "BRA-C04",
        "이야기에 날짜가 있는 장면이 하나 이상 있다",
        "통과" if not 문제 else "실패",
        "문제: " + ", ".join(문제) if 문제 else "이야기 안에 'YYYY년 M월' 형태의 날짜가 있음",
    )


def c05():
    숫자자료 = json.loads(읽기(장치 / "마지막결과" / "숫자.json"))
    칸 = 숫자자료["숫자"]
    출처없음 = [n["이름"] for n in 칸 if not n.get("출처")]
    기록출처 = [n for n in 칸 if "리추얼" in n["출처"] or "출석" in n["출처"]]
    if 출처없음:
        상태, 근거 = "실패", "출처 없는 칸: " + ", ".join(출처없음)
    elif not 기록출처:
        상태 = "대기"
        근거 = (
            f"숫자 {len(칸)}개 모두 출처 있음. 다만 리추얼 기록·출석 기록에서 나온 숫자가 없음 "
            "— 입력/리추얼기록.json 과 입력/출석.json 을 채우면 자동으로 들어감"
        )
    else:
        상태, 근거 = "통과", f"숫자 {len(칸)}개 모두 출처 있고, 기록에서 나온 숫자 {len(기록출처)}개 포함"
    적기("BRA-C05", "13주 기록에서 나온 숫자가 있고 각각 출처가 적혀 있다", 상태, 근거)


def c06():
    문제 = []
    for 키, 폴더 in 사이트.items():
        글 = 사이트글(키)
        논문있음 = "논문" in 글 and (폴더 / "자료" / "논문.docx").exists()
        앱자리 = 'class="work pending"' in 글
        if not (논문있음 and 앱자리):
            문제.append(키)
    적기(
        "BRA-C06",
        "대표작 자리에 10번 논문이 있고 13번 앱 자리가 마련되어 있다",
        "통과" if not 문제 else "실패",
        "문제: " + ", ".join(문제) if 문제 else "논문 파일이 두 사이트에 모두 올라가 있고 앱 자리(점선 칸)가 있음",
    )


def c07():
    필요 = [
        f"{꼬리}_{종류}.md"
        for 꼬리 in ("백엔드", "클라우드")
        for 종류 in ("이력서", "자기소개서", "경력기술서")
    ]
    없음 = [이름 for 이름 in 필요 if not (문서폴더 / 이름).exists()]
    적기(
        "BRA-C07",
        "이력서·자기소개서·경력기술서가 문서로 있다",
        "통과" if not 없음 else "실패",
        "없는 파일: " + ", ".join(없음) if 없음 else f"문서 {len(필요)}개 존재 (트랙별 3종 × 2벌)",
    )


def c08():
    문제 = []
    for 꼬리 in ("백엔드", "클라우드"):
        경로 = 문서폴더 / f"{꼬리}_경력기술서.md"
        if not 경로.exists():
            문제.append(f"{꼬리}: 파일 없음")
            continue
        글 = 읽기(경로)
        과제수 = len(re.findall(r"^## \d+번 —", 글, re.M))
        for 항목 in ("**해당 능력**", "**상황**", "**행동**", "**결과**"):
            if 글.count(항목) < 과제수:
                문제.append(f"{꼬리}: {항목} 누락")
    적기(
        "BRA-C08",
        "경력기술서에 과제마다 능력과 상황·행동·결과가 적혀 있다",
        "통과" if not 문제 else "실패",
        "문제: " + ", ".join(문제) if 문제 else "두 경력기술서 모두 과제 수만큼 네 항목이 채워져 있음",
    )


def c09():
    대상 = [사이트["backend"] / "index.html", 사이트["cloud"] / "index.html"] + sorted(
        문서폴더.glob("*.md")
    )
    전 = {p: 해시(p) for p in 대상}
    subprocess.run(
        [sys.executable, str(장치 / "build.py")],
        cwd=장치,
        capture_output=True,
        check=True,
    )
    후 = {p: 해시(p) for p in 대상}
    다름 = [p.name for p in 대상 if 전[p] != 후[p]]
    적기(
        "BRA-C09",
        "장치가 같은 입력에 같은 결과를 낸다",
        "통과" if not 다름 else "실패",
        "달라진 파일: " + ", ".join(다름) if 다름 else f"다시 실행 후 결과 파일 {len(대상)}개 전부 동일",
    )


def c10():
    # 찾을 이름 목록은 제출물 밖(프로젝트 최상단 점검어.txt)에 둔다.
    # 실명을 이 파일에 적으면 ZIP에 그대로 실려 나가기 때문이다.
    목록파일 = 사업장 / "점검어.txt"
    if not 목록파일.exists():
        적기(
            "BRA-C10",
            "본인 이름 외 타인 실명·연락처, 비밀번호·토큰·API 키가 없다",
            "대기",
            "점검어.txt 가 없어 이름 검사를 건너뜀 (파일에 한 줄에 하나씩 적으면 검사함)",
        )
        return
    금지이름 = [
        줄.strip()
        for 줄 in 목록파일.read_text(encoding="utf-8").splitlines()
        if 줄.strip() and not 줄.startswith("#")
    ]
    금지값 = re.compile(r"(api[_-]?key|secret|token|passwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}", re.I)
    걸린것 = []
    대상폴더 = [사이트["backend"], 사이트["cloud"], 문서폴더, 사업장 / "본문", 장치, 제출물]
    for 폴더 in 대상폴더:
        for 경로 in sorted(폴더.rglob("*")):
            if 경로.is_dir() or 경로.suffix in (".docx", ".zip", ".pyc"):
                continue
            try:
                글 = 읽기(경로)
            except UnicodeDecodeError:
                continue
            for 이름 in 금지이름:
                if 이름 in 글:
                    걸린것.append(f"{경로.name}: {이름}")
            if 금지값.search(글):
                걸린것.append(f"{경로.name}: 비밀값 형태")
    적기(
        "BRA-C10",
        "본인 이름 외 타인 실명·연락처, 비밀번호·토큰·API 키가 없다",
        "통과" if not 걸린것 else "실패",
        "걸린 것: " + ", ".join(걸린것) if 걸린것 else "제출 대상 전체에서 타인 이름·비밀값 0건",
    )


def c11():
    경로 = 제출물 / "짧은_확인_방법.md"
    if not 경로.exists():
        적기("BRA-C11", "짧은 확인 방법이 있다", "실패", "파일 없음")
        return
    글 = 읽기(경로)
    필요 = ["어디로 가나요", "세 단계", "무엇이 보이면", "안 될 때", "문서와 장치는 어디에"]
    빠짐 = [k for k in 필요 if k not in 글]
    미정 = "배포 후" in 글
    적기(
        "BRA-C11",
        "짧은 확인 방법에 주소·위치·문서와 장치 내용이 적혀 있다",
        "실패" if 빠짐 else ("대기" if 미정 else "통과"),
        "빠진 항목: " + ", ".join(빠짐)
        if 빠짐
        else ("항목은 모두 있으나 사이트 주소가 아직 비어 있음" if 미정 else "항목과 주소 모두 채워짐"),
    )


def c12():
    경로 = 제출물 / "제출문.md"
    if not 경로.exists():
        적기("BRA-C12", "제출문에 AI·내 판단 세 항목이 있다", "실패", "파일 없음")
        return
    글 = 읽기(경로)
    필요 = ["AI에게 맡긴 일", "내가 직접 판단한 일", "AI 제안을 따르지 않은 일"]
    빠짐 = [k for k in 필요 if k not in 글]
    적기(
        "BRA-C12",
        "제출문에 ①맡긴 일 ②직접 판단한 일 ③따르지 않은 일이 나뉘어 있다",
        "통과" if not 빠짐 else "실패",
        "빠진 항목: " + ", ".join(빠짐) if 빠짐 else "세 항목이 각각 나뉘어 적혀 있음",
    )


def c13_c20():
    배포 = json.loads(읽기(사업장 / "본문" / "배포주소.json"))
    제출트랙 = 배포.get("제출할_트랙", "backend")
    주소 = (배포.get(제출트랙) or "").strip()
    상대 = (배포.get("cloud" if 제출트랙 == "backend" else "backend") or "").strip()
    if not 주소:
        적기("BRA-C20", "결과물 URL 필드에 HTTPS URL 한 개", "대기", "아직 배포 전 — 본문/배포주소.json 이 비어 있음")
        적기("BRA-C13", "제출한 모든 URL이 로그인 없이 열린다", "대기", "배포 후 새 시크릿 창에서 두 주소를 직접 확인 필요")
        return
    적기(
        "BRA-C20",
        "결과물 URL 필드에 HTTPS URL 한 개",
        "통과" if 주소.startswith("https://") else "실패",
        f"제출 주소: {주소}",
    )
    적기(
        "BRA-C13",
        "제출한 모든 URL이 로그인 없이 열린다",
        "대기",
        f"주소 2개({주소}, {상대 or '상대 트랙 미입력'})를 새 시크릿 창에서 직접 확인하세요",
    )


def c21():
    경로 = 제출물 / "제출_문서와장치.zip"
    if not 경로.exists():
        적기("BRA-C21", "문서와 장치 ZIP이 비밀번호 없이 열린다", "실패", "ZIP 없음 — 장치/묶기.py 실행 필요")
        return
    with zipfile.ZipFile(경로) as z:
        이름들 = z.namelist()
        암호 = any(정보.flag_bits & 0x1 for 정보 in z.infolist())
        문서수 = len([n for n in 이름들 if n.startswith("문서/") and n.endswith(".md")])
        장치있음 = any(n == "장치/build.py" for n in 이름들)
        리드미 = any(n == "장치/README.md" for n in 이름들)
        결과있음 = any(n.startswith("장치/마지막결과/") for n in 이름들)
    좋음 = (not 암호) and 문서수 == 6 and 장치있음 and 리드미 and 결과있음
    적기(
        "BRA-C21",
        "문서와 장치 ZIP이 파일로 있고 비밀번호 없이 열린다",
        "통과" if 좋음 else "실패",
        f"파일 {len(이름들)}개 · 문서 {문서수}개 · build.py {'O' if 장치있음 else 'X'} · "
        f"README {'O' if 리드미 else 'X'} · 마지막결과 {'O' if 결과있음 else 'X'} · "
        f"비밀번호 {'있음' if 암호 else '없음'}",
    )


def 실행():
    for 검사 in (c01, c02, c03, c04, c05, c06, c07, c08, c09, c10, c11, c12, c13_c20, c21):
        검사()
    표시 = {"통과": "[통과]", "실패": "[실패]", "대기": "[대기]"}
    print("=" * 78)
    print("과제 A 통과 기준 점검")
    print("=" * 78)
    for 코드, 설명, 상태, 근거 in sorted(결과):
        print(f"{표시[상태]} {코드}  {설명}")
        print(f"        └ {근거}")
    통과 = sum(1 for r in 결과 if r[2] == "통과")
    대기 = sum(1 for r in 결과 if r[2] == "대기")
    실패 = sum(1 for r in 결과 if r[2] == "실패")
    print("-" * 78)
    print(f"통과 {통과} · 대기 {대기} · 실패 {실패} (전체 {len(결과)})")
    return 1 if 실패 else 0


if __name__ == "__main__":
    sys.exit(실행())
