"use client";

import { QueryResponse } from "@/lib/types";

interface ResultsDisplayProps {
  result: QueryResponse | null;
  sessionId: string | null;
}

export default function ResultsDisplay({
  result,
  sessionId,
}: ResultsDisplayProps) {
  if (!sessionId) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900">Generated SQL</h2>
        <p className="text-gray-500 italic">
          Upload a schema and ask a question to generate SQL
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900">Generated SQL</h2>
        <p className="text-gray-500 italic">SQL will appear here</p>
      </div>
    );
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900">Generated SQL</h2>

      {result.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-semibold">Error</p>
          <p className="text-red-700 text-sm">{result.error}</p>
        </div>
      )}

      {result.generated_sql && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold text-gray-900">SQL Query</h3>
            <button
              onClick={() => copyToClipboard(result.generated_sql)}
              className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Copy SQL
            </button>
          </div>
          <pre className="bg-white border border-gray-300 rounded p-3 overflow-x-auto text-sm text-gray-800 font-mono">
            {result.generated_sql}
          </pre>
        </div>
      )}
    </div>
  );
}
