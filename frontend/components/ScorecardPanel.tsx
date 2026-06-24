import { ScoreBreakdown } from "../lib/types";

interface ScorecardPanelProps {
  breakdown: ScoreBreakdown;
  explanation: string;
}

export default function ScorecardPanel({ breakdown, explanation }: ScorecardPanelProps) {
  const dimensions = [
    { key: "evidence_quality", label: "Evidence Quality", data: breakdown.evidence_quality },
    { key: "assumption_strength", label: "Assumption Strength", data: breakdown.assumption_strength },
    { key: "counterargument_resistance", label: "Counterargument Resistance", data: breakdown.counterargument_resistance },
    { key: "practical_feasibility", label: "Practical Feasibility", data: breakdown.practical_feasibility },
    { key: "scope_precision", label: "Scope Precision", data: breakdown.scope_precision },
  ];

  return (
    <div className="flex flex-col border-b border-steel p-6 bg-ink text-warm-white">
      <div className="flex items-center gap-3 mb-4 font-mono text-sm tracking-widest text-ghost uppercase">
        <span className="text-amber">⊞</span> 
        <span>Resilience Scorecard</span>
      </div>
      
      <div className="pl-6 ml-1 flex flex-col gap-6 border-l border-steel">
        <div className="text-sm text-ghost italic border-l-2 border-ghost pl-4">
          {explanation}
        </div>
        
        <div className="flex flex-col gap-4">
          {dimensions.map((dim) => (
            <div key={dim.key} className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-sm font-mono tracking-wide">
                <span className="text-warm-white">{dim.label}</span>
                <span className="text-amber font-bold">{dim.data.score}/20</span>
              </div>
              <div className="w-full bg-steel/30 h-1.5 rounded-full overflow-hidden mb-1">
                <div 
                  className="bg-amber h-full rounded-full transition-all duration-1000" 
                  style={{ width: `${(dim.data.score / 20) * 100}%` }}
                />
              </div>
              <span className="text-xs text-ghost leading-relaxed">{dim.data.reason}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
