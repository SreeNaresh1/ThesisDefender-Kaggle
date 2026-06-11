import { DefenseOutput } from "../lib/types";

interface SteelManPanelProps {
  defense: DefenseOutput;
}

export default function SteelManPanel({ defense }: SteelManPanelProps) {
  return (
    <div className="flex flex-col border-b border-steel p-6 bg-ink text-warm-white">
      <div className="flex items-center gap-3 mb-4 font-mono text-sm tracking-widest text-ghost uppercase">
        <span className="text-sage">⚖️</span> 
        <span>Steel-Man Defense</span>
      </div>
      
      <p className="text-sm text-warm-white leading-relaxed mb-4 pl-6 border-l border-steel ml-1">
        {defense.best_defense}
      </p>
      
      <div className="pl-6 ml-1">
        <ul className="space-y-2">
          {defense.supporting_points.map((point, i) => (
            <li key={i} className="flex gap-3 text-sm text-ghost">
              <span className="text-sage">▸</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
