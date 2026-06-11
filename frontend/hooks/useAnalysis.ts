"use client";

import { useReducer, useRef, useEffect } from "react";
import { AnalysisStatus, ArgumentAnalysis } from "../lib/types";
import { startAnalysis, getJobStatus, getResult, ApiError } from "../lib/api";

type Phase = "idle" | "submitting" | "polling" | "complete" | "error";

interface State {
  phase: Phase;
  jobId: string | null;
  jobStatus: AnalysisStatus | null;
  currentStep: number;
  currentStepLabel: string;
  result: ArgumentAnalysis | null;
  error: string | null;
}

type Action =
  | { type: "START_SUBMIT" }
  | { type: "JOB_CREATED"; jobId: string }
  | { type: "STATUS_UPDATE"; status: AnalysisStatus; step: number; label: string }
  | { type: "COMPLETE"; result: ArgumentAnalysis }
  | { type: "ERROR"; error: string }
  | { type: "RESET" };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "START_SUBMIT":
      return { ...state, phase: "submitting", error: null };
    case "JOB_CREATED":
      return { ...state, phase: "polling", jobId: action.jobId };
    case "STATUS_UPDATE":
      return {
        ...state,
        jobStatus: action.status,
        currentStep: action.step,
        currentStepLabel: action.label,
      };
    case "COMPLETE":
      return { ...state, phase: "complete", result: action.result };
    case "ERROR":
      return { ...state, phase: "error", error: action.error };
    case "RESET":
      return {
        phase: "idle",
        jobId: null,
        jobStatus: null,
        currentStep: 0,
        currentStepLabel: "",
        result: null,
        error: null,
      };
    default:
      return state;
  }
}

const initialState: State = {
  phase: "idle",
  jobId: null,
  jobStatus: null,
  currentStep: 0,
  currentStepLabel: "",
  result: null,
  error: null,
};

export function useAnalysis() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const cleanup = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    return cleanup;
  }, []);

  useEffect(() => {
    if (state.phase === "polling" && state.jobId) {
      intervalRef.current = setInterval(async () => {
        try {
          const job = await getJobStatus(state.jobId!);
          dispatch({
            type: "STATUS_UPDATE",
            status: job.status,
            step: job.current_step,
            label: job.current_step_label,
          });

          if (job.status === "complete") {
            cleanup();
            const result = await getResult(state.jobId!);
            dispatch({ type: "COMPLETE", result });
          } else if (job.status === "failed") {
            cleanup();
            dispatch({ type: "ERROR", error: job.error_message || "Analysis failed" });
          }
        } catch (err: any) {
          if (err instanceof ApiError && err.status === 404) {
            cleanup();
            dispatch({ type: "ERROR", error: "Job not found" });
          } else {
            console.warn("Polling error (transient):", err);
          }
        }
      }, 2000);
    }
    return cleanup;
  }, [state.phase, state.jobId]);

  const analyze = async (argument: string) => {
    dispatch({ type: "START_SUBMIT" });
    try {
      const { job_id } = await startAnalysis(argument);
      dispatch({ type: "JOB_CREATED", jobId: job_id });
    } catch (err: any) {
      dispatch({ type: "ERROR", error: err.message || "Failed to start analysis" });
    }
  };

  const reset = () => {
    cleanup();
    dispatch({ type: "RESET" });
  };

  return { ...state, analyze, reset };
}
