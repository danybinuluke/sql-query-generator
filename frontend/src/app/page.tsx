"use client";

import { useState, useEffect } from "react";
import SchemaUpload from "@/components/SchemaUpload";
import QueryForm from "@/components/QueryForm";
import ResultsDisplay from "@/components/ResultsDisplay";
import TablePreview from "@/components/TablePreview";
import { apiClient } from "@/lib/api";
import { TableSchema, QueryResponse } from "@/lib/types";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [tables, setTables] = useState<TableSchema[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    apiClient.healthCheck().then((connected) => {
      setIsConnected(connected);
      if (!connected) {
        setError(
          "Backend not available. Make sure the backend is running on http://localhost:8000"
        );
      }
    });
  }, []);

  const handleSchemaUpload = (newSessionId: string, newTables: TableSchema[]) => {
    setSessionId(newSessionId);
    setTables(newTables);
    setQueryResult(null);
    setError(null);
  };

  const handleQuerySubmit = async (question: string) => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);
    setQueryResult(null);

    try {
      const result = await apiClient.queryQuestion(sessionId, question);
      setQueryResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearSession = () => {
    setSessionId(null);
    setTables([]);
    setQueryResult(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            SQLGenie
          </h1>
          <p className="text-gray-600">
            AI SQL Assistant - Convert natural language to SQL queries
          </p>
        </div>

        {!isConnected && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 font-semibold">⚠️ Connection Error</p>
            <p className="text-red-700 text-sm">
              Cannot connect to backend. Please ensure it's running on
              http://localhost:8000
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 font-semibold">Error</p>
            <p className="text-red-700 text-sm">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800 text-sm mt-2 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {sessionId && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-green-800 font-semibold">
                  ✓ Schema Loaded ({tables.length} table
                  {tables.length !== 1 ? "s" : ""})
                </p>
                <p className="text-green-700 text-sm font-mono">
                  Session: {sessionId}
                </p>
              </div>
              <button
                onClick={handleClearSession}
                className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
              >
                Clear & Upload New
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <SchemaUpload
                onUploadSuccess={handleSchemaUpload}
                onError={(err) => setError(err)}
              />
            </div>

            {tables.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <TablePreview tables={tables} sessionId={sessionId} />
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <QueryForm
                sessionId={sessionId}
                isLoading={isLoading}
                onSubmit={handleQuerySubmit}
              />
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <ResultsDisplay result={queryResult} sessionId={sessionId} />
            </div>
          </div>
        </div>

        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>SQLGenie v0.1.0 - AI SQL Assistant</p>
          <p>Powered by TinyLlama and FastAPI</p>
        </div>
      </div>
    </main>
  );
}
