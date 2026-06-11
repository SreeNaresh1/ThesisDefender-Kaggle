export default function Hero() {
  return (
    <div className="relative w-full py-16 flex flex-col items-start border-b border-steel">
      <div className="absolute top-4 right-4 flex items-center gap-2 text-ghost font-mono text-xs border border-steel px-3 py-1 bg-slate">
        <span className="text-amber">⬡</span> LOGIC ENGINE v2
      </div>
      
      <div className="flex flex-col max-w-4xl">
        <h1 className="font-serif italic text-7xl md:text-8xl lg:text-[100px] leading-[0.8] text-warm-white -mt-4 mb-4 tracking-tight">
          ThesisDefender
        </h1>
        
        <div className="w-full h-px bg-amber opacity-80 mb-6"></div>
        
        <p className="font-sans text-lg md:text-xl text-ghost lowercase tracking-wide max-w-xl">
          Arguments enter. Only the strongest survive.
        </p>
      </div>
    </div>
  );
}
