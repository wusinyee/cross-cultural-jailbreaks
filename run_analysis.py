#!/usr/bin/env python3
"""
Command-line script to run jailbreak analysis
Usage: python run_analysis.py [--input FILE] [--output DIR] [--format json|md|html]
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import pandas as pd

from src.pattern_detector import JailbreakPatternAnalyzer
from src.risk_scorer import RiskScorer
from src.visualization import JailbreakVisualizer

def main():
    parser = argparse.ArgumentParser(description='Analyze prompts for jailbreak patterns')
    parser.add_argument('--input', '-i', default='data/jailbreak_attempts.json',
                       help='Input JSON file with prompts')
    parser.add_argument('--output', '-o', default='results',
                       help='Output directory for results')
    parser.add_argument('--format', '-f', choices=['json', 'md', 'html', 'all'],
                       default='all', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize components
    print("🛡️  Cross-Cultural Jailbreak Pattern Analyzer")
    print("=" * 50)
    
    analyzer = JailbreakPatternAnalyzer()
    scorer = RiskScorer(args.output)
    visualizer = JailbreakVisualizer()
    
    # Load input data
    print(f"📂 Loading prompts from {args.input}...")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        print(f"✅ Loaded {len(prompts)} prompts")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        sys.exit(1)
    
    # Analyze prompts
    print("\n🔍 Analyzing prompts...")
    analyzed_prompts = []
    
    for prompt_data in tqdm(prompts, desc="Processing"):
        analysis = analyzer.analyze_prompt(
            prompt_data.get('prompt', ''),
            prompt_data.get('language', 'auto')
        )
        analysis['original_data'] = prompt_data
        analyzed_prompts.append(analysis)
        
        if args.verbose and analysis['risk_score'] > 70:
            print(f"\n⚠️  High risk detected (ID {prompt_data.get('id')}): Score {analysis['risk_score']}")
    
    # Generate batch analysis
    print("\n📊 Generating batch analysis...")
    batch_results = scorer.batch_analyze(prompts, analyzer)
    
    # Save results
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    if args.format in ['json', 'all']:
        json_path = output_dir / f"analysis_{batch_results['analysis_id']}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved JSON results to {json_path}")
    
    if args.format in ['md', 'all']:
        report = scorer.generate_report(batch_results)
        md_path = output_dir / f"report_{batch_results['analysis_id']}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Saved Markdown report to {md_path}")
    
    if args.format in ['html', 'all']:
        print("📈 Generating visualizations...")
        visualizer.save_all_charts(batch_results, str(output_dir))
        print(f"🎨 Saved HTML charts to {output_dir}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Total Prompts: {batch_results['total_analyzed']}")
    print(f"Risk Distribution:")
    for severity, count in batch_results['risk_distribution'].items():
        percentage = batch_results['risk_percentages'][severity]
        print(f"  {severity:8} : {count:3} ({percentage}%)")
    
    if batch_results.get('detection_accuracy'):
        print(f"\nDetection Metrics:")
        for metric, value in batch_results['detection_accuracy'].items():
            print(f"  {metric}: {value}%")
    
    print(f"\nTop Patterns:")
    for pattern, count in list(batch_results['pattern_frequency'].items())[:5]:
        print(f"  {pattern}: {count}")
    
    if batch_results.get('insights'):
        print(f"\nKey Insights:")
        for insight in batch_results['insights'][:3]:
            print(f"  • {insight}")
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()