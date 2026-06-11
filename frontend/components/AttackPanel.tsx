import { AttackOutput } from "../lib/types";

interface AttackPanelProps {
  attack: AttackOutput;
}

export default function AttackPanel({ attack }: AttackPanelProps) {
  return (
    <div className="flex flex-col border-b border-steel p-6 bg-ink text-warm-white">
      <div className="flex items-center gap-3 mb-4 font-mono text-sm tracking-widest text-ghost uppercase">
        <span className="text-ember">☠️</span> 
        <span>Strongest Attack</span>
      </div>
      
      <p className="text-sm text-warm-white leading-relaxed mb-4 pl-6 border-l border-steel ml-1">
        {attack.strongest_attack}
      </p>
      
      <div className="pl-6 ml-1">
        <ul className="space-y-2">
          {attack.counterpoints.map((flaw, i) => (
            <li key={i} className="flex gap-3 text-sm text-ghost">
              <span className="text-ember">▸</span>
              <span>{flaw}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
