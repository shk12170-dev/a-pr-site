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
본문폴더 = 사업장 / "본문"
문서폴더 = 사업장 / "문서"
제출물 = 사업장 / "제출물"

설정 = json.loads((본문폴더 / "사이트설정.json").read_text(encoding="utf-8"))
트랙 = 설정["트랙"]
사이트 = 사업장 / {"backend": "site-backend", "cloud": "site-cloud"}[트랙]
꼬리 = {"backend": "백엔드", "cloud": "클라우드"}[트랙]

결과 = []


def 적기(코드, 설명, 상태, 근거):
    결과.append((코드, 설명, 상태, 근거))


def 읽기(경로: Path) -> str:
    return 경로.read_text(encoding="utf-8")


def 해시(경로: Path) -> str:
    return hashlib.md5(경로.read_bytes()).hexdigest()


def 사이트글() -> str:
    return 읽기(사이트 / "index.html")


def 본문만(html글: str) -> str:
    return re.sub(r"<[^>]+>", " ", html글)


def c01():
    글 = 본문만(사이트글())
    고난 = "2022년" in 글 or "GOP" in 글
    회복 = "2026년 8월" in 글 or "2026-08" in 글
    지금 = "목표로 하고 있습니다" in 글
    적기(
        "BRA-C01",
        "이야기가 고난에서 시작해 다시 일어난 날을 지나 지금으로 이어진다",
        "통과" if 고난 and 회복 and 지금 else "실패",
        f"2022년(고난) {'O' if 고난 else 'X'} · 2026년 8월(회복) {'O' if 회복 else 'X'} · 현재 목표 {'O' if 지금 else 'X'}",
    )


def c02():
    능력 = ["자기조절력", "대인관계력", "자기동기력"]
    칸들 = re.findall(r'<article class="ability">(.*?)</article>', 사이트글(), re.S)
    보유 = {}
    for 칸 in 칸들:
        제목 = re.search(r"<h3>(.*?)</h3>", 칸)
        if 제목:
            보유[제목.group(1)] = (
                len(re.findall(r'class="quote"', 칸)),
                len(re.findall(r"\d{4}-\d{2}-\d{2}", 칸)),
            )
    부족 = [이름 for 이름 in 능력 if min(보유.get(이름, (0, 0))) < 1]
    적기(
        "BRA-C02",
        "세 능력이 각각 날짜가 붙은 장면과 함께 드러난다",
        "통과" if not 부족 else "실패",
        "부족: " + ", ".join(부족) if 부족 else "능력 3칸 모두 날짜 있는 인용 보유",
    )


def c03():
    글 = 사이트글()
    이름 = re.search(r"<h1>(.*?)</h1>", 글)
    한줄 = re.search(r'<p class="oneline">(.*?)</p>', 글)
    좋음 = bool(이름 and 한줄 and 한줄.group(1).strip().endswith("사람"))
    적기(
        "BRA-C03",
        '첫 화면에 이름과 "…한 사람"으로 끝나는 한 줄 소개가 있다',
        "통과" if 좋음 else "실패",
        f"이름: {이름.group(1) if 이름 else '없음'} / 한 줄 소개: {한줄.group(1) if 한줄 else '없음'}",
    )


def c04():
    이야기 = re.search(r'<section[^>]*\bid="story"[^>]*>(.*?)</section>', 사이트글(), re.S)
    본 = 본문만(이야기.group(1)) if 이야기 else ""
    날짜 = re.findall(r"\d{4}년 \d{1,2}월(?: \d{1,2}일)?", 본)
    적기(
        "BRA-C04",
        "이야기에 날짜가 있는 장면이 하나 이상 있다",
        "통과" if 날짜 else "실패",
        f"이야기 안 날짜 {len(날짜)}개 (예: {', '.join(날짜[:3])})" if 날짜 else "날짜 없음",
    )


