"use client";

import { useState } from "react";

interface QueryFormProps {
  sessionId: string | null;
  isLoading: boolean;
  onSubmit: (question: string) => Promise<void>;
}

export default function QueryForm({
  sessionId,
  isLoading,
  onSubmit,
}: QueryFormProps) {
  const [question, setQuestion] = useState("");
  const MAX_CHARS = 1000;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      await onSubmit(question);
      setQuestion("");
    }
  };

  const isDisabled = !sessionId || isLoading || !question.trim();

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900">Ask a Question</h2>

      <div>
        <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
          Natural Language Question
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value.slice(0, MAX_CHARS))}
          placeholder="e.g., Show me all users with their order counts"
          disabled={!sessionId}
          className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
          rows={5}
        />
        <p className="text-xs text-gray-500 mt-1">
          {question.length} / {MAX_CHARS} characters
        </p>
      </div>

      <button
        type="submit"
        disabled={isDisabled}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isLoading ? "Executing..." : "Generate & Execute SQL"}
      </button>

      {!sessionId && (
        <p className="text-sm text-amber-600">
          ⚠️ Please upload a schema first
        </p>
      )}
    </form>
  );
}
