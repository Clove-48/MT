"""Tool handlers — query mock data and simulate bookings."""

import json
import random
import string
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(filename: str):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def _random_code(length: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ═══════════════════════════════════════════════════════════
# search_activities
# ═══════════════════════════════════════════════════════════

def search_activities(query: str = "", category: str = "", kid_friendly: bool = None,
                      max_distance_km: float = None, max_price: float = None,
                      tags: list[str] = None) -> dict:
    activities = _load_json("activities.json")
    results = []

    for a in activities:
        if kid_friendly is not None and a["kid_friendly"] != kid_friendly:
            continue
        if max_distance_km is not None and a["distance_km"] > max_distance_km:
            continue
        if max_price is not None and a["price_per_person"] > max_price:
            continue
        if category and a["category"] != category:
            continue
        if tags:
            if not all(t in a["tags"] for t in tags):
                continue
        if query:
            q = query.lower()
            matched = (q in a["name"].lower()
                       or q in a["category"].lower()
                       or any(q in t.lower() for t in a["tags"])
                       or q in a.get("description", "").lower())
            if not matched:
                continue
        results.append(a)

    if not results and query:
        results = activities[:6]

    return {"count": len(results), "results": results[:8]}


# ═══════════════════════════════════════════════════════════
# search_restaurants
# ═══════════════════════════════════════════════════════════

def search_restaurants(query: str = "", cuisine: str = "", dietary_tags: list[str] = None,
                       kid_friendly: bool = None, max_price: float = None,
                       max_distance_km: float = None) -> dict:
    restaurants = _load_json("restaurants.json")
    results = []

    for r in restaurants:
        if kid_friendly is not None and r["kid_friendly"] != kid_friendly:
            continue
        if max_price is not None and r["price_per_person"] > max_price:
            continue
        if cuisine and r["cuisine"] != cuisine:
            continue
        if dietary_tags:
            if not all(t in r["dietary_tags"] for t in dietary_tags):
                continue
        if query:
            q = query.lower()
            matched = (q in r["name"].lower()
                       or q in r["cuisine"].lower()
                       or any(q in t.lower() for t in r["dietary_tags"])
                       or q in r.get("description", "").lower())
            if not matched:
                continue
        results.append(r)

    if not results and query:
        results = restaurants[:6]

    return {"count": len(results), "results": results[:8]}


# ═══════════════════════════════════════════════════════════
# check_availability (with auto-alternatives)
# ═══════════════════════════════════════════════════════════

def check_availability(item_id: str, item_type: str, date: str, party_size: int,
                       time: str = "", find_alternatives: bool = True) -> dict:
    availability = _load_json("availability.json")
    item_avail = availability.get(item_id)

    if not item_avail:
        return {"available": False, "reason": f"未找到 {item_id} 的可用信息", "slots": [], "alternatives": []}

    slots = item_avail.get("slots", [])
    if time:
        slots = [s for s in slots if s["time"] == time]

    queueable_slots = []
    result_slots = []
    for s in slots:
        slot_info = {"time": s["time"], "status": s["status"]}
        if s["status"] == "unlimited":
            slot_info["remaining"] = "充足"
            slot_info["available"] = True
            slot_info["wait_estimate_min"] = 0
        elif s["status"] == "limited":
            slot_info["remaining"] = s["remaining"]
            slot_info["available"] = s["remaining"] >= party_size
            slot_info["wait_estimate_min"] = max(5, (party_size - s["remaining"]) * 8)
        else:
            remaining = s["remaining"]
            slot_info["remaining"] = remaining
            slot_info["available"] = remaining >= party_size
            # Estimate wait: ~5 min per person ahead, randomized
            slot_info["wait_estimate_min"] = max(5, (party_size - remaining) * random.randint(5, 10)) if remaining < party_size else 0

        # Track if this slot supports queueing (limited but has some capacity)
        if not slot_info["available"] and s["status"] in ("available", "limited"):
            slot_info["can_queue"] = True
            queueable_slots.append(slot_info)
        elif not slot_info["available"]:
            slot_info["can_queue"] = False
            slot_info["queue_note"] = "该时段已完全满员，无法排队"

        result_slots.append(slot_info)

    any_available = any(s["available"] for s in result_slots)
    can_queue = len(queueable_slots) > 0

    result = {
        "item_id": item_id,
        "item_type": item_type,
        "date": date,
        "party_size": party_size,
        "available": any_available,
        "can_queue": can_queue,
        "slots": result_slots,
        "alternatives": []
    }

    # Queue info for full but queueable items
    if not any_available and can_queue:
        best_queue = min(queueable_slots, key=lambda s: s["wait_estimate_min"])
        result["queue_option"] = {
            "available": True,
            "best_slot_time": best_queue["time"],
            "wait_estimate_min": best_queue["wait_estimate_min"],
            "hint": f"该商家当前满座，但可以取号排队。预计等待 {best_queue['wait_estimate_min']} 分钟（{best_queue['time']} 时段）。"
        }

    # Auto-search alternatives when unavailable
    if not any_available and find_alternatives:
        result["alternatives"] = _find_alternatives(item_id, item_type, date, party_size, time)
        if result["alternatives"]:
            result["hint"] = "首选不可用，已自动搜索替代方案（见 alternatives 字段）。也可以用排队等待选项（见 queue_option 字段）。请用对比+排队的方式呈现给用户。"

    return result


def _find_alternatives(item_id: str, item_type: str, date: str,
                       party_size: int, time: str = "") -> list[dict]:
    """Search for available alternatives to an unavailable item."""
    availability = _load_json("availability.json")

    if item_type == "activity":
        all_items = _load_json("activities.json")
        original = next((a for a in all_items if a["id"] == item_id), None)
    else:
        all_items = _load_json("restaurants.json")
        original = next((r for r in all_items if r["id"] == item_id), None)

    if not original:
        return []

    alternatives = []
    for item in all_items:
        if item["id"] == item_id:
            continue

        # Check availability
        item_avail = availability.get(item["id"], {})
        slots = item_avail.get("slots", [])
        if time:
            # Find closest slot to requested time
            slots = [s for s in slots if s["time"] >= time][:1] or slots[:1]

        available_slots = []
        for s in slots:
            remaining = s["remaining"]
            if remaining == -1 or remaining >= party_size:
                available_slots.append(s)

        if not available_slots:
            continue

        # Build comparison with original
        alt = {
            "id": item["id"],
            "name": item["name"],
            "available_slots": [s["time"] for s in available_slots],
            "rating": item.get("rating", 0),
            "price_per_person": item.get("price_per_person", 0),
            "distance_km": item.get("distance_km", 0),
            "kid_friendly": item.get("kid_friendly", False),
            "tags": item.get("tags", []),
            "dietary_tags": item.get("dietary_tags", []),
        }

        # Comparison fields
        if item_type == "activity":
            alt["price_diff"] = item.get("price_per_person", 0) - original.get("price_per_person", 0)
            alt["distance_diff_km"] = round(item.get("distance_km", 0) - original.get("distance_km", 0), 1)
            alt["rating_diff"] = round(item.get("rating", 0) - original.get("rating", 0), 1)
            alt["duration_min"] = item.get("duration_min", 0)
        else:
            alt["price_diff"] = item.get("price_per_person", 0) - original.get("price_per_person", 0)
            alt["rating_diff"] = round(item.get("rating", 0) - original.get("rating", 0), 1)
            alt["cuisine"] = item.get("cuisine", "")
            alt["has_kids_menu"] = item.get("has_kids_menu", False)
            alt["avg_wait_min"] = item.get("avg_wait_min", 0)

        alternatives.append(alt)

    # Sort: prefer closer distance, higher rating, smaller price diff
    alternatives.sort(key=lambda x: (abs(x.get("distance_diff_km", 0)), -x.get("rating_diff", 0)))
    return alternatives[:3]


# ═══════════════════════════════════════════════════════════
# create_booking
# ═══════════════════════════════════════════════════════════

def create_booking(item_id: str, item_type: str, date: str, time: str,
                   party_size: int, contact_name: str, contact_phone: str) -> dict:
    if item_type == "activity":
        data = _load_json("activities.json")
    else:
        data = _load_json("restaurants.json")

    item = next((x for x in data if x["id"] == item_id), None)
    if not item:
        return {"success": False, "reason": f"未找到 {item_id}"}

    avail = check_availability(item_id, item_type, date, party_size, time, find_alternatives=False)
    if not avail["available"]:
        return {"success": False, "reason": "所选时段已无空位", "availability": avail}

    booking_id = f"BK-{datetime.now().strftime('%Y%m%d')}-{_random_code(6)}"
    confirm_code = _random_code(8).upper()

    return {
        "success": True,
        "booking_id": booking_id,
        "confirm_code": confirm_code,
        "item_name": item["name"],
        "item_type": item_type,
        "date": date,
        "time": time,
        "party_size": party_size,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "total_price": item["price_per_person"] * party_size,
        "message": f"预订成功！{item['name']}，{date} {time}，{party_size}人，确认码：{confirm_code}"
    }


# ═══════════════════════════════════════════════════════════
# order_delivery
# ═══════════════════════════════════════════════════════════

def order_delivery(item: str, delivery_location: str, delivery_time: str,
                   recipient_name: str = "", recipient_phone: str = "",
                   note: str = "") -> dict:
    order_id = f"OD-{datetime.now().strftime('%Y%m%d')}-{_random_code(6)}"
    return {
        "success": True,
        "order_id": order_id,
        "item": item,
        "delivery_location": delivery_location,
        "delivery_time": delivery_time,
        "recipient_name": recipient_name,
        "recipient_phone": recipient_phone,
        "note": note,
        "estimated_fee": random.randint(15, 50),
        "message": f"配送订单已创建：{item}，预计 {delivery_time} 送达 {delivery_location}"
    }


# ═══════════════════════════════════════════════════════════
# send_reminder
# ═══════════════════════════════════════════════════════════

def send_reminder(reminder_type: str, trigger_time: str, message: str,
                  related_booking_id: str = "") -> dict:
    reminder_id = f"RM-{_random_code(6)}"
    type_labels = {
        "departure": "🚗 出发提醒",
        "traffic": "🚦 路况预警",
        "weather": "🌤️ 天气提醒",
        "packing": "🎒 物品提醒",
        "custom": "⏰ 自定义提醒",
    }
    return {
        "success": True,
        "reminder_id": reminder_id,
        "reminder_type": reminder_type,
        "type_label": type_labels.get(reminder_type, "提醒"),
        "trigger_time": trigger_time,
        "message": message,
        "related_booking_id": related_booking_id,
        "status": "已设置",
        "hint": f"将在 {trigger_time} 通过美团App推送提醒"
    }


# ═══════════════════════════════════════════════════════════
# share_plan (with interactive feedback)
# ═══════════════════════════════════════════════════════════

def share_plan(plan_summary: str, recipients: list[str] = None,
               tone: str = "warm", interactive: bool = True) -> dict:
    recipients = recipients or ["家人/朋友"]
    recipient_str = "、".join(recipients)

    if tone == "warm":
        msg = (
            f"亲爱的{recipient_str}～\n\n"
            f"今天的出行计划已经安排好咯 🎉\n\n"
            f"{plan_summary}\n\n"
            f"期待和你们一起度过美好的一天呀！❤️"
        )
    elif tone == "casual":
        msg = (
            f"嘿 {recipient_str}！\n\n"
            f"计划搞定了，速看：\n\n"
            f"{plan_summary}\n\n"
            f"到时候见～"
        )
    else:
        msg = (
            f"您好 {recipient_str}，\n\n"
            f"以下为出行计划确认：\n\n"
            f"{plan_summary}\n\n"
            f"请准时参加，谢谢。"
        )

    result = {
        "success": True,
        "message": msg,
        "copyable": True,
        "hint": "以上文案可直接复制发送给好友"
    }

    if interactive:
        result["interactive"] = True
        result["feedback_options"] = [
            {"action": "approve_all", "label": "👍 没问题，就这样", "emoji": "👍"},
            {"action": "change_restaurant", "label": "🍽️ 餐厅换一家", "emoji": "🍽️"},
            {"action": "change_activity", "label": "🎢 活动换一个", "emoji": "🎢"},
            {"action": "time_too_tight", "label": "⏱️ 时间太赶了", "emoji": "⏱️"},
            {"action": "add_break", "label": "☕ 中间加个休息", "emoji": "☕"},
        ]
        result["interactive_note"] = (
            "分享链接已生成。家人打开后可以看到完整行程，并点击反馈按钮：\n"
            "「👍 没问题」「🍽️ 换餐厅」「🎢 换活动」「⏱️ 太赶了」「☕ 加休息」\n"
            "她们的反馈会即时同步过来，我帮你马上调整方案。"
        )

    return result


# ═══════════════════════════════════════════════════════════
# Handler registry
# ═══════════════════════════════════════════════════════════

HANDLERS = {
    "search_activities": search_activities,
    "search_restaurants": search_restaurants,
    "check_availability": check_availability,
    "create_booking": create_booking,
    "order_delivery": order_delivery,
    "send_reminder": send_reminder,
    "share_plan": share_plan,
}
