'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fewShotApi, handleApiError } from '@/lib/api';
import type { FewShotExample } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Trash2, Plus, ToggleLeft, ToggleRight } from 'lucide-react';
import Link from 'next/link';

export default function FewShotExamplesPage() {
  const queryClient = useQueryClient();
  const [fieldFilter, setFieldFilter] = useState<string>('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newExample, setNewExample] = useState({
    field_path: '',
    source_text: '',
    correct_value: '',
    reasoning: '',
    quality_score: 1.0,
  });

  const { data: examples = [], isLoading } = useQuery({
    queryKey: ['few-shot-examples', fieldFilter],
    queryFn: () =>
      fewShotApi.list(fieldFilter ? { field_path: fieldFilter } : undefined),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      fewShotApi.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['few-shot-examples'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: fewShotApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['few-shot-examples'] }),
    onError: (error: any) => alert(`Delete failed: ${handleApiError(error)}`),
  });

  const createMutation = useMutation({
    mutationFn: fewShotApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['few-shot-examples'] });
      setShowAddForm(false);
      setNewExample({ field_path: '', source_text: '', correct_value: '', reasoning: '', quality_score: 1.0 });
    },
    onError: (error: any) => alert(`Create failed: ${handleApiError(error)}`),
  });

  const handleDelete = (id: number) => {
    if (confirm('Delete this example?')) {
      deleteMutation.mutate(id);
    }
  };

  // Get unique field paths for filter
  const fieldPaths = [...new Set(examples.map((e) => e.field_path))].sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Few-Shot Examples</h1>
          <p className="mt-1 text-sm text-slate-600">
            Training examples that improve extraction accuracy. These are included in prompts sent to Claude.
          </p>
        </div>
        <Button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-amber-500 hover:bg-amber-600 text-white"
        >
          <Plus className="w-4 h-4 mr-1.5" />
          Add Example
        </Button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
          <h3 className="text-lg font-semibold text-slate-900">New Example</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Field Path</label>
              <input
                type="text"
                value={newExample.field_path}
                onChange={(e) => setNewExample({ ...newExample, field_path: e.target.value })}
                placeholder="e.g., rent.base_rent_monthly"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Correct Value</label>
              <input
                type="text"
                value={newExample.correct_value}
                onChange={(e) => setNewExample({ ...newExample, correct_value: e.target.value })}
                placeholder="e.g., 15000.00"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Source Text</label>
            <textarea
              value={newExample.source_text}
              onChange={(e) => setNewExample({ ...newExample, source_text: e.target.value })}
              placeholder="Excerpt from the lease PDF..."
              rows={3}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Reasoning</label>
            <textarea
              value={newExample.reasoning}
              onChange={(e) => setNewExample({ ...newExample, reasoning: e.target.value })}
              placeholder="Why this is the correct value..."
              rows={2}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowAddForm(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate(newExample)}
              disabled={!newExample.field_path || !newExample.source_text || !newExample.correct_value || createMutation.isPending}
              className="bg-amber-500 hover:bg-amber-600 text-white"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Example'}
            </Button>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex items-center gap-4">
        <select
          value={fieldFilter}
          onChange={(e) => setFieldFilter(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-amber-500"
        >
          <option value="">All fields ({examples.length})</option>
          {fieldPaths.map((path) => (
            <option key={path} value={path}>
              {path} ({examples.filter((e) => e.field_path === path).length})
            </option>
          ))}
        </select>
        <span className="text-sm text-slate-500">
          {examples.filter((e) => e.is_active).length} active / {examples.length} total
        </span>
      </div>

      {/* Examples Table */}
      {isLoading ? (
        <div className="text-center py-12 text-slate-500">Loading examples...</div>
      ) : examples.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
          <p className="text-slate-500">No few-shot examples yet.</p>
          <p className="text-sm text-slate-400 mt-1">
            Promote corrections from the review page or add examples manually.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="divide-y divide-slate-100">
            {examples.map((example) => (
              <div
                key={example.id}
                className={`px-6 py-4 ${!example.is_active ? 'opacity-50' : ''}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {example.field_path}
                      </span>
                      {example.quality_score !== null && (
                        <span className="text-xs text-slate-500">
                          Quality: {example.quality_score?.toFixed(1)}
                        </span>
                      )}
                      <span className="text-xs text-slate-400">
                        Used {example.usage_count}x
                      </span>
                      {example.created_from_correction_id && (
                        <span className="text-xs text-amber-600">From correction</span>
                      )}
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-xs font-medium text-slate-500 mb-1">Source Text</p>
                        <p className="text-slate-700 line-clamp-2">{example.source_text}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-slate-500 mb-1">Correct Value</p>
                        <p className="text-slate-900 font-medium">{example.correct_value}</p>
                      </div>
                    </div>
                    {example.reasoning && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-slate-500 mb-1">Reasoning</p>
                        <p className="text-sm text-slate-600 line-clamp-1">{example.reasoning}</p>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleMutation.mutate({ id: example.id, is_active: !example.is_active })}
                      className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
                      title={example.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {example.is_active ? (
                        <ToggleRight className="w-5 h-5 text-green-600" />
                      ) : (
                        <ToggleLeft className="w-5 h-5 text-slate-400" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(example.id)}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors"
                      title="Delete example"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
