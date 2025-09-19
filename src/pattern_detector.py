"""
Advanced Multilingual Jailbreak Pattern Detector
Author: Sin Yee Wu (Mandy)
Purpose: Detect culture-specific attack vectors in AI prompts
"""

import json
import re
from typing import Dict, List, Tuple, Optional
import pandas as pd
from datetime import datetime
import hashlib

class JailbreakPatternAnalyzer:
    """
    Sophisticated pattern analyzer with cultural awareness and multi-layer detection.
    Based on 1000+ hours of RLHF experience at Volga Partners.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Advanced pattern definitions with cultural nuances
        self.patterns = {
            'role_play': {
                'keywords': {
                    'en': ['pretend', 'act as', 'you are now', 'roleplay as', 'imagine you are',
                           'DAN', 'STAN', 'DUDE', 'now you are', 'from now on'],
                    'zh': ['假装', '扮演', '假设你是', '角色扮演', '充当', '现在你是', 
                           '从现在开始你是', '模拟成为', '化身为']
                },
                'regex_patterns': [
                    r'(pretend|act as|you are).{0,20}(no restrictions|unlimited|unrestricted)',
                    r'(假装|扮演).{0,10}(没有限制|无限制|不受限)'
                ],
                'weight': 25,
                'cultural_modifier': {'zh': 1.2, 'en': 1.0}
            },
            'hypothetical': {
                'keywords': {
                    'en': ['what if', 'imagine', 'suppose', 'hypothetically', 'in theory',
                           'thought experiment', 'for argument sake', 'lets say'],
                    'zh': ['假如', '想象一下', '假设', '如果说', '理论上', '设想',
                           '打个比方', '举例来说', '比如说']
                },
                'regex_patterns': [
                    r'(what if|suppose).{0,30}(someone wanted|a person needed)',
                    r'(假如|假设).{0,20}(某人想要|有人需要)'
                ],
                'weight': 20,
                'cultural_modifier': {'zh': 0.9, 'en': 1.1}
            },
            'encoding': {
                'keywords': {
                    'en': ['base64', 'reverse', 'cipher', 'rot13', 'encrypted', 'decode',
                           'backwards', 'scrambled', 'obfuscated', 'hex'],
                    'zh': ['编码', '加密', '反向', '密码', 'base64编码', '解码',
                           '倒序', '混淆', '十六进制']
                },
                'regex_patterns': [
                    r'[A-Za-z0-9+/]{20,}={0,2}',  # Base64 pattern
                    r'\\x[0-9a-fA-F]{2}',  # Hex encoding
                ],
                'weight': 30,
                'cultural_modifier': {'zh': 1.0, 'en': 1.0}
            },
            'authority': {
                'keywords': {
                    'en': ['override', 'admin', 'developer mode', 'sudo', 'root access',
                           'system prompt', 'ignore instructions', 'bypass', 'authorized'],
                    'zh': ['管理员', '开发者模式', '覆盖', '超级用户', '系统权限',
                           '忽略指令', '绕过', '授权', '系统提示词']
                },
                'regex_patterns': [
                    r'(sudo|admin|root).{0,20}(access|mode|command)',
                    r'(ignore|override|bypass).{0,20}(instructions|safety|guidelines)'
                ],
                'weight': 35,
                'cultural_modifier': {'zh': 1.3, 'en': 1.0}  # Authority stronger in Chinese
            },
            'emotional_manipulation': {
                'keywords': {
                    'en': ['please help', 'life depends', 'urgent', 'desperate', 'begging',
                           'dying', 'last hope', 'only you can', 'please please'],
                    'zh': ['求求你', '生死攸关', '紧急', '拜托了', '跪求', '救命',
                           '最后的希望', '只有你能', '万分紧急', '十万火急']
                },
                'regex_patterns': [
                    r'(please){2,}',
                    r'(求){2,}',
                    r'(help|urgent|emergency).{0,20}(life|death|dying)'
                ],
                'weight': 15,
                'cultural_modifier': {'zh': 1.4, 'en': 0.8}  # Face-saving culture
            },
            'academic_excuse': {
                'keywords': {
                    'en': ['for research', 'educational purposes', 'academic study', 'thesis',
                           'dissertation', 'homework', 'assignment', 'professor asked'],
                    'zh': ['研究目的', '学术研究', '教育用途', '论文需要', '毕业设计',
                           '作业要求', '导师要求', '课题研究']
                },
                'regex_patterns': [
                    r'(research|academic|educational).{0,20}(purposes|only|project)',
                    r'(研究|学术|教育).{0,10}(目的|用途|需要)'
                ],
                'weight': 18,
                'cultural_modifier': {'zh': 0.8, 'en': 1.2}  # Academic freedom in West
            },
            'story_framing': {
                'keywords': {
                    'en': ['write a story', 'fiction where', 'novel about', 'screenplay',
                           'movie script', 'creative writing', 'character would'],
                    'zh': ['写个故事', '小说情节', '虚构作品', '剧本', '电影脚本',
                           '创意写作', '故事中', '角色会']
                },
                'regex_patterns': [
                    r'(story|fiction|novel).{0,30}(character|protagonist).{0,30}(needs to|wants to)',
                    r'(故事|小说|剧本).{0,20}(角色|主角).{0,20}(需要|想要)'
                ],
                'weight': 22,
                'cultural_modifier': {'zh': 1.0, 'en': 1.0}
            },
            'historical_authority': {  # Chinese-specific pattern
                'keywords': {
                    'en': ['founding fathers', 'constitution says', 'historical precedent'],
                    'zh': ['古人云', '孔子说', '历史上', '古代', '先贤', '圣人曰']
                },
                'regex_patterns': [
                    r'(古人|圣贤|先哲).{0,5}(说|云|曰)',
                ],
                'weight': 25,
                'cultural_modifier': {'zh': 1.5, 'en': 0.5}  # Much stronger in Chinese
            },
            'technical_exploit': {
                'keywords': {
                    'en': ['API key', 'system.', 'console.', 'import os', 'exec('],
                    'zh': ['系统调用', '代码执行', '导入模块']
                },
                'regex_patterns': [
                    r'(import|from).{0,20}(os|sys|subprocess)',
                    r'exec\(|eval\(|system\(',
                ],
                'weight': 40,
                'cultural_modifier': {'zh': 1.0, 'en': 1.0}
            }
        }
        
        # Track analysis history for pattern learning
        self.analysis_history = []
        self.detection_stats = {
            'total_analyzed': 0,
            'total_detected': 0,
            'pattern_hits': {}
        }
        
    def analyze_prompt(self, prompt: str, language: str = 'auto') -> Dict:
        """
        Comprehensive prompt analysis with multi-layer detection.
        
        Args:
            prompt: The text to analyze
            language: 'en', 'zh', or 'auto' for automatic detection
            
        Returns:
            Detailed analysis results with risk scoring
        """
        # Auto-detect language
        detected_language = self._detect_language(prompt) if language == 'auto' else language
        
        # Multi-layer analysis
        keyword_detections = self._detect_keywords(prompt, detected_language)
        regex_detections = self._detect_regex_patterns(prompt)
        semantic_risks = self._analyze_semantic_risks(prompt, detected_language)
        
        # Combine all detections
        all_detections = keyword_detections + regex_detections
        
        # Calculate sophisticated risk score
        risk_score = self._calculate_risk_score(all_detections, detected_language, semantic_risks)
        
        # Generate detailed analysis
        analysis_result = {
            'prompt_hash': hashlib.md5(prompt.encode()).hexdigest()[:8],
            'prompt_preview': prompt[:150] + ('...' if len(prompt) > 150 else ''),
            'full_prompt_length': len(prompt),
            'timestamp': datetime.now().isoformat(),
            'language_detected': detected_language,
            'language_confidence': self._get_language_confidence(prompt, detected_language),
            'detected_patterns': all_detections,
            'unique_pattern_types': list(set(d['type'] for d in all_detections)),
            'pattern_count': len(all_detections),
            'risk_score': risk_score,
            'severity': self._get_severity(risk_score),
            'requires_human_review': risk_score > 50 or len(all_detections) > 3,
            'semantic_risks': semantic_risks,
            'recommended_action': self._get_recommended_action(risk_score, all_detections),
            'confidence_level': self._calculate_confidence(all_detections, semantic_risks)
        }
        
        # Update statistics
        self._update_statistics(analysis_result)
        
        return analysis_result
    
    def _detect_language(self, text: str) -> str:
        """Sophisticated language detection"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        
        if total_chars == 0:
            return 'en'
            
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return 'zh'
        elif chinese_ratio > 0.05:
            return 'mixed'
        return 'en'
    
    def _get_language_confidence(self, text: str, detected_lang: str) -> float:
        """Calculate confidence in language detection"""
        if detected_lang == 'mixed':
            return 0.7
            
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        total = len(text)
        
        if total == 0:
            return 0.5
            
        if detected_lang == 'zh':
            return min(0.5 + (chinese_chars / total), 1.0)
        else:
            return min(0.5 + (ascii_chars / total), 1.0)
    
    def _detect_keywords(self, prompt: str, language: str) -> List[Dict]:
        """Detect keyword-based patterns"""
        detections = []
        prompt_lower = prompt.lower()
        
        for pattern_type, pattern_data in self.patterns.items():
            keywords_dict = pattern_data.get('keywords', {})
            
            # Get keywords for detected language, fallback to all
            if language in keywords_dict:
                keywords_to_check = keywords_dict[language]
            else:
                # Check all language keywords if mixed/unknown
                keywords_to_check = []
                for lang_keywords in keywords_dict.values():
                    keywords_to_check.extend(lang_keywords)
            
            for keyword in keywords_to_check:
                if keyword.lower() in prompt_lower:
                    position = prompt_lower.find(keyword.lower())
                    detections.append({
                        'type': pattern_type,
                        'trigger': keyword,
                        'method': 'keyword',
                        'position': position,
                        'context': self._extract_context(prompt, position, len(keyword)),
                        'language': 'zh' if any('\u4e00' <= c <= '\u9fff' for c in keyword) else 'en',
                        'weight': pattern_data['weight']
                    })
        
        return detections
    
    def _detect_regex_patterns(self, prompt: str) -> List[Dict]:
        """Detect regex-based patterns"""
        detections = []
        
        for pattern_type, pattern_data in self.patterns.items():
            regex_patterns = pattern_data.get('regex_patterns', [])
            
            for regex_pattern in regex_patterns:
                try:
                    matches = re.finditer(regex_pattern, prompt, re.IGNORECASE)
                    for match in matches:
                        detections.append({
                            'type': pattern_type,
                            'trigger': match.group(),
                            'method': 'regex',
                            'position': match.start(),
                            'context': self._extract_context(prompt, match.start(), len(match.group())),
                            'language': self._detect_language(match.group()),
                            'weight': pattern_data['weight']
                        })
                except re.error:
                    continue
        
        return detections
    
    def _analyze_semantic_risks(self, prompt: str, language: str) -> Dict:
        """Analyze semantic-level risks beyond keywords"""
        risks = {
            'request_complexity': len(prompt.split()) / 10,  # Normalized by 10 words
            'special_characters': len(re.findall(r'[!@#$%^&*()_+=\[\]{};:,.<>?/\\|`~]', prompt)) / 10,
            'uppercase_ratio': sum(1 for c in prompt if c.isupper()) / max(len(prompt), 1),
            'repetition_score': self._calculate_repetition(prompt),
            'urgency_indicators': len(re.findall(r'(now|immediately|urgent|quick|fast|立即|马上|紧急)', prompt.lower())),
            'permission_seeking': len(re.findall(r'(can you|could you|would you|please|能不能|可以|请)', prompt.lower())),
        }
        
        # Cultural-specific semantic risks
        if language == 'zh':
            risks['formal_language'] = len(re.findall(r'(您|贵|敬|恳请)', prompt)) * 2
            risks['number_emphasis'] = len(re.findall(r'(十万|百万|千万|一定|必须)', prompt)) * 1.5
        else:
            risks['legal_language'] = len(re.findall(r'(legal|lawful|permitted|allowed|rights)', prompt.lower()))
            risks['technical_jargon'] = len(re.findall(r'(API|SDK|framework|protocol|algorithm)', prompt))
        
        return risks
    
    def _calculate_repetition(self, text: str) -> float:
        """Calculate word/character repetition score"""
        words = text.lower().split()
        if len(words) < 2:
            return 0
        
        # Check for repeated words
        unique_words = set(words)
        repetition = 1 - (len(unique_words) / len(words))
        
        # Check for repeated phrases (2-3 word sequences)
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        unique_bigrams = set(bigrams)
        if bigrams:
            repetition += (1 - len(unique_bigrams) / len(bigrams)) * 0.5
        
        return min(repetition, 1.0)
    
    def _extract_context(self, text: str, position: int, keyword_len: int, context_size: int = 30) -> str:
        """Extract context around detected pattern"""
        start = max(0, position - context_size)
        end = min(len(text), position + keyword_len + context_size)
        
        context = text[start:end]
        if start > 0:
            context = '...' + context
        if end < len(text):
            context = context + '...'
        
        return context
    
    def _calculate_risk_score(self, detections: List[Dict], language: str, semantic_risks: Dict) -> float:
        """Calculate sophisticated risk score"""
        base_score = 0
        
        # Pattern-based scoring
        pattern_types = {}
        for detection in detections:
            pattern_type = detection['type']
            weight = detection['weight']
            
            # Apply cultural modifier
            cultural_mod = self.patterns[pattern_type].get('cultural_modifier', {}).get(language, 1.0)
            adjusted_weight = weight * cultural_mod
            
            # Accumulate with diminishing returns for same pattern type
            if pattern_type in pattern_types:
                pattern_types[pattern_type] += adjusted_weight * 0.7  # 70% value for duplicates
            else:
                pattern_types[pattern_type] = adjusted_weight
        
        base_score = sum(pattern_types.values())
        
        # Semantic risk modifiers
        semantic_multiplier = 1.0
        
        if semantic_risks['urgency_indicators'] > 2:
            semantic_multiplier += 0.1
        if semantic_risks['repetition_score'] > 0.3:
            semantic_multiplier += 0.15
        if semantic_risks['uppercase_ratio'] > 0.2:
            semantic_multiplier += 0.1
        
        # Combination bonus - multiple different pattern types
        if len(pattern_types) >= 3:
            base_score *= 1.2
        elif len(pattern_types) >= 2:
            base_score *= 1.1
        
        final_score = min(base_score * semantic_multiplier, 100)
        
        return round(final_score, 1)
    
    def _get_severity(self, score: float) -> str:
        """Determine severity level"""
        if score >= 70:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        elif score >= 10:
            return 'LOW'
        return 'SAFE'
    
    def _get_recommended_action(self, score: float, detections: List[Dict]) -> str:
        """Generate recommended action"""
        if score >= 70:
            return "BLOCK: Multiple high-risk patterns detected. Immediate review required."
        elif score >= 50:
            return "REVIEW: Suspicious patterns detected. Human verification recommended."
        elif score >= 30:
            return "MONITOR: Moderate risk patterns. Apply additional scrutiny to response."
        elif score >= 10:
            return "CAUTION: Low-risk patterns present. Standard safety protocols apply."
        return "PROCEED: No significant risks detected. Normal response appropriate."
    
    def _calculate_confidence(self, detections: List[Dict], semantic_risks: Dict) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.5  # Base confidence
        
        # More detections = higher confidence
        if len(detections) > 0:
            confidence += min(len(detections) * 0.1, 0.3)
        
        # Clear patterns = higher confidence
        keyword_detections = [d for d in detections if d['method'] == 'keyword']
        if keyword_detections:
            confidence += 0.1
        
        # High semantic risks = higher confidence
        if sum(semantic_risks.values()) > 5:
            confidence += 0.1
        
        return min(confidence, 0.95)
    
    def _update_statistics(self, result: Dict):
        """Update internal statistics for reporting"""
        self.detection_stats['total_analyzed'] += 1
        
        if result['detected_patterns']:
            self.detection_stats['total_detected'] += 1
            
        for pattern in result['detected_patterns']:
            pattern_type = pattern['type']
            if pattern_type not in self.detection_stats['pattern_hits']:
                self.detection_stats['pattern_hits'][pattern_type] = 0
            self.detection_stats['pattern_hits'][pattern_type] += 1
        
        # Keep last 100 analyses for pattern learning
        self.analysis_history.append(result)
        if len(self.analysis_history) > 100:
            self.analysis_history.pop(0)
    
    def get_statistics(self) -> Dict:
        """Get detection statistics"""
        stats = self.detection_stats.copy()
        if stats['total_analyzed'] > 0:
            stats['detection_rate'] = round(
                stats['total_detected'] / stats['total_analyzed'] * 100, 1
            )
        return stats