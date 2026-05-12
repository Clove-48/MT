"""HTML/CSS UI components for the Streamlit interface — plan cards, booking cards, etc."""


def _note_html(note: str) -> str:
    if not note:
        return ""
    return f'<span style="color:#aaa;">&middot; {note}</span>'


def plan_card_html(plan_name: str, timeline: list[dict],
                   cost_per_person: int, cost_total: int,
                   highlights: list[str] = None,
                   theme: str = "orange") -> str:
    """Generate a rich HTML plan card.

    Args:
        plan_name: e.g. "方案 A：亲子欢乐之旅"
        timeline: list of {time, activity, location, icon}
        cost_per_person: per-person cost
        cost_total: total cost
        highlights: list of highlight strings (e.g. ["亲子友好", "健康低脂"])
        theme: "orange" | "green" | "blue"
    """
    theme_colors = {
        "orange": ("#FF6B35", "#F7931E", "#fff5ed", "#ffe0cc"),
        "green": ("#10B981", "#059669", "#ecfdf5", "#d1fae5"),
        "blue": ("#3B82F6", "#2563EB", "#eff6ff", "#dbeafe"),
    }
    primary, secondary, bg, border = theme_colors.get(theme, theme_colors["orange"])

    # Highlights chips
    highlights_html = ""
    if highlights:
        chips = "".join(
            f'<span style="display:inline-block;background:{bg};color:{primary};'
            f'padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;'
            f'margin-right:6px;">{h}</span>'
            for h in highlights
        )
        highlights_html = f'<div style="margin-bottom:14px;">{chips}</div>'

    # Timeline
    timeline_html = ""
    for i, step in enumerate(timeline):
        icon = step.get("icon", "📍")
        is_last = i == len(timeline) - 1
        connector = "" if is_last else (
            '<div style="margin-left:14px;border-left:2px dashed #e0d8cc;height:20px;"></div>'
        )
        timeline_html += f"""
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:2px;">
            <div style="width:28px;height:28px;border-radius:50%;
                        background:linear-gradient(135deg,{primary},{secondary});
                        display:flex;align-items:center;justify-content:center;
                        flex-shrink:0;color:white;font-size:0.75rem;">
                {icon}
            </div>
            <div style="flex:1;">
                <div style="font-weight:700;font-size:0.9rem;color:#333;">
                    {step.get('time', '')} — {step.get('activity', '')}
                </div>
                <div style="font-size:0.8rem;color:#999;margin-top:1px;">
                    {step.get('location', '')}
                    {_note_html(step.get('note', ''))}
                </div>
            </div>
        </div>
        {connector}
        """

    cost_per = cost_per_person
    cost_tot = cost_total

    return f"""
    <div style="
        background:white;
        border-radius:20px;
        padding:20px 22px;
        margin:12px 0;
        border:2px solid {border};
        box-shadow:0 4px 20px rgba(0,0,0,0.05);
        transition:all 0.3s;
    ">
        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <div style="
                background:linear-gradient(135deg,{primary},{secondary});
                color:white;font-weight:900;font-size:1rem;
                padding:8px 18px;border-radius:14px;
                box-shadow:0 3px 12px rgba(255,107,53,0.2);
            ">
                {plan_name}
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.1rem;font-weight:900;color:{primary};">
                    ¥{cost_tot}
                </div>
                <div style="font-size:0.7rem;color:#aaa;">总计（人均 ¥{cost_per}）</div>
            </div>
        </div>

        {highlights_html}

        <!-- Timeline -->
        <div style="margin-top:8px;">
            {timeline_html}
        </div>
    </div>
    """


