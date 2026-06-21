import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import IntakeForm from "@/components/IntakeForm";
import ResultsList from "@/components/ResultsList";
import type { TrialMatch } from "@/lib/types";

afterEach(cleanup);

describe("IntakeForm", () => {
  it("prefills the example patient into the form", async () => {
    render(<IntakeForm onSubmit={vi.fn()} pending={false} />);

    const condition = screen.getByLabelText("Primary condition") as HTMLInputElement;
    expect(condition.value).toBe("");

    fireEvent.click(screen.getByRole("button", { name: /prefill example/i }));

    await waitFor(() => expect(condition.value).toBe("non-small cell lung cancer"));
  });
});

describe("ResultsList", () => {
  const trial: TrialMatch = {
    nct_id: "NCT00000001",
    brief_title: "A Study of Osimertinib in EGFR-positive NSCLC",
    url: "https://clinicaltrials.gov/study/NCT00000001",
    eligibility: "likely_eligible",
    confidence: 0.8,
    similarity: 0.91,
    criteria: [
      {
        type: "inclusion",
        text: "ECOG performance status 0 or 1",
        status: "met",
        reason: "Patient ECOG is 1.",
      },
      {
        type: "exclusion",
        text: "Active brain metastases",
        status: "unknown",
        reason: "No data on brain metastases.",
      },
    ],
  };

  it("renders a trial card and expands its criteria", () => {
    render(<ResultsList results={[trial]} />);

    expect(
      screen.getByText("A Study of Osimertinib in EGFR-positive NSCLC"),
    ).toBeInTheDocument();

    // Criteria are collapsed until the toggle is clicked.
    expect(screen.queryByText("ECOG performance status 0 or 1")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /criteria/i }));

    expect(screen.getByText("ECOG performance status 0 or 1")).toBeInTheDocument();
    expect(screen.getByText("Patient ECOG is 1.")).toBeInTheDocument();
  });

  it("shows an empty state when there are no results", () => {
    render(<ResultsList results={[]} />);
    expect(screen.getByText(/no matching trials found/i)).toBeInTheDocument();
  });
});
