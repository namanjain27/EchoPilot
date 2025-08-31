"""
LangSmith Monitoring Module for EchoPilot

RESEARCH FINDINGS:
================

1. LangSmith API Analysis:
   - Primary method: client.list_runs() with filters
   - Automatic token tracking for Gemini via LangChain (already enabled in echo.py)
   - Cost data available if pricing configured in LangSmith dashboard
   - Latency calculated from run start_time/end_time timestamps

2. Available Data Fields:
   - usage_metadata: {input_tokens, output_tokens, total_tokens}
   - total_cost: Available if pricing table configured
   - start_time/end_time: For latency calculation
   - run_type, error status, model_name

3. Best Practices Discovered:
   - Use API over webhooks for batch reporting
   - Filter by project_name and start_time for efficiency
   - Handle missing data gracefully (not all runs have cost/token data)
   - P55/P99 percentiles require statistics.quantiles() with proper handling

IMPLEMENTATION APPROACH:
=======================

1. Core Strategy:
   - Single class (LangSmithMonitor) with environment-based configuration
   - Method-based approach: daily/weekly/monthly helpers
   - Error handling for API failures and missing data
   - Statistics calculations with edge case handling

2. Key Metrics Focus:
   ✓ input_tokens, output_tokens, total_tokens
   ✓ median_tokens per run
   ✓ total_cost, average_cost_per_run
   ✓ latency_p55, latency_p99 (milliseconds)
   ✓ Coverage metrics (runs with data availability)

3. Architecture Decisions:
   - Environment variables for configuration (reusing existing .env)
   - Dict return format for easy JSON serialization
   - Formatted print methods for human-readable output
   - Modular design allowing integration with existing chat system

4. Integration Points:
   - Compatible with current .env setup (LANGSMITH_* variables)
   - Can be imported into echo.py for real-time monitoring
   - Standalone executable for scheduled monitoring scripts
   - JSON output suitable for dashboard/logging systems

5. Limitations Addressed:
   - Cost data depends on LangSmith pricing configuration
   - Token data automatic for Gemini but may be missing for custom models
   - Latency calculation assumes UTC timestamps
   - Percentile calculations need minimum 2 data points

NEXT STEPS:
===========
1. Test with actual project data
2. Add cost threshold alerts
3. Consider CSV export functionality
4. Integration with workdone.md updates
5. Scheduled execution setup (cron/systemd)
"""

from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from langsmith import Client
import statistics

load_dotenv()

