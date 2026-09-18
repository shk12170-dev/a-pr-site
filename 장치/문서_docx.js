// 이력서·자기소개서·경력기술서를 Word 문서 한 파일로 만든다.
// build.py와 같은 데이터 파일(본문/, 장치/입력/, 장치/승인문장/, 장치/마지막결과/)만 읽는다.
// 사용법: node 장치/문서_docx.js   (먼저 python 장치/build.py 를 실행해 마지막결과/숫자.json 을 갱신)

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, ShadingType, BorderStyle,
  LevelFormat, PageBreak, Footer, PageNumber,
} = require("docx");

const 장치 = __dirname;
const 사업장 = path.dirname(장치);
const 본문 = path.join(사업장, "본문");
const 읽기 = (p) => JSON.parse(fs.readFileSync(p, "utf-8"));

const 설정 = 읽기(path.join(본문, "사이트설정.json"));
const 메타파일 = { backend: "트랙_백엔드.json", cloud: "트랙_클라우드.json" }[설정.트랙];
const 메타 = 읽기(path.join(본문, 메타파일));
const 기본 = 읽기(path.join(본문, "이력_기본정보.json"));
const 연락 = 읽기(path.join(본문, "연락처.json"));
const 과제자료 = 읽기(path.join(장치, "입력", "과제목록.json"));
const 장면들 = 읽기(path.join(장치, "승인문장", "능력별_장면.json")).장면.filter((s) => s.승인);
const 숫자 = 읽기(path.join(장치, "마지막결과", "숫자.json")).숫자;
const 본문원문 = fs.readFileSync(path.join(본문, "자기소개_본문.md"), "utf-8");
const 몸통 = 본문원문.split("---").slice(1).join("---").trim();
const 문단들 = 몸통.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);

const 능력순서 = ["자기조절력", "대인관계력", "자기동기력"];
const 글꼴 = "Malgun Gothic";
const 강조 = "0F6F8C";
const 폭 = 9638; // A4(11906) - 좌우 여백 1134 × 2
const 칸왼쪽 = 1900;
const 칸오른쪽 = 폭 - 칸왼쪽;
const 테두리 = { style: BorderStyle.SINGLE, size: 4, color: "D5DBE1" };
const 테두리들 = { top: 테두리, bottom: 테두리, left: 테두리, right: 테두리 };

const 과제들 = 과제자료.과제
  .filter((t) => t.트랙.includes(메타.track_id) && t.상태 !== "예정")
  .sort((a, b) => a.번호 - b.번호);

function 글(text, opts = {}) {
  return new TextRun({ text, font: 글꼴, ...opts });
}
function 문단(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120, line: 320 }, children: [글(text, opts)], ...(opts.para || {}) });
}
function 제목1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [글(text)] });
}
function 제목2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [글(text)] });
}
function 글머리(text) {
  return new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [글(text)] });
}
function 굵은글머리(굵게, 나머지) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [글(굵게, { bold: true }), 글(나머지)],
  });
}
function 칸(text, { 머리 = false, 너비 }) {
  return new TableCell({
    borders: 테두리들,
    width: { size: 너비, type: WidthType.DXA },
    shading: 머리 ? { fill: "EAF4F8", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [글(text, { bold: 머리, size: 20 })] })],
  });
}
function 이단표(행들) {
  return new Table({
    width: { size: 폭, type: WidthType.DXA },
    columnWidths: [칸왼쪽, 칸오른쪽],
    rows: 행들.map(([왼, 오]) => new TableRow({
      children: [칸(왼, { 머리: true, 너비: 칸왼쪽 }), 칸(오, { 너비: 칸오른쪽 })],
    })),
  });
}
function 간격() {
  return new Paragraph({ spacing: { after: 120 }, children: [] });
}

