import os
import re
import tempfile
import zipfile
from io import BytesIO
from typing import List, Dict, Tuple

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

API_TOKEN = "8496124038:AAF1p5RjSwtZM1NHrXUuCLvlWZ5ZDPRw8xU"  # ضع توكنك
ALLOWED_USER_IDS = {8276803480}  # معرفات المستخدمين المسموح لهم

# حدود الأمان
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_ZIP_FILES = 300
MAX_LINE_LENGTH = 20000
LONG_STRING_THRESHOLD = 1000

# أنماط خطرة
DANGEROUS_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("eval", re.compile(r"\beval\s*\(", re.IGNORECASE)),
    ("assert", re.compile(r"\bassert\s*\(", re.IGNORECASE)),
    ("create_function", re.compile(r"\bcreate_function\s*\(", re.IGNORECASE)),
    ("exec", re.compile(r"\bexec\s*\(", re.IGNORECASE)),
    ("shell_exec", re.compile(r"\bshell_exec\s*\(", re.IGNORECASE)),
    ("system", re.compile(r"\bsystem\s*\(", re.IGNORECASE)),
    ("passthru", re.compile(r"\bpassthru\s*\(", re.IGNORECASE)),
    ("popen", re.compile(r"\bpopen\s*\(", re.IGNORECASE)),
    ("proc_open", re.compile(r"\bproc_open\s*\(", re.IGNORECASE)),
    ("curl_exec", re.compile(r"\bcurl_exec\s*\(", re.IGNORECASE)),
    ("curl_multi_exec", re.compile(r"\bcurl_multi_exec\s*\(", re.IGNORECASE)),
    ("fsockopen", re.compile(r"\bfsockopen\s*\(", re.IGNORECASE)),
    ("pfsockopen", re.compile(r"\bpfsockopen\s*\(", re.IGNORECASE)),
    ("file_put_contents", re.compile(r"\bfile_put_contents\s*\(", re.IGNORECASE)),
    ("fopen", re.compile(r"\bfopen\s*\(", re.IGNORECASE)),
    ("unlink", re.compile(r"\bunlink\s*\(", re.IGNORECASE)),
    ("rename", re.compile(r"\brename\s*\(", re.IGNORECASE)),
    ("base64_decode", re.compile(r"\bbase64_decode\s*\(", re.IGNORECASE)),
    ("gzinflate", re.compile(r"\bgzinflate\s*\(", re.IGNORECASE)),
    ("str_rot13", re.compile(r"\bstr_rot13\s*\(", re.IGNORECASE)),
    ("dynamic_include", re.compile(r"\b(include|require|include_once|require_once)\s*\(\s*\$[A-Za-z_]\w*", re.IGNORECASE)),
    ("user_input_in_exec", re.compile(r"(eval|system|exec|shell_exec|passthru)\s*\(\s*\$_(GET|POST|REQUEST)", re.IGNORECASE)),
    ("variable_function_call", re.compile(r"\$\w+\s*\(", re.IGNORECASE)),
]

def is_php_file(name: str) -> bool:
    return name.lower().endswith(".php")

def safe_join(base: str, *paths: str) -> str:
    final_path = os.path.abspath(os.path.join(base, *paths))
    if not final_path.startswith(os.path.abspath(base) + os.sep):
        raise ValueError("Unsafe path detected.")
    return final_path

def extract_zip_safely(zip_bytes: bytes, temp_dir: str) -> List[str]:
    php_files = []
    with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
        count = 0
        for name in z.namelist():
            if name.endswith("/") or name.strip() == "":
                continue
            target_path = safe_join(temp_dir, name)
            with z.open(name) as src, open(target_path, "wb") as dst:
                data = src.read()
                if len(data) > MAX_FILE_SIZE_BYTES:
                    continue
                dst.write(data)
            if is_php_file(name):
                php_files.append(target_path)
                count += 1
                if count >= MAX_ZIP_FILES:
                    break
    return php_files