class LangSmithMonitor:
    def __init__(self):
        """Initialize LangSmith client for monitoring"""
        self.client = Client(
            api_key=os.getenv('LANGSMITH_API_KEY'),
            api_url=os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
        )
        self.project_name = os.getenv('LANGSMITH_PROJECT', 'echopilot')
    
    def get_runs_metrics(self, 
                        days_back: int = 1, 
                        limit: int = 1000) -> Dict[str, Any]:
        """
        Fetch runs data from LangSmith and calculate metrics
        
        Args:
            days_back: Number of days back to fetch data (default: 1 for daily)
            limit: Maximum number of runs to fetch
            
        Returns:
            Dictionary containing aggregated metrics
        """
        try:
            # Calculate start time
            start_time = datetime.now() - timedelta(days=days_back)
            
            # Fetch runs from LangSmith
            runs = list(self.client.list_runs(
                project_name=self.project_name,
                start_time=start_time,
                limit=limit
            ))
            
            if not runs:
                return {
                    'error': f'No runs found for project {self.project_name} in last {days_back} days',
                    'total_runs': 0
                }
            
            # Extract metrics from runs
            metrics = self._calculate_metrics(runs)
            metrics['period_days'] = days_back
            metrics['total_runs'] = len(runs)
            metrics['project_name'] = self.project_name
            metrics['fetched_at'] = datetime.now().isoformat()
            
            return metrics
            
        except Exception as e:
            return {
                'error': f'Failed to fetch runs: {str(e)}',
                'total_runs': 0
            }
    
    def _calculate_metrics(self, runs: List) -> Dict[str, Any]:
        """Calculate aggregated metrics from runs data"""
        
        # Initialize collections for metrics
        input_tokens = []
        output_tokens = []
        total_tokens = []
        costs = []
        latencies = []  # in milliseconds
        
        for run in runs:
            # Extract token data from usage_metadata or other fields
            if hasattr(run, 'usage_metadata') and run.usage_metadata:
                usage = run.usage_metadata
                if 'input_tokens' in usage:
                    input_tokens.append(usage['input_tokens'])
                if 'output_tokens' in usage:
                    output_tokens.append(usage['output_tokens'])
                if 'total_tokens' in usage:
                    total_tokens.append(usage['total_tokens'])
                elif 'input_tokens' in usage and 'output_tokens' in usage:
                    total_tokens.append(usage['input_tokens'] + usage['output_tokens'])
            
            # Extract cost data
            if hasattr(run, 'total_cost') and run.total_cost:
                costs.append(float(run.total_cost))
            
            # Calculate latency from start_time and end_time
            if hasattr(run, 'start_time') and hasattr(run, 'end_time') and run.start_time and run.end_time:
                # Convert to milliseconds
                latency_ms = (run.end_time - run.start_time).total_seconds() * 1000
                latencies.append(latency_ms)
        
        # Calculate statistics
        metrics = {
            # Token metrics
            'total_input_tokens': sum(input_tokens) if input_tokens else 0,
            'total_output_tokens': sum(output_tokens) if output_tokens else 0,
            'total_tokens': sum(total_tokens) if total_tokens else sum(input_tokens) + sum(output_tokens),
            'median_tokens': statistics.median(total_tokens) if total_tokens else 0,
            
            # Cost metrics
            'total_cost': round(sum(costs), 4) if costs else 0,
            'average_cost_per_run': round(statistics.mean(costs), 4) if costs else 0,
            
            # Latency metrics (in milliseconds)
            'latency_p55': round(statistics.quantiles(latencies, n=20)[10], 2) if len(latencies) >= 2 else 0,  # 55th percentile
            'latency_p99': round(statistics.quantiles(latencies, n=100)[98], 2) if len(latencies) >= 2 else 0,  # 99th percentile
            'median_latency_ms': round(statistics.median(latencies), 2) if latencies else 0,
            'average_latency_ms': round(statistics.mean(latencies), 2) if latencies else 0,
            
            # Additional metrics
            'runs_with_tokens': len(total_tokens),
            'runs_with_cost': len(costs),
            'runs_with_latency': len(latencies),
        }
        
        return metrics
    
    def get_daily_metrics(self) -> Dict[str, Any]:
        """Get metrics for the last 24 hours"""
        return self.get_runs_metrics(days_back=1)
    
    def get_weekly_metrics(self) -> Dict[str, Any]:
        """Get metrics for the last 7 days"""
        return self.get_runs_metrics(days_back=7)
    
    def get_monthly_metrics(self) -> Dict[str, Any]:
        """Get metrics for the last 30 days"""
        return self.get_runs_metrics(days_back=30)
    
    def print_metrics_summary(self, metrics: Dict[str, Any]):
        """Print a formatted summary of metrics"""
        if 'error' in metrics:
            print(f"Error: {metrics['error']}")
            return
        
        print(f"\n=== LangSmith Metrics Summary ===")
        print(f"Project: {metrics.get('project_name', 'N/A')}")
        print(f"Period: Last {metrics.get('period_days', 'N/A')} days")
        print(f"Total Runs: {metrics.get('total_runs', 0)}")
        print(f"Fetched at: {metrics.get('fetched_at', 'N/A')}")
        
        print(f"\n--- Token Usage ---")
        print(f"Total Input Tokens: {metrics.get('total_input_tokens', 0):,}")
        print(f"Total Output Tokens: {metrics.get('total_output_tokens', 0):,}")
        print(f"Total Tokens: {metrics.get('total_tokens', 0):,}")
        print(f"Median Tokens per Run: {metrics.get('median_tokens', 0):,.0f}")
        
        print(f"\n--- Cost ---")
        print(f"Total Cost: ${metrics.get('total_cost', 0)}")
        print(f"Average Cost per Run: ${metrics.get('average_cost_per_run', 0)}")
        
        print(f"\n--- Latency ---")
        print(f"Median Latency: {metrics.get('median_latency_ms', 0)} ms")
        print(f"Average Latency: {metrics.get('average_latency_ms', 0)} ms")
        print(f"P55 Latency: {metrics.get('latency_p55', 0)} ms")
        print(f"P99 Latency: {metrics.get('latency_p99', 0)} ms")
        
        print(f"\n--- Coverage ---")
        print(f"Runs with Token Data: {metrics.get('runs_with_tokens', 0)}")
        print(f"Runs with Cost Data: {metrics.get('runs_with_cost', 0)}")
        print(f"Runs with Latency Data: {metrics.get('runs_with_latency', 0)}")


def main():
    """Example usage of the monitoring functions"""
    monitor = LangSmithMonitor()
    
    # Get daily metrics
    print("Fetching daily metrics...")
    daily_metrics = monitor.get_daily_metrics()
    monitor.print_metrics_summary(daily_metrics)
    
    # Uncomment for weekly/monthly metrics
    # print("\n" + "="*50)
    # weekly_metrics = monitor.get_weekly_metrics()
    # monitor.print_metrics_summary(weekly_metrics)


if __name__ == "__main__":
    main()