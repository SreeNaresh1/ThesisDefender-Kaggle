interface WeakestLinkPanelProps {
  vulnerability: string;
}

export default function WeakestLinkPanel({ vulnerability }: WeakestLinkPanelProps) {
  return (
    <div className="flex flex-col border-b border-steel p-6 bg-slate text-warm-white relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-amber opacity-5 rounded-full blur-3xl"></div>
      
      <div className="flex items-center gap-3 mb-4 font-mono text-sm tracking-widest text-amber uppercase">
        <span className="text-amber">⬡</span> 
        <span>Critical Vulnerability</span>
      </div>
      
      <div className="pl-6 ml-1">
        <p className="text-base text-amber leading-relaxed font-sans font-medium">
          {vulnerability}
        </p>
      </div>
    </div>
  );
}
