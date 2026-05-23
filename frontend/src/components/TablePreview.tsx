"use client";

import { TableSchema } from "@/lib/types";

interface TablePreviewProps {
  tables: TableSchema[];
  sessionId: string | null;
}

export default function TablePreview({ tables, sessionId }: TablePreviewProps) {
  if (!sessionId || tables.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-900">Uploaded Tables</h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {tables.map((table) => (
          <div
            key={table.name}
            className="border border-gray-200 rounded-lg p-3 bg-white"
          >
            <p className="font-semibold text-blue-600 text-sm mb-2">
              {table.name}
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {table.columns.map((col) => (
                <div key={col.name} className="text-gray-700">
                  <span className="font-mono">{col.name}</span>
                  <span className="text-gray-500"> {col.type}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