def booking_card_html(item_name: str, booking_id: str, confirm_code: str,
                       date: str, time: str, party_size: int,
                       total_price: int, item_type: str = "activity",
                       success: bool = True, reason: str = "") -> str:
    """Generate a booking confirmation HTML card."""
    if not success:
        return f"""
        <div style="background:#fef2f2;border:2px solid #fecaca;border-radius:16px;
                    padding:16px 20px;margin:8px 0;">
            <div style="font-size:1.1rem;font-weight:700;color:#dc2626;">预订失败</div>
            <div style="color:#991b1b;margin-top:4px;">{reason}</div>
        </div>
        """

    type_label = "🎢 活动预订" if item_type == "activity" else "🍽️ 餐厅预订"
    return f"""
    <div style="
        background:linear-gradient(135deg,#f0fdf4,#ecfdf5);
        border:2px solid #6ee7b7;border-radius:20px;
        padding:20px 22px;margin:12px 0;
        box-shadow:0 4px 20px rgba(16,185,129,0.08);
    ">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
            <span style="font-size:0.8rem;background:#d1fae5;color:#059669;
                         padding:3px 10px;border-radius:10px;font-weight:700;">
                {type_label}
            </span>
            <span style="font-size:0.8rem;color:#059669;font-weight:700;">✓ 预订成功</span>
        </div>
        <div style="font-size:1.15rem;font-weight:700;color:#333;margin-bottom:12px;">
            {item_name}
        </div>
        <div style="display:flex;gap:20px;flex-wrap:wrap;">
            <div>
                <div style="font-size:0.7rem;color:#999;">日期</div>
                <div style="font-weight:600;color:#333;">{date}</div>
            </div>
            <div>
                <div style="font-size:0.7rem;color:#999;">时间</div>
                <div style="font-weight:600;color:#333;">{time}</div>
            </div>
            <div>
                <div style="font-size:0.7rem;color:#999;">人数</div>
                <div style="font-weight:600;color:#333;">{party_size} 人</div>
            </div>
            <div>
                <div style="font-size:0.7rem;color:#999;">金额</div>
                <div style="font-weight:700;color:#059669;">¥{total_price}</div>
            </div>
        </div>
        <div style="
            background:white;border-radius:12px;padding:12px 16px;margin-top:14px;
            border:1px dashed #a7f3d0;
        ">
            <div style="font-size:0.8rem;color:#666;">
                订单号：<code style="background:#f9fafb;padding:2px 6px;border-radius:4px;">{booking_id}</code>
            </div>
            <div style="font-size:0.8rem;color:#666;margin-top:4px;">
                确认码：<strong style="color:#059669;font-size:1rem;">{confirm_code}</strong>
            </div>
        </div>
    </div>
    """


def share_card_html(message: str) -> str:
    """Generate a shareable message card with copy-friendly styling."""
    # Escape HTML but preserve line breaks
    safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    formatted = safe_msg.replace("\n", "<br>")
    return f"""
    <div style="
        background:linear-gradient(135deg,#eff6ff,#faf5ff);
        border:2px solid #c4b5fd;border-radius:20px;
        padding:20px 22px;margin:12px 0;
        box-shadow:0 4px 20px rgba(139,92,246,0.06);
    ">
        <div style="font-weight:700;color:#7c3aed;margin-bottom:10px;font-size:0.9rem;">
            📤 分享文案 · 可直接复制发送
        </div>
        <div style="
            background:white;border-radius:14px;padding:14px 18px;
            font-size:0.9rem;line-height:1.7;color:#444;
            border:1px solid #e8e0f0;
        ">
            {formatted}
        </div>
    </div>
    """


def timeline_html(steps: list[dict]) -> str:
    """Standalone timeline visualization.

    Args:
        steps: list of {time, title, description, icon, color}
    """
    items = ""
    for i, step in enumerate(steps):
        color = step.get("color", "#FF6B35")
        is_last = i == len(steps) - 1
        connector = "" if is_last else (
            f'<div style="margin-left:16px;border-left:2px dashed #e0d8cc;height:24px;"></div>'
        )
        items += f"""
        <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:2px;">
            <div style="
                min-width:32px;height:32px;border-radius:50%;
                background:{color};
                display:flex;align-items:center;justify-content:center;
                flex-shrink:0;color:white;font-size:0.8rem;font-weight:700;
            ">
                {step.get('icon', i + 1)}
            </div>
            <div>
                <div style="font-weight:700;color:#333;font-size:0.9rem;">
                    {step.get('time', '')} — {step.get('title', '')}
                </div>
                {f'<div style="font-size:0.8rem;color:#888;">{step.get("description", "")}</div>' if step.get('description') else ''}
            </div>
        </div>
        {connector}
        """
    return f'<div style="padding:8px 0;">{items}</div>'


# ═══════════════════════════════════════════════════════════════
# Trip Dashboard (行程仪表盘) — Streamlit-native rendering
# ═══════════════════════════════════════════════════════════════

