#!/usr/bin/env python3
"""
generate_html_report.py — Threat-scan-security HTML 리포트 생성기 (v2.2.0+)

bilingual JSON 스캔 리포트를 입력받아, 보안담당자용 정적 HTML 리포트를 생성한다.
뷰어(security-template.html)의 exportHTML() 동작을 브라우저·LLM 없이 1:1 재현한다:
RAW 템플릿에 ① export 스타일(헤더 축소) ② JSON 데이터블록 ③ boot script 를 주입한다.
열었을 때 템플릿 내장 JS가 boot script가 심은 JSON으로 렌더하므로 헤더(EN/KO+프린트)·
푸터(버전/Author/Org/모델/생성일)·도넛 차트가 자동 구성된다.

표준 라이브러리만 사용. 외부 네트워크·의존성 없음. 동일 입력 → 동일 출력(결정론).

사용법:
  python3 generate_html_report.py <report.json> [--lang ko|en]
      [--profile security] [--template <path>] [--out <path>]
"""
import argparse
import json
import os
import sys

# 향후 확장: it-staff / dev / advanced 프로파일 → 각 템플릿 파일 매핑
PROFILE_TEMPLATES = {
    "security": "security-template.html",
}

# 스크립트(scripts/) 기준 dictionary 디렉토리. 배포(dist) 구조에서는 references/dictionary.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_template(profile, template_arg):
    """--template 우선, 없으면 --profile → dictionary/<template>. 후보 경로를 차례로 탐색."""
    if template_arg:
        if not os.path.isfile(template_arg):
            sys.exit("[ERROR] 템플릿 파일을 찾을 수 없습니다: %s" % template_arg)
        return template_arg

    if profile not in PROFILE_TEMPLATES:
        sys.exit("[ERROR] 알 수 없는 프로파일 '%s'. 사용 가능: %s"
                 % (profile, ", ".join(sorted(PROFILE_TEMPLATES))))
    fname = PROFILE_TEMPLATES[profile]

    # 플러그인 환경(CLAUDE_PLUGIN_ROOT) → repo(scripts/) → dist(references/scripts/) 순으로 탐색
    candidates = []
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        candidates.append(os.path.join(plugin_root, "dictionary", fname))
    candidates += [
        os.path.join(_SCRIPT_DIR, "..", "dictionary", fname),
        os.path.join(_SCRIPT_DIR, "..", "..", "dictionary", fname),
        os.path.join(_SCRIPT_DIR, fname),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.normpath(c)
    sys.exit("[ERROR] 프로파일 '%s' 템플릿(%s)을 찾을 수 없습니다. 탐색 경로:\n  %s"
             % (profile, fname, "\n  ".join(os.path.normpath(c) for c in candidates)))


def build_data_block(report):
    """exportHTML과 동일: 컴팩트 JSON + '<' → '\\u003C'(HTML 파서가 </script>를 못 보게)."""
    data = dict(report)
    data.pop("_filename", None)
    # JS JSON.stringify 기본값과 동일한 컴팩트 형식(공백 없음), 한글 등 유니코드 원형 유지
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    data_json = data_json.replace("<", "\\u003C")
    return ('<script id="__TSS__" type="application/json">\n'
            + data_json + "\n</script>")


def build_boot_script(json_filename, lang):
    """exportHTML의 boot script 1:1 재현. JS 문자열 리터럴용으로 파일명 이스케이프."""
    safe_filename = json_filename.replace("\\", "\\\\").replace('"', '\\"')
    return (
        "<script>\n"
        "(function(){\n"
        '  var _D=JSON.parse(document.getElementById("__TSS__").textContent);\n'
        '  _D._filename="' + safe_filename + '";\n'
        '  currentLang="' + lang + '";\n'
        "  function _init(){\n"
        "    reports=[_D]; currentReportIndex=0;\n"
        '    document.querySelectorAll(".lang-btn").forEach(function(b){\n'
        '      b.classList.toggle("active",b.dataset.lang===currentLang);\n'
        "    });\n"
        "    renderReport(reports[0]); updateNav();\n"
        "  }\n"
        '  if(document.readyState==="loading")\n'
        '    document.addEventListener("DOMContentLoaded",_init);\n'
        "  else _init();\n"
        "})();\n"
        "</script>"
    )


def render_html(template_html, report, json_filename, lang):
    """RAW 템플릿에 스타일/데이터블록/boot script 주입. exportHTML과 동일한 삽입 위치."""
    export_style = ('<style id="__tss_ex__">'
                    "#exportBtn,.upload-btn,.nav-controls{display:none!important}"
                    "</style>")
    data_block = build_data_block(report)
    boot_script = build_boot_script(json_filename, lang)

    html = template_html

    # export 스타일: 첫 </head> 앞
    head_close = html.find("</head>")
    if head_close != -1:
        html = html[:head_close] + export_style + "\n</head>" + html[head_close + len("</head>"):]

    # 데이터블록 + boot script: 마지막 </body> 앞
    body_close = html.rfind("</body>")
    if body_close == -1:
        body_close = html.rfind("</BODY>")
    if body_close == -1:
        html = html + "\n" + data_block + "\n" + boot_script
    else:
        html = html[:body_close] + data_block + "\n" + boot_script + "\n</body>"
    return html


def main(argv=None):
    p = argparse.ArgumentParser(
        description="bilingual JSON 스캔 리포트 → 정적 HTML 리포트 생성")
    p.add_argument("report", help="입력 JSON 리포트 경로")
    p.add_argument("--lang", choices=["ko", "en"], default="ko",
                   help="리포트 표시 언어 (기본 ko)")
    p.add_argument("--profile", default="security",
                   help="템플릿 프로파일 (기본 security). 향후 it-staff/dev/advanced")
    p.add_argument("--template", default=None,
                   help="템플릿 파일 직접 지정 (--profile 무시)")
    p.add_argument("--out", default=None,
                   help="출력 HTML 경로 (기본: 입력과 같은 디렉토리의 <basename>.html)")
    args = p.parse_args(argv)

    if not os.path.isfile(args.report):
        sys.exit("[ERROR] 입력 JSON을 찾을 수 없습니다: %s" % args.report)

    with open(args.report, "r", encoding="utf-8") as f:
        try:
            report = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit("[ERROR] JSON 파싱 실패: %s" % e)

    template_path = resolve_template(args.profile, args.template)
    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    json_basename = os.path.basename(args.report)
    out_path = args.out
    if not out_path:
        base = os.path.splitext(args.report)[0]
        out_path = base + ".html"

    html = render_html(template_html, report, json_basename, args.lang)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 오케스트레이터/사용자 안내용 (stdout)
    print("[OK] HTML 리포트 생성: %s (lang=%s, profile=%s, template=%s)"
          % (out_path, args.lang, args.profile, os.path.basename(template_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