def scan_php_content(content: str) -> Dict[str, List[str]]:
    findings: Dict[str, List[str]] = {}
    lines = [line[:MAX_LINE_LENGTH] if len(line) > MAX_LINE_LENGTH else line for line in content.splitlines()]

    for label, pattern in DANGEROUS_PATTERNS:
        matches = []
        for i, line in enumerate(lines, start=1):
            if pattern.search(line):
                snippet = line.strip().replace("\t", " ")[:300]
                matches.append(f"Line {i}: {snippet}")
                if len(matches) >= 30:
                    matches.append("...more matches truncated...")
                    break
        if matches:
            findings[label] = matches

long_lines = []
    for i, line in enumerate(lines, start=1):
        if len(line) > LONG_STRING_THRESHOLD:
            long_lines.append(f"Line {i} (len {len(line)}): {line[:120]}...")
            if len(long_lines) >= 30:
                long_lines.append("...more long lines truncated...")
                break
    if long_lines:
        findings["long_strings"] = long_lines

    return findings

def format_report(file_path: str, findings: Dict[str, List[str]]) -> str:
    name = os.path.basename(file_path)
    if not findings:
        return f"✅ لا توجد أنماط خطرة واضحة: {name}"
    parts = [f"⚠️ نتائج الفحص: {name}"]
    for label, matches in findings.items():
        parts.append(f"- {label}: {len(matches)} match(es)")
        for m in matches:
            parts.append(f"  • {m}")
    return "\n".join(parts)

def split_message(text: str, limit: int = 3900) -> List[str]:
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks

def authorized(update: Update) -> bool:
    user_id = update.effective_user.id if update.effective_user else None
    return user_id in ALLOWED_USER_IDS

# ====================== Handlers ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        await update.message.reply_text("🚫 غير مسموح.")
        return
    await update.message.reply_text("أرسل ملف PHP (index.php) أو ZIP يحتوي على ملفات PHP وسأفحصها 🔍")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        await update.message.reply_text("🚫 غير مسموح.")
        return

    doc = update.message.document
    if not doc:
        await update.message.reply_text("❌ لم يتم استلام أي ملف.")
        return

    if doc.file_size and doc.file_size > MAX_FILE_SIZE_BYTES:
        await update.message.reply_text("❌ الملف كبير جدًا. أرسل ملفًا أصغر من 10MB.")
        return

    file_name = (doc.file_name or "file").strip()
    mime = (doc.mime_type or "").lower()
    is_zip = file_name.lower().endswith(".zip") or "zip" in mime
    is_php = is_php_file(file_name) or ("php" in mime and not is_zip)

    if not (is_zip or is_php):
        await update.message.reply_text("❌ أنواع مسموح بها فقط: .php أو .zip")
        return

    try:
        tg_file = await doc.get_file()
        buf = BytesIO()
        await tg_file.download_to_memory(out=buf)
        data = buf.getvalue()
    except Exception:
        await update.message.reply_text("❌ فشل تنزيل الملف.")
        return

    if len(data) > MAX_FILE_SIZE_BYTES:
        await update.message.reply_text("❌ الملف أكبر من الحد المسموح.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        if is_zip:
            try:
                php_files = extract_zip_safely(data, tmp)
            except zipfile.BadZipFile:
                await update.message.reply_text("❌ أرشيف ZIP غير صالح.")
                return
            except ValueError:
                await update.message.reply_text("❌ تم اكتشاف مسار غير آمن داخل ZIP.")
                return

            if not php_files:
                await update.message.reply_text("ℹ️ لا توجد ملفات PHP صالحة داخل الأرشيف.")
                return

            reports = []
            for path in php_files:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    findings = scan_php_content(content)
                    reports.append(format_report(path, findings))
                except Exception:
                    reports.append(f"❌ خطأ في قراءة: {os.path.basename(path)}")

            output = "\n\n".join(reports)
            for chunk in split_message(output):
                await update.message.reply_text(chunk)

elif is_php:
            temp_path = os.path.join(tmp, os.path.basename(file_name))
            with open(temp_path, "wb") as f:
                f.write(data)
            try:
                with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                findings = scan_php_content(content)
                report = format_report(temp_path, findings)
            except Exception:
                report = "❌ خطأ في قراءة الملف."
            for chunk in split_message(report):
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text("❌ نوع ملف غير مدعوم.")

# ====================== Main ======================

def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()

if name == "main":
    main()