// ── 이력서 ──
const 이력서 = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [글(`이력서 — ${메타.이름}`)] }),
  이단표([
    ["이름", 메타.이름],
    ["지원 직무", 메타.목표],
    ["연락처", 연락.이메일 || "(공개할 주소 미정)"],
    ["소개 사이트", 설정.배포주소 || "(배포 후 기재)"],
  ]),
  제목1("교육"),
  ...기본.교육.map((e) => 굵은글머리(`${e.기간}  ${e.이름}`, ` — ${e.내용}`)),
  제목1("경력"),
  ...기본.군경력.map((m) => 굵은글머리(`${m.기간}  ${m.소속}`, ` — ${m.구분}`)),
  제목1("프로젝트 (교육과정 과제)"),
  ...과제들.map((t) => 굵은글머리(`${t.번호}번 ${t.이름}`, t.공개URL ? ` — ${t.공개URL}` : "")),
  제목1("자격"),
  ...기본.자격증.map((c) => 글머리(`${c.이름} (${c.상태})`)),
  제목1("기록으로 본 숫자"),
  new Table({
    width: { size: 폭, type: WidthType.DXA },
    columnWidths: [2800, 1900, 4938],
    rows: [
      new TableRow({ children: [칸("항목", { 머리: true, 너비: 2800 }), 칸("값", { 머리: true, 너비: 1900 }), 칸("출처", { 머리: true, 너비: 4938 })] }),
      ...숫자.map((n) => new TableRow({
        children: [
          칸(n.보조 ? `${n.이름} (${n.보조})` : n.이름, { 너비: 2800 }),
          칸(n.값, { 너비: 1900 }),
          칸(n.출처, { 너비: 4938 }),
        ],
      })),
    ],
  }),
];

// ── 자기소개서 ──
const 자기소개서 = [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.TITLE, children: [글(`자기소개서 — ${메타.이름}`)] }),
  문단(`${메타.목표} 지원`, { color: "5B6472" }),
  ...문단들.map((p) => 문단(p)),
  문단(메타.마무리_목표문),
  제목1("기록으로 확인되는 세 가지 능력"),
  ...능력순서.flatMap((능력) => [
    제목2(능력),
    문단(메타.능력_해석[능력]),
    ...장면들.filter((s) => s.능력 === 능력).map((s) => new Paragraph({
      spacing: { after: 100 },
      indent: { left: 360 },
      border: { left: { style: BorderStyle.SINGLE, size: 18, color: 강조, space: 8 } },
      children: [
        글(`${s.날짜} · ${s.칸}  `, { bold: true, color: 강조, size: 19 }),
        글(`“${s.인용}”`, { size: 20 }),
        글(`  — ${s.출처}`, { color: "5B6472", size: 18 }),
      ],
    })),
  ]),
];

// ── 경력기술서 ──
const 경력기술서 = [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.TITLE, children: [글(`경력기술서 — ${메타.이름}`)] }),
  문단("과제마다 세 가지 능력 중 어디에 해당하는지와 상황·행동·결과를 적었습니다.", { color: "5B6472" }),
  ...과제들.flatMap((t) => [
    제목2(`${t.번호}번 — ${t.이름}`),
    이단표([
      ["해당 능력", t.능력],
      ["상황", t.상황],
      ["행동", t.행동],
      ["결과", t.결과],
      ...(t.공개URL ? [["확인", `${t.공개URL} (로그인 없이 열림)`]] : []),
    ]),
    간격(),
  ]),
  제목2("진행 예정"),
  ...과제자료.과제.filter((t) => t.상태 === "예정").map((t) => 글머리(`${t.번호}번 ${t.이름} — 완료 후 추가합니다.`)),
];

const 문서 = new Document({
  creator: 메타.이름,
  title: `${메타.이름} 이력서·자기소개서·경력기술서`,
  styles: {
    default: { document: { run: { font: 글꼴, size: 21 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 36, bold: true, font: 글꼴, color: "16191D" }, paragraph: { spacing: { after: 200 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: 글꼴, color: 강조 }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, font: 글꼴, color: "16191D" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }],
  },
  sections: [{
    properties: { page: { margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 } } },
    footers: {
      default: new Footer({
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [글("- ", { size: 18, color: "8A94A3" }), new TextRun({ children: [PageNumber.CURRENT], font: 글꼴, size: 18, color: "8A94A3" }), 글(" -", { size: 18, color: "8A94A3" })] })],
      }),
    },
    children: [...이력서, ...자기소개서, ...경력기술서],
  }],
});

const 출력 = path.join(사업장, "문서", `${메타.이름}_${메타.목표.replace(/ /g, "")}_이력서_자기소개서_경력기술서.docx`);
Packer.toBuffer(문서).then((buf) => {
  fs.writeFileSync(출력, buf);
  console.log(`[완료] 문서/${path.basename(출력)}`);
});
