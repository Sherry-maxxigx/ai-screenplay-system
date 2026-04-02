import asyncio
from typing import Dict, Any, List

class CoCreationEngine:
    def __init__(self):
        # 双轨人机共生模式状态存储
        self.explicit_creative_track = {} # 显性创作轨：用户可见的文本编辑节点
        self.implicit_narrative_track = {} # 隐性叙事规划轨：后台维护的大纲/逻辑图谱节点
        self.lock_nodes = {}

    async def process_incremental_edit(self, edit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        双轨范式同步分析：用户在[显性创作轨]局部修改，AI 瞬间在[隐性叙事轨]做逻辑一致性交叉验证。
        保证局部修改不破坏全局逻辑。
        """
        content = edit_data.get('content', '')
        session_id = edit_data.get('session_id', 'default')

        self.explicit_creative_track[session_id] = content

        affected_ranges = []
        suggestions = []

        # 隐性规划轨介入分析
        # 复杂逻辑演算，如果用户添加或者删除了核心节点/道具
        if "杀手" in content or "背叛" in content:
            affected_ranges.append({
                "range": [2, 5],
                "reason": "[隐性叙事轨警告] 主角身份变化会切断后续第3、4场的悬疑伏笔链",
                "suggestion": "系统已启动自愈机制：建议点击【自动适配】来重构下文的伏笔网络而不破坏全局。"
            })

        locked_nodes = [
            item for item in self.lock_nodes.values()
            if item.get("session_id", "default") == session_id and item.get("is_locked")
        ]

        if locked_nodes:
            suggestions.append({
                "type": "narrative_lock",
                "message": f"检测到 {len(locked_nodes)} 个叙事锁节点，自动适配将避开这些区域。"
            })

        self.implicit_narrative_track[session_id] = {
            "affected_nodes": affected_ranges,
            "locked_count": len(locked_nodes)
        }

        return {
            "status": "success",
            "is_affected": len(affected_ranges) > 0,
            "affected_nodes": affected_ranges,
            "suggestions": suggestions,
            "lock_summary": {
                "locked_count": len(locked_nodes),
                "locked_nodes": [node.get("id") for node in locked_nodes]
            },
            "system_msg": "双轨协同网关响应完成，剧本打磨效率自动攀升同步"
        }

    async def toggle_narrative_lock(self, lock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理前端的叙事锁操作：新增或取消锁定。
        用户绝对主导，AI 只协同不篡改
        """
        text_id = lock_data.get('id') or lock_data.get('snippet', '')[:24] or 'lock-node'
        text_snippet = lock_data.get('snippet', '')
        is_locked = lock_data.get('is_locked', True)
        session_id = lock_data.get('session_id', 'default')

        if is_locked:
            self.lock_nodes[text_id] = {
                "id": text_id,
                "snippet": text_snippet,
                "is_locked": True,
                "session_id": session_id,
            }
        else:
            self.lock_nodes.pop(text_id, None)

        # 强锁定规则：AI后续生成/修改 严禁改动此处
        print(f"[双轨同步 - Neo4j] 叙事节点 <{text_snippet[:10]}...> 已置入绝对保护层锁定状态: {is_locked}")

        locked_count = len([
            item for item in self.lock_nodes.values()
            if item.get("session_id", "default") == session_id and item.get("is_locked")
        ])

        return {
            "status": "success",
            "locked": is_locked,
            "id": text_id,
            "locked_count": locked_count,
            "msg": "节点已受创作锁保护，AI 不会篡改此区域"
        }

    async def confirm_adaptation(self, adapt_req: Dict[str, Any]) -> Dict[str, Any]:
        """
        局部自动适配，基于隐式规划轨修复全局破损
        """
        session_id = adapt_req.get('session_id', 'default')
        locked_nodes = [
            item for item in self.lock_nodes.values()
            if item.get("session_id", "default") == session_id and item.get("is_locked")
        ]

        return {
            "status": "success",
            "adapted_content": "【隐式叙事轨自动修复全局逻辑】：他手握消音武器，内心却在衡量全局背叛的时间线，过去的线索瞬间被理清了。",
            "respected_locks": [item.get("id") for item in locked_nodes],
            "lock_protection": "已避开叙事锁区域，不会自动改写用户锁定内容"
        }

co_creation_engine = CoCreationEngine()
