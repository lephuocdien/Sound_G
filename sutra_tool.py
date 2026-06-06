#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool quản lý SutraDatabase.remote.json — thêm / chèn / xoá / đổi bài kinh.
Quy ước: id = vị trí (1-based) trong danh sách. Mọi thao tác tự "resequence"
=> id luôn liền mạch 1..N, khỏi sửa tay.

Tự backup ra file .bak trước khi ghi.

Cách dùng (chạy trong thư mục chứa file json, hoặc thêm --file <path>):

  # Xem danh sách
  python3 sutra_tool.py list

  # Chèn 1 bài vào vị trí 83 (mọi bài >=83 tự dời xuống)
  python3 sutra_tool.py insert --at 83 \
      --title "49 và 53 đại hạn, ai cũng sợ" \
      --teacher "Đạt Lai Lạt Ma" \
      --url "https://.../DatLaiLatMa/49_va_53_dai_han_ai_cung_so.mp3"

  # Thêm 1 bài vào cuối
  python3 sutra_tool.py add --title "..." --teacher "..." --url "..."

  # Xoá bài id 83 (các bài dưới tự dời lên)
  python3 sutra_tool.py delete --id 83

  # Đánh lại id 1..N theo thứ tự hiện tại
  python3 sutra_tool.py renumber

  # Đổi field 1 bài (chỉ field nào truyền mới đổi)
  python3 sutra_tool.py edit --id 83 --title "Tên mới"

  # Đổi file khác (vd nhạc thiền)
  python3 sutra_tool.py list --file SutraDatabaseNhacThien.remote.json
"""

import argparse
import json
import os
import shutil
import sys

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "SutraDatabase.remote.json")

# Thứ tự field trong mỗi entry (giữ giống file gốc)
ENTRY_KEYS = ["id", "title", "teacher", "audioUrl", "durationSeconds"]


def load(path):
    if not os.path.exists(path):
        sys.exit(f"[LỖI] Không thấy file: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "sutras" not in data or not isinstance(data["sutras"], list):
        sys.exit("[LỖI] File không có mảng 'sutras'.")
    return data


def save(path, data):
    if os.path.exists(path):
        shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def resequence(sutras):
    """id = vị trí (1-based)."""
    for i, e in enumerate(sutras):
        e["id"] = str(i + 1)


def make_entry(title, teacher, url, duration=0):
    e = {"id": "0", "title": title, "teacher": teacher,
         "audioUrl": url, "durationSeconds": duration}
    # đảm bảo đúng thứ tự key
    return {k: e[k] for k in ENTRY_KEYS}


def find_index_by_id(sutras, target):
    target = str(target)
    for i, e in enumerate(sutras):
        if str(e.get("id")) == target:
            return i
    return -1


# ---------- Commands ----------

def cmd_list(data, args):
    for e in data["sutras"]:
        title = (e.get("title", "") or "")[:50]
        print(f'{str(e.get("id","")):>4}  {title:<50}  {e.get("teacher","")}')
    print(f'\nTổng: {len(data["sutras"])} bài')
    return False  # không ghi file


def cmd_insert(data, args):
    s = data["sutras"]
    if args.at < 1 or args.at > len(s) + 1:
        sys.exit(f"[LỖI] --at phải trong khoảng 1..{len(s)+1}")
    s.insert(args.at - 1, make_entry(args.title, args.teacher, args.url, args.duration))
    resequence(s)
    print(f'Đã chèn "{args.title}" làm id {args.at}. Tổng {len(s)} bài.')
    return True


def cmd_add(data, args):
    s = data["sutras"]
    s.append(make_entry(args.title, args.teacher, args.url, args.duration))
    resequence(s)
    print(f'Đã thêm "{args.title}" làm id {len(s)} (cuối). Tổng {len(s)} bài.')
    return True


def cmd_delete(data, args):
    s = data["sutras"]
    idx = find_index_by_id(s, args.id)
    if idx < 0:
        sys.exit(f"[LỖI] Không thấy id {args.id}")
    removed = s.pop(idx)
    resequence(s)
    print(f'Đã xoá "{removed.get("title","")}" (id cũ {args.id}). Tổng {len(s)} bài.')
    return True


def cmd_renumber(data, args):
    resequence(data["sutras"])
    print(f'Đã đánh lại id 1..{len(data["sutras"])}.')
    return True


def cmd_edit(data, args):
    s = data["sutras"]
    idx = find_index_by_id(s, args.id)
    if idx < 0:
        sys.exit(f"[LỖI] Không thấy id {args.id}")
    e = s[idx]
    if args.title is not None:    e["title"] = args.title
    if args.teacher is not None:  e["teacher"] = args.teacher
    if args.url is not None:      e["audioUrl"] = args.url
    if args.duration is not None: e["durationSeconds"] = args.duration
    # giữ thứ tự key
    s[idx] = {k: e.get(k) for k in ENTRY_KEYS}
    print(f'Đã sửa id {args.id}: "{s[idx].get("title","")}"')
    return True


def build_parser():
    p = argparse.ArgumentParser(description="Quản lý SutraDatabase.remote.json")
    p.add_argument("--file", default=DEFAULT_FILE, help="đường dẫn file json (mặc định: SutraDatabase.remote.json cạnh tool)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="xem danh sách")

    sp = sub.add_parser("insert", help="chèn bài vào vị trí --at")
    sp.add_argument("--at", type=int, required=True)
    sp.add_argument("--title", required=True)
    sp.add_argument("--teacher", required=True)
    sp.add_argument("--url", required=True)
    sp.add_argument("--duration", type=int, default=0)

    sp = sub.add_parser("add", help="thêm bài vào cuối")
    sp.add_argument("--title", required=True)
    sp.add_argument("--teacher", required=True)
    sp.add_argument("--url", required=True)
    sp.add_argument("--duration", type=int, default=0)

    sp = sub.add_parser("delete", help="xoá bài theo id")
    sp.add_argument("--id", type=int, required=True)

    sub.add_parser("renumber", help="đánh lại id 1..N")

    sp = sub.add_parser("edit", help="sửa field 1 bài")
    sp.add_argument("--id", type=int, required=True)
    sp.add_argument("--title", default=None)
    sp.add_argument("--teacher", default=None)
    sp.add_argument("--url", default=None)
    sp.add_argument("--duration", type=int, default=None)

    return p


def main():
    args = build_parser().parse_args()
    data = load(args.file)

    cmds = {
        "list": cmd_list, "insert": cmd_insert, "add": cmd_add,
        "delete": cmd_delete, "renumber": cmd_renumber, "edit": cmd_edit,
    }
    changed = cmds[args.cmd](data, args)

    if changed:
        save(args.file, data)
        print(f"Đã lưu: {args.file}  (backup: {os.path.basename(args.file)}.bak)")


if __name__ == "__main__":
    main()
