#!/usr/bin/env python3
"""
本地意图识别器
不依赖大模型API，使用关键词匹配、规则引擎和文本相似度算法

支持的识别策略：
1. 精确关键词匹配
2. 模糊关键词匹配（包含关系）
3. 同义词扩展
4. 正则表达式规则
5. 编辑距离相似度
6. TF-IDF + 余弦相似度
7. 组合权重评分
"""

import re
import math
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class MatchStrategy(Enum):
    """匹配策略"""
    EXACT = "exact"           # 精确匹配
    CONTAINS = "contains"     # 包含匹配
    FUZZY = "fuzzy"          # 模糊匹配
    REGEX = "regex"          # 正则匹配
    SIMILARITY = "similarity" # 相似度匹配


@dataclass
class IntentPattern:
    """意图模式定义"""
    intent: str                           # 意图名称
    keywords: List[str] = field(default_factory=list)      # 关键词列表
    synonyms: Dict[str, List[str]] = field(default_factory=dict)  # 同义词映射
    patterns: List[str] = field(default_factory=list)      # 正则表达式模式
    examples: List[str] = field(default_factory=list)      # 示例句子
    weight: float = 1.0                   # 权重
    priority: int = 0                     # 优先级（数字越大优先级越高）


@dataclass
class RecognitionResult:
    """识别结果"""
    intent: str                           # 识别出的意图
    confidence: float                     # 置信度 (0-1)
    matched_keywords: List[str]           # 匹配到的关键词
    match_strategy: str                   # 使用的匹配策略
    details: Dict = field(default_factory=dict)  # 详细信息


class TextPreprocessor:
    """文本预处理器"""
    
    # 停用词列表
    STOPWORDS = {
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '什么', '吗', '啊', '呢', '吧', '嗯', '哦', '呀', '哈',
        '请', '请问', '想', '想要', '可以', '能', '能不能', '可不可以', '帮', '帮我',
        '麻烦', '一下', '下', '谢谢', '感谢', '您好', '你好', '喂', '嘿'
    }
    
    # 标点符号
    PUNCTUATION = set('，。！？、；：""''（）【】《》—…·～,.!?;:\'"()[]<>-')
    
    @classmethod
    def preprocess(cls, text: str) -> str:
        """预处理文本"""
        if not text:
            return ""
        
        # 转小写（对英文）
        text = text.lower()
        
        # 去除标点
        text = ''.join(c for c in text if c not in cls.PUNCTUATION)
        
        # 去除多余空格
        text = ' '.join(text.split())
        
        return text.strip()
    
    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """分词（简单实现，按字符和空格分割）"""
        text = cls.preprocess(text)
        if not text:
            return []
        
        # 简单分词：中文按字符，英文按空格
        tokens = []
        current_word = ""
        
        for char in text:
            if char == ' ':
                if current_word:
                    tokens.append(current_word)
                    current_word = ""
            elif '\u4e00' <= char <= '\u9fff':
                # 中文字符
                if current_word:
                    tokens.append(current_word)
                    current_word = ""
                tokens.append(char)
            else:
                # 英文或数字
                current_word += char
        
        if current_word:
            tokens.append(current_word)
        
        return tokens
    
    @classmethod
    def remove_stopwords(cls, tokens: List[str]) -> List[str]:
        """去除停用词"""
        return [t for t in tokens if t not in cls.STOPWORDS]
    
    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        """提取关键词"""
        tokens = cls.tokenize(text)
        return cls.remove_stopwords(tokens)


