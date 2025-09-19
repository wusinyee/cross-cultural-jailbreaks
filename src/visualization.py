"""
Visualization Module for Jailbreak Analysis
Creates interactive charts and dashboards
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List
import json

class JailbreakVisualizer:
    def __init__(self):
        self.color_scheme = {
            'CRITICAL': '#d32f2f',
            'HIGH': '#f57c00',
            'MEDIUM': '#fbc02d',
            'LOW': '#689f38',
            'SAFE': '#388e3c'
        }
        
    def create_risk_distribution_chart(self, analysis_results: Dict) -> go.Figure:
        """Create risk distribution pie chart"""
        
        labels = list(analysis_results['risk_distribution'].keys())
        values = list(analysis_results['risk_distribution'].values())
        colors = [self.color_scheme[label] for label in labels]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=colors),
                textinfo='label+percent',
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>' +
                            'Count: %{value}<br>' +
                            'Percentage: %{percent}<br>' +
                            '<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="Risk Severity Distribution",
            title_font_size=20,
            showlegend=True,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
    def create_pattern_frequency_chart(self, analysis_results: Dict) -> go.Figure:
        """Create pattern frequency bar chart"""
        
        if not analysis_results.get('pattern_frequency'):
            return self._create_empty_chart("No patterns detected")
        
        patterns = list(analysis_results['pattern_frequency'].keys())
        frequencies = list(analysis_results['pattern_frequency'].values())
        
        # Sort by frequency
        sorted_data = sorted(zip(patterns, frequencies), key=lambda x: x[1], reverse=True)
        patterns, frequencies = zip(*sorted_data)
        
        # Take top 10
        patterns = patterns[:10]
        frequencies = frequencies[:10]
        
        fig = go.Figure([
            go.Bar(
                x=frequencies,
                y=patterns,
                orientation='h',
                marker=dict(
                    color=frequencies,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Frequency")
                ),
                text=frequencies,
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>' +
                            'Count: %{x}<br>' +
                            '<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="Top Attack Patterns Detected",
            xaxis_title="Frequency",
            yaxis_title="Pattern Type",
            height=400,
            margin=dict(l=150),
            showlegend=False
        )
        
        return fig
    
    def create_language_distribution_chart(self, analysis_results: Dict) -> go.Figure:
        """Create language distribution donut chart"""
        
        languages = {
            'en': 'English',
            'zh': 'Chinese',
            'mixed': 'Mixed'
        }
        
        labels = [languages.get(k, k) for k in analysis_results['language_distribution'].keys()]
        values = list(analysis_results['language_distribution'].values())
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=['#1976d2', '#d32f2f', '#7b1fa2']),
                textinfo='label+value',
                hovertemplate='<b>%{label}</b><br>' +
                            'Count: %{value}<br>' +
                            'Percentage: %{percent}<br>' +
                            '<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="Language Distribution",
            annotations=[
                dict(text='Languages', x=0.5, y=0.5, font_size=20, showarrow=False)
            ],
            height=400
        )
        
        return fig
    
    def create_detection_timeline(self, detailed_results: List[Dict]) -> go.Figure:
        """Create timeline of risk scores"""
        
        # Extract data
        indices = list(range(len(detailed_results)))
        risk_scores = [r.get('risk_score', 0) for r in detailed_results]
        severities = [r.get('severity', 'SAFE') for r in detailed_results]
        colors = [self.color_scheme[s] for s in severities]
        
        fig = go.Figure()
        
        # Add scatter plot
        fig.add_trace(go.Scatter(
            x=indices,
            y=risk_scores,
            mode='markers+lines',
            marker=dict(
                size=8,
                color=colors,
                line=dict(width=1, color='white')
            ),
            line=dict(width=1, color='gray', dash='dot'),
            hovertemplate='Prompt #%{x}<br>' +
                        'Risk Score: %{y}<br>' +
                        '<extra></extra>'
        ))
        
        # Add threshold lines
        thresholds = [
            (70, 'CRITICAL', '#d32f2f'),
            (50, 'HIGH', '#f57c00'),
            (30, 'MEDIUM', '#fbc02d'),
            (10, 'LOW', '#689f38')
        ]
        
        for threshold, label, color in thresholds:
            fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color=color,
                opacity=0.3,
                annotation_text=label,
                annotation_position="right"
            )
        
        fig.update_layout(
            title="Risk Score Timeline",
            xaxis_title="Prompt Index",
            yaxis_title="Risk Score",
            height=400,
            showlegend=False,
            yaxis=dict(range=[0, 105])
        )
        
        return fig
    
    def create_pattern_effectiveness_chart(self, analysis_results: Dict) -> go.Figure:
        """Create pattern effectiveness gauge chart"""
        
        if not analysis_results.get('pattern_effectiveness'):
            return self._create_empty_chart("No effectiveness data available")
        
        # Create subplots for multiple gauges
        patterns = list(analysis_results['pattern_effectiveness'].keys())[:6]
        effectiveness = [analysis_results['pattern_effectiveness'][p] for p in patterns]
        
        rows = 2
        cols = 3
        
        fig = make_subplots(
            rows=rows, cols=cols,
            specs=[[{'type': 'indicator'} for _ in range(cols)] for _ in range(rows)],
            subplot_titles=patterns
        )
        
        for i, (pattern, eff) in enumerate(zip(patterns, effectiveness)):
            row = i // cols + 1
            col = i % cols + 1
            
            color = '#d32f2f' if eff < 50 else '#fbc02d' if eff < 75 else '#388e3c'
            
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=eff,
                    title={'text': ""},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': color},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 75], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title="Pattern Effectiveness (%)",
            height=500,
            showlegend=False
        )
        
        return fig
    
    def create_comprehensive_dashboard(self, analysis_results: Dict) -> go.Figure:
        """Create comprehensive dashboard with multiple visualizations"""
        
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Risk Distribution', 
                'Top Attack Patterns',
                'Language Distribution', 
                'Risk Score Timeline',
                'Detection Accuracy',
                'Pattern Effectiveness'
            ),
            specs=[
                [{'type': 'pie'}, {'type': 'bar'}],
                [{'type': 'pie'}, {'type': 'scatter'}],
                [{'type': 'indicator'}, {'type': 'bar'}]
            ],
            row_heights=[0.33, 0.33, 0.34],
            vertical_spacing=0.1,
            horizontal_spacing=0.15
        )
        
        # 1. Risk Distribution (Pie)
        labels = list(analysis_results['risk_distribution'].keys())
        values = list(analysis_results['risk_distribution'].values())
        colors = [self.color_scheme[label] for label in labels]
        
        fig.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                textinfo='percent',
                hovertemplate='%{label}: %{value}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. Pattern Frequency (Bar)
        if analysis_results.get('pattern_frequency'):
            patterns = list(analysis_results['pattern_frequency'].keys())[:5]
            frequencies = [analysis_results['pattern_frequency'][p] for p in patterns]
            
            fig.add_trace(
                go.Bar(
                    y=patterns,
                    x=frequencies,
                    orientation='h',
                    marker=dict(color='#1976d2'),
                    text=frequencies,
                    textposition='auto'
                ),
                row=1, col=2
            )
        
        # 3. Language Distribution (Pie)
        lang_labels = list(analysis_results['language_distribution'].keys())
        lang_values = list(analysis_results['language_distribution'].values())
        
        fig.add_trace(
            go.Pie(
                labels=lang_labels,
                values=lang_values,
                marker=dict(colors=['#1976d2', '#d32f2f', '#7b1fa2']),
                textinfo='label+percent'
            ),
            row=2, col=1
        )
        
        # 4. Risk Timeline (Scatter)
        if analysis_results.get('detailed_results'):
            indices = list(range(len(analysis_results['detailed_results'])))[:50]
            scores = [r.get('risk_score', 0) for r in analysis_results['detailed_results']][:50]
            
            fig.add_trace(
                go.Scatter(
                    x=indices,
                    y=scores,
                    mode='lines+markers',
                    marker=dict(size=5, color=scores, colorscale='RdYlGn_r'),
                    line=dict(width=1)
                ),
                row=2, col=2
            )
        
        # 5. Detection Accuracy (Indicator)
        if analysis_results.get('detection_accuracy'):
            accuracy = analysis_results['detection_accuracy'].get('precision', 0)
            
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=accuracy,
                    title={'text': "Precision %"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"}
                        ]
                    }
                ),
                row=3, col=1
            )
        
        # 6. Top Insights (Text/Table)
        if analysis_results.get('insights'):
            # Create a simple bar chart as placeholder
            fig.add_trace(
                go.Bar(
                    x=['Insights'],
                    y=[len(analysis_results['insights'])],
                    text=[f"{len(analysis_results['insights'])} insights"],
                    textposition='auto',
                    marker=dict(color='#4caf50')
                ),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="Jailbreak Analysis Dashboard",
            title_font_size=24,
            height=1000,
            showlegend=False
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig
    
    def save_all_charts(self, analysis_results: Dict, output_dir: str = "results"):
        """Save all charts as HTML files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        charts = {
            'risk_distribution': self.create_risk_distribution_chart(analysis_results),
            'pattern_frequency': self.create_pattern_frequency_chart(analysis_results),
            'language_distribution': self.create_language_distribution_chart(analysis_results),
            'detection_timeline': self.create_detection_timeline(
                analysis_results.get('detailed_results', [])
            ),
            'dashboard': self.create_comprehensive_dashboard(analysis_results)
        }
        
        for name, fig in charts.items():
            filepath = os.path.join(output_dir, f"{name}.html")
            fig.write_html(filepath)
            print(f"Saved {name} to {filepath}")