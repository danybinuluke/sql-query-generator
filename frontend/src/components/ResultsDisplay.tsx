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
        <h2 className="text-2xl font-bold text-gray-900">Results</h2>
        <p className="text-gray-500 italic">
          Upload a schema and ask a question to see results
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900">Results</h2>
        <p className="text-gray-500 italic">Results will appear here</p>
      </div>
    );
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900">Results</h2>

      {result.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-semibold">Error</p>
          <p className="text-red-700 text-sm">{result.error}</p>
        </div>
      )}

      <div className="bg-gray-50 rounded-lg p-4 space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-gray-900">Generated SQL</h3>
          <button
            onClick={() => copyToClipboard(result.generated_sql)}
            className="text-xs px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded"
          >
            Copy
          </button>
        </div>
        <pre className="bg-white border border-gray-300 rounded p-3 overflow-x-auto text-sm text-gray-800">
          {result.generated_sql}
        </pre>
      </div>

      {result.result && !result.error && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <h3 className="font-semibold text-gray-900">Query Result</h3>
          <div className="bg-white border border-gray-300 rounded p-3 overflow-x-auto max-h-96">
            {typeof result.result === "object" && result.result !== null ? (
              <>
                {Array.isArray(result.result) ? (
                  result.result.length > 0 ? (
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          {Object.keys(result.result[0]).map((key) => (
                            <th
                              key={key}
                              className="text-left px-2 py-1 font-semibold"
                            >
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {result.result.map((row, idx) => (
                          <tr key={idx} className="border-b hover:bg-blue-50">
                            {Object.values(row).map((val, colIdx) => (
                              <td key={colIdx} className="px-2 py-1">
                                {val === null ? (
                                  <span className="text-gray-400 italic">
                                    NULL
                                  </span>
                                ) : (
                                  String(val)
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="text-gray-500 italic">No results found</p>
                  )
                ) : (
                  <pre className="text-sm">
                    {JSON.stringify(result.result, null, 2)}
                  </pre>
                )}
              </>
            ) : (
              <p className="text-lg font-semibold">
                {String(result.result)}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