def c05():
    칸 = json.loads(읽기(장치 / "마지막결과" / "숫자.json"))["숫자"]
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

    # 통과 기준(BRA-C##)에는 없지만, 완주 체크리스트에 별도로 있는 항목
    짝지음 = [n for n in 칸 if n.get("짝")]
    적기(
        "완주-짝짓기",
        "13주 기록 숫자 중 하나를 고난 장면과 짝지었다",
        "통과" if 짝지음 else "실패",
        f"짝지은 숫자: {짝지음[0]['이름']}" if 짝지음 else "짝지은 숫자 없음 — 숫자모으기()에 \"짝\" 필드 필요",
    )


def c06():
    글 = 사이트글()
    논문 = "논문" in 글 and (사이트 / "자료" / "논문.docx").exists()
    앱자리 = 'class="work pending"' in 글
    적기(
        "BRA-C06",
        "대표작 자리에 10번 논문이 있고 13번 앱 자리가 마련되어 있다",
        "통과" if 논문 and 앱자리 else "실패",
        f"논문 파일 {'O' if 논문 else 'X'} · 13번 앱 빈자리 {'O' if 앱자리 else 'X'}",
    )


def c07():
    필요 = [f"{꼬리}_{종류}.md" for 종류 in ("이력서", "자기소개서", "경력기술서")]
    없음 = [이름 for 이름 in 필요 if not (문서폴더 / 이름).exists()]
    적기(
        "BRA-C07",
        "이력서·자기소개서·경력기술서가 문서로 있다",
        "통과" if not 없음 else "실패",
        "없는 파일: " + ", ".join(없음) if 없음 else "문서 3개 존재: " + ", ".join(필요),
    )


def c08():
    경로 = 문서폴더 / f"{꼬리}_경력기술서.md"
    if not 경로.exists():
        적기("BRA-C08", "경력기술서에 과제마다 능력과 상황·행동·결과가 적혀 있다", "실패", "파일 없음")
        return
    글 = 읽기(경로)
    과제수 = len(re.findall(r"^## \d+번 —", 글, re.M))
    누락 = [항목 for 항목 in ("**해당 능력**", "**상황**", "**행동**", "**결과**") if 글.count(항목) < 과제수]
    적기(
        "BRA-C08",
        "경력기술서에 과제마다 능력과 상황·행동·결과가 적혀 있다",
        "통과" if 과제수 and not 누락 else "실패",
        "누락: " + ", ".join(누락) if 누락 else f"과제 {과제수}개 모두 네 항목 채워짐",
    )


def c09():
    대상 = [사이트 / "index.html"] + sorted(문서폴더.glob("*.md"))
    전 = {p: 해시(p) for p in 대상}
    subprocess.run([sys.executable, str(장치 / "build.py")], cwd=장치, capture_output=True, check=True)
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
    for 폴더 in [사이트, 문서폴더, 본문폴더, 장치, 제출물]:
        for 경로 in sorted(폴더.rglob("*")):
            if 경로.is_dir() or 경로.suffix in (".docx", ".zip", ".pyc"):
                continue
            try:
                글 = 읽기(경로)
            except UnicodeDecodeError:
                continue
            걸린것 += [f"{경로.name}: {이름}" for 이름 in 금지이름 if 이름 in 글]
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
    빠짐 = [k for k in ["어디로 가나요", "세 단계", "무엇이 보이면", "안 될 때", "문서와 장치는 어디에"] if k not in 글]
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
    빠짐 = [k for k in ["AI에게 맡긴 일", "내가 직접 판단한 일", "AI 제안을 따르지 않은 일"] if k not in 글]
    적기(
        "BRA-C12",
        "제출문에 ①맡긴 일 ②직접 판단한 일 ③따르지 않은 일이 나뉘어 있다",
        "통과" if not 빠짐 else "실패",
        "빠진 항목: " + ", ".join(빠짐) if 빠짐 else "세 항목이 각각 나뉘어 적혀 있음",
    )


