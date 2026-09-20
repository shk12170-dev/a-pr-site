#!/usr/bin/env python3
"""리추얼 기록·과제 목록·출석 파일을 읽어 사이트와 문서를 다시 만든다.

어느 트랙(백엔드 개발자 / 클라우드 엔지니어)의 사이트를 만들지는
본문/사이트설정.json 의 "트랙" 값으로 정한다.

실행 중 AI를 호출하지 않는다. 사이트에 들어가는 문장은 승인문장 폴더에서만 읽고,
숫자는 입력 폴더의 파일에서만 센다. 실행 시각을 결과에 넣지 않으므로
같은 입력이면 항상 같은 결과가 나온다.

사용법:  python build.py
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

장치 = Path(__file__).resolve().parent
사업장 = 장치.parent
입력 = 장치 / "입력"
승인문장 = 장치 / "승인문장"
템플릿파일 = 장치 / "템플릿" / "site.html.tmpl"
마지막결과 = 장치 / "마지막결과"
본문폴더 = 사업장 / "본문"

능력순서 = ["자기조절력", "대인관계력", "자기동기력"]

트랙정보 = {
    "backend": {
        "메타파일": "트랙_백엔드.json",
        "사이트폴더": "site-backend",
        "꼬리": "백엔드",
        "강조색": "#0f6f8c",
        "강조색_연한": "#e6f2f6",
        "강조색_다크": "#5fc3e4",
    },
    "cloud": {
        "메타파일": "트랙_클라우드.json",
        "사이트폴더": "site-cloud",
        "꼬리": "클라우드",
        "강조색": "#4a4ec4",
        "강조색_연한": "#ecedfa",
        "강조색_다크": "#9ea2f5",
    },
}

날짜칸 = ("날짜", "date", "일자", "day")
아침칸 = ("아침", "morning", "am", "오전", "open")
마무리칸 = ("마무리", "저녁", "evening", "pm", "회고", "close")


def 읽기(경로: Path):
    return json.loads(경로.read_text(encoding="utf-8"))


def 칸찾기(행: dict, 후보: tuple[str, ...]):
    for 키 in 후보:
        if 키 in 행:
            return 행[키]
    return None


def 글자로(값) -> str:
    if 값 is None:
        return ""
    if isinstance(값, str):
        return 값.strip()
    if isinstance(값, dict):
        return " ".join(글자로(v) for v in 값.values()).strip()
    if isinstance(값, list):
        return " ".join(글자로(v) for v in 값).strip()
    return str(값).strip()


원본경로 = 입력 / "리추얼기록.json"
정제경로 = 입력 / "리추얼기록.정제.json"


def 원본에서_표뽑기(자료):
    if isinstance(자료, list):
        행들 = 자료
    elif isinstance(자료, dict):
        행들 = next(
            (자료[키] for 키 in ("기록", "days", "records", "list", "entries") if isinstance(자료.get(키), list)),
            None,
        )
    else:
        행들 = None
    if not isinstance(행들, list):
        raise SystemExit(f"[중단] {원본경로.name}에서 기록 목록을 찾지 못했습니다.")

    표 = []
    for 행 in 행들:
        if not isinstance(행, dict):
            continue
        날짜 = 글자로(칸찾기(행, 날짜칸))
        if not 날짜:
            continue
        마무리글 = 글자로(칸찾기(행, 마무리칸))
        표.append(
            {
                "날짜": 날짜[:10],
                "아침있음": bool(글자로(칸찾기(행, 아침칸))),
                "마무리있음": bool(마무리글),
                "마무리_일부": ("일부" in 마무리글) if 마무리글 else None,
            }
        )
    표.sort(key=lambda r: r["날짜"])
    return 표


def 정제하기():
    """원본(개인 상세 텍스트)이 있으면 계산에 필요한 최소 정보만 뽑아 정제본으로 저장한다.

    원본은 개인정보가 담겨 있어 저장소에 올리지 않는다(.gitignore). 정제본만 커밋되므로
    새 폴더에서 원본 없이 정제본만으로도 같은 숫자가 재현된다.
    """
    if 원본경로.exists():
        표 = 원본에서_표뽑기(읽기(원본경로))
        정제경로.write_text(
            json.dumps(
                {
                    "설명": (
                        "원본 리추얼기록.json(개인 상세 텍스트)에서 계산에 필요한 최소 정보만 "
                        "자동으로 뽑아낸 정제본입니다. 원본은 저장소에 올리지 않고, 이 정제본만 "
                        "커밋해도 숫자가 그대로 재현됩니다."
                    ),
                    "기록": 표,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 표
    if 정제경로.exists():
        return 읽기(정제경로)["기록"]
    return None


def 리추얼세기():
    """리추얼 기록에서 숫자를 센다. 원본·정제본 모두 없으면 None을 돌려준다."""
    표 = 정제하기()
    if 표 is None:
        return None

    마무리있음 = [r for r in 표 if r["마무리있음"]]
    일부표현 = [r for r in 마무리있음 if r["마무리_일부"]]
    달별 = {}
    for r in 마무리있음:
        달 = r["날짜"][:7]
        칸 = 달별.setdefault(달, {"일부": 0, "완료": 0})
        칸["일부" if r["마무리_일부"] else "완료"] += 1

    return {
        "기록일수": len(표),
        "아침수": len([r for r in 표 if r["아침있음"]]),
        "마무리수": len(마무리있음),
        "첫날": 표[0]["날짜"] if 표 else "",
        "마지막날": 표[-1]["날짜"] if 표 else "",
        "일부표현수": len(일부표현),
        "달별": {달: 달별[달] for 달 in sorted(달별)},
    }


def 숫자모으기(리추얼, 과제자료):
    숫자 = []

    if 리추얼:
        기간 = f"{리추얼['첫날']} ~ {리추얼['마지막날']}"
        숫자.append(
            {
                "이름": "리추얼 기록",
                "값": f"{리추얼['기록일수']}일",
                "보조": f"아침 {리추얼['아침수']} · 마무리 {리추얼['마무리수']}",
                "출처": f"내 리추얼 기록 ({기간})",
            }
        )
        달별 = 리추얼["달별"]
        if len(달별) >= 2:
            달목록 = list(달별)
            첫달, 끝달 = 달목록[0], 달목록[-1]
            숫자.append(
                {
                    "이름": '"일부 했다"로 끝난 마무리',
                    "값": f"{달별[첫달]['일부']} → {달별[끝달]['일부']}",
                    "보조": f"{첫달} → {끝달}",
                    "출처": "내 리추얼 기록 (마무리 칸 문장을 그대로 셈)",
                    "짝": "이야기 속 고난 장면과 연결: 오류에 막혀 \"일부 했다\"만 쓸 수 있던 8월이, 9월 들어 \"했다\"로 자주 바뀌었습니다.",
                }
            )

    출석 = 읽기(입력 / "출석.json")
    if 출석.get("출석일") and 출석.get("총_교육일"):
        숫자.append(
            {
                "이름": "출석",
                "값": f"{출석['출석일']} / {출석['총_교육일']}일",
                "보조": 출석.get("기간", ""),
                "출처": 출석.get("출처", "내 출석 기록"),
            }
        )

    과제들 = [t for t in 과제자료["과제"] if t.get("상태") != "예정"]
    공개 = [t for t in 과제들 if t.get("공개URL")]
    예정들 = [t for t in 과제자료["과제"] if t.get("상태") == "예정"]
    진행중_보조 = (
        ", ".join(f"{t['번호']}번" for t in sorted(예정들, key=lambda x: x["번호"])) + " 진행 예정"
        if 예정들
        else "전체 과제 완료"
    )
    숫자.append(
        {
            "이름": "완료한 과제",
            "값": f"{len(과제들)}개",
            "보조": 진행중_보조,
            "출처": "내 제출 현황 · GitHub 저장소",
        }
    )
    숫자.append(
        {
            "이름": "로그인 없이 열리는 결과물",
            "값": f"{len(공개)}개",
            "보조": "",
            "출처": "각 과제 배포 주소",
        }
    )

    for 항목 in 읽기(입력 / "검증숫자.json")["숫자"]:
        숫자.append(
            {
                "이름": 항목["이름"],
                "값": 항목["값"],
                "보조": 항목.get("보조", ""),
                "출처": 항목["출처"],
                "짝": 항목.get("짝", ""),
            }
        )
    return 숫자


def 본문_html() -> str:
    원문 = (본문폴더 / "자기소개_본문.md").read_text(encoding="utf-8")
    몸통 = 원문.split("---", 2)[-1]
    문단 = [p.strip() for p in re.split(r"\n\s*\n", 몸통) if p.strip()]
    return "\n".join(f"    <p>{html.escape(p)}</p>" for p in 문단)


def 능력_html(트랙메타) -> str:
    장면들 = [s for s in 읽기(승인문장 / "능력별_장면.json")["장면"] if s.get("승인")]
    해석 = 트랙메타["능력_해석"]
    덩어리 = []
    for 능력 in 능력순서:
        골라낸 = [s for s in 장면들 if s["능력"] == 능력]
        인용 = "\n".join(
            f'      <blockquote class="quote">'
            f'<span class="when">{html.escape(s["날짜"])} · {html.escape(s["칸"])}</span>'
            f'<span class="text">“{html.escape(s["인용"])}”</span>'
            f'<span class="src">{html.escape(s["출처"])}</span>'
            f"</blockquote>"
            for s in 골라낸
        )
        덩어리.append(
            f'    <article class="ability">\n'
            f"      <h3>{html.escape(능력)}</h3>\n"
            f'      <p class="note">{html.escape(해석.get(능력, ""))}</p>\n'
            f"{인용}\n"
            f"    </article>"
        )
    return "\n".join(덩어리)


def 숫자_html(숫자) -> str:
    칸 = []
    for n in 숫자:
        보조 = f'<span class="b">{html.escape(n["보조"])}</span>' if n["보조"] else ""
        짝 = n.get("짝", "")
        짝문구 = f'<span class="link">{html.escape(짝)}</span>' if 짝 else ""
        칸.append(
            f'    <div class="num">'
            f'<span class="v">{html.escape(n["값"])}</span>'
            f'<span class="k">{html.escape(n["이름"])}</span>'
            f"{보조}"
            f'<span class="s">출처: {html.escape(n["출처"])}</span>'
            f"{짝문구}"
            f"</div>"
        )
    return "\n".join(칸)


def 대표작_html(트랙메타) -> str:
    덩어리 = []
    for w in 트랙메타["대표작"]:
        예정 = w.get("상태") == "예정"
        머리 = (
            f'      <span class="no">{html.escape(w["번호"])}</span>\n'
            f'      <h3>{html.escape(w["제목"])}</h3>\n'
            f'      <p>{html.escape(w["설명"])}</p>\n'
        )
        if 예정:
            예정일 = w.get("예정일", "").strip()
            안내 = (
                f"예정일 {html.escape(예정일)}. 그날 과제를 마치면 이 자리에 결과물과 소스 링크가 들어갑니다."
                if 예정일
                else "아직 진행 전입니다. 과제를 마치면 이 자리에 결과물과 소스 링크가 들어갑니다."
            )
            덩어리.append(
                f'    <article class="work pending">\n{머리}'
                f'      <span class="badge">{안내}</span>\n'
                f"    </article>"
            )
        else:
            덩어리.append(
                f'    <article class="work">\n{머리}'
                f'      <a class="btn" href="{html.escape(w["링크"])}">{html.escape(w["링크문구"])}</a>\n'
                f"    </article>"
            )
    return "\n".join(덩어리)


def 과제목록_html(과제자료, 트랙아이디) -> str:
    줄 = []
    for t in sorted(과제자료["과제"], key=lambda x: x["번호"]):
        if 트랙아이디 not in t["트랙"]:
            continue
        if t.get("상태") == "예정":
            줄.append(
                f'      <tr><td class="n">{t["번호"]}번</td>'
                f'<td>{html.escape(t["이름"])}</td><td class="n">—</td></tr>'
            )
            continue
        이름 = html.escape(t["이름"])
        if t.get("공개URL"):
            이름 = f'<a href="{html.escape(t["공개URL"])}">{이름}</a>'
        줄.append(
            f'      <tr><td class="n">{t["번호"]}번</td>'
            f'<td><strong>{이름}</strong><br>{html.escape(t["결과"])}</td>'
            f'<td class="n">{html.escape(t["능력"])}</td></tr>'
        )
    return "\n".join(줄)


def 연락처_html() -> str:
    연락 = 읽기(본문폴더 / "연락처.json")
    주소 = 연락.get("이메일", "").strip()
    문구 = html.escape(연락.get("표시문구", "연락"))
    if not 주소:
        return f"{문구}: <span style=\"color:var(--muted)\">공개할 주소 미정</span>"
    안전 = html.escape(주소)
    return f'{문구}: <a href="mailto:{안전}">{안전}</a>'


def 동료의_말_읽기():
    경로 = 승인문장 / "동료의_말.json"
    if not 경로.exists():
        return None
    자료 = 읽기(경로)
    자료["말"] = [m for m in 자료["말"] if m.get("승인")]
    return 자료


def 동료의_말_html(자료) -> str:
    덩어리 = []
    for m in 자료["말"]:
        묶음 = f'<span class="tag">{html.escape(m["묶음"])}</span>' if m.get("묶음") else ""
        덩어리.append(
            f'    <blockquote class="peer">'
            f"{묶음}"
            f'<span class="q">“{html.escape(m["인용"])}”</span>'
            f'<span class="m">리추얼 기록 {html.escape(m["날짜"])} · {html.escape(m["칸"])}</span>'
            f"</blockquote>"
        )
    return "\n".join(덩어리)


def 문서파일_이름() -> str:
    후보 = sorted((사업장 / "문서").glob("*.docx"))
    return 후보[0].name if 후보 else ""


def 연락처_칩_html() -> str:
    연락 = 읽기(본문폴더 / "연락처.json")
    주소 = 연락.get("이메일", "").strip()
    if not 주소:
        return '<span>연락 수단 미정</span>'
    안전 = html.escape(주소)
    return f'<a href="mailto:{안전}">✉ {안전}</a>'


def 다른버전_html(설정) -> str:
    """다른 트랙 사이트 주소가 설정에 있을 때만 상단 링크를 보여준다."""
    url = 설정.get("다른버전_주소", "").strip()
    if not url:
        return ""
    이름 = html.escape(설정.get("다른버전_이름", "다른 버전"))
    return f'<a href="{html.escape(url)}">↗ {이름}</a>'


def 문서페이지만들기(메타, 정보, 과제자료, 숫자, 출력, 값):
    """이력서·자기소개서·경력기술서를 한 페이지로 보여 주는 이력서.html 을 만든다 (첫 화면 배너의 목적지)."""
    기본 = 읽기(본문폴더 / "이력_기본정보.json")
    과제들 = [
        t for t in sorted(과제자료["과제"], key=lambda x: x["번호"])
        if 메타["track_id"] in t["트랙"] and t.get("상태") != "예정"
    ]

    이력 = ["  <p class=\"sub\">지원 직무 · " + html.escape(메타["목표"]) + "</p>", "  <h3>교육</h3>", "  <ul>"]
    이력 += [f'    <li><strong>{html.escape(e["기간"])}</strong> {html.escape(e["이름"])} — {html.escape(e["내용"])}</li>' for e in 기본["교육"]]
    이력 += ["  </ul>", "  <h3>경력</h3>", "  <ul>"]
    이력 += [f'    <li><strong>{html.escape(m["기간"])}</strong> {html.escape(m["소속"])} — {html.escape(m["구분"])}</li>' for m in 기본["군경력"]]
    이력 += ["  </ul>", "  <h3>프로젝트 (교육과정 과제)</h3>", "  <ul>"]
    for t in 과제들:
        링크 = f' — <a href="{html.escape(t["공개URL"])}">{html.escape(t["공개URL"])}</a>' if t["공개URL"] else ""
        이력.append(f'    <li><strong>{t["번호"]}번 {html.escape(t["이름"])}</strong>{링크}</li>')
    이력 += ["  </ul>", "  <h3>자격</h3>", "  <ul>"]
    이력 += [f'    <li>{html.escape(c["이름"])} ({html.escape(c["상태"])})</li>' for c in 기본["자격증"]]
    이력 += ["  </ul>", "  <h3>기록으로 본 숫자</h3>", '  <div class="numbers">', 숫자_html(숫자), "  </div>"]

    장면들 = [s for s in 읽기(승인문장 / "능력별_장면.json")["장면"] if s.get("승인")]
    소개 = [본문_html(), f'    <p>{html.escape(메타["마무리_목표문"])}</p>', "  <h3>기록으로 확인되는 세 가지 능력</h3>", 능력_html(메타)]

    경력 = []
    for t in 과제들:
        경력.append(f'  <h3>{t["번호"]}번 — {html.escape(t["이름"])}</h3>')
        경력.append("  <ul>")
        경력.append(f'    <li><strong>해당 능력</strong>: {html.escape(t["능력"])}</li>')
        경력.append(f'    <li><strong>상황</strong>: {html.escape(t["상황"])}</li>')
        경력.append(f'    <li><strong>행동</strong>: {html.escape(t["행동"])}</li>')
        경력.append(f'    <li><strong>결과</strong>: {html.escape(t["결과"])}</li>')
        if t["공개URL"]:
            경력.append(f'    <li><strong>확인</strong>: <a href="{html.escape(t["공개URL"])}">{html.escape(t["공개URL"])}</a> (로그인 없이 열림)</li>')
        경력.append("  </ul>")
    예정 = [t for t in 과제자료["과제"] if t.get("상태") == "예정"]
    if 예정:
        경력.append("  <h3>진행 예정</h3>")
        경력.append("  <ul>")
        경력 += [f'    <li>{t["번호"]}번 {html.escape(t["이름"])} — 완료 후 이 문서에 추가합니다.</li>' for t in 예정]
        경력.append("  </ul>")

    docx = 문서파일_이름()
    if docx:
        shutil.copyfile(사업장 / "문서" / docx, 출력 / "자료" / docx)
        내려받기 = f'      <a class="btn-main" href="자료/{html.escape(docx)}">Word 파일로 내려받기 ↓</a>'
    else:
        내려받기 = '      <span class="btn-sub">Word 파일은 node 장치/문서_docx.js 를 실행하면 만들어집니다</span>'

    페이지값 = {
        "{{이름}}": 값["{{이름}}"],
        "{{목표}}": 값["{{목표}}"],
        "{{한줄소개}}": 값["{{한줄소개}}"],
        "{{문서_내려받기}}": 내려받기,
        "{{이력서}}": "\n".join(이력),
        "{{자기소개서}}": "\n".join(소개),
        "{{경력기술서}}": "\n".join(경력),
        "{{연락처}}": 값["{{연락처}}"],
        "{{하단_안내}}": 값["{{하단_안내}}"],
    }
    페이지 = (장치 / "템플릿" / "문서.html.tmpl").read_text(encoding="utf-8")
    for 키, 내용 in 페이지값.items():
        페이지 = 페이지.replace(키, 내용)
    남은 = re.findall(r"\{\{[^}]+\}\}", 페이지)
    if 남은:
        raise SystemExit(f"[중단] 이력서 페이지에서 채우지 못한 자리: {sorted(set(남은))}")
    (출력 / "이력서.html").write_text(페이지, encoding="utf-8")
    print(f"[완료] {출력.name}/이력서.html" + (f", 자료/{docx}" if docx else ""))


def 이름표_문서(메타) -> str:
    return f"문서/{메타['이름']}_{메타['목표'].replace(' ', '')}_이력서_자기소개서_경력기술서.docx"


def 제출물만들기(설정, 메타, 정보, 숫자, 과제자료):
    """짧은 확인 방법과 제출문을 만든다(BRA-C11, C12, C20)."""
    폴더 = 사업장 / "제출물"
    폴더.mkdir(parents=True, exist_ok=True)
    미정 = "(배포 후 본문/사이트설정.json에 적으면 채워집니다)"
    제출URL = 설정.get("배포주소", "").strip() or 미정
    소스 = 설정.get("소스저장소", "").strip() or 미정
    다른URL = 설정.get("다른버전_주소", "").strip()
    다른이름 = 설정.get("다른버전_이름", "다른 버전")
    꼬리 = 정보["꼬리"]

    확인 = [
        "# 짧은 확인 방법",
        "",
        f"- **어디로 가나요**: {제출URL}",
        f"  - {메타['목표']} 지원용 사이트입니다. 계정 만들기·로그인·비밀번호 없이 새 시크릿 창에서 바로 열립니다.",
    ]
    if 다른URL:
        확인.append(f"  - {다른이름}은 첫 화면 맨 위 링크로 이어집니다: {다른URL}")
    확인 += [
        "",
        "- **세 단계 안에 무엇을 하나요**",
        "  1. 첫 화면에서 이름과 한 줄 소개를 읽습니다. 한 줄 소개에는 날짜가 들어 있습니다.",
        "  2. 첫 화면의 이동 단추로 `이야기 → 세 가지 능력 → 숫자 → 대표작` 순서로 내려갑니다.",
        "  3. 대표작 칸의 `논문 파일 내려받기`를 눌러 로그인 없이 파일이 열리는지 확인합니다.",
        "",
        "- **무엇이 보이면 통과인가요**",
        "  - 이야기: 군 복무 시기의 고난에서 시작해 2026년 8~9월에 다시 일어나고 지금에 이르는 흐름",
        "  - 세 가지 능력: 자기조절력·대인관계력·자기동기력 칸마다 날짜가 붙은 기록 인용과 출처",
        f"  - 숫자: {len(숫자)}개 칸 각각에 `출처:` 줄이 붙어 있음",
        "  - 대표작: 10번 논문 파일과, 13번 앱이 들어갈 점선 테두리의 빈자리",
        "",
        "- **안 될 때는 무엇이 보이나요**",
        "  - 로그인 화면이나 오류 페이지가 뜨면 통과가 아닙니다.",
        "  - 숫자 칸에 `출처:` 줄이 없는 항목이 있으면 통과가 아닙니다.",
        "",
        "## 문서와 장치는 어디에 있나요",
        "",
        "제출한 ZIP(`제출_문서와장치.zip`)을 풀면 폴더 네 개가 나옵니다. 비밀번호는 없습니다.",
        "",
        "| 폴더 | 내용 |",
        "|---|---|",
        f"| `문서/` | `{꼬리}_이력서.md`, `{꼬리}_자기소개서.md`, `{꼬리}_경력기술서.md` 3개와, 세 문서를 한 파일에 담은 Word 문서(`.docx`) |",
        "| `제출물/` | 이 짧은 확인 방법, 제출문(AI와 나의 판단 세 줄), 두 번 실행한 결과 비교(`재현성_확인.md`) |",
        "| `장치/` | 실행 파일 `build.py`, 돌리는 방법을 적은 `README.md`, 입력 파일, 마지막 실행 결과(`마지막결과/`) |",
        "| `본문/` | 장치가 읽는 자기소개 본문과 사이트 설정. 장치를 돌리려면 이 폴더가 함께 있어야 합니다 |",
        "",
        "장치를 돌리는 방법은 `장치/README.md`의 3단계에 있습니다. 같은 입력이면 같은 결과가 나옵니다.",
        "",
        "같은 폴더에서 두 번, 그리고 이 ZIP을 새 폴더에 풀어서 한 번, 총 세 번 실행해 5개 파일의 MD5 해시가 "
        "모두 같은 것을 확인한 기록은 `제출물/재현성_확인.md`에 있습니다.",
        "",
        f"소스: {소스}",
        "",
    ]
    (폴더 / "짧은_확인_방법.md").write_text("\n".join(확인) + "\n", encoding="utf-8")

    판단 = 읽기(본문폴더 / "AI와_나의_판단.json")
    글 = [
        "# 제출문",
        "",
        "## 제출 URL",
        "",
        f"- 결과물 HTTPS URL: {제출URL}",
        f"- 소스: {소스}",
        "",
        "## 제출 파일",
        "",
        f"- `{이름표_문서(메타)}` — 이력서·자기소개서·경력기술서를 한 파일에 담은 Word 문서",
        f"- `제출_문서와장치.zip` — 위 문서와 같은 내용의 MD 3개 + 장치(실행 소스·README·마지막 결과) + 본문 + 짧은 확인 방법·제출문·두 번 실행한 결과 비교",
        "",
        "## AI와 나의 판단 세 줄",
        "",
    ]
    제목표 = {
        "AI에게_맡긴_일": "AI에게 맡긴 일",
        "내가_직접_판단한_일": "내가 직접 판단한 일",
        "AI_제안을_따르지_않은_일": "AI 제안을 따르지 않은 일",
    }
    for 번호, 키 in enumerate(제목표, start=1):
        글.append(f"{번호}. **{제목표[키]}**: {판단['세줄'][키]}")
    글 += ["", "### 세부 근거", ""]
    for 키, 제목 in 제목표.items():
        글.append(f"**{제목}**")
        글.append("")
        for 항목 in 판단[키]:
            글.append(f"- {항목}")
        글.append("")
    과제수 = len(
        [t for t in 과제자료["과제"] if t.get("상태") != "예정" and 메타["track_id"] in t["트랙"]]
    )
    글 += [
        "## 완주 확인",
        "",
        "- 소설에서 뽑은 자기소개 본문이 사이트 가운데에 있고, 각색된 대화·묘사는 넣지 않았습니다.",
        "- 첫 화면에 이름과 “…한 사람”으로 끝나는 한 줄 소개가 있고, 그 안에 날짜가 있습니다.",
        f"- 숫자 칸 {len(숫자)}개에 모두 출처를 적었습니다.",
        "- 대표작 자리에 10번 논문 파일을 직접 올렸고, 13번 앱 자리를 비워 두었습니다.",
        f"- 과제 {과제수}개를 경력기술서에 능력별로 나눠 적었습니다.",
        "- 장치를 두 번 돌리고 새 폴더에서도 돌려 결과가 같은 것을 확인했습니다.",
        "- 제출물에 본인 이름과 공개하기로 한 연락 수단 외의 개인정보, 비밀번호·토큰·API 키는 없습니다.",
        "",
    ]
    (폴더 / "제출문.md").write_text("\n".join(글) + "\n", encoding="utf-8")
    print("[완료] 제출물/짧은_확인_방법.md, 제출물/제출문.md")


def 연락처_글자() -> str:
    연락 = 읽기(본문폴더 / "연락처.json")
    주소 = 연락.get("이메일", "").strip()
    return 주소 if 주소 else "(공개할 주소 미정 — 채워 주세요)"


def 문서만들기(메타, 정보, 과제자료, 숫자):
    """이력서·자기소개서·경력기술서를 만든다."""
    기본 = 읽기(본문폴더 / "이력_기본정보.json")
    이름 = 메타["이름"]
    목표 = 메타["목표"]
    문서폴더 = 사업장 / "문서"
    문서폴더.mkdir(parents=True, exist_ok=True)
    꼬리 = 정보["꼬리"]

    과제들 = [
        t
        for t in sorted(과제자료["과제"], key=lambda x: x["번호"])
        if 메타["track_id"] in t["트랙"] and t.get("상태") != "예정"
    ]

    # 이력서
    줄 = [f"# 이력서 — {이름}", "", f"**지원 직무**: {목표}", f"**연락처**: {연락처_글자()}", ""]
    줄 += ["## 교육", ""]
    for e in 기본["교육"]:
        줄.append(f"- **{e['기간']}** {e['이름']} — {e['내용']}")
    줄 += ["", "## 경력", ""]
    for m in 기본["군경력"]:
        줄.append(f"- **{m['기간']}** {m['소속']} — {m['구분']}")
    줄 += ["", "## 프로젝트 (교육과정 과제)", ""]
    for t in 과제들:
        링크 = f" — {t['공개URL']}" if t["공개URL"] else ""
        줄.append(f"- **{t['번호']}번 {t['이름']}**{링크}")
    줄 += ["", "## 자격", ""]
    for c in 기본["자격증"]:
        줄.append(f"- {c['이름']} ({c['상태']})")
    줄 += ["", "## 기록", ""]
    for n in 숫자:
        보조 = f" ({n['보조']})" if n["보조"] else ""
        줄.append(f"- {n['이름']}: {n['값']}{보조} — 출처: {n['출처']}")
    (문서폴더 / f"{꼬리}_이력서.md").write_text("\n".join(줄) + "\n", encoding="utf-8")

    # 자기소개서
    원문 = (본문폴더 / "자기소개_본문.md").read_text(encoding="utf-8")
    몸통 = 원문.split("---", 2)[-1].strip()
    장면들 = [s for s in 읽기(승인문장 / "능력별_장면.json")["장면"] if s.get("승인")]
    글 = [f"# 자기소개서 — {이름} ({목표} 지원)", "", 몸통, "", 메타["마무리_목표문"], ""]
    글 += ["---", "", "## 기록으로 확인되는 세 가지 능력", ""]
    for 능력 in 능력순서:
        글.append(f"### {능력}")
        글.append(메타["능력_해석"][능력])
        글.append("")
        for s in [x for x in 장면들 if x["능력"] == 능력]:
            글.append(f"> “{s['인용']}” — {s['출처']}")
            글.append("")
    (문서폴더 / f"{꼬리}_자기소개서.md").write_text("\n".join(글) + "\n", encoding="utf-8")

    # 경력기술서
    경력 = [
        f"# 경력기술서 — {이름} ({목표} 지원)",
        "",
        "과제마다 세 가지 능력 중 어디에 해당하는지와 상황·행동·결과를 적었습니다.",
        "",
    ]
    for t in 과제들:
        경력.append(f"## {t['번호']}번 — {t['이름']}")
        경력.append("")
        경력.append(f"- **해당 능력**: {t['능력']}")
        경력.append(f"- **상황**: {t['상황']}")
        경력.append(f"- **행동**: {t['행동']}")
        경력.append(f"- **결과**: {t['결과']}")
        if t["공개URL"]:
            경력.append(f"- **확인**: {t['공개URL']} (로그인 없이 열림)")
        경력.append("")
    예정 = [t for t in 과제자료["과제"] if t.get("상태") == "예정"]
    if 예정:
        경력.append("## 진행 예정")
        경력.append("")
        for t in 예정:
            경력.append(f"- {t['번호']}번 {t['이름']} — 완료 후 이 문서에 추가합니다.")
        경력.append("")
    (문서폴더 / f"{꼬리}_경력기술서.md").write_text("\n".join(경력) + "\n", encoding="utf-8")
    print(f"[완료] 문서/{꼬리}_이력서.md, {꼬리}_자기소개서.md, {꼬리}_경력기술서.md")


def 만들기():
    설정 = 읽기(본문폴더 / "사이트설정.json")
    트랙 = 설정.get("트랙")
    if 트랙 not in 트랙정보:
        raise SystemExit(f"[중단] 사이트설정.json 의 트랙 값은 {sorted(트랙정보)} 중 하나여야 합니다.")
    정보 = 트랙정보[트랙]
    메타 = 읽기(본문폴더 / 정보["메타파일"])

    과제자료 = 읽기(입력 / "과제목록.json")
    리추얼 = 리추얼세기()
    숫자 = 숫자모으기(리추얼, 과제자료)

    if 리추얼 is None:
        print("[안내] 입력/리추얼기록.json 이 없어 리추얼 숫자는 비워 두고 만들었습니다.")

    기록일수문구 = f"{리추얼['기록일수']}일" if 리추얼 else "리추얼"
    첫화면_보조문 = 메타["첫화면_보조문"].replace("{기록일수}", 기록일수문구)
    동료자료 = 동료의_말_읽기()

    값 = {
        "{{이름}}": html.escape(메타["이름"]),
        "{{목표}}": html.escape(메타["목표"]),
        "{{한줄소개}}": html.escape(메타["한줄소개"]),
        "{{한줄소개_출처}}": html.escape(메타["한줄소개_출처"]),
        "{{첫화면_보조문}}": html.escape(첫화면_보조문),
        "{{다른버전_링크}}": 다른버전_html(설정),
        "{{연락처_칩}}": 연락처_칩_html(),
        "{{이야기_본문}}": 본문_html() + f"\n    <p>{html.escape(메타['마무리_목표문'])}</p>",
        "{{능력_카드}}": 능력_html(메타),
        "{{동료의_말_제목}}": html.escape(동료자료["제목"]) if 동료자료 else "함께 일한 동료가 적어 준 말",
        "{{동료의_말}}": 동료의_말_html(동료자료) if 동료자료 else "",
        "{{동료의_말_안내}}": (
            "리추얼 기록의 “동료가 말해 준 내 장점” 칸에 동료들이 직접 적어 준 문장을 날짜와 함께 옮긴 것입니다. "
            "내가 쓴 말이 아니라 같이 일한 사람이 쓴 말이고, 동료 이름은 넣지 않았습니다."
        ),
        "{{숫자_칸}}": 숫자_html(숫자),
        "{{숫자_안내}}": "이 칸의 숫자는 기록 파일에서 그대로 센 것입니다. 새 기록을 넣고 장치를 한 번 돌리면 다시 계산됩니다.",
        "{{대표작}}": 대표작_html(메타),
        "{{과제_목록}}": 과제목록_html(과제자료, 메타["track_id"]),
        "{{연락처}}": 연락처_html(),
        "{{하단_안내}}": (
            "이 페이지는 장치(build.py)가 리추얼 기록·과제 목록·출석 파일에서 다시 만든 것입니다. "
            "본인 이름과 위 연락 수단 외의 개인정보는 넣지 않았고, 동료는 모두 \"동료\"로만 적었습니다."
        ),
        "{{강조색}}": 정보["강조색"],
        "{{강조색_연한}}": 정보["강조색_연한"],
        "{{강조색_다크}}": 정보["강조색_다크"],
    }
    문서 = 템플릿파일.read_text(encoding="utf-8")
    for 키, 내용 in 값.items():
        문서 = 문서.replace(키, 내용)

    남은 = re.findall(r"\{\{[^}]+\}\}", 문서)
    if 남은:
        raise SystemExit(f"[중단] 채우지 못한 자리: {sorted(set(남은))}")

    출력 = 사업장 / 정보["사이트폴더"]
    (출력 / "자료").mkdir(parents=True, exist_ok=True)
    (출력 / "index.html").write_text(문서, encoding="utf-8")

    스타일 = (장치 / "템플릿" / "style.css.tmpl").read_text(encoding="utf-8")
    for 키 in ("{{강조색}}", "{{강조색_연한}}", "{{강조색_다크}}"):
        스타일 = 스타일.replace(키, 값[키])
    (출력 / "자료" / "style.css").write_text(스타일, encoding="utf-8")
    print(f"[완료] {출력.name}/index.html, 자료/style.css")

    문서페이지만들기(메타, 정보, 과제자료, 숫자, 출력, 값)

    문서만들기(메타, 정보, 과제자료, 숫자)

    마지막결과.mkdir(parents=True, exist_ok=True)
    (마지막결과 / "숫자.json").write_text(
        json.dumps({"숫자": 숫자, "리추얼집계": 리추얼}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    후보 = ["# 능력별 문단 후보 (승인된 문장만)", ""]
    for 장면 in 읽기(승인문장 / "능력별_장면.json")["장면"]:
        표시 = "승인" if 장면.get("승인") else "보류"
        후보.append(
            f"- [{표시}] **{장면['능력']}** {장면['날짜']} {장면['칸']} — "
            f"“{장면['인용']}” ({장면['출처']})"
        )
    (마지막결과 / "문단후보.md").write_text("\n".join(후보) + "\n", encoding="utf-8")
    print("[완료] 마지막결과/숫자.json, 마지막결과/문단후보.md")

    제출물만들기(설정, 메타, 정보, 숫자, 과제자료)


if __name__ == "__main__":
    sys.exit(만들기())
