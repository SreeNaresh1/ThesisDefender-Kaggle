interface StrengthPanelProps {
  originalClaim: string;
  strengthenedClaim: string;
}

export default function StrengthPanel({ originalClaim, strengthenedClaim }: StrengthPanelProps) {
  return (
    <div className="flex flex-col border-b border-steel p-6 bg-ink text-warm-white">
      <div className="flex items-center gap-3 mb-4 font-mono text-sm tracking-widest text-ghost uppercase">
        <span className="text-sage">✦</span> 
        <span>Recommended Revision</span>
      </div>
      
      <div className="pl-6 ml-1 flex flex-col gap-4 border-l border-steel">
        <div className="flex flex-col gap-1 pl-4">
          <span className="font-mono text-[10px] text-ghost">ORIGINAL</span>
          <span className="text-sm text-ghost line-through opacity-70">"{originalClaim}"</span>
        </div>
        
        <div className="flex flex-col gap-1 pl-4 border-l-2 border-sage">
          <span className="font-mono text-[10px] text-sage">REVISION</span>
          <span className="text-base text-warm-white">"{strengthenedClaim}"</span>
        </div>
      </div>
    </div>
  );
}