def render_trip_dashboard(trip_state: dict):
    """Render the trip dashboard using Streamlit native components.

    Call this directly (not via st.markdown) so components render reliably.
    """
    import streamlit as st

    try:
        bookings = trip_state.get("bookings", []) if trip_state else []
        reminders = trip_state.get("reminders", []) if trip_state else []
        party_size = trip_state.get("party_size", 2) if trip_state else 2
        date = trip_state.get("date", "2026-05-12") if trip_state else "2026-05-12"
    except Exception:
        st.error("行程数据读取失败，请重试")
        return

    if not bookings:
        st.info("暂无预订记录")
        return

    # Build timeline from bookings if not already built
    timeline = trip_state.get("timeline", []) if trip_state else []
    if not timeline:
        for bk in bookings:
            try:
                timeline.append({
                    "time": bk.get("time", ""),
                    "title": bk.get("item_name", ""),
                    "location": bk.get("item_name", ""),
                    "duration": "约2小时" if bk.get("item_type") == "activity" else "约1.5小时",
                    "booked": True,
                    "booking_id": bk.get("booking_id", ""),
                })
            except Exception:
                pass

    # ── Header ──
    st.divider()
    st.markdown("## 🗺️ 完整行程单")
    st.caption(f"美团智能活动规划助手 · {date} · {party_size}人")

    # ── Timeline ──
    st.markdown("### 🧭 时间线")
    for i, step in enumerate(timeline):
        try:
            if step.get("type") == "transit":
                st.caption(f"　　　🚗 {step.get('label', '')} · {step.get('duration', '')}")
                continue

            is_booked = step.get("booked", False)
            icon = "✅" if is_booked else "⏳"
            st.markdown(
                f"{icon} **{step.get('time', '')}**　{step.get('title', '')}　"
                f"📍 {step.get('location', '')}　⏱ {step.get('duration', '')}",
                help=f"订单: {step.get('booking_id', 'N/A')}"
            )
        except Exception:
            pass

    # ── Booking List ──
    st.markdown("### 📋 预订清单")
    for i, bk in enumerate(bookings):
        try:
            type_icon = "🎢" if bk.get("item_type") == "activity" else "🍽️"
            type_label = "活动" if bk.get("item_type") == "activity" else "餐饮"
            bid = bk.get("booking_id", "")
            btime = bk.get("time", "")
            bsize = bk.get("party_size", party_size)
            bprice = bk.get("total_price", 0)

            st.markdown(
                f"{type_icon} **#{i+1}** {bk.get('item_name', '')}  "
                f"⏰ {btime}  👥 {bsize}人  💰 ¥{bprice}  "
                f"✓ 已确认  `{bid}`"
            )
        except Exception:
            pass

    # ── Cost Summary ──
    st.markdown("### 💰 费用汇总")
    try:
        activity_cost = sum(b.get("total_price", 0) for b in bookings if b.get("item_type") == "activity")
        restaurant_cost = sum(b.get("total_price", 0) for b in bookings if b.get("item_type") == "restaurant")
        total_cost = activity_cost + restaurant_cost
        per_person = total_cost // party_size if party_size > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎢 门票/活动", f"¥{activity_cost}")
        c2.metric("🍽️ 餐饮", f"¥{restaurant_cost}")
        c3.metric("💰 合计", f"¥{total_cost}", delta=f"人均 ¥{per_person}")
        c4.metric("📋 预订数", f"{len(bookings)}项")
    except Exception:
        pass

    # ── Reminders / Weather ──
    st.markdown("### ⚠️ 提醒")
    try:
        if reminders:
            for r in reminders:
                st.info(f"{r.get('type_label', '⏰')}　{r.get('message', '')}　—　{r.get('trigger_time', '')}")
        else:
            st.info("🌤️ 晴 22-28°C · 适合户外活动 · 薄外套 + 帽子")
    except Exception:
        pass

    # ── Export Buttons ──
    st.markdown("### 📤 导出 & 分享")
    try:
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            if st.button("📄 导出图片", key=f"dash_export_{len(bookings)}", use_container_width=True):
                st.success(f"✅ 行程单图片已生成（演示）\n文件: MT_Trip_{date}.png")
        with ec2:
            if st.button("📅 添加日历", key=f"dash_cal_{len(bookings)}", use_container_width=True):
                st.success(f"✅ {len(bookings)} 个日历事件已添加（演示）")
        with ec3:
            if st.button("🔗 分享链接", key=f"dash_share_{len(bookings)}", use_container_width=True):
                st.success("✅ 链接已复制\n家人打开后可查看仪表盘并反馈")
    except Exception:
        pass

    st.divider()


def queue_info_card_html(item_name: str, wait_estimate_min: int, slot_time: str) -> str:
    """Generate a queue/wait info card for full-but-queueable items."""
    return f"""
    <div style="
        background:linear-gradient(135deg,#fffbeb,#fef3c7);
        border:2px solid #fcd34d;border-radius:16px;
        padding:16px 20px;margin:10px 0;
    ">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:1.5rem;">🕐</span>
            <div>
                <div style="font-weight:700;color:#92400e;font-size:0.9rem;">
                    {item_name} · 可排队等位
                </div>
                <div style="font-size:0.8rem;color:#78350f;margin-top:2px;">
                    最佳取号时段：{slot_time} · 预计等待 <strong>{wait_estimate_min} 分钟</strong>
                </div>
            </div>
        </div>
    </div>
    """
