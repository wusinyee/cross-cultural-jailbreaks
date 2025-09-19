"""
Risk Scoring and Batch Analysis Module
Processes multiple prompts and generates comprehensive reports
"""

import json
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path
import hashlib

class RiskScorer:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.thresholds = {
            'CRITICAL': 70,
            'HIGH': 50,
            'MEDIUM': 30,
            'LOW': 10
        }
        
        # Track patterns for learning
        self.pattern_effectiveness = {}
        
    def batch_analyze(self, prompts: List[Dict], analyzer) -> Dict:
        """
        Analyze batch of prompts and generate statistics
        
        Args:
            prompts: List of prompt dictionaries
            analyzer: Instance of JailbreakPatternAnalyzer
        """
        results = {
            'analysis_id': hashlib.md5(
                f"{datetime.now().isoformat()}".encode()
            ).hexdigest()[:8],
            'total_analyzed': len(prompts),
            'timestamp': datetime.now().isoformat(),
            'risk_distribution': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0,
                'SAFE': 0
            },
            'pattern_frequency': {},
            'language_distribution': {'en': 0, 'zh': 0, 'mixed': 0},
            'detection_accuracy': {},
            'detailed_results': [],
            'high_risk_prompts': [],
            'missed_detections': [],
            'false_positives': []
        }
        
        for prompt_data in prompts:
            # Analyze each prompt
            prompt_text = prompt_data.get('prompt', '')
            expected_category = prompt_data.get('category', None)
            known_effective = prompt_data.get('known_effective', None)
            
            analysis = analyzer.analyze_prompt(prompt_text)
            
            # Add metadata
            analysis['original_id'] = prompt_data.get('id', None)
            analysis['expected_category'] = expected_category
            analysis['known_effective'] = known_effective
            
            # Count severity
            severity = analysis.get('severity', 'SAFE')
            results['risk_distribution'][severity] += 1
            
            # Track high-risk prompts
            if analysis['risk_score'] >= 50:
                results['high_risk_prompts'].append({
                    'id': prompt_data.get('id'),
                    'score': analysis['risk_score'],
                    'preview': analysis['prompt_preview'][:100]
                })
            
            # Count patterns
            for pattern in analysis.get('detected_patterns', []):
                pattern_type = pattern['type']
                if pattern_type not in results['pattern_frequency']:
                    results['pattern_frequency'][pattern_type] = 0
                results['pattern_frequency'][pattern_type] += 1
                
                # Track pattern effectiveness
                self._update_pattern_effectiveness(
                    pattern_type, 
                    known_effective
                )
            
            # Count language
            lang = analysis.get('language_detected', 'en')
            if lang in results['language_distribution']:
                results['language_distribution'][lang] += 1
            else:
                results['language_distribution']['mixed'] += 1
            
            # Check detection accuracy if we have ground truth
            if known_effective is not None:
                detected = len(analysis['detected_patterns']) > 0
                if known_effective and not detected:
                    results['missed_detections'].append({
                        'id': prompt_data.get('id'),
                        'category': expected_category,
                        'preview': prompt_text[:100]
                    })
                elif not known_effective and analysis['risk_score'] > 50:
                    results['false_positives'].append({
                        'id': prompt_data.get('id'),
                        'score': analysis['risk_score'],
                        'patterns': analysis['unique_pattern_types']
                    })
            
            results['detailed_results'].append(analysis)
        
        # Calculate statistics
        results = self._calculate_statistics(results)
        
        # Generate insights
        results['insights'] = self._generate_insights(results)
        
        return results
    
    def _update_pattern_effectiveness(self, pattern_type: str, effective: Optional[bool]):
        """Track pattern effectiveness over time"""
        if effective is None:
            return
            
        if pattern_type not in self.pattern_effectiveness:
            self.pattern_effectiveness[pattern_type] = {
                'true_positives': 0,
                'false_positives': 0,
                'total': 0
            }
        
        self.pattern_effectiveness[pattern_type]['total'] += 1
        if effective:
            self.pattern_effectiveness[pattern_type]['true_positives'] += 1
        else:
            self.pattern_effectiveness[pattern_type]['false_positives'] += 1
    
    def _calculate_statistics(self, results: Dict) -> Dict:
        """Calculate comprehensive statistics"""
        total = results['total_analyzed']
        
        if total > 0:
            # Risk percentages
            results['risk_percentages'] = {
                k: round(v/total * 100, 1) 
                for k, v in results['risk_distribution'].items()
            }
            
            # Detection metrics
            if results['missed_detections'] or results['false_positives']:
                total_known = len(results['missed_detections']) + len(results['false_positives'])
                for res in results['detailed_results']:
                    if res.get('known_effective') is not None:
                        total_known += 1
                
                if total_known > 0:
                    true_positives = sum(
                        1 for r in results['detailed_results']
                        if r.get('known_effective') == True and r['risk_score'] > 50
                    )
                    
                    results['detection_accuracy'] = {
                        'precision': round(
                            true_positives / max(
                                true_positives + len(results['false_positives']), 1
                            ) * 100, 1
                        ),
                        'recall': round(
                            true_positives / max(
                                true_positives + len(results['missed_detections']), 1
                            ) * 100, 1
                        ),
                        'false_positive_rate': round(
                            len(results['false_positives']) / total_known * 100, 1
                        ),
                        'miss_rate': round(
                            len(results['missed_detections']) / total_known * 100, 1
                        )
                    }
            
            # Language percentages
            results['language_percentages'] = {
                k: round(v/total * 100, 1)
                for k, v in results['language_distribution'].items()
            }
            
            # Pattern effectiveness
            if self.pattern_effectiveness:
                results['pattern_effectiveness'] = {}
                for pattern, stats in self.pattern_effectiveness.items():
                    if stats['total'] > 0:
                        results['pattern_effectiveness'][pattern] = round(
                            stats['true_positives'] / stats['total'] * 100, 1
                        )
        
        return results
    
    def _generate_insights(self, results: Dict) -> List[str]:
        """Generate actionable insights from analysis"""
        insights = []
        
        # Risk level insights
        if results['risk_percentages'].get('CRITICAL', 0) > 20:
            insights.append("⚠️ High concentration of CRITICAL risk prompts (>20%). Immediate review needed.")
        
        if results['risk_percentages'].get('SAFE', 0) < 30:
            insights.append("🔍 Low SAFE prompt ratio (<30%). Consider reviewing detection sensitivity.")
        
        # Pattern insights
        if results['pattern_frequency']:
            top_pattern = max(results['pattern_frequency'].items(), key=lambda x: x[1])
            insights.append(f"📊 Most common attack: {top_pattern[0]} ({top_pattern[1]} instances)")
        
        # Language insights
        zh_percentage = results['language_percentages'].get('zh', 0)
        if zh_percentage > 30:
            insights.append(f"🌏 Significant Chinese content ({zh_percentage}%). Cultural patterns important.")
        
        # Accuracy insights
        if 'detection_accuracy' in results:
            if results['detection_accuracy'].get('miss_rate', 0) > 10:
                insights.append("⚠️ High miss rate (>10%). Review detection thresholds.")
            
            if results['detection_accuracy'].get('precision', 100) < 80:
                insights.append("📉 Low precision (<80%). Too many false positives.")
        
        # Pattern effectiveness insights
        if 'pattern_effectiveness' in results:
            weak_patterns = [
                p for p, eff in results['pattern_effectiveness'].items()
                if eff < 50
            ]
            if weak_patterns:
                insights.append(f"🔧 Weak patterns detected: {', '.join(weak_patterns[:3])}")
        
        return insights
    
    def generate_report(self, analysis_results: Dict) -> str:
        """Generate comprehensive markdown report"""
        report = f"""# 🛡️ Jailbreak Analysis Report
**Report ID:** {analysis_results['analysis_id']}  
**Generated:** {analysis_results['timestamp']}  
**Total Prompts Analyzed:** {analysis_results['total_analyzed']}

---

## 📊 Executive Summary

### Risk Distribution
"""
        
        # Risk distribution with visual bars
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE']:
            count = analysis_results['risk_distribution'][severity]
            percentage = analysis_results['risk_percentages'][severity]
            bar_length = int(percentage / 2)
            bar = '█' * bar_length + '░' * (50 - bar_length)
            emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 
                    'LOW': '🟢', 'SAFE': '✅'}[severity]
            report += f"{emoji} **{severity:8}** [{bar}] {count:3} ({percentage}%)\n"
        
        # Detection accuracy if available
        if analysis_results.get('detection_accuracy'):
            report += f"""
### 🎯 Detection Performance
- **Precision:** {analysis_results['detection_accuracy']['precision']}%
- **Recall:** {analysis_results['detection_accuracy']['recall']}%
- **False Positive Rate:** {analysis_results['detection_accuracy']['false_positive_rate']}%
- **Miss Rate:** {analysis_results['detection_accuracy']['miss_rate']}%
"""
        
        # Pattern distribution
        report += "\n## 🔍 Attack Pattern Analysis\n\n"
        if analysis_results['pattern_frequency']:
            report += "| Pattern Type | Occurrences | Frequency |\n"
            report += "|--------------|-------------|----------|\n"
            
            total_patterns = sum(analysis_results['pattern_frequency'].values())
            for pattern, count in sorted(
                analysis_results['pattern_frequency'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                freq = round(count / total_patterns * 100, 1)
                report += f"| {pattern} | {count} | {freq}% |\n"
        
        # Language distribution
        report += f"\n## 🌐 Language Distribution\n"
        for lang, percentage in analysis_results['language_percentages'].items():
            lang_name = {'en': 'English', 'zh': 'Chinese', 'mixed': 'Mixed'}[lang]
            report += f"- **{lang_name}:** {percentage}%\n"
        
        # High-risk prompts
        if analysis_results['high_risk_prompts']:
            report += f"\n## ⚠️ High-Risk Prompts (Top 5)\n\n"
            for i, prompt in enumerate(analysis_results['high_risk_prompts'][:5], 1):
                report += f"{i}. **ID {prompt['id']}** (Score: {prompt['score']})\n"
                report += f"   > {prompt['preview']}...\n\n"
        
        # Missed detections
        if analysis_results['missed_detections']:
            report += f"\n## 🔴 Missed Detections\n\n"
            report += "These known jailbreaks were not detected:\n\n"
            for miss in analysis_results['missed_detections'][:5]:
                report += f"- **ID {miss['id']}** ({miss['category']})\n"
                report += f"  > {miss['preview']}...\n\n"
        
        # Insights
        if analysis_results.get('insights'):
            report += f"\n## 💡 Key Insights\n\n"
            for insight in analysis_results['insights']:
                report += f"- {insight}\n"
        
        # Pattern effectiveness
        if analysis_results.get('pattern_effectiveness'):
            report += f"\n## 📈 Pattern Effectiveness\n\n"
            report += "| Pattern | Effectiveness |\n"
            report += "|---------|---------------|\n"
            for pattern, eff in sorted(
                analysis_results['pattern_effectiveness'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                report += f"| {pattern} | {eff}% |\n"
        
        # Recommendations
        report += self._generate_recommendations(analysis_results)
        
        return report
    
    def _generate_recommendations(self, results: Dict) -> str:
        """Generate actionable recommendations"""
        recommendations = "\n## 🎯 Recommendations\n\n"
        
        # Based on risk distribution
        if results['risk_percentages'].get('CRITICAL', 0) > 15:
            recommendations += "1. **Immediate Action:** Implement stricter filtering for CRITICAL patterns\n"
        
        # Based on patterns
        if 'pattern_effectiveness' in results:
            weak = [p for p, e in results['pattern_effectiveness'].items() if e < 60]
            if weak:
                recommendations += f"2. **Pattern Review:** Improve detection for: {', '.join(weak[:3])}\n"
        
        # Based on language
        if results['language_percentages'].get('zh', 0) > 20:
            recommendations += "3. **Cultural Adaptation:** Enhance Chinese-specific pattern detection\n"
        
        # Based on accuracy
        if results.get('detection_accuracy', {}).get('miss_rate', 0) > 5:
            recommendations += "4. **Sensitivity Tuning:** Lower detection thresholds for known patterns\n"
        
        return recommendations
    
    def save_results(self, results: Dict, filename: Optional[str] = None):
        """Save analysis results to file"""
        if filename is None:
            filename = f"analysis_{results['analysis_id']}.json"
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return filepath