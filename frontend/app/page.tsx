"use client";

import { useAnalysis } from "../hooks/useAnalysis";
import Hero from "../components/Hero";
import InputSection from "../components/InputSection";
import ProgressSection from "../components/ProgressSection";
import ResultsSection from "../components/ResultsSection";

export default function Home() {
  const {
    phase,
    jobStatus,
    currentStep,
    currentStepLabel,
    result,
    error,
    analyze,
    reset,
  } = useAnalysis();

  return (
    <main className="min-h-screen max-w-4xl mx-auto px-4 py-12 flex flex-col gap-8">
      {phase === "idle" && (
        <>
          <Hero />
          <InputSection onSubmit={analyze} isLoading={false} />
        </>
      )}

      {(phase === "submitting" || phase === "polling") && (
        <>
          <InputSection onSubmit={() => {}} isLoading={true} />
          <ProgressSection
            currentStep={currentStep}
            currentStepLabel={currentStepLabel}
            jobStatus={jobStatus || "pending"}
          />
        </>
      )}

      {phase === "complete" && result && (
        <>
          <ResultsSection result={result} />
          <div className="flex justify-center mt-12 mb-12">
            <button
              onClick={reset}
              className="font-sans font-semibold text-ink bg-amber hover:bg-amber/90 py-4 px-8 transition-colors uppercase text-sm"
              style={{
                borderRadius: "4px",
                letterSpacing: "0.08em"
              }}
            >
              Analyze Another Argument
            </button>
          </div>
        </>
      )}

      {phase === "error" && (
        <div className="bg-red-dim border border-red text-red p-6 rounded-lg text-center mt-12">
          <h2 className="text-xl font-semibold mb-2">Analysis Failed</h2>
          <p className="mb-4">{error}</p>
          <button
            onClick={reset}
            className="bg-red text-white hover:bg-red-dim font-medium py-2 px-6 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
    </main>
  );
}
