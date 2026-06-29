"""
Entity Linking and Alias Merging Service (Bilingual Support)
=============================================================

实体链接与别名合并服务，支持中英文双语概念融合。

Intelligently links extracted entities to existing concepts in the knowledge
graph. Uses a multi-strategy fusion approach to find the best canonical name
for each entity, handling exact matches, fuzzy matches, alias resolution,
and cross-language translation matching.

Fusion strategy / 融合策略::

    1. Case-insensitive exact match → use existing concept name
    2. Substring/similarity fuzzy match → merge into most similar concept
    3. Translation pair match (e.g., "知识图谱" ↔ "Knowledge Graph")
       / 翻译对匹配 → link as aliases
    4. No match → create new concept node

This prevents concept duplication and maintains graph consistency.
"""
from typing import List, Dict, Optional, Set
from models.document import Triplet
from infra.neo4j_client import neo4j_client
import re


class EntityLinker:
    """
    Link entities to existing concepts and merge aliases with intelligent fusion.
    实体链接与智能合并，将抽取的实体关联到已有的概念。

    Maintains an in-memory alias dictionary and concept cache to accelerate
    repeated lookups during batch processing.

    Attributes:
        alias_dict:     In-memory alias → canonical name mapping
                        / 内存中的别名到规范名称映射
        concept_cache:  Recently accessed concepts cache
                       / 最近访问的概念缓存
    """

    def __init__(self):
        # Bilingual alias dictionary / 双语别名词典
        self.alias_dict: Dict[str, str] = {}
        # Cache for recently linked concepts / 最近链接的概念缓存
        self.concept_cache: Dict[str, Dict] = {}

    def link_and_merge(self, triplets: List[Triplet]) -> List[Triplet]:
        """
        Link entities to existing concepts and merge into the graph.
        将实体链接到已有概念并合并到图中。

        For each triplet, normalizes the subject and object names, then
        applies the fusion strategy to find canonical names.

        Args:
            triplets:  List of extracted triplets / 抽取的三元组列表

        Returns:
            List of triplets with entities linked to canonical names
            实体已链接到规范名称的三元组列表
        """
        print(f"\n{'='*80}")
        print(
            f"🔗 [实体链接] 开始处理 {len(triplets)} 个三元组"
        )

        linked_triplets = []
        link_stats = {
            "exact_match": 0,
            "fuzzy_match": 0,
            "translation_match": 0,
            "new_concept": 0,
            "cached": 0,
            "normalized": 0,
        }

        for idx, triplet in enumerate(triplets, 1):
            original_subject = triplet.subject
            original_object = triplet.object

            # Normalize subject and object / 标准化主体和客体
            subject_normalized = self._normalize_entity(triplet.subject)
            object_normalized = self._normalize_entity(triplet.object)

            if (
                subject_normalized != original_subject
                or object_normalized != original_object
            ):
                link_stats["normalized"] += 1
                if idx <= 5:
                    print(
                        f"📝 [{idx}] 规范化: "
                        f"'{original_subject}' → '{subject_normalized}', "
                        f"'{original_object}' → '{object_normalized}'"
                    )

            # Find canonical names / 查找规范化名称（合并）
            subject_canonical, subject_match_type = (
                self._find_or_merge_concept(subject_normalized)
            )
            object_canonical, object_match_type = (
                self._find_or_merge_concept(object_normalized)
            )

            # Update statistics / 更新统计信息
            if subject_match_type in link_stats:
                link_stats[subject_match_type] += 1
            if object_match_type in link_stats:
                link_stats[object_match_type] += 1

            # Update triplet with canonical names / 更新三元组
            triplet.subject = subject_canonical
            triplet.object = object_canonical

            # Display link results (first 5) / 显示链接结果（前5个）
            if idx <= 5:
                if subject_canonical != subject_normalized:
                    print(
                        f"   🔗 主体链接: "
                        f"'{subject_normalized}' → '{subject_canonical}' "
                        f"({subject_match_type})"
                    )
                if object_canonical != object_normalized:
                    print(
                        f"   🔗 客体链接: "
                        f"'{object_normalized}' → '{object_canonical}' "
                        f"({object_match_type})"
                    )

            linked_triplets.append(triplet)

        # Display final statistics / 显示最终统计信息
        print(f"\n📊 [实体链接] 统计信息:")
        print(f"   - 精确匹配: {link_stats['exact_match']} 次")
        print(f"   - 模糊匹配: {link_stats['fuzzy_match']} 次")
        print(f"   - 翻译匹配: {link_stats['translation_match']} 次")
        print(f"   - 新建概念: {link_stats['new_concept']} 次")
        print(f"   - 规范化处理: {link_stats['normalized']} 次")
        print(
            f"✅ [实体链接] 完成，处理了 "
            f"{len(linked_triplets)} 个三元组"
        )
        print(f"{'='*80}\n")

        return linked_triplets

    def _normalize_entity(self, entity: str) -> str:
        """
        Normalize an entity name with bilingual support.
        规范化实体名称，支持中英文。

        Operations performed / 执行的操作::
            - Trim whitespace / 去除前后空格
            - Remove multiple consecutive spaces / 移除多余空格
            - Check alias dictionary for existing mappings
              / 检查别名词典中的映射

        Args:
            entity:  Raw entity name / 原始实体名称

        Returns:
            Normalized entity name / 规范化后的实体名称
        """
        if not entity:
            return entity

        # Basic normalization / 基本规范化
        normalized = entity.strip()
        normalized = re.sub(r'\s+', ' ', normalized)

        # Check alias dictionary / 检查别名词典
        normalized_lower = normalized.lower()
        if normalized_lower in self.alias_dict:
            return self.alias_dict[normalized_lower]

        return normalized

    def _find_or_merge_concept(
        self, name: str
    ) -> tuple[str, str]:
        """
        Find existing concept or intelligently merge with similar ones.
        查找已有概念或智能合并到相似概念。

        Returns (canonical_name, match_type) for graph insertion.

        Fusion strategy / 融合策略::

            1. Exact match (case-insensitive) → use existing
            2. Fuzzy match (similarity) → merge into most similar
            3. Translation match (bilingual pairs) → link as aliases
            4. No match → create new concept

        Args:
            name:  Entity name to resolve / 要解析的实体名称

        Returns:
            Tuple of (canonical_name, match_type)
            元组：(规范名称, 匹配类型)
            match_type is one of:
            "exact_match", "fuzzy_match", "translation_match",
            "new_concept", "cached"
        """
        if not name:
            return name, "exact_match"

        # Check cache first / 先检查缓存
        if name in self.concept_cache:
            cached = self.concept_cache[name]
            return cached.get('canonical_name', name), "cached"

        # 1. Exact match (case-insensitive) / 精确匹配不区分大小写
        existing = neo4j_client.find_concept_by_name(name)
        if existing:
            self.concept_cache[name] = existing['c']
            return name, "exact_match"

        # 2. Fuzzy match / 模糊匹配
        similar_concepts = neo4j_client.find_similar_concepts(
            name, threshold=0.7
        )

        if similar_concepts:
            best_match = self._select_best_match(name, similar_concepts)

            if best_match:
                canonical = best_match['c']['name']

                # Store alias mapping for future lookups
                # 存储别名映射供后续查询
                self.alias_dict[name.lower()] = canonical

                # Add as alias in Neo4j / 在 Neo4j 中添加别名
                neo4j_client.add_concept_alias(canonical, name)

                self.concept_cache[name] = best_match['c']
                return canonical, "fuzzy_match"

        # 3. Translation match (bilingual) / 翻译对匹配（双语）
        translation_match = self._find_translation_match(name)
        if translation_match:
            canonical = translation_match['name']
            self.alias_dict[name.lower()] = canonical
            neo4j_client.add_concept_alias(canonical, name)
            return canonical, "translation_match"

        # 4. No match — create new concept / 无匹配——创建新概念
        neo4j_client.create_concept(name)
        self.concept_cache[name] = {'name': name}
        return name, "new_concept"

    def _select_best_match(
        self, name: str, candidates: List[Dict]
    ) -> Optional[Dict]:
        """
        Select the best matching concept from a list of candidates.
        从候选列表中选出最佳匹配的概念。

        Scoring criteria / 评分标准::

            - Exact substring containment → high score (0.8)
            - Name length similarity → medium score (0.2 × ratio)
            - Combined score must exceed threshold (0.7)

        Args:
            name:        Entity name to match / 待匹配的实体名称
            candidates:  List of candidate concept records / 候选概念记录列表

        Returns:
            Best matching candidate, or None if below threshold
            最佳匹配候选，低于阈值则返回 None
        """
        if not candidates:
            return None

        best_score = 0.0
        best_candidate = None

        name_lower = name.lower()

        for candidate in candidates:
            candidate_name = candidate['c']['name']
            candidate_lower = candidate_name.lower()

            score = 0.0

            # Exact match (case-insensitive) / 精确匹配（不区分大小写）
            if name_lower == candidate_lower:
                return candidate

            # Substring match / 子串匹配
            if (
                name_lower in candidate_lower
                or candidate_lower in name_lower
            ):
                score += 0.8

            # Length similarity / 长度相似度
            len_ratio = min(
                len(name), len(candidate_name)
            ) / max(len(name), len(candidate_name))
            score += len_ratio * 0.2

            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate if best_score >= 0.7 else None

    def _find_translation_match(
        self, name: str
    ) -> Optional[Dict]:
        """
        Find potential translation matches between Chinese and English.
        查找潜在的中英文翻译对。

        Uses a built-in dictionary of common technical translations.
        This is a simplified version — a production system would use a
        translation API or comprehensive bilingual dictionary.

        Args:
            name:  Entity name to check / 待检查的实体名称

        Returns:
            Concept record if a translation match is found, None otherwise
            如果找到翻译匹配则返回概念记录，否则返回 None
        """
        # Common translation pairs (both directions)
        # 常见翻译对（双向）
        translation_pairs = {
            # Chinese → English / 中文 → 英文
            '知识图谱': 'Knowledge Graph',
            '人工智能': 'Artificial Intelligence',
            '机器学习': 'Machine Learning',
            '深度学习': 'Deep Learning',
            '神经网络': 'Neural Network',
            '自然语言处理': 'Natural Language Processing',
            '计算机视觉': 'Computer Vision',
            '数据库': 'Database',
            '算法': 'Algorithm',
            '数据结构': 'Data Structure',
            # English → Chinese / 英文 → 中文
            'knowledge graph': '知识图谱',
            'artificial intelligence': '人工智能',
            'machine learning': '机器学习',
            'deep learning': '深度学习',
            'neural network': '神经网络',
            'natural language processing': '自然语言处理',
            'computer vision': '计算机视觉',
            'database': '数据库',
            'algorithm': '算法',
            'data structure': '数据结构',
        }

        name_lower = name.lower()

        if name_lower in translation_pairs:
            translated = translation_pairs[name_lower]
            existing = neo4j_client.find_concept_by_name(translated)
            if existing:
                return existing['c']

        return None

    def add_alias(self, alias: str, canonical: str):
        """
        Manually add an alias mapping.
        手动添加别名映射。

        Args:
            alias:      Alias name / 别名
            canonical:  Canonical name / 规范名称
        """
        self.alias_dict[alias.lower()] = canonical

    def get_concept_stats(self) -> Dict[str, int]:
        """
        Get statistics about the concept cache and alias dictionary.
        获取概念缓存和别名词典的统计信息。

        Returns:
            Dict with cached_concepts and alias_mappings counts
            包含缓存概念数和别名映射数的字典
        """
        return {
            'cached_concepts': len(self.concept_cache),
            'alias_mappings': len(self.alias_dict),
        }
