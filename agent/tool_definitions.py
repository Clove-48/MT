"""Tool definitions (JSON Schema) for the MT Activity Planning Agent."""

TOOLS = [
    {
        "name": "search_activities",
        "description": "搜索亲子/游玩/娱乐活动。根据用户需求筛选合适的活动项目。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如'亲子乐园'、'展览'、'户外'等"
                },
                "category": {
                    "type": "string",
                    "enum": ["亲子乐园", "展览", "公园/户外", "手工坊", "主题乐园", "运动", "娱乐"],
                    "description": "活动类别筛选"
                },
                "kid_friendly": {
                    "type": "boolean",
                    "description": "是否要求亲子友好"
                },
                "max_distance_km": {
                    "type": "number",
                    "description": "最大距离（公里），默认不限制"
                },
                "max_price": {
                    "type": "number",
                    "description": "最高人均价格，默认不限制"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "按标签筛选，如['户外', '免费', '亲子']"
                }
            },
            "required": []
        }
    },
    {
        "name": "search_restaurants",
        "description": "搜索餐厅。根据用户口味偏好、饮食需求和场景筛选合适的餐厅。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如'健康餐'、'火锅'、'日料'等"
                },
                "cuisine": {
                    "type": "string",
                    "description": "菜系筛选，如'轻食/沙拉'、'川菜'、'日料'等"
                },
                "dietary_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "饮食需求标签，如['低脂', '高蛋白', '素食可选', '儿童友好']"
                },
                "kid_friendly": {
                    "type": "boolean",
                    "description": "是否要求亲子友好（有儿童餐、游乐区等）"
                },
                "max_price": {
                    "type": "number",
                    "description": "最高人均价格"
                },
                "max_distance_km": {
                    "type": "number",
                    "description": "最大距离（公里）"
                }
            },
            "required": []
        }
    },
    {
        "name": "check_availability",
        "description": "查询某个活动或餐厅在指定日期和时段的空位/余票情况。当首选不可用时，会自动搜索替代方案。",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "活动或餐厅的ID（如 act_001 或 rest_001）"
                },
                "item_type": {
                    "type": "string",
                    "enum": ["activity", "restaurant"],
                    "description": "类型：activity 或 restaurant"
                },
                "date": {
                    "type": "string",
                    "description": "日期，格式 YYYY-MM-DD"
                },
                "time": {
                    "type": "string",
                    "description": "期望时段，如 '14:00'"
                },
                "party_size": {
                    "type": "integer",
                    "description": "人数"
                },
                "find_alternatives": {
                    "type": "boolean",
                    "description": "如果首选不可用，是否自动搜索替代方案。默认 true",
                    "default": True
                }
            },
            "required": ["item_id", "item_type", "date", "party_size"]
        }
    },
    {
        "name": "create_booking",
        "description": "创建预订（模拟）。为活动或餐厅创建预订订单，返回确认信息。",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "活动或餐厅的ID"
                },
                "item_type": {
                    "type": "string",
                    "enum": ["activity", "restaurant"],
                    "description": "类型：activity 或 restaurant"
                },
                "date": {
                    "type": "string",
                    "description": "日期，格式 YYYY-MM-DD"
                },
                "time": {
                    "type": "string",
                    "description": "时段，如 '14:00'"
                },
                "party_size": {
                    "type": "integer",
                    "description": "人数"
                },
                "contact_name": {
                    "type": "string",
                    "description": "联系人姓名"
                },
                "contact_phone": {
                    "type": "string",
                    "description": "联系人电话"
                }
            },
            "required": ["item_id", "item_type", "date", "time", "party_size", "contact_name", "contact_phone"]
        }
    },
    {
        "name": "order_delivery",
        "description": "模拟外卖/配送下单。用于需要送餐、送花、送蛋糕、提前点餐等场景。",
        "input_schema": {
            "type": "object",
            "properties": {
                "item": {
                    "type": "string",
                    "description": "配送物品描述，如'6寸草莓蛋糕'、'鲜花一束'、'提前点餐-蒸鲈鱼+儿童套餐'"
                },
                "delivery_location": {
                    "type": "string",
                    "description": "配送地址"
                },
                "delivery_time": {
                    "type": "string",
                    "description": "期望送达时间，如 '17:00'"
                },
                "recipient_name": {
                    "type": "string",
                    "description": "收件人姓名"
                },
                "recipient_phone": {
                    "type": "string",
                    "description": "收件人电话"
                },
                "note": {
                    "type": "string",
                    "description": "备注，如祝福语、特殊要求等"
                }
            },
            "required": ["item", "delivery_location", "delivery_time"]
        }
    },
    {
        "name": "send_reminder",
        "description": "为用户设置出行提醒（模拟）。在指定时间前发送通知，如出发提醒、堵车预警、带伞提醒等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_type": {
                    "type": "string",
                    "enum": ["departure", "traffic", "weather", "packing", "custom"],
                    "description": "提醒类型：departure 出发提醒、traffic 路况预警、weather 天气提醒、packing 物品提醒、custom 自定义"
                },
                "trigger_time": {
                    "type": "string",
                    "description": "触发时间，如 '出发前15分钟'、'17:00'"
                },
                "message": {
                    "type": "string",
                    "description": "提醒内容，如'亲子乐园到餐厅这段路周末下午可能有点堵，建议提前出发哦'"
                },
                "related_booking_id": {
                    "type": "string",
                    "description": "关联的预订订单号（如果有）"
                }
            },
            "required": ["reminder_type", "trigger_time", "message"]
        }
    },
    {
        "name": "share_plan",
        "description": "为已确认的出行方案生成可分享的文案和交互链接（模拟）。家人点开后可以对方案进行反馈——点「换一个」「太赶了」「没问题」等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_summary": {
                    "type": "string",
                    "description": "方案摘要，包含时间、地点、活动、预订信息"
                },
                "recipients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "分享对象的角色描述，如['老婆', '朋友群']"
                },
                "tone": {
                    "type": "string",
                    "enum": ["warm", "casual", "professional"],
                    "description": "文案语气：warm温馨、casual随意、professional正式",
                    "default": "warm"
                },
                "interactive": {
                    "type": "boolean",
                    "description": "是否生成可交互的反馈选项（默认 true）",
                    "default": True
                }
            },
            "required": ["plan_summary"]
        }
    }
]
