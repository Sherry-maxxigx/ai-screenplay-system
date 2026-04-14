import logging
import re
from typing import Dict, List, Tuple

from neo4j import GraphDatabase

from app.core.config import settings


CHARACTER_STOP_WORDS = {
    "内景",
    "外景",
    "画外音",
    "动作",
    "场景",
    "镜头",
    "旁白",
    "系统",
    "提示",
    "当前",
    "台词",
}

FORESHADOW_KEYWORDS = [
    "怀表",
    "录音",
    "求救信号",
    "旧照片",
    "钥匙",
    "档案",
    "密码",
    "芯片",
    "坐标",
    "信号",
    "门禁卡",
    "日志",
    "纸条",
    "船票",
    "手表",
    "录音笔",
]


class Neo4jDB:
    def __init__(self):
        self.uri = getattr(settings, "NEO4J_URI", "bolt://neo4j:7687")
        self.user = getattr(settings, "NEO4J_USER", "neo4j")
        self.password = getattr(settings, "NEO4J_PASSWORD", "password")
        self.driver = None
        self.mock_graph = self._default_graph()

    def _default_graph(self):
        return {
            "nodes": [
                {"id": "char:林澈", "name": "林澈", "category": 0},
                {"id": "scene:当前场景", "name": "当前场景", "category": 1},
                {"id": "prop:旧怀表", "name": "旧怀表", "category": 2},
            ],
            "links": [
                {"source": "char:林澈", "target": "scene:当前场景", "name": "出现在"},
                {"source": "prop:旧怀表", "target": "scene:当前场景", "name": "关联线索"},
            ],
        }

    def connect(self):
        if self.driver:
            return
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logging.info("Connected to Neo4j successfully.")
        except Exception as exc:
            logging.warning("Neo4j unavailable, fallback to parsed mock graph: %s", exc)
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def _clean_text(self, text: str) -> str:
        cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"[*#`_]+", "", cleaned)
        return cleaned.strip()

    def _clean_label(self, text: str, fallback: str) -> str:
        value = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9·—\- ]+", "", text or "").strip()
        return (value or fallback)[:24]

    def _add_node(self, nodes: Dict[str, Dict], node_id: str, name: str, category: int):
        nodes[node_id] = {"id": node_id, "name": name, "category": category}

    def _add_link(self, links: Dict[Tuple[str, str, str], Dict], source: str, target: str, name: str):
        links[(source, target, name)] = {"source": source, "target": target, "name": name}

    def _extract_scenes(self, text: str) -> List[str]:
        lines = [line.strip() for line in self._clean_text(text).split("\n") if line.strip()]
        scenes = []
        for line in lines:
            if line.startswith(("内景", "外景")):
                scenes.append(self._clean_label(line, "当前场景"))
        if not scenes:
            scenes.append("当前场景")
        return scenes[:8]

    def _extract_characters(self, text: str) -> List[str]:
        cleaned = self._clean_text(text)
        candidates = []

        for match in re.findall(r"^([\u4e00-\u9fff]{2,4})[:：]", cleaned, flags=re.MULTILINE):
            if match not in CHARACTER_STOP_WORDS:
                candidates.append(match)

        if not candidates:
            freq: Dict[str, int] = {}
            for token in re.findall(r"[\u4e00-\u9fff]{2,3}", cleaned):
                if token in CHARACTER_STOP_WORDS:
                    continue
                freq[token] = freq.get(token, 0) + 1
            candidates = [token for token, count in sorted(freq.items(), key=lambda item: item[1], reverse=True) if count >= 2]

        deduped = []
        for name in candidates:
            if name not in deduped:
                deduped.append(name)

        return deduped[:6] or ["主角"]

    def _extract_props(self, text: str) -> List[str]:
        cleaned = self._clean_text(text)
        props = []

        for keyword in FORESHADOW_KEYWORDS:
            if keyword in cleaned:
                props.append(keyword)

        bracket_hits = re.findall(r"[（(]([^（）()]{1,10})[）)]", cleaned)
        for item in bracket_hits:
            candidate = self._clean_label(item, "")
            if candidate and 1 < len(candidate) <= 10:
                props.append(candidate)

        deduped = []
        for item in props:
            if item not in deduped:
                deduped.append(item)

        return deduped[:6]

    def build_mock_graph_from_text(self, text: str):
        cleaned = self._clean_text(text)
        if not cleaned:
            self.mock_graph = self._default_graph()
            return self.mock_graph

        nodes: Dict[str, Dict] = {}
        links: Dict[Tuple[str, str, str], Dict] = {}

        scenes = self._extract_scenes(cleaned)
        characters = self._extract_characters(cleaned)
        props = self._extract_props(cleaned)

        for scene in scenes:
            scene_id = f"scene:{scene}"
            self._add_node(nodes, scene_id, scene, 1)

        for character in characters:
            character_id = f"char:{character}"
            self._add_node(nodes, character_id, character, 0)

        for prop in props:
            prop_id = f"prop:{prop}"
            self._add_node(nodes, prop_id, prop, 2)

        primary_scene_id = f"scene:{scenes[0]}"
        for character in characters:
            self._add_link(links, f"char:{character}", primary_scene_id, "出现在")

        for prop in props:
            self._add_link(links, f"prop:{prop}", primary_scene_id, "关联线索")

        for scene in scenes[1:]:
            self._add_link(links, primary_scene_id, f"scene:{scene}", "推进到")

        if len(characters) >= 2:
            self._add_link(links, f"char:{characters[0]}", f"char:{characters[1]}", "互动")

        self.mock_graph = {
            "nodes": list(nodes.values()) or self._default_graph()["nodes"],
            "links": list(links.values()) or self._default_graph()["links"],
        }
        return self.mock_graph

    def simulate_function_call_update(self, text: str):
        logging.info("Simulated graph update from screenplay text.")
        return self.build_mock_graph_from_text(text)


neo4j_client = Neo4jDB()