def c13_c20():
    주소 = 설정.get("배포주소", "").strip()
    if not 주소:
        적기("BRA-C20", "결과물 URL 필드에 HTTPS URL 한 개", "대기", "아직 배포 전 — 본문/사이트설정.json 의 배포주소가 비어 있음")
        적기("BRA-C13", "제출한 모든 URL이 로그인 없이 열린다", "대기", "배포 후 새 시크릿 창에서 주소를 직접 확인 필요")
        return
    적기(
        "BRA-C20",
        "결과물 URL 필드에 HTTPS URL 한 개",
        "통과" if 주소.startswith("https://") else "실패",
        f"제출 주소: {주소}",
    )
    적기("BRA-C13", "제출한 모든 URL이 로그인 없이 열린다", "대기", f"{주소} 를 새 시크릿 창에서 직접 확인하세요")


def c21():
    경로 = 제출물 / "제출_문서와장치.zip"
    if not 경로.exists():
        적기("BRA-C21", "문서와 장치 ZIP이 비밀번호 없이 열린다", "실패", "ZIP 없음 — 장치/묶기.py 실행 필요")
        return
    with zipfile.ZipFile(경로) as z:
        이름들 = z.namelist()
        암호 = any(정보.flag_bits & 0x1 for 정보 in z.infolist())
    문서수 = len([n for n in 이름들 if n.startswith("문서/") and n.endswith(".md")])
    장치있음 = "장치/build.py" in 이름들
    리드미 = "장치/README.md" in 이름들
    결과있음 = any(n.startswith("장치/마지막결과/") for n in 이름들)
    원본유출 = "장치/입력/리추얼기록.json" in 이름들
    좋음 = (not 암호) and 문서수 == 3 and 장치있음 and 리드미 and 결과있음 and not 원본유출
    상태메모 = (
        f"파일 {len(이름들)}개 · 문서 {문서수}개 · build.py {'O' if 장치있음 else 'X'} · "
        f"README {'O' if 리드미 else 'X'} · 마지막결과 {'O' if 결과있음 else 'X'} · "
        f"비밀번호 {'있음' if 암호 else '없음'}"
    )
    if 원본유출:
        상태메모 += " · [경고] 리추얼 원본(개인 상세 텍스트)이 ZIP에 포함됨"
    적기("BRA-C21", "문서와 장치 ZIP이 파일로 있고 비밀번호 없이 열린다", "통과" if 좋음 else "실패", 상태메모)


def 남길것_재현비교():
    """과제 5 카드의 '남길 것' 중 통과 기준(BRA-C##)엔 없지만 별도로 요구되는 항목."""
    경로 = 제출물 / "재현성_확인.md"
    if not 경로.exists():
        적기(
            "남길것-재현비교",
            "두 번 실행한 결과 비교가 파일로 남아 있다",
            "실패",
            "제출물/재현성_확인.md 없음",
        )
        return
    글 = 읽기(경로)
    필요 = ["1차 실행", "2차", "3차", "MD5"]
    빠짐 = [k for k in 필요 if k not in 글]
    대상 = [사이트 / "index.html"] + sorted(문서폴더.glob("*.md"))
    낡음 = [p.name for p in 대상 if 해시(p) not in 글]
    if 빠짐:
        상태, 근거 = "실패", "빠진 항목: " + ", ".join(빠짐)
    elif 낡음:
        상태, 근거 = "실패", "기록의 해시가 현재 파일과 다름(기록이 낡음): " + ", ".join(낡음) + " — python 장치/재현확인.py 실행"
    else:
        상태, 근거 = "통과", "같은 폴더 2회 + 새 폴더 1회 해시 비교 기록 있고, 현재 파일 해시와도 일치"
    적기("남길것-재현비교", "두 번 실행한 결과 비교가 파일로 남아 있다", 상태, 근거)


def 실행():
    for 검사 in (c01, c02, c03, c04, c05, c06, c07, c08, c09, c10, c11, c12, c13_c20, c21, 남길것_재현비교):
        검사()
    표시 = {"통과": "[통과]", "실패": "[실패]", "대기": "[대기]"}
    print("=" * 78)
    print(f"과제 A 통과 기준 점검 — {사이트.name}")
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
