interface ImprovementsPanelProps {
  improvements: string[];
}

export default function ImprovementsPanel({ improvements }: ImprovementsPanelProps) {
  return (
    <div className="flex flex-col p-6 bg-ink text-warm-white">
      <div className="flex items-center gap-3 mb-4 font-mono text-sm tracking-widest text-ghost uppercase">
        <span className="text-amber">✓</span> 
        <span>Actionable Fixes</span>
      </div>
      
      <div className="pl-6 ml-1">
        <ul className="space-y-3">
          {improvements.map((improvement, i) => (
            <li key={i} className="flex gap-3 text-sm text-ghost">
              <span className="text-amber font-mono text-xs mt-0.5">[{i + 1}]</span>
              <span className="leading-relaxed">{improvement}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
