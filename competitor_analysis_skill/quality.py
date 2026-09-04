from dataclasses import dataclass
from pathlib import Path
import hashlib

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:  # pragma: no cover
    Image = None

MIN_IMAGE_WIDTH = 240
MIN_IMAGE_HEIGHT = 240
MIN_FILE_SIZE = 256

@dataclass
class QualityResult:
    status: str
    reason: str
    width: int = 0
    height: int = 0
    format: str = ""
    content_sha256: str = ""

def assess_image(path: Path) -> QualityResult:
    path = Path(path)
    if not path.exists() or not path.is_file():
        return QualityResult("missing", "文件不存在或不是普通文件")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return QualityResult("rejected", "扩展名不是支持的图片格式")
    if path.stat().st_size < MIN_FILE_SIZE:
        return QualityResult("rejected", "图片文件为空或明显过小")
    if Image is None:
        return QualityResult("rejected", "缺少 Pillow 图片解码依赖")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height, fmt = image.width, image.height, image.format or ""
        expected = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".gif": "GIF", ".webp": "WEBP"}[path.suffix.lower()]
        if fmt.upper() != expected:
            return QualityResult("rejected", "实际图片格式与扩展名不一致", width, height, fmt)
        if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
            return QualityResult("rejected", f"图片尺寸过小，至少需要 {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}", width, height, fmt)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return QualityResult("accepted", "真实解码、格式和尺寸通过", width, height, fmt, digest)
    except Exception as exc:
        return QualityResult("rejected", f"图片无法解码或已损坏: {exc}")
