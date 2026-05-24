export type RequestStatus =
  | "idle"
  | "loading"
  | "streaming"
  | "success"
  | "error";

export type DocumentQAStatus =
  | "idle"
  | "loading"
  | "success"
  | "error";

export type ToolCallStatus =
  | "idle"
  | "loading"
  | "pending_approval"
  | "approved"
  | "executing"
  | "success"
  | "cancelled"
  | "error";
