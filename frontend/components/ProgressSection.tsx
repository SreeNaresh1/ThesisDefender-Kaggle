interface ProgressSectionProps {
  currentStep: number;
  currentStepLabel: string;
  jobStatus: string;
}

export default function ProgressSection({ currentStep, currentStepLabel, jobStatus }: ProgressSectionProps) {
  const steps = [
    { num: 1, title: "Orchestrator: Parsing Argument" },
    { num: 2, title: "Defense Counsel: Steel-manning" },
    { num: 3, title: "Prosecutor: Attacking the Defense" },
    { num: 4, title: "Judge: Final Verdict" },
  ];

  return (
    <div className="w-full bg-bg-card p-8 rounded-xl border border-border shadow-lg my-8">
      <div className="flex flex-col gap-6">
        {steps.map((step) => {
          const isActive = currentStep === step.num;
          const isDone = currentStep > step.num || jobStatus === "complete";
          
          return (
            <div key={step.num} className="flex items-start gap-4">
              <div className="mt-1 flex-shrink-0">
                {isDone ? (
                  <div className="w-4 h-4 rounded-full bg-green flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                ) : isActive ? (
                  <div className="relative flex items-center justify-center w-4 h-4">
                    <span className="absolute w-4 h-4 rounded-full bg-accent animate-ping opacity-75"></span>
                    <span className="relative w-4 h-4 rounded-full bg-accent"></span>
                  </div>
                ) : (
                  <div className="w-4 h-4 rounded-full bg-text-muted opacity-50"></div>
                )}
              </div>
              
              <div className="flex flex-col">
                <span className={`text-lg ${isActive || isDone ? "text-text-primary" : "text-text-muted"}`}>
                  {step.title}
                </span>
                {isActive && (
                  <span className="text-sm text-text-secondary mt-1 animate-pulse">
                    {currentStepLabel}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="mt-8 pt-6 border-t border-border text-center text-sm text-text-muted">
        This takes 15\u201330 seconds
      </div>
    </div>
  );
}