class SimilarityCalculator:
    """相似度计算器"""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """计算编辑距离（Levenshtein距离）"""
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def edit_distance_similarity(s1: str, s2: str) -> float:
        """基于编辑距离的相似度 (0-1)"""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        distance = SimilarityCalculator.levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        return 1 - (distance / max_len)
    
    @staticmethod
    def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
        """Jaccard相似度"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
        
        # 计算点积
        dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in set(vec1) | set(vec2))
        
        # 计算模
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class TFIDFVectorizer:
    """TF-IDF向量化器"""
    
    def __init__(self):
        self.document_freq: Dict[str, int] = defaultdict(int)
        self.total_docs = 0
        self.vocabulary: Set[str] = set()
    
    def fit(self, documents: List[str]):
        """训练（计算文档频率）"""
        self.document_freq.clear()
        self.vocabulary.clear()
        self.total_docs = len(documents)
        
        for doc in documents:
            tokens = set(TextPreprocessor.extract_keywords(doc))
            self.vocabulary.update(tokens)
            for token in tokens:
                self.document_freq[token] += 1
    
    def transform(self, text: str) -> Dict[str, float]:
        """转换为TF-IDF向量"""
        tokens = TextPreprocessor.extract_keywords(text)
        if not tokens:
            return {}
        
        # 计算TF（词频）
        tf = defaultdict(int)
        for token in tokens:
            tf[token] += 1
        
        # 归一化TF
        max_tf = max(tf.values()) if tf else 1
        
        # 计算TF-IDF
        tfidf = {}
        for token, freq in tf.items():
            tf_normalized = freq / max_tf
            # IDF = log(总文档数 / (包含该词的文档数 + 1))
            idf = math.log((self.total_docs + 1) / (self.document_freq.get(token, 0) + 1)) + 1
            tfidf[token] = tf_normalized * idf
        
        return tfidf


class LocalIntentRecognizer:
    """本地意图识别器"""
    
    def __init__(self):
        self.intent_patterns: Dict[str, IntentPattern] = {}
        self.tfidf = TFIDFVectorizer()
        self.intent_vectors: Dict[str, Dict[str, float]] = {}
        self._trained = False
        
        # 默认配置
        self.config = {
            'keyword_weight': 0.4,        # 关键词匹配权重
            'similarity_weight': 0.3,     # 相似度匹配权重
            'pattern_weight': 0.3,        # 正则匹配权重
            'min_confidence': 0.3,        # 最小置信度阈值
            'fuzzy_threshold': 0.6,       # 模糊匹配阈值
        }
    
    def add_intent(self, pattern: IntentPattern):
        """添加意图模式"""
        self.intent_patterns[pattern.intent] = pattern
        self._trained = False
    
    def add_intents_from_dict(self, intent_dict: Dict[str, Dict]):
        """从字典批量添加意图"""
        for intent_name, config in intent_dict.items():
            pattern = IntentPattern(
                intent=intent_name,
                keywords=config.get('keywords', []),
                synonyms=config.get('synonyms', {}),
                patterns=config.get('patterns', []),
                examples=config.get('examples', []),
                weight=config.get('weight', 1.0),
                priority=config.get('priority', 0)
            )
            self.add_intent(pattern)
    
    def train(self):
        """训练模型（计算TF-IDF）"""
        if not self.intent_patterns:
            return
        
        # 收集所有示例文本
        all_examples = []
        for pattern in self.intent_patterns.values():
            all_examples.extend(pattern.examples)
            all_examples.extend(pattern.keywords)
        
        # 训练TF-IDF
        if all_examples:
            self.tfidf.fit(all_examples)
        
        # 计算每个意图的向量（基于关键词和示例）
        for intent, pattern in self.intent_patterns.items():
            combined_text = ' '.join(pattern.keywords + pattern.examples)
            self.intent_vectors[intent] = self.tfidf.transform(combined_text)
        
        self._trained = True
    
    def _expand_synonyms(self, text: str, pattern: IntentPattern) -> str:
        """扩展同义词"""
        expanded = text
        for word, synonyms in pattern.synonyms.items():
            for synonym in synonyms:
                if synonym in expanded:
                    expanded = expanded.replace(synonym, word)
        return expanded
    
    def _keyword_match(self, text: str, pattern: IntentPattern) -> Tuple[float, List[str]]:
        """关键词匹配"""
        text_lower = text.lower()
        matched = []
        
        # 扩展同义词
        expanded_text = self._expand_synonyms(text_lower, pattern)
        
        for keyword in pattern.keywords:
            keyword_lower = keyword.lower()
            # 精确包含匹配
            if keyword_lower in expanded_text:
                matched.append(keyword)
            # 模糊匹配
            elif self._fuzzy_match(keyword_lower, expanded_text):
                matched.append(keyword)
        
        if not pattern.keywords:
            return 0.0, []
        
        score = len(matched) / len(pattern.keywords)
        return score, matched
    
    def _fuzzy_match(self, keyword: str, text: str) -> bool:
        """模糊匹配"""
        # 检查文本中是否有与关键词相似的部分
        tokens = TextPreprocessor.tokenize(text)
        
        for i in range(len(tokens)):
            # 尝试不同长度的组合
            for j in range(i + 1, min(i + len(keyword) + 2, len(tokens) + 1)):
                segment = ''.join(tokens[i:j])
                similarity = SimilarityCalculator.edit_distance_similarity(keyword, segment)
                if similarity >= self.config['fuzzy_threshold']:
                    return True
        
        return False
    
    def _pattern_match(self, text: str, pattern: IntentPattern) -> Tuple[float, List[str]]:
        """正则表达式匹配"""
        if not pattern.patterns:
            return 0.0, []
        
        matched = []
        for regex_pattern in pattern.patterns:
            try:
                if re.search(regex_pattern, text, re.IGNORECASE):
                    matched.append(regex_pattern)
            except re.error:
                continue
        
        score = len(matched) / len(pattern.patterns)
        return score, matched
    
    def _similarity_match(self, text: str, intent: str) -> float:
        """相似度匹配"""
        if not self._trained or intent not in self.intent_vectors:
            return 0.0
        
        text_vector = self.tfidf.transform(text)
        intent_vector = self.intent_vectors[intent]
        
        return SimilarityCalculator.cosine_similarity(text_vector, intent_vector)
    
    def _example_similarity(self, text: str, pattern: IntentPattern) -> float:
        """与示例句子的相似度"""
        if not pattern.examples:
            return 0.0
        
        max_similarity = 0.0
        text_tokens = set(TextPreprocessor.extract_keywords(text))
        
        for example in pattern.examples:
            example_tokens = set(TextPreprocessor.extract_keywords(example))
            similarity = SimilarityCalculator.jaccard_similarity(text_tokens, example_tokens)
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def recognize(self, text: str, available_intents: List[str] = None) -> RecognitionResult:
        """
        识别用户意图
        
        Args:
            text: 用户输入文本
            available_intents: 可选的意图列表（如果指定，只在这些意图中识别）
        
        Returns:
            RecognitionResult: 识别结果
        """
        if not text or not text.strip():
            return RecognitionResult(
                intent="silence",
                confidence=1.0,
                matched_keywords=[],
                match_strategy="empty_input",
                details={"reason": "用户输入为空"}
            )
        
        # 确保已训练
        if not self._trained:
            self.train()
        
        # 预处理文本
        processed_text = TextPreprocessor.preprocess(text)
        
        # 确定候选意图
        if available_intents:
            candidates = {k: v for k, v in self.intent_patterns.items() if k in available_intents}
        else:
            candidates = self.intent_patterns
        
        if not candidates:
            return RecognitionResult(
                intent="default",
                confidence=0.0,
                matched_keywords=[],
                match_strategy="no_candidates",
                details={"reason": "没有可用的意图候选"}
            )
        
        # 计算每个意图的得分
        scores: List[Tuple[str, float, Dict]] = []
        
        for intent, pattern in candidates.items():
            # 关键词匹配
            keyword_score, matched_keywords = self._keyword_match(processed_text, pattern)
            
            # 正则匹配
            pattern_score, matched_patterns = self._pattern_match(text, pattern)
            
            # 相似度匹配
            similarity_score = self._similarity_match(processed_text, intent)
            
            # 示例相似度
            example_score = self._example_similarity(processed_text, pattern)
            
            # 综合得分
            combined_score = (
                keyword_score * self.config['keyword_weight'] +
                max(similarity_score, example_score) * self.config['similarity_weight'] +
                pattern_score * self.config['pattern_weight']
            ) * pattern.weight
            
            details = {
                'keyword_score': keyword_score,
                'pattern_score': pattern_score,
                'similarity_score': similarity_score,
                'example_score': example_score,
                'matched_keywords': matched_keywords,
                'matched_patterns': matched_patterns,
                'priority': pattern.priority
            }
            
            scores.append((intent, combined_score, details))
        
        # 按得分和优先级排序
        scores.sort(key=lambda x: (x[1], x[2]['priority']), reverse=True)
        
        # 获取最佳匹配
        best_intent, best_score, best_details = scores[0]
        
        # 检查是否达到最小置信度
        if best_score < self.config['min_confidence']:
            return RecognitionResult(
                intent="default",
                confidence=best_score,
                matched_keywords=best_details['matched_keywords'],
                match_strategy="below_threshold",
                details={
                    "reason": f"最高得分 {best_score:.2f} 低于阈值 {self.config['min_confidence']}",
                    "best_match": best_intent,
                    "all_scores": {s[0]: s[1] for s in scores[:5]}
                }
            )
        
        # 确定使用的主要匹配策略
        strategy = "combined"
        if best_details['keyword_score'] >= 0.5:
            strategy = "keyword"
        elif best_details['pattern_score'] >= 0.5:
            strategy = "pattern"
        elif best_details['similarity_score'] >= 0.5 or best_details['example_score'] >= 0.5:
            strategy = "similarity"
        
        return RecognitionResult(
            intent=best_intent,
            confidence=min(best_score, 1.0),
            matched_keywords=best_details['matched_keywords'],
            match_strategy=strategy,
            details={
                "scores": best_details,
                "all_candidates": {s[0]: round(s[1], 3) for s in scores[:5]}
            }
        )
    
    def recognize_with_fallback(self, text: str, available_intents: List[str] = None) -> str:
        """
        识别意图，返回意图字符串（兼容原有接口）
        
        Args:
            text: 用户输入
            available_intents: 可用意图列表
        
        Returns:
            str: 识别出的意图
        """
        result = self.recognize(text, available_intents)
        return result.intent


# ==================== 预定义意图库 ====================

class IntentLibrary:
    """预定义意图库"""
    
    # 医院场景意图
    HOSPITAL_INTENTS = {
        "挂号": {
            "keywords": ["挂号", "预约", "看病", "就诊", "门诊", "排号"],
            "synonyms": {
                "挂号": ["挂个号", "挂号码", "取号", "排队"],
                "预约": ["约", "订", "预定"]
            },
            "patterns": [
                r"想.*挂号",
                r"要.*看病",
                r"预约.*门诊",
                r"挂.*科"
            ],
            "examples": [
                "我想挂号",
                "帮我预约一下",
                "我要看病",
                "挂个内科的号",
                "预约明天的门诊"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "缴费": {
            "keywords": ["缴费", "付款", "交钱", "付钱", "支付", "结算", "费用"],
            "synonyms": {
                "缴费": ["交费", "缴款", "付费"],
                "支付": ["付", "给钱"]
            },
            "patterns": [
                r"(缴|交|付)(费|款|钱)",
                r"多少钱",
                r"费用.*查询"
            ],
            "examples": [
                "我要缴费",
                "帮我付款",
                "查一下费用",
                "需要交多少钱",
                "结算一下"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "取药": {
            "keywords": ["取药", "拿药", "药房", "开药", "药品", "处方"],
            "synonyms": {
                "取药": ["领药", "拿药品"],
                "药房": ["药店", "药局"]
            },
            "patterns": [
                r"取.*药",
                r"拿.*药",
                r"药.*在哪"
            ],
            "examples": [
                "我要取药",
                "药开好了去哪拿",
                "药房在哪里",
                "帮我查一下药"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "查询": {
            "keywords": ["查询", "查看", "查", "看看", "了解", "咨询"],
            "synonyms": {},
            "patterns": [
                r"查.*一下",
                r"看看.*情况"
            ],
            "examples": [
                "查询一下",
                "帮我查查",
                "看看进度"
            ],
            "weight": 0.8,
            "priority": 0
        },
        "内科": {
            "keywords": ["内科", "感冒", "发烧", "咳嗽", "头疼", "头痛", "肚子疼", "胃疼"],
            "synonyms": {
                "头疼": ["头痛", "脑袋疼"],
                "肚子疼": ["肚子痛", "腹痛", "胃痛"]
            },
            "patterns": [
                r"感冒|发烧|咳嗽",
                r"内科"
            ],
            "examples": [
                "我感冒了",
                "有点发烧",
                "挂内科",
                "头疼想看看"
            ],
            "weight": 1.0,
            "priority": 2
        },
        "外科": {
            "keywords": ["外科", "受伤", "骨折", "扭伤", "摔伤", "手术"],
            "synonyms": {},
            "patterns": [
                r"受伤|骨折|扭伤",
                r"外科"
            ],
            "examples": [
                "我受伤了",
                "骨头可能断了",
                "挂外科"
            ],
            "weight": 1.0,
            "priority": 2
        },
        "确认": {
            "keywords": ["确认", "好的", "可以", "行", "没问题", "对", "是的", "确定", "同意"],
            "synonyms": {
                "好的": ["好", "OK", "ok", "嗯", "恩"],
                "可以": ["行", "成", "得"]
            },
            "patterns": [
                r"^(好|行|对|是|嗯|ok)$",
                r"没问题",
                r"确认|确定"
            ],
            "examples": [
                "好的",
                "可以",
                "确认",
                "没问题",
                "行"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "取消": {
            "keywords": ["取消", "不要", "算了", "不用", "放弃", "不想"],
            "synonyms": {},
            "patterns": [
                r"取消|不要|算了",
                r"不.*了"
            ],
            "examples": [
                "取消吧",
                "不要了",
                "算了",
                "我不想要了"
            ],
            "weight": 1.0,
            "priority": 1
        }
    }
    
    # 餐厅场景意图
    RESTAURANT_INTENTS = {
        "点餐": {
            "keywords": ["点餐", "点菜", "下单", "要", "来", "点"],
            "synonyms": {
                "点餐": ["点单", "下单", "点菜"],
            },
            "patterns": [
                r"(点|要|来).*(菜|餐|个|份)",
                r"下单"
            ],
            "examples": [
                "我要点餐",
                "点菜",
                "来一份宫保鸡丁",
                "要一碗米饭"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "菜单": {
            "keywords": ["菜单", "菜品", "有什么", "推荐", "招牌", "特色"],
            "synonyms": {
                "菜单": ["菜谱", "餐单"],
            },
            "patterns": [
                r"(看|要|给).*菜单",
                r"有什么.*吃",
                r"推荐.*菜"
            ],
            "examples": [
                "看看菜单",
                "有什么推荐的",
                "招牌菜是什么"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "结账": {
            "keywords": ["结账", "买单", "付款", "多少钱", "账单", "付钱"],
            "synonyms": {
                "结账": ["结帐", "埋单", "买单"],
            },
            "patterns": [
                r"(结|买|付|给).*单",
                r"多少钱",
                r"账单"
            ],
            "examples": [
                "结账",
                "买单",
                "一共多少钱"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "加菜": {
            "keywords": ["加菜", "再来", "再要", "追加", "多要"],
            "synonyms": {},
            "patterns": [
                r"(再|多|加).*(来|要|点)",
            ],
            "examples": [
                "再来一份",
                "加个菜",
                "多要一碗饭"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "川菜": {
            "keywords": ["川菜", "麻辣", "辣", "四川", "宫保鸡丁", "麻婆豆腐", "水煮鱼"],
            "synonyms": {},
            "patterns": [
                r"川菜|麻辣|辣.*的"
            ],
            "examples": [
                "来点川菜",
                "要辣的",
                "麻辣口味"
            ],
            "weight": 1.0,
            "priority": 2
        },
        "粤菜": {
            "keywords": ["粤菜", "广东", "清淡", "蒸", "白切鸡", "烧鹅"],
            "synonyms": {},
            "patterns": [
                r"粤菜|广东|清淡"
            ],
            "examples": [
                "来点粤菜",
                "清淡一点的",
                "广东菜"
            ],
            "weight": 1.0,
            "priority": 2
        }
    }
    
    # 剧院场景意图
    THEATER_INTENTS = {
        "购票": {
            "keywords": ["购票", "买票", "订票", "预订", "要票"],
            "synonyms": {
                "购票": ["买票", "订票", "预订票"],
            },
            "patterns": [
                r"(买|订|购|要).*票",
            ],
            "examples": [
                "我要买票",
                "订两张票",
                "购票"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "取票": {
            "keywords": ["取票", "拿票", "领票", "换票"],
            "synonyms": {
                "取票": ["拿票", "领票"],
            },
            "patterns": [
                r"(取|拿|领|换).*票",
            ],
            "examples": [
                "取票",
                "来拿票的",
                "换取纸质票"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "演出查询": {
            "keywords": ["演出", "节目", "表演", "剧目", "什么戏", "演什么"],
            "synonyms": {},
            "patterns": [
                r"(有|演)什么",
                r"(节目|演出|剧目).*表"
            ],
            "examples": [
                "今天有什么演出",
                "看看节目单",
                "演什么剧"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "会员": {
            "keywords": ["会员", "积分", "VIP", "会员卡", "办卡"],
            "synonyms": {},
            "patterns": [
                r"会员|积分|VIP",
                r"办.*卡"
            ],
            "examples": [
                "查一下会员积分",
                "办张会员卡",
                "VIP有什么优惠"
            ],
            "weight": 1.0,
            "priority": 1
        },
        "话剧": {
            "keywords": ["话剧", "戏剧", "舞台剧"],
            "synonyms": {},
            "patterns": [r"话剧|戏剧"],
            "examples": ["看话剧", "有什么话剧"],
            "weight": 1.0,
            "priority": 2
        },
        "音乐会": {
            "keywords": ["音乐会", "交响乐", "演唱会", "音乐"],
            "synonyms": {},
            "patterns": [r"音乐会|交响乐|演唱会"],
            "examples": ["听音乐会", "交响乐演出"],
            "weight": 1.0,
            "priority": 2
        },
        "选座": {
            "keywords": ["选座", "座位", "位置", "哪排", "前排", "后排"],
            "synonyms": {},
            "patterns": [
                r"(选|要|换).*座",
                r"座位|位置"
            ],
            "examples": [
                "选座位",
                "要前排的",
                "换个位置"
            ],
            "weight": 1.0,
            "priority": 1
        }
    }
    
    # 通用意图
    COMMON_INTENTS = {
        "确认": {
            "keywords": ["确认", "好的", "可以", "行", "没问题", "对", "是的", "确定", "同意", "好", "嗯", "对的"],
            "synonyms": {
                "好的": ["好", "OK", "ok", "嗯", "恩", "好呀", "好啊"],
                "可以": ["行", "成", "得", "可", "中"]
            },
            "patterns": [
                r"^(好|行|对|是|嗯|ok|可以|没问题|确认|确定)的?$",
            ],
            "examples": ["好的", "可以", "确认", "没问题", "行", "嗯", "对"],
            "weight": 1.2,
            "priority": 3
        },
        "取消": {
            "keywords": ["取消", "不要", "算了", "不用", "放弃", "不想", "不了", "不"],
            "synonyms": {},
            "patterns": [
                r"取消|不要了?|算了|不用了?",
                r"^不$"
            ],
            "examples": ["取消", "不要了", "算了", "不用", "不想要了"],
            "weight": 1.2,
            "priority": 3
        },
        "帮助": {
            "keywords": ["帮助", "帮忙", "怎么", "如何", "怎样", "help"],
            "synonyms": {},
            "patterns": [
                r"怎么.*办",
                r"如何.*操作"
            ],
            "examples": ["帮帮我", "怎么操作", "如何使用"],
            "weight": 0.8,
            "priority": 0
        },
        "返回": {
            "keywords": ["返回", "回去", "上一步", "退回", "back"],
            "synonyms": {},
            "patterns": [r"返回|回去|上一步"],
            "examples": ["返回上一步", "回去", "退回"],
            "weight": 1.0,
            "priority": 1
        }
    }


def create_local_recognizer(scenario: str = None) -> LocalIntentRecognizer:
    """
    创建本地意图识别器工厂函数
    
    Args:
        scenario: 场景名称 ("hospital", "restaurant", "theater", None表示通用)
    
    Returns:
        LocalIntentRecognizer: 配置好的识别器实例
    """
    recognizer = LocalIntentRecognizer()
    
    # 添加通用意图
    recognizer.add_intents_from_dict(IntentLibrary.COMMON_INTENTS)
    
    # 根据场景添加特定意图
    if scenario == "hospital":
        recognizer.add_intents_from_dict(IntentLibrary.HOSPITAL_INTENTS)
    elif scenario == "restaurant":
        recognizer.add_intents_from_dict(IntentLibrary.RESTAURANT_INTENTS)
    elif scenario == "theater":
        recognizer.add_intents_from_dict(IntentLibrary.THEATER_INTENTS)
    else:
        # 添加所有场景意图
        recognizer.add_intents_from_dict(IntentLibrary.HOSPITAL_INTENTS)
        recognizer.add_intents_from_dict(IntentLibrary.RESTAURANT_INTENTS)
        recognizer.add_intents_from_dict(IntentLibrary.THEATER_INTENTS)
    
    # 训练模型
    recognizer.train()
    
    return recognizer


# ==================== 兼容原有接口的适配器 ====================

class LocalIntentRecognizerAdapter:
    """
    本地意图识别器适配器
    提供与GeminiIntentRecognizer相同的接口
    """
    
    def __init__(self, scenario: str = None):
        self.recognizer = create_local_recognizer(scenario)
        self.scenario = scenario
    
    def recognize(self, user_input: str, available_intents: List[str]) -> str:
        """
        识别用户意图（兼容原有接口）
        
        Args:
            user_input: 用户输入
            available_intents: 可用意图列表
        
        Returns:
            str: 识别出的意图
        """
        if not user_input or not user_input.strip():
            return "silence"
        
        result = self.recognizer.recognize(user_input, available_intents)
        
        # 如果识别结果不在可用意图中，返回default
        if result.intent not in available_intents and result.intent not in ["silence", "default"]:
            return "default"
        
        return result.intent


def create_intent_recognizer_local(scenario: str = None) -> LocalIntentRecognizerAdapter:
    """
    创建本地意图识别器（工厂函数，用于替换create_intent_recognizer）
    
    Args:
        scenario: 场景名称
    
    Returns:
        LocalIntentRecognizerAdapter: 识别器实例
    """
    return LocalIntentRecognizerAdapter(scenario)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("本地意图识别器测试")
    print("=" * 60)
    
    # 创建医院场景识别器
    recognizer = create_local_recognizer("hospital")
    
    # 测试用例
    test_cases = [
        ("我想挂号", ["挂号", "缴费", "取药", "查询"]),
        ("帮我预约一下门诊", ["挂号", "缴费", "取药"]),
        ("要交钱", ["挂号", "缴费", "取药"]),
        ("药开好了去哪拿", ["挂号", "缴费", "取药"]),
        ("我感冒了", ["内科", "外科", "眼科"]),
        ("好的", ["确认", "取消"]),
        ("不要了", ["确认", "取消"]),
        ("", ["挂号", "缴费"]),
        ("随便说点什么", ["挂号", "缴费"]),
    ]
    
    print("\n医院场景测试:")
    print("-" * 60)
    
    for text, intents in test_cases:
        result = recognizer.recognize(text, intents)
        print(f"输入: '{text}'")
        print(f"  可用意图: {intents}")
        print(f"  识别结果: {result.intent} (置信度: {result.confidence:.2f})")
        print(f"  匹配策略: {result.match_strategy}")
        if result.matched_keywords:
            print(f"  匹配关键词: {result.matched_keywords}")
        print()
    
    # 测试餐厅场景
    print("\n餐厅场景测试:")
    print("-" * 60)
    
    restaurant_recognizer = create_local_recognizer("restaurant")
    restaurant_tests = [
        ("我要点餐", ["点餐", "菜单", "结账"]),
        ("看看菜单", ["点餐", "菜单", "结账"]),
        ("买单", ["点餐", "菜单", "结账"]),
        ("来点辣的", ["川菜", "粤菜"]),
    ]
    
    for text, intents in restaurant_tests:
        result = restaurant_recognizer.recognize(text, intents)
        print(f"输入: '{text}' -> 识别: {result.intent} (置信度: {result.confidence:.2f})")
    
    print("\n" + "=" * 60)
    print("测试完成")
