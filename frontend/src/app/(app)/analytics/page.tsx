'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, TrendingUp, TrendingDown, Target, CheckCircle2, XCircle, AlertCircle, Lightbulb, BarChart3, Activity, Play, FlaskConical, Clock, ArrowDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { useMemo, useState, useEffect, useCallback, useRef } from 'react';

interface AccuracyRun {
  run_id: string;
  label: string;
  timestamp: string;
  leases_tested: number;
  leases_errored: number;
  average_accuracy: number;
  total_cost: number;
  total_time: number;
  field_accuracy: Record<string, number>;
  per_lease: Array<{ tenant: string; accuracy: number; error?: string | null }>;
}

function formatFieldName(field: string) {
  return field.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

function accuracyColor(value: number): string {
  if (value >= 80) return '#22c55e';
  if (value >= 50) return '#eab308';
  return '#ef4444';
}

function accuracyBg(value: number): string {
  if (value >= 80) return 'bg-green-100 text-green-700';
  if (value >= 50) return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}

interface BaselineProgress {
  status: 'idle' | 'running' | 'complete' | 'error';
  run_id?: string;
  current_lease?: number;
  total_leases?: number;
  current_tenant?: string;
  completed_results?: Array<{
    tenant: string;
    accuracy: number;
    fields_correct?: number;
    fields_total?: number;
    error?: string;
  }>;
  elapsed_seconds?: number;
  estimated_remaining?: number;
  overall_accuracy?: number;
  run_summary?: any;
  error?: string;
}

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export default function AnalyticsPage() {
  const queryClient = useQueryClient();

  const { data: metrics, isLoading } = useQuery<any>({
    queryKey: ['analytics', 'metrics'],
    queryFn: () => analyticsApi.getMetrics(),
  });

  const { data: fieldStats } = useQuery<any[]>({
    queryKey: ['analytics', 'fields'],
    queryFn: () => analyticsApi.getFieldStats(),
  });

  const { data: insights } = useQuery<any[]>({
    queryKey: ['analytics', 'insights'],
    queryFn: () => analyticsApi.getInsights(),
  });

  const { data: accuracyHistory } = useQuery<AccuracyRun[]>({
    queryKey: ['analytics', 'accuracy-history'],
    queryFn: () => analyticsApi.getAccuracyHistory(),
  });

  const { data: eligibleData } = useQuery<{ count: number }>({
    queryKey: ['analytics', 'eligible-count'],
    queryFn: () => analyticsApi.getEligibleCount(),
  });

  // Baseline test runner state
  const [numLeases, setNumLeases] = useState(2);
  const [multiPass, setMultiPass] = useState(false);
  const [progress, setProgress] = useState<BaselineProgress>({ status: 'idle' });
  const [startError, setStartError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const maxLeases = eligibleData?.count ?? 43;

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const p = await analyticsApi.getBaselineProgress();
        setProgress(p);
        if (p.status === 'complete' || p.status === 'error') {
          stopPolling();
          // Invalidate accuracy history so charts refresh
          queryClient.invalidateQueries({ queryKey: ['analytics', 'accuracy-history'] });
        }
      } catch {
        // ignore transient errors
      }
    }, 3000);
  }, [stopPolling, queryClient]);

  // Check for an in-progress run on mount
  useEffect(() => {
    (async () => {
      try {
        const p = await analyticsApi.getBaselineProgress();
        if (p.status === 'running') {
          setProgress(p);
          startPolling();
        }
      } catch {
        // ignore
      }
    })();
    return stopPolling;
  }, [startPolling, stopPolling]);

  const handleStartRun = async () => {
    setStartError(null);
    try {
      await analyticsApi.startBaselineRun({ num_leases: numLeases, multi_pass: multiPass });
      setProgress({ status: 'running', current_lease: 0, total_leases: numLeases, completed_results: [], elapsed_seconds: 0, estimated_remaining: 0, overall_accuracy: 0 });
      startPolling();
    } catch (err: any) {
      if (err.message?.includes('409')) {
        setStartError('A test is already running');
      } else {
        setStartError(err.message || 'Failed to start test');
      }
    }
  };

  const handleReset = () => {
    setProgress({ status: 'idle' });
  };

  // Derive chart data from accuracy history
  const trendData = useMemo(() => {
    if (!accuracyHistory || accuracyHistory.length === 0) return [];
    return accuracyHistory.map((run) => ({
      date: new Date(run.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      label: run.label,
      accuracy: Math.round(run.average_accuracy * 10) / 10,
      leases: run.leases_tested,
    }));
  }, [accuracyHistory]);

  const latestRun = accuracyHistory?.[accuracyHistory.length - 1];

  const fieldBarData = useMemo(() => {
    if (!latestRun) return [];
    return Object.entries(latestRun.field_accuracy)
      .map(([field, accuracy]) => ({ field: formatFieldName(field), accuracy: Math.round(accuracy * 10) / 10, raw: field }))
      .sort((a, b) => b.accuracy - a.accuracy);
  }, [latestRun]);

  const improvementDelta = useMemo(() => {
    if (!accuracyHistory || accuracyHistory.length < 2) return null;
    const first = accuracyHistory[0].average_accuracy;
    const last = accuracyHistory[accuracyHistory.length - 1].average_accuracy;
    return Math.round((last - first) * 10) / 10;
  }, [accuracyHistory]);

  if (isLoading || !metrics) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-12 w-12 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Insights & Analytics</h1>
        <p className="mt-2 text-slate-600">
          Monitor extraction accuracy and continuous improvement over time
        </p>
      </div>

      {/* Accuracy Test Runner */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-amber-500" />
            Accuracy Test
          </CardTitle>
          <p className="text-sm text-slate-600 mt-1">
            Runs extraction on gold-standard leases and scores accuracy against known correct values
          </p>
        </CardHeader>
        <CardContent>
          {progress.status === 'idle' && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-end gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Number of leases
                  </label>
                  <Input
                    type="number"
                    min={1}
                    max={maxLeases}
                    value={numLeases}
                    onChange={(e) => setNumLeases(Math.max(1, Math.min(maxLeases, parseInt(e.target.value) || 1)))}
                    className="w-24"
                  />
                  <p className="text-xs text-slate-500 mt-1">{maxLeases} eligible</p>
                </div>
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <input
                      type="checkbox"
                      checked={multiPass}
                      onChange={(e) => setMultiPass(e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    Multi-pass refinement
                  </label>
                  <p className="text-xs text-slate-500 mt-1">Slower but may improve accuracy</p>
                </div>
                <Button onClick={handleStartRun} className="gap-2">
                  <Play className="h-4 w-4" />
                  Run Test
                </Button>
              </div>
              {startError && (
                <p className="text-sm text-red-600">{startError}</p>
              )}
            </div>
          )}

          {progress.status === 'running' && (
            <div className="space-y-4">
              {/* Progress header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-amber-500" />
                  <span className="text-sm font-medium text-slate-900">
                    Testing lease {progress.current_lease}/{progress.total_leases}
                    {progress.current_tenant && <> &mdash; {progress.current_tenant}</>}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatElapsed(progress.elapsed_seconds ?? 0)}
                  </span>
                  {(progress.estimated_remaining ?? 0) > 0 && (
                    <span>~{formatElapsed(progress.estimated_remaining!)} remaining</span>
                  )}
                </div>
              </div>

              {/* Progress bar */}
              <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full transition-all duration-500"
                  style={{ width: `${((progress.current_lease ?? 0) / (progress.total_leases ?? 1)) * 100}%` }}
                />
              </div>

              {/* Overall accuracy so far */}
              {(progress.overall_accuracy ?? 0) > 0 && (
                <div className="text-sm text-slate-600">
                  Overall accuracy so far: <span className="font-semibold text-slate-900">{progress.overall_accuracy?.toFixed(1)}%</span>
                </div>
              )}

              {/* Completed lease results */}
              {progress.completed_results && progress.completed_results.length > 0 && (
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200">
                        <th className="text-left py-2 px-3 text-xs font-medium text-slate-600">Tenant</th>
                        <th className="text-center py-2 px-3 text-xs font-medium text-slate-600">Accuracy</th>
                        <th className="text-center py-2 px-3 text-xs font-medium text-slate-600">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {progress.completed_results.map((r, idx) => (
                        <tr key={idx} className="border-b border-slate-100">
                          <td className="py-2 px-3 text-sm text-slate-900">{r.tenant}</td>
                          <td className="text-center py-2 px-3">
                            <div className="inline-flex items-center gap-2">
                              <span className="text-sm font-semibold text-slate-900">
                                {r.error ? 'ERR' : `${r.accuracy.toFixed(1)}%`}
                              </span>
                              {!r.error && (
                                <div className="h-1.5 w-16 bg-slate-200 rounded-full overflow-hidden">
                                  <div
                                    className="h-full rounded-full"
                                    style={{ width: `${Math.min(r.accuracy, 100)}%`, backgroundColor: accuracyColor(r.accuracy) }}
                                  />
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="text-center py-2 px-3">
                            {r.error ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                <XCircle className="h-3 w-3" /> Error
                              </span>
                            ) : (
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${accuracyBg(r.accuracy)}`}>
                                {r.accuracy >= 80 ? <CheckCircle2 className="h-3 w-3" /> : r.accuracy >= 50 ? <AlertCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                                {r.accuracy >= 80 ? 'Good' : r.accuracy >= 50 ? 'Needs Work' : 'Poor'}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {progress.status === 'complete' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                  <span className="text-base font-semibold text-slate-900">
                    Test complete &mdash; {progress.overall_accuracy?.toFixed(1)}% accuracy across {progress.total_leases} leases
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' })}
                    className="gap-1"
                  >
                    <ArrowDown className="h-3 w-3" />
                    View Full Results
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handleReset}>
                    New Test
                  </Button>
                </div>
              </div>

              {/* Completed results summary */}
              {progress.completed_results && progress.completed_results.length > 0 && (
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200">
                        <th className="text-left py-2 px-3 text-xs font-medium text-slate-600">Tenant</th>
                        <th className="text-center py-2 px-3 text-xs font-medium text-slate-600">Accuracy</th>
                        <th className="text-center py-2 px-3 text-xs font-medium text-slate-600">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {progress.completed_results.map((r, idx) => (
                        <tr key={idx} className="border-b border-slate-100">
                          <td className="py-2 px-3 text-sm text-slate-900">{r.tenant}</td>
                          <td className="text-center py-2 px-3">
                            <span className="text-sm font-semibold text-slate-900">
                              {r.error ? 'ERR' : `${r.accuracy.toFixed(1)}%`}
                            </span>
                          </td>
                          <td className="text-center py-2 px-3">
                            {r.error ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                <XCircle className="h-3 w-3" /> Error
                              </span>
                            ) : (
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${accuracyBg(r.accuracy)}`}>
                                {r.accuracy >= 80 ? <CheckCircle2 className="h-3 w-3" /> : r.accuracy >= 50 ? <AlertCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                                {r.accuracy >= 80 ? 'Good' : r.accuracy >= 50 ? 'Needs Work' : 'Poor'}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {progress.status === 'error' && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-red-600">
                <XCircle className="h-5 w-5" />
                <span className="font-medium">Test failed: {progress.error}</span>
              </div>
              <Button variant="secondary" size="sm" onClick={handleReset}>
                Try Again
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">
              Overall Accuracy
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold text-slate-900">
                {(metrics.overallAccuracy * 100).toFixed(1)}%
              </div>
              {metrics.trend === 'up' ? (
                <TrendingUp className="h-5 w-5 text-green-600" />
              ) : (
                <TrendingDown className="h-5 w-5 text-red-600" />
              )}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Based on {metrics.totalCorrections} reviews
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">
              Total Extractions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">
              {metrics.totalExtractions}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Leases processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">
              Avg Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">
              {(metrics.avgConfidence * 100).toFixed(1)}%
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Model confidence score
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">
              Corrections
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">
              {metrics.totalCorrections}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Human feedback submitted
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Model Accuracy Section */}
      <div ref={resultsRef} />
      {accuracyHistory && accuracyHistory.length > 0 && (
        <>
          {/* Accuracy Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">
                  Latest Accuracy
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <div className="text-3xl font-bold text-slate-900">
                    {latestRun?.average_accuracy.toFixed(1)}%
                  </div>
                  {improvementDelta !== null && (
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                      improvementDelta >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {improvementDelta >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                      {improvementDelta >= 0 ? '+' : ''}{improvementDelta}pp
                    </span>
                  )}
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Run: {latestRun?.label}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">
                  Total Test Runs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-slate-900">
                  {accuracyHistory.length}
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Accuracy evaluation runs
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">
                  Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-slate-900">
                  {improvementDelta !== null ? (
                    <span className={improvementDelta >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {improvementDelta >= 0 ? '+' : ''}{improvementDelta}pp
                    </span>
                  ) : 'N/A'}
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Since first run ({accuracyHistory[0]?.average_accuracy.toFixed(1)}%)
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Accuracy Over Time Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-amber-500" />
                Accuracy Over Time
              </CardTitle>
              <p className="text-sm text-slate-600 mt-1">
                Model accuracy across evaluation runs
              </p>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#64748b' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} tickFormatter={(v) => `${v}%`} />
                    <Tooltip
                      contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: 13 }}
                      formatter={(value: any) => [`${value}%`, 'Accuracy']}
                      labelFormatter={(label) => `Run: ${label}`}
                    />
                    <Line
                      type="monotone"
                      dataKey="accuracy"
                      stroke="#f59e0b"
                      strokeWidth={2.5}
                      dot={{ r: 5, fill: '#f59e0b', stroke: '#fff', strokeWidth: 2 }}
                      activeDot={{ r: 7 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Per-Field Accuracy Bar Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-amber-500" />
                Per-Field Accuracy
              </CardTitle>
              <p className="text-sm text-slate-600 mt-1">
                Field-level accuracy from latest run ({latestRun?.label})
              </p>
            </CardHeader>
            <CardContent>
              <div style={{ height: Math.max(300, fieldBarData.length * 36) }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fieldBarData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} tickFormatter={(v) => `${v}%`} />
                    <YAxis type="category" dataKey="field" tick={{ fontSize: 11, fill: '#334155' }} width={115} />
                    <Tooltip
                      contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: 13 }}
                      formatter={(value: any) => [`${value}%`, 'Accuracy']}
                    />
                    <Bar dataKey="accuracy" radius={[0, 4, 4, 0]} barSize={20}>
                      {fieldBarData.map((entry, index) => (
                        <Cell key={index} fill={accuracyColor(entry.accuracy)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Per-Lease Breakdown Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-amber-500" />
                Per-Lease Breakdown
              </CardTitle>
              <p className="text-sm text-slate-600 mt-1">
                Individual lease accuracy from latest run ({latestRun?.label})
              </p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Tenant</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Accuracy</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {latestRun?.per_lease.map((lease, idx) => (
                      <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4 text-sm font-medium text-slate-900">
                          {lease.tenant}
                        </td>
                        <td className="text-center py-3 px-4">
                          <div className="inline-flex items-center gap-2">
                            <span className="text-sm font-semibold text-slate-900">
                              {lease.accuracy.toFixed(1)}%
                            </span>
                            <div className="h-2 w-20 bg-slate-200 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${Math.min(lease.accuracy, 100)}%`,
                                  backgroundColor: accuracyColor(lease.accuracy),
                                }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="text-center py-3 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${accuracyBg(lease.accuracy)}`}>
                            {lease.accuracy >= 80 ? (
                              <><CheckCircle2 className="h-3 w-3" /> Good</>
                            ) : lease.accuracy >= 50 ? (
                              <><AlertCircle className="h-3 w-3" /> Needs Work</>
                            ) : (
                              <><XCircle className="h-3 w-3" /> Poor</>
                            )}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Field Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-amber-500" />
            Field Performance
          </CardTitle>
          <p className="text-sm text-slate-600 mt-1">
            Accuracy and confidence by field (from user reviews)
          </p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Field</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Accuracy</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Corrections</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Avg Confidence</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {fieldStats?.map((field: any) => (
                  <tr key={field.field} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-4 text-sm font-medium text-slate-900">
                      {field.field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                    </td>
                    <td className="text-center py-3 px-4">
                      <div className="inline-flex items-center gap-2">
                        <div className="text-sm font-semibold text-slate-900">
                          {(field.accuracy * 100).toFixed(1)}%
                        </div>
                        <div className="h-2 w-20 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              field.accuracy >= 0.9
                                ? 'bg-green-500'
                                : field.accuracy >= 0.7
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${field.accuracy * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="text-center py-3 px-4 text-sm text-slate-600">
                      {field.corrections}
                    </td>
                    <td className="text-center py-3 px-4 text-sm text-slate-600">
                      {(field.avgConfidence * 100).toFixed(1)}%
                    </td>
                    <td className="text-center py-3 px-4">
                      {field.accuracy >= 0.9 ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                          <CheckCircle2 className="h-3 w-3" />
                          Excellent
                        </span>
                      ) : field.accuracy >= 0.7 ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs font-medium">
                          <AlertCircle className="h-3 w-3" />
                          Needs Work
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-medium">
                          <XCircle className="h-3 w-3" />
                          Critical
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Insights & Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-amber-500" />
            AI Insights & Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          {insights && insights.length > 0 ? (
            <div className="space-y-4">
              {insights.map((insight: any, index: number) => {
                const colors: Record<string, any> = {
                  critical: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', titleText: 'text-red-900', iconColor: 'text-red-600', icon: AlertCircle },
                  warning: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', titleText: 'text-yellow-900', iconColor: 'text-yellow-600', icon: AlertCircle },
                  success: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', titleText: 'text-green-900', iconColor: 'text-green-600', icon: CheckCircle2 },
                };
                const { bg, border, text, titleText, iconColor, icon: Icon } = colors[insight.type];

                return (
                  <div key={index} className={`flex gap-3 p-4 ${bg} border ${border} rounded-lg`}>
                    <Icon className={`h-5 w-5 ${iconColor} shrink-0 mt-0.5`} />
                    <div>
                      <h4 className={`font-medium ${titleText}`}>{insight.title}</h4>
                      <p className={`text-sm ${text} mt-1`}>{insight.message}</p>
                      {insight.recommendation && (
                        <p className={`text-sm ${text} mt-2 font-medium`}>
                          Recommendation: {insight.recommendation}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-600">
              <Lightbulb className="h-12 w-12 mx-auto mb-3 text-slate-400" />
              <p>No insights available yet. Submit more reviews to get AI-powered recommendations.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
