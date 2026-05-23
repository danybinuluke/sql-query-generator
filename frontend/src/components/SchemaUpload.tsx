"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api";
import { TableSchema } from "@/lib/types";

interface SchemaUploadProps {
  onUploadSuccess: (sessionId: string, tables: TableSchema[]) => void;
  onError: (error: string) => void;
}

export default function SchemaUpload({
  onUploadSuccess,
  onError,
}: SchemaUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      const file = files[0];
      if (file.name.endsWith(".sql")) {
        setSelectedFile(file);
      } else {
        onError("Please select a .sql file");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      const file = files[0];
      if (file.name.endsWith(".sql")) {
        setSelectedFile(file);
      } else {
        onError("Please select a .sql file");
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      onError("Please select a file first");
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiClient.uploadSchema(selectedFile);
      onUploadSuccess(response.session_id, response.tables);
      setSelectedFile(null);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900">Upload Schema</h2>

      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          isDragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-gray-50"
        }`}
      >
        <div className="space-y-2">
          <p className="text-gray-600">Drag and drop your SQL file here</p>
          <p className="text-gray-500 text-sm">or</p>

          <label className="relative inline-block">
            <span className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 cursor-pointer">
              Browse Files
            </span>
            <input
              type="file"
              accept=".sql"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          {selectedFile && (
            <p className="text-green-600 text-sm mt-2">
              Selected: {selectedFile.name}
            </p>
          )}
        </div>
      </div>

      <button
        onClick={handleUpload}
        disabled={!selectedFile || isLoading}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isLoading ? "Uploading..." : "Upload Schema"}
      </button>
    </div>
  );
}
