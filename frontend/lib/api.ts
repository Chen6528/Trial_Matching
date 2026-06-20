/**
 * Client for the matching backend.
 *
 * The browser calls the FastAPI backend directly (not via a Next.js route
 * handler): `/api/match` runs one Sonnet reasoning call per shortlisted trial in
 * parallel and can take tens of seconds, which would exceed a serverless function
 * timeout. A direct browser→backend request has no such cap, and CORS is already
 * configured on the backend.
 */
import type { MatchResponse, PatientProfile } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Generous headroom for the per-criterion reasoning pass.
const MATCH_TIMEOUT_MS = 120_000;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function matchTrials(profile: PatientProfile): Promise<MatchResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), MATCH_TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(
        "The request timed out. Matching can take up to two minutes — please try again.",
        408,
      );
    }
    throw new ApiError(
      "Couldn't reach the matching service. Is the backend running?",
      0,
    );
  } finally {
    clearTimeout(timeout);
  }

  if (!res.ok) {
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Non-JSON error body — fall back to a generic message below.
    }
    throw new ApiError(detail || `Matching failed (HTTP ${res.status}).`, res.status);
  }

  return (await res.json()) as MatchResponse;
}
