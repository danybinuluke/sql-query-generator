import {
  SchemaUploadResponse,
  QueryResponse,
  QueryRequest,
  ApiError,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const apiClient = {
  async uploadSchema(file: File): Promise<SchemaUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/upload-schema`, {
      method: "POST",
      body: formData,
    });

    return handleResponse<SchemaUploadResponse>(response);
  },

  async queryQuestion(
    sessionId: string,
    question: string
  ): Promise<QueryResponse> {
    const request: QueryRequest = {
      session_id: sessionId,
      question,
    };

    const response = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    return handleResponse<QueryResponse>(response);
  },

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: "GET",
      });
      return response.ok;
    } catch {
      return false;
    }
  },
};
