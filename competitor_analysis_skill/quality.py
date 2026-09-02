from dataclasses import dataclass
from pathlib import Path


@dataclass
class QualityResult:
    status: str
    reason: str


def assess_image(path: Path) -> QualityResult:
    if not path.exists():
        return QualityResult("rejected", "文件不存在")
    data = path.read_bytes()[:16]
    signatures = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF8")
    if not data.startswith(signatures):
        return QualityResult("rejected", "不是可识别的图片文件")
    if path.stat().st_size < 32:
        return QualityResult("rejected", "图片文件过小")
    return QualityResult("accepted", "格式与文件大小通过基础检查")

