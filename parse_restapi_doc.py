import json
import re
from pathlib import Path
from typing import Dict


def parse_mapping(doc_path: Path) -> Dict[str, str]:
    # Kiwoom doc is CP949/EUC-KR encoded; fall back to default if needed
    content = doc_path.read_bytes()
    for enc in ("cp949", "euc-kr", "utf-8", "utf-8-sig"):
        try:
            text = content.decode(enc)
            break
        except Exception:
            continue
    else:
        raise RuntimeError("Failed to decode restapi.txt; unsupported encoding")

    mapping: Dict[str, str] = {}
    current_id: str | None = None
    api_id_re = re.compile(r"^\s*API ID\s+([A-Za-z0-9]+)\s*$")
    url_re = re.compile(r"^\s*URL\s+(/\S+)\s*$")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        m_id = api_id_re.match(line)
        if m_id:
            current_id = m_id.group(1)
            continue
        m_url = url_re.match(line)
        if m_url and current_id:
            mapping[current_id] = m_url.group(1)
            # do not reset current_id to keep last until next API ID; a section may include multiple URLs
            # but usually first URL is the request endpoint we need
    return mapping


def main() -> None:
    doc_path = Path("restapi.txt")
    if not doc_path.exists():
        raise SystemExit("restapi.txt not found in current directory")
    mapping = parse_mapping(doc_path)
    out_path = Path("restapi_map.json")
    out_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} with {len(mapping)} entries")


if __name__ == "__main__":
    main()

