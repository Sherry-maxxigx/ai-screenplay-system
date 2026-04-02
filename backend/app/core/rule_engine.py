import re
from typing import Any, Dict, List


class NarrativeRuleEngine:
    """叙事规则内生引擎（轻量版）

    - 强制合规层：硬性一致性规则，不通过则触发修正
    - 创意参考层：节奏与创意建议，只预警不拦截
    """

    ARC_KEYWORDS = ["懵懂", "觉醒", "挣扎", "成长", "蜕变"]

    def evaluate(
        self,
        text: str,
        *,
        stage: str,
        idea: str = "",
        characters: str = "",
    ) -> Dict[str, Any]:
        cleaned = (text or "").strip()
        hard_errors = self._hard_checks(cleaned, stage=stage, idea=idea, characters=characters)
        soft_warnings = self._soft_checks(cleaned, stage=stage)
        metrics = self._build_metrics(cleaned, stage=stage, hard_errors=hard_errors, soft_warnings=soft_warnings)

        return {
            "stage": stage,
            "is_valid": len(hard_errors) == 0,
            "hard_errors": hard_errors,
            "soft_warnings": soft_warnings,
            "metrics": metrics,
        }

    def _hard_checks(self, text: str, *, stage: str, idea: str, characters: str) -> List[Dict[str, str]]:
        errors: List[Dict[str, str]] = []

        if not text:
            errors.append(
                {
                    "code": "EMPTY_OUTPUT",
                    "description": "模型返回为空，无法进入下一阶段。",
                    "fix_instruction": "请补全该阶段内容，确保至少包含核心剧情信息。",
                }
            )
            return errors

        if stage == "outline":
            required = ["第一幕", "第二幕", "第三幕"]
            if not all(item in text for item in required):
                errors.append(
                    {
                        "code": "OUTLINE_3ACT_MISSING",
                        "description": "大纲缺少完整三幕结构。",
                        "fix_instruction": "请补全第一幕、第二幕、第三幕，并明确每幕冲突升级。",
                    }
                )

        if stage == "script":
            scene_hits = len(re.findall(r"^(内景|外景)", text, flags=re.MULTILINE))
            if scene_hits < 2:
                errors.append(
                    {
                        "code": "SCENE_HEADER_MISSING",
                        "description": "剧本场景标题不足，无法形成可执行分场。",
                        "fix_instruction": "请至少输出两场戏，并使用“内景/外景 + 场所 + 时间”格式。",
                    }
                )

            act_section_hits = len(re.findall(r"(第一幕|第二幕|第三幕|结局)·第\d+节", text))
            if act_section_hits == 0:
                errors.append(
                    {
                        "code": "ACT_SECTION_MISSING",
                        "description": "剧本缺少“第几幕第几节”标记，用户难以定位结构。",
                        "fix_instruction": "请在每场前加“第一幕·第1节”这类标签，并与场次一一对应。",
                    }
                )

            has_dialogue = bool(re.search(r"[\u4e00-\u9fff]{2,6}[：:]", text))
            if not has_dialogue:
                errors.append(
                    {
                        "code": "DIALOGUE_MISSING",
                        "description": "剧本缺少人物对白。",
                        "fix_instruction": "请加入角色对白，并通过对白推动冲突。",
                    }
                )

        foreshadow_count = text.count("伏笔")
        recovery_count = text.count("回收")
        if foreshadow_count > 0 and recovery_count == 0 and stage in {"outline", "script"}:
            errors.append(
                {
                    "code": "FORESHADOW_NOT_RECOVERED",
                    "description": "检测到伏笔但未出现回收说明。",
                    "fix_instruction": "请补充至少一个伏笔回收节点，形成闭环。",
                }
            )

        expected_names = self._extract_character_names(characters)
        if expected_names and stage in {"outline", "script"}:
            covered = [name for name in expected_names if name in text]
            if len(covered) == 0:
                errors.append(
                    {
                        "code": "CHARACTER_INCONSISTENT",
                        "description": "生成内容未覆盖输入人物设定。",
                        "fix_instruction": "请确保至少出现一个核心角色，并体现其目标或冲突。",
                    }
                )

        return errors

    def _soft_checks(self, text: str, *, stage: str) -> List[Dict[str, str]]:
        warnings: List[Dict[str, str]] = []

        if stage in {"outline", "script"}:
            conflict_hits = len(re.findall(r"冲突|对抗|矛盾|危机", text))
            if conflict_hits < 2:
                warnings.append(
                    {
                        "code": "LOW_CONFLICT_DENSITY",
                        "description": "冲突密度偏低，建议增加对抗场面或价值冲突。",
                    }
                )

            arc_hits = sum(1 for key in self.ARC_KEYWORDS if key in text)
            if arc_hits < 2:
                warnings.append(
                    {
                        "code": "WEAK_ARC_SIGNAL",
                        "description": "人物弧光信号较弱，建议补足“觉醒-挣扎-蜕变”的变化路径。",
                    }
                )

        if stage == "script":
            beat_hits = len(re.findall(r"第[一二三四五六七八九十\d]+场", text))
            if beat_hits < 3:
                warnings.append(
                    {
                        "code": "BEAT_COUNT_LOW",
                        "description": "分场数量偏少，建议至少三场以保证节奏推进。",
                    }
                )

        return warnings

    def _build_metrics(
        self,
        text: str,
        *,
        stage: str,
        hard_errors: List[Dict[str, str]],
        soft_warnings: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        scene_hits = len(re.findall(r"^(内景|外景)", text, flags=re.MULTILINE))
        beat_hits = len(re.findall(r"第[一二三四五六七八九十\d]+场", text))
        foreshadow_count = text.count("伏笔")
        recovery_count = text.count("回收")

        foreshadow_ratio = 100.0 if foreshadow_count == 0 else min(100.0, recovery_count / foreshadow_count * 100)
        compliance = 100.0 if not hard_errors else max(0.0, 100.0 - len(hard_errors) * 25)
        creative_score = max(60.0, 100.0 - len(soft_warnings) * 10)

        return {
            "stage": stage,
            "scene_count": scene_hits,
            "beat_count": beat_hits,
            "foreshadow_count": foreshadow_count,
            "recovery_count": recovery_count,
            "foreshadow_recovery_rate": round(foreshadow_ratio, 1),
            "hard_compliance_score": round(compliance, 1),
            "creative_reference_score": round(creative_score, 1),
        }

    def _extract_character_names(self, characters: str) -> List[str]:
        names: List[str] = []
        text = characters or ""

        for match in re.findall(r"姓名[：:]\s*([\u4e00-\u9fff]{2,6})", text):
            if match not in names:
                names.append(match)

        for match in re.findall(r"([\u4e00-\u9fff]{2,6})（", text):
            if match not in names:
                names.append(match)

        return names
