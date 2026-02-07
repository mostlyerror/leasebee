'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, TrendingUp, TrendingDown, Target, CheckCircle2, XCircle, AlertCircle, Lightbulb } from 'lucide-react';

export default function AnalyticsPage() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['analytics', 'metrics'],
    queryFn: () => analyticsApi.getMetrics(),
  });

  const { data: fieldStats } = useQuery({
    queryKey: ['analytics', 'fields'],
    queryFn: () => analyticsApi.getFieldStats(),
  });

  const { data: insights } = useQuery({
    queryKey: ['analytics', 'insights'],
    queryFn: () => analyticsApi.getInsights(),
  });

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

      {/* Field Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-amber-500" />
            Field Performance
          </CardTitle>
          <p className="text-sm text-slate-600 mt-1">
            Accuracy and confidence by field
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
                {fieldStats?.map((field) => (
                  <tr key={field.field} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-4 text-sm font-medium text-slate-900">
                      {field.field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
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
              {insights.map((insight, index) => {
                const colors = {
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
                          💡 {insight.recommendation}
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

      {/* Coming Soon */}
      <Card className="border-2 border-dashed border-slate-300">
        <CardHeader>
          <CardTitle className="text-slate-600">Coming Soon</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-slate-600">
            <li className="flex items-center gap-2">
              <div className="w-2 h-2 bg-slate-400 rounded-full" />
              <span>Few-shot example management</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="w-2 h-2 bg-slate-400 rounded-full" />
              <span>Prompt version comparison</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="w-2 h-2 bg-slate-400 rounded-full" />
              <span>Time-series accuracy trends</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="w-2 h-2 bg-slate-400 rounded-full" />
              <span>Confidence calibration analysis</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="w-2 h-2 bg-slate-400 rounded-full" />
              <span>Reasoning quality scores</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
