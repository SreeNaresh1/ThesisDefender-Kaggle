import { useState, useEffect } from "react";

interface InputSectionProps {
  onSubmit: (argument: string) => void;
  isLoading: boolean;
}

type Mode = "steelman" | "attack" | "weakest";

export default function InputSection({ onSubmit, isLoading }: InputSectionProps) {
  const [text, setText] = useState("");
  const [activeMode, setActiveMode] = useState<Mode>("steelman");
  const [wordCount, setWordCount] = useState(0);
  const [sentenceCount, setSentenceCount] = useState(0);
  const [healthScore, setHealthScore] = useState(0);

  useEffect(() => {
    const words = text.trim() === "" ? 0 : text.trim().split(/\s+/).length;
    const sentences = text.trim() === "" ? 0 : text.split(/[.!?]+/).filter(Boolean).length;
    setWordCount(words);
    setSentenceCount(sentences);
    
    // Cosmetic health score based on length and punctuation
    const lengthScore = Math.min(words / 150, 1) * 60;
    const structureScore = Math.min(sentences / 5, 1) * 40;
    setHealthScore(Math.round(lengthScore + structureScore));
  }, [text]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim().length >= 20 && !isLoading) {
      onSubmit(text);
    }
  };

  const isButtonDisabled = text.trim().length < 20 || isLoading;

  return (
    <div className="w-full py-12 flex flex-col lg:flex-row gap-8">
      {/* Mode Selector Sidebar */}
      <div className="flex flex-col gap-4 lg:w-64 flex-shrink-0">
        <button
          onClick={() => setActiveMode("steelman")}
          className={`flex flex-col text-left p-4 border-l-4 transition-all duration-200 ${
            activeMode === "steelman"
              ? "border-sage bg-gradient-to-r from-sage/10 to-transparent"
              : "border-steel hover:border-sage/50"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sage">⚜</span>
            <span className="font-mono text-sm tracking-wide text-warm-white">STEELMAN</span>
          </div>
          <span className="text-xs text-ghost">Build the strongest version of your argument</span>
        </button>

        <button
          onClick={() => setActiveMode("attack")}
          className={`flex flex-col text-left p-4 border-l-4 transition-all duration-200 ${
            activeMode === "attack"
              ? "border-ember bg-gradient-to-r from-ember/10 to-transparent"
              : "border-steel hover:border-ember/50"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-ember">☠</span>
            <span className="font-mono text-sm tracking-wide text-warm-white">ATTACK</span>
          </div>
          <span className="text-xs text-ghost">Find every vulnerability, ranked by severity</span>
        </button>

        <button
          onClick={() => setActiveMode("weakest")}
          className={`flex flex-col text-left p-4 border-l-4 transition-all duration-200 ${
            activeMode === "weakest"
              ? "border-amber bg-gradient-to-r from-amber/10 to-transparent"
              : "border-steel hover:border-amber/50"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-amber">⬡</span>
            <span className="font-mono text-sm tracking-wide text-warm-white">WEAKEST</span>
          </div>
          <span className="text-xs text-ghost">Expose the single point most likely to fail</span>
        </button>
      </div>

      {/* Input Area */}
      <div className="flex-grow flex flex-col gap-4">
        <div className="relative w-full rounded-md border border-steel bg-slate overflow-hidden focus-within:ring-2 focus-within:ring-amber/30 focus-within:border-amber transition-colors duration-200">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="State your claim. Provide your reasoning. Dare to be wrong."
            className="w-full h-80 bg-transparent bg-document-grid bg-grid-sm p-6 text-warm-white text-lg leading-relaxed focus:outline-none resize-none placeholder-ghost/50"
            spellCheck={false}
          />
          
          <div className="absolute bottom-0 left-0 right-0 bg-slate/90 border-t border-steel px-4 py-2 flex items-center justify-between font-mono text-xs text-ghost backdrop-blur-sm">
            <div className="flex gap-4">
              <span>{wordCount} W</span>
              <span>{sentenceCount} S</span>
            </div>
            
            {/* Health Meter */}
            <div className="flex items-center gap-3 w-48">
              <span className="text-[10px] uppercase tracking-wider">Health</span>
              <div className="flex-grow h-1.5 bg-ink rounded-full overflow-hidden">
                <div 
                  className="h-full bg-amber transition-all duration-500 ease-out"
                  style={{ width: `${healthScore}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Example Buttons */}
        <div className="flex flex-wrap gap-2 mt-1">
          <span className="text-xs text-ghost mr-1 mt-1.5 uppercase font-mono tracking-widest">Try:</span>
          {[
            "Remote work increases productivity",
            "College degrees will become less important because of AI",
            "Open-source AI is better for innovation"
          ].map((example, i) => (
            <button
              key={i}
              onClick={() => setText(example)}
              className="text-xs border border-steel hover:border-amber hover:text-amber text-ghost px-3 py-1.5 rounded transition-colors"
            >
              {example}
            </button>
          ))}
        </div>

        <button
          onClick={handleSubmit}
          disabled={isButtonDisabled}
          className={`relative w-full py-4 bg-amber text-ink font-sans font-semibold text-lg overflow-hidden transition-all hover:animate-voltage-flicker disabled:opacity-50 disabled:hover:animate-none ${isLoading ? 'cursor-wait' : ''}`}
        >
          {isLoading && (
            <div className="absolute inset-0 bg-white/20 animate-scan-line w-1/4 skew-x-[-20deg]"></div>
          )}
          <span className="relative z-10 flex items-center justify-center gap-2">
            {isLoading ? "ANALYZING..." : "Run Analysis →"}
          </span>
        </button>
        
        <div className="text-center text-xs text-ghost font-mono uppercase tracking-widest mt-1">
          ⬡ 3-stage adversarial reasoning
        </div>
      </div>
    </div>
  );
}
