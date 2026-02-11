'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { promptApi, handleApiError } from '@/lib/api';
import type { PromptTemplate } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Check, Copy, Plus, Save } from 'lucide-react';

const TABS = [
  { key: 'system_prompt', label: 'System Prompt' },
  { key: 'field_type_guidance', label: 'Field Type Guidance' },
  { key: 'extraction_examples', label: 'Extraction Examples' },
  { key: 'null_value_guidance', label: 'Null Value Guidance' },
] as const;

type TabKey = (typeof TABS)[number]['key'];

export default function PromptEditorPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('system_prompt');
  const [editBuffer, setEditBuffer] = useState<Record<TabKey, string>>({
    system_prompt: '',
    field_type_guidance: '',
    extraction_examples: '',
    null_value_guidance: '',
  });
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  const { data: promptsList = [], isLoading } = useQuery({
    queryKey: ['prompts'],
    queryFn: promptApi.list,
  });

  // Select the first prompt if none selected
  useEffect(() => {
    if (promptsList.length > 0 && selectedId === null) {
      const active = promptsList.find((p) => p.is_active);
      setSelectedId(active?.id ?? promptsList[0].id);
    }
  }, [promptsList, selectedId]);

  // Load selected prompt into edit buffer
  const selectedPrompt = promptsList.find((p) => p.id === selectedId);
  useEffect(() => {
    if (selectedPrompt) {
      setEditBuffer({
        system_prompt: selectedPrompt.system_prompt,
        field_type_guidance: selectedPrompt.field_type_guidance,
        extraction_examples: selectedPrompt.extraction_examples,
        null_value_guidance: selectedPrompt.null_value_guidance,
      });
      setEditName(selectedPrompt.name);
      setEditDescription(selectedPrompt.description || '');
      setIsDirty(false);
    }
  }, [selectedPrompt?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selectedId) return;
      return promptApi.update(selectedId, {
        name: editName,
        description: editDescription,
        ...editBuffer,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      setIsDirty(false);
    },
    onError: (error: any) => alert(`Save failed: ${handleApiError(error)}`),
  });

  const activateMutation = useMutation({
    mutationFn: (id: number) => promptApi.activate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prompts'] }),
    onError: (error: any) => alert(`Activate failed: ${handleApiError(error)}`),
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: number) => promptApi.duplicate(id),
    onSuccess: (newPrompt) => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      setSelectedId(newPrompt.id);
    },
    onError: (error: any) => alert(`Duplicate failed: ${handleApiError(error)}`),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      promptApi.create({
        name: 'New Prompt',
        system_prompt: '',
        field_type_guidance: '',
        extraction_examples: '',
        null_value_guidance: '',
      }),
    onSuccess: (newPrompt) => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      setSelectedId(newPrompt.id);
    },
    onError: (error: any) => alert(`Create failed: ${handleApiError(error)}`),
  });

  const handleTabEdit = (value: string) => {
    setEditBuffer((prev) => ({ ...prev, [activeTab]: value }));
    setIsDirty(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Prompt Editor</h1>
        <p className="mt-1 text-sm text-slate-600">
          Version and edit extraction prompts. Only the active prompt is used during extraction.
        </p>
      </div>

      <div className="flex gap-6 min-h-[600px]">
        {/* Left: Version List */}
        <div className="w-72 flex-shrink-0 space-y-3">
          <Button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            variant="outline"
            className="w-full"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Version
          </Button>

          {isLoading ? (
            <div className="text-center py-8 text-slate-500">Loading...</div>
          ) : (
            <div className="space-y-1">
              {promptsList.map((prompt) => (
                <button
                  key={prompt.id}
                  onClick={() => {
                    if (isDirty && !confirm('Discard unsaved changes?')) return;
                    setSelectedId(prompt.id);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                    selectedId === prompt.id
                      ? 'border-amber-300 bg-amber-50'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-900 truncate">
                      v{prompt.version}
                    </span>
                    {prompt.is_active && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 truncate mt-0.5">
                    {prompt.name}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                    <span>{prompt.usage_count} uses</span>
                    {prompt.avg_confidence != null && (
                      <span>{Math.round(prompt.avg_confidence * 100)}% avg</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Editor */}
        {selectedPrompt ? (
          <div className="flex-1 bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div className="flex-1 mr-4">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => {
                    setEditName(e.target.value);
                    setIsDirty(true);
                  }}
                  className="text-lg font-semibold text-slate-900 bg-transparent border-none outline-none w-full"
                  placeholder="Prompt name"
                />
                <input
                  type="text"
                  value={editDescription}
                  onChange={(e) => {
                    setEditDescription(e.target.value);
                    setIsDirty(true);
                  }}
                  className="text-sm text-slate-500 bg-transparent border-none outline-none w-full mt-0.5"
                  placeholder="Description (optional)"
                />
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => duplicateMutation.mutate(selectedPrompt.id)}
                  disabled={duplicateMutation.isPending}
                  variant="outline"
                  size="sm"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Duplicate
                </Button>
                {!selectedPrompt.is_active && (
                  <Button
                    onClick={() => {
                      if (confirm(`Activate v${selectedPrompt.version}? This will deactivate the current active prompt.`)) {
                        activateMutation.mutate(selectedPrompt.id);
                      }
                    }}
                    disabled={activateMutation.isPending}
                    variant="outline"
                    size="sm"
                    className="text-green-700 border-green-300 hover:bg-green-50"
                  >
                    <Check className="w-4 h-4 mr-1" />
                    Activate
                  </Button>
                )}
                <Button
                  onClick={() => saveMutation.mutate()}
                  disabled={!isDirty || saveMutation.isPending}
                  size="sm"
                  className="bg-amber-500 hover:bg-amber-600 text-white"
                >
                  <Save className="w-4 h-4 mr-1" />
                  {saveMutation.isPending ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-200">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? 'text-amber-700 border-b-2 border-amber-500 bg-amber-50/50'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Editor */}
            <div className="flex-1 p-0">
              <textarea
                value={editBuffer[activeTab]}
                onChange={(e) => handleTabEdit(e.target.value)}
                className="w-full h-full min-h-[400px] p-6 text-sm font-mono text-slate-800 bg-slate-50 border-none outline-none resize-none"
                placeholder={`Enter ${TABS.find((t) => t.key === activeTab)?.label.toLowerCase()}...`}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-white rounded-xl border border-slate-200">
            <p className="text-slate-500">Select or create a prompt template</p>
          </div>
        )}
      </div>
    </div>
  );
}
