"""Streamlit chat interface for MT Activity Planning Agent."""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent.core import run_agent_streaming
from web.components import render_trip_dashboard

st.set_page_config(
    page_title="美团智能活动规划助手",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #fdf6f0 0%, #fef9f4 30%, #fff7ed 60%, #fef2e4 100%);
    }

    .main-header {
        display: flex; align-items: center; gap: 12px;
        padding: 16px 0 4px 0;
        border-bottom: 3px solid transparent;
        border-image: linear-gradient(135deg, #FF6B35, #F7931E, #FFC107) 1;
    }
    .main-header .icon {
        font-size: 2.2rem;
        filter: drop-shadow(0 2px 4px rgba(255,107,53,0.3));
    }
    .main-header .title {
        font-size: 1.6rem; font-weight: 900;
        background: linear-gradient(135deg, #FF6B35, #F7931E);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .main-header .badge {
        background: linear-gradient(135deg, #FF6B35, #F7931E);
        color: white; font-size: 0.7rem; font-weight: 700;
        padding: 3px 10px; border-radius: 20px; letter-spacing: 0.5px;
    }

    /* Dashboard fixed-entry button */
    .dashboard-entry {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: white; border-radius: 14px; padding: 12px 20px;
        margin: 8px 0 16px 0; cursor: pointer;
        display: flex; align-items: center; gap: 10px;
        transition: all 0.2s;
        border: 2px solid #1a1a2e;
    }
    .dashboard-entry:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }

    /* Welcome */
    .welcome-container {
        display: flex; flex-direction: column; align-items: center;
        padding: 48px 20px; text-align: center;
    }
    .welcome-icon { font-size: 4rem; animation: float 3s ease-in-out infinite; }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-12px); }
    }
    .welcome-title { font-size: 1.4rem; font-weight: 700; color: #333; margin-top: 16px; }
    .welcome-subtitle { font-size: 0.95rem; color: #888; max-width: 480px; margin-top: 8px; line-height: 1.6; }
    .welcome-chips {
        display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;
        margin-top: 20px; max-width: 700px;
    }
    .welcome-chip {
        background: white; border: 1.5px solid #ffe0cc;
        border-radius: 20px; padding: 8px 18px;
        font-size: 0.85rem; color: #FF6B35; cursor: pointer;
        transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* Chat bubbles */
    div[data-testid="stChatMessage"] {
        background: white; border-radius: 16px; padding: 16px 20px;
        margin: 8px 0; box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        border: 1px solid #f0ece8;
    }

    /* Chat input */
    div[data-testid="stChatInput"] textarea {
        border-radius: 24px !important; border: 2px solid #e8e0d8 !important;
        padding: 12px 16px !important; transition: all 0.3s;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border-color: #FF6B35 !important;
        box-shadow: 0 0 0 3px rgba(255,107,53,0.1) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fffaf5 0%, #fff5ed 100%);
        border-right: 1px solid #f0e8dc;
    }
    section[data-testid="stSidebar"] .stButton > button {
        border-radius: 12px; border: 1.5px solid #ffe0cc;
        background: white; color: #555; font-size: 0.8rem;
        transition: all 0.2s; text-align: left;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #FF6B35; color: #FF6B35; background: #fff5ed;
    }

    /* Interactive button groups */
    .btn-group {
        display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px;
        padding: 12px 0; border-top: 1px solid #f0e8dc;
    }
    .btn-group-label {
        font-size: 0.75rem; color: #aaa; font-weight: 600;
        width: 100%; margin-bottom: 2px; letter-spacing: 0.5px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <span class="icon">🎯</span>
    <span class="title">美团智能活动规划助手</span>
    <span class="badge">AI Beta</span>
</div>
""", unsafe_allow_html=True)
st.caption("说一句话，出行计划全搞定 · 协商 → 规划 → 预订 → 分享，每一步都有温度")

# ── Session State ──────────────────────────────────────────
defaults = {
    "messages": [],
    "chat_history": [],
    "pending_input": None,
    "last_tool_results": {},
    "bookings": [],       # flat list — direct from create_booking results
    "reminders": [],      # flat list — direct from send_reminder results
    "dashboard_collapsed": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def handle_quick_action(action_text: str):
    st.session_state.pending_input = action_text


def _add_bookings_and_reminders(tool_results: dict):
    """Directly append booking/reminder results into flat session_state lists."""
    def _as_list(val):
        if isinstance(val, list):
            return val
        return [val] if val else []

    for result in _as_list(tool_results.get("create_booking")):
        if isinstance(result, dict) and result.get("success"):
            existing = {b.get("booking_id") for b in st.session_state.bookings}
            if result.get("booking_id") not in existing:
                st.session_state.bookings.append(result)

    for result in _as_list(tool_results.get("send_reminder")):
        if isinstance(result, dict) and result.get("success"):
            st.session_state.reminders.append(result)


def _extract_bookings_from_text(full_response: str):
    """Fallback: if the agent called create_booking but the tool result was
    lost during streaming, try to extract booking info from the response text.

    Only triggers when an actual booking_id pattern (BK-YYYYMMDD-XXXXXX) is
    found in the text — this prevents false positives from the agent merely
    mentioning booking-related terms during the planning phase.
    """
    import re
    # Must contain an actual booking ID pattern to confirm a real booking occurred
    booking_id_pattern = r'BK-\d{8}-[A-Z0-9]{6}'
    match = re.search(booking_id_pattern, full_response)
    if not match:
        return

    # Try to extract confirm_code (8-char uppercase alphanumeric near "confirm" or "确认码")
    confirm_match = re.search(r'(?:confirm|确认码)[:\s]*([A-Z0-9]{8})', full_response, re.IGNORECASE)
    confirm_code = confirm_match.group(1) if confirm_match else "SEE-CHAT"

    # Try to extract item name
    item_match = re.search(r'「([^」]+)」', full_response)
    item_name = item_match.group(1) if item_match else "预订项目（详见对话）"

    # Try to extract total price
    price_match = re.search(r'(?:¥|￥)\s*(\d+)', full_response)
    total_price = int(price_match.group(1)) if price_match else 0

    st.session_state.bookings.append({
        "success": True,
        "booking_id": match.group(0),
        "confirm_code": confirm_code,
        "item_name": item_name,
        "item_type": "activity",
        "date": "2026-05-12",
        "time": "",
        "party_size": 2,
        "total_price": total_price,
        "message": "从文本中提取（tool 结果可能丢失）",
    })


# ── Debug Info (Hidden in sidebar) ─────────────────────────
with st.sidebar:
    with st.expander("🔧 调试信息", expanded=False):
        secret_key = ""
        try:
            if hasattr(st, 'secrets'):
                secret_key = st.secrets.get("ANTHROPIC_API_KEY", "").strip() if hasattr(st.secrets, 'get') else ""
        except Exception:
            secret_key = ""
        
        env_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        
        st.markdown(f"**Secrets 配置**: {'✅ 已配置' if secret_key else '❌ 未配置'}")
        st.markdown(f"**环境变量**: {'✅ 已配置' if env_key else '❌ 未配置'}")
        
        if secret_key:
            st.markdown(f"**密钥长度**: {len(secret_key)} 字符")
            st.markdown(f"**密钥格式**: {'✅ 正确 (sk-开头)' if secret_key.startswith('sk-') else '❌ 错误'}")
        elif env_key:
            st.markdown(f"**密钥长度**: {len(env_key)} 字符")
            st.markdown(f"**密钥格式**: {'✅ 正确 (sk-开头)' if env_key.startswith('sk-') else '❌ 错误'}")

    st.divider()

    st.markdown("#### 💡 试试这些场景")
    examples = [
        ("👨‍👩‍👧 家庭出游", "今天下午想带老婆和5岁孩子出去玩，别离家太远，老婆在减肥要吃得健康"),
        ("👫 朋友聚会", "周末想和朋友4个人聚聚，找点有意思的活动和好吃的"),
        ("🧘 下班放松", "下班后想放松一下，1-2小时，有没有什么推荐"),
    ]
    for label, text in examples:
        if st.button(label, key=f"ex_{label}", use_container_width=True):
            st.session_state.pending_input = text
            st.rerun()

    st.divider()

    # Dashboard quick access
    if st.session_state.bookings:
        if st.button("🗺️ 查看行程单", use_container_width=True):
            st.session_state.dashboard_collapsed = not st.session_state.dashboard_collapsed
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 清空对话", use_container_width=True):
            for k in defaults:
                st.session_state[k] = defaults[k]
            st.rerun()
    with col2:
        st.caption("📍 北京朝阳区")

# ── Display Chat History ───────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-icon">🌤️</div>
        <div class="welcome-title">今天想去哪儿玩？</div>
        <div class="welcome-subtitle">
            我是你的智能出行管家，不只会搜、会订，还会和你商量<br>
            每一个细节都帮你想好，每一个备选都有理有据
        </div>
        <div class="welcome-chips">
            <span class="welcome-chip">🎢 亲子乐园走起</span>
            <span class="welcome-chip">🍣 找好吃的日料</span>
            <span class="welcome-chip">🎨 看展览拍照</span>
            <span class="welcome-chip">🌿 户外徒步放松</span>
            <span class="welcome-chip">🍲 朋友聚会涮火锅</span>
            <span class="welcome-chip">🎂 给老婆过生日</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    is_last = i == len(st.session_state.messages) - 1
    if not is_last or msg["role"] != "assistant":
        continue

    content = msg.get("content", "")

    # ── Reliable state checks (session-based, not text-based) ──
    has_bookings = len(st.session_state.bookings) > 0
    has_reminders = len(st.session_state.reminders) > 0

    # Text-based phase detection (used only when bookings DON'T exist yet)
    has_brief = ("约束确认" in content or "两条主线" in content or "梳理" in content) and \
                ("方向" in content or "主线" in content or "倾向于" in content)
    has_plans = "方案" in content and ("时间" in content or "费用" in content)
    has_booking_text = "预订成功" in content or "confirm_code" in content
    has_share = "分享" in content and ("反馈" in content or "链接" in content)
    has_alternatives = ("备选" in content or "替代" in content or "排队" in content or "等位" in content)
    has_queue = "排队" in content or "等位" in content or "取号" in content

    # ── Button Group 1: Direction selection (维度一：协商) ──
    # Only show when agent gave a brief but hasn't generated plans yet
    if has_brief and not has_plans and not has_bookings:
        st.markdown('<div class="btn-group">'
                     '<div class="btn-group-label">👉 选择方向</div></div>',
                     unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("🧭 方案A方向", key=f"dir_a_{i}", use_container_width=True):
                handle_quick_action("我选方向A，帮我生成详细方案吧")
                st.rerun()
        with c2:
            if st.button("🧭 方案B方向", key=f"dir_b_{i}", use_container_width=True):
                handle_quick_action("我选方向B，帮我生成详细方案吧")
                st.rerun()
        with c3:
            if st.button("📋 两个方向都看看", key=f"dir_both_{i}", use_container_width=True):
                handle_quick_action("两个方向都挺感兴趣的，各帮我出一个详细方案对比一下吧")
                st.rerun()

    # ── Button Group 2: Plan selection ──
    # CRITICAL: only show if NO bookings exist yet
    if has_plans and not has_bookings:
        st.markdown('<div class="btn-group">'
                     '<div class="btn-group-label">✅ 确认方案</div></div>',
                     unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("✅ 选方案 A，帮我预订", key=f"plan_a_{i}", use_container_width=True):
                handle_quick_action("我选方案A，请帮我预订。联系人：小明，电话：13800000000")
                st.rerun()
        with c2:
            if st.button("✅ 选方案 B，帮我预订", key=f"plan_b_{i}", use_container_width=True):
                handle_quick_action("我选方案B，请帮我预订。联系人：小明，电话：13800000000")
                st.rerun()
        with c3:
            if st.button("🔄 换一批方案", key=f"refresh_{i}", use_container_width=True):
                handle_quick_action("这两个方案都不太满意，帮我重新推荐一批吧")
                st.rerun()

    # ── Button Group 3: Alternatives + Queue (维度二) ──
    # CRITICAL: only show if NO bookings exist yet
    if has_alternatives and not has_bookings:
        st.markdown('<div class="btn-group">'
                     '<div class="btn-group-label">🔄 备选 & 排队选项</div></div>',
                     unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            if st.button("👍 听你推荐的", key=f"alt_rec_{i}", use_container_width=True):
                handle_quick_action("听你的推荐，帮我订你推荐的那个吧。联系人：小明，电话：13800000000")
                st.rerun()
        with c2:
            if has_queue:
                if st.button("🕐 排队等位", key=f"alt_queue_{i}", use_container_width=True):
                    handle_quick_action("帮我取号排队等位吧，等一会儿没关系。联系人：小明，电话：13800000000")
                    st.rerun()
            else:
                if st.button("📋 再换一批", key=f"alt_more_{i}", use_container_width=True):
                    handle_quick_action("还能再换一批备选吗？再看看有没有更好的")
                    st.rerun()
        with c3:
            if st.button("⏰ 换个时段", key=f"alt_time_{i}", use_container_width=True):
                handle_quick_action("帮我在其他时段再看看，也许早点或晚点有空位")
                st.rerun()
        with c4:
            if st.button("↩️ 回原方案", key=f"alt_back_{i}", use_container_width=True):
                handle_quick_action("还是回到原来的方案吧，看看有没有其他时段可以选")
                st.rerun()

    # ── Button Group 4: Last-centimeter follow-up (维度三) ──
    # Show when bookings exist OR text indicates booking just completed
    if has_bookings or has_booking_text:
        st.markdown('<div class="btn-group">'
                     '<div class="btn-group-label">🔔 最后一厘米 · 还能帮你做这些</div></div>',
                     unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            if st.button("🚗 设置出发提醒", key=f"lc_remind_{i}", use_container_width=True):
                handle_quick_action("好的，帮我设置出发前15分钟的提醒")
                st.rerun()
        with c2:
            if st.button("🍽️ 提前点餐", key=f"lc_order_{i}", use_container_width=True):
                handle_quick_action("帮我提前点好餐厅的招牌菜吧，到了就能吃")
                st.rerun()
        with c3:
            if st.button("📤 分享给家人", key=f"lc_share_{i}", use_container_width=True):
                handle_quick_action("帮我生成分享文案发给老婆看看")
                st.rerun()
        with c4:
            if st.button("✅ 全部搞定", key=f"lc_done_{i}", use_container_width=True):
                handle_quick_action("都搞定了，谢谢你！")
                st.rerun()

    # ── Button Group 5: Share feedback simulation (维度四) ──
    if has_share:
        st.markdown('<div class="btn-group">'
                     '<div class="btn-group-label">👨‍👩‍👧 模拟家人反馈（点击测试协作流程）</div></div>',
                     unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
        with c1:
            if st.button("👍 没问题", key=f"fb_ok_{i}", use_container_width=True):
                handle_quick_action("我老婆回复说「没问题，就这样」，太好了！")
                st.rerun()
        with c2:
            if st.button("🍽️ 换餐厅", key=f"fb_rest_{i}", use_container_width=True):
                handle_quick_action("我老婆说餐厅太远了，能不能换一家近一点的？")
                st.rerun()
        with c3:
            if st.button("⏱️ 太赶了", key=f"fb_time_{i}", use_container_width=True):
                handle_quick_action("我老婆说时间安排太赶了，中间能不能缓一缓？")
                st.rerun()
        with c4:
            if st.button("🎢 换活动", key=f"fb_act_{i}", use_container_width=True):
                handle_quick_action("我老婆说亲子乐园太闹了，想换一个安静一点的活动")
                st.rerun()
        with c5:
            if st.button("☕ 加休息", key=f"fb_brk_{i}", use_container_width=True):
                handle_quick_action("中间能不能加一个喝咖啡的地方，休息半小时？")
                st.rerun()

# ── Trip Dashboard (auto-appears at bottom when bookings exist) ──
if st.session_state.bookings:
    if st.session_state.dashboard_collapsed:
        if st.button("🗺️ 展开行程单", key="dash_expand", use_container_width=True):
            st.session_state.dashboard_collapsed = False
            st.rerun()
    else:
        _ts = {
            "bookings": st.session_state.bookings,
            "reminders": st.session_state.reminders,
            "date": st.session_state.bookings[0].get("date", "2026-05-12") if st.session_state.bookings else "2026-05-12",
            "party_size": st.session_state.bookings[0].get("party_size", 2) if st.session_state.bookings else 2,
        }
        render_trip_dashboard(_ts)
        if st.button("🔽 收起行程单", key="dash_close", use_container_width=True):
            st.session_state.dashboard_collapsed = True
            st.rerun()
else:
    # Debug: show why dashboard isn't appearing
    has_messages = len(st.session_state.messages) > 0
    last_tools = st.session_state.get("last_tool_results", {})
    if has_messages and last_tools:
        tool_names = list(last_tools.keys())
        st.caption(f"调试: tool_results = {tool_names}, bookings = {len(st.session_state.bookings)}")

# ── Chat Input (ALWAYS rendered) ───────────────────────────
user_input = st.chat_input("说说你的出行想法吧...")

if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

# ── Process User Input ─────────────────────────────────────
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        tool_status_placeholder = st.empty()
        full_response = ""
        tool_results = {}
        stream_error = None

        try:
            for event in run_agent_streaming(
                user_message=user_input,
                chat_history=st.session_state.chat_history,
            ):
                if event["type"] == "text":
                    full_response += event["content"]
                    response_placeholder.markdown(full_response + "▌")

                elif event["type"] == "tool_start":
                    tool_labels = {
                        "search_activities": "🔍 正在搜索活动...",
                        "search_restaurants": "🍽️ 正在查找餐厅...",
                        "check_availability": "📅 查询空位中...",
                        "create_booking": "🎫 正在预订...",
                        "order_delivery": "🛵 创建配送订单...",
                        "send_reminder": "⏰ 设置提醒中...",
                        "share_plan": "📤 生成可交互分享...",
                    }
                    label = tool_labels.get(event["name"], f"🔧 {event['name']}")
                    tool_status_placeholder.info(f"{label}")

                elif event["type"] == "tool_result":
                    name = event["name"]
                    if name in tool_results:
                        if isinstance(tool_results[name], list):
                            tool_results[name].append(event["result"])
                        else:
                            tool_results[name] = [tool_results[name], event["result"]]
                    else:
                        tool_results[name] = event["result"]
                    tool_status_placeholder.empty()

                elif event["type"] == "done":
                    break

        except RuntimeError as e:
            stream_error = str(e)
            if "认证失败" in str(e) or "invalid" in str(e).lower():
                stream_error = f"❌ 认证错误：{str(e)}\n\n可能的原因：\n1. API 密钥已过期或被撤销\n2. 密钥输入有误（请检查是否有多余空格）\n3. Anthropic 服务暂时故障\n\n请访问 https://console.anthropic.com/ 检查您的 API 密钥状态。"
        except Exception as e:
            stream_error = f"未知错误：{str(e)}\n\n错误类型：{type(e).__name__}"

        # Always show response (even if partial)
        if full_response:
            response_placeholder.markdown(full_response)
        if stream_error:
            response_placeholder.error(f"流式输出中断: {stream_error}")
        tool_status_placeholder.empty()

        # Always save messages
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
        st.session_state.last_tool_results = tool_results

        # Always try to collect bookings (runs even if streaming errored)
        _add_bookings_and_reminders(tool_results)

        # Fallback: if no bookings from tools but text contains confirm_code,
        # extract booking info from the response text (agent may have called tool
        # but streaming dropped the result, or agent simulated booking in text)
        if not st.session_state.bookings and ("confirm_code" in full_response or "预订成功" in full_response):
            _extract_bookings_from_text(full_response)

        st.rerun()
