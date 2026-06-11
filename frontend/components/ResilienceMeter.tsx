import { motion } from "framer-motion";
import { getScoreColor } from "../lib/types";

interface ResilienceMeterProps {
  score: number;
  label: string;
}

export default function ResilienceMeter({ score, label }: ResilienceMeterProps) {
  const color = getScoreColor(score);
  const positionPercentage = `${Math.max(2, Math.min(98, score))}%`;

  return (
    <div className="w-full flex flex-col items-center my-8">
      <div className="flex flex-col items-center mb-6 w-full max-w-3xl">
        <span className="text-sm font-semibold uppercase tracking-widest text-ghost mb-2">Argument Resilience Score</span>
        <span 
          className="text-6xl font-medium tracking-tight mb-1" 
          style={{ color }}
        >
          {score} <span className="text-3xl text-ghost">/ 100</span>
        </span>
        <div className="flex flex-col items-center mt-2 px-4 text-center">
          {(() => {
            const match = label.match(/^([^.]+\.)(.*)/s);
            if (match) {
              return (
                <>
                  <span className="text-xl md:text-2xl font-bold uppercase tracking-wider mb-3" style={{ color }}>{match[1]}</span>
                  <span className="text-sm font-sans text-ghost leading-relaxed">{match[2].trim()}</span>
                </>
              );
            }
            return (
              <span className="text-xl md:text-2xl font-bold uppercase tracking-wider" style={{ color }}>{label}</span>
            );
          })()}
        </div>
      </div>

      <div className="w-full max-w-2xl relative">
        <div className="relative h-3 w-full rounded-full overflow-hidden mb-6 bg-ink border border-steel">
          <motion.div
            initial={{ clipPath: "inset(0 100% 0 0)" }}
            animate={{ clipPath: `inset(0 ${100 - Math.max(2, Math.min(98, score))}% 0 0)` }}
            transition={{ duration: 1.0, ease: "easeOut" }}
            className="absolute top-0 left-0 w-full h-full rounded-full"
            style={{
              background: "linear-gradient(to right, var(--red) 0%, #BA7517 40%, var(--green) 100%)"
            }}
          />
        </div>
        
        <motion.div
          initial={{ left: "0%" }}
          animate={{ left: positionPercentage }}
          transition={{ duration: 1.0, ease: "easeOut" }}
          className="absolute top-[-14px] transform -translate-x-1/2 flex flex-col items-center"
        >
          <div className="w-0 h-0 border-l-[8px] border-r-[8px] border-t-[10px] border-l-transparent border-r-transparent border-t-white mb-1"></div>
          <div className="w-1 h-8 bg-white rounded-full shadow-[0_0_8px_rgba(255,255,255,0.5)]"></div>
        </motion.div>

        <div className="flex justify-between w-full px-2 mt-4 text-[11px] font-bold tracking-wider uppercase text-text-muted">
          <span style={{ color: "var(--red)" }}>Fragile</span>
          <span style={{ color: "#D85A30" }}>Weak</span>
          <span style={{ color: "#BA7517" }}>Defensible</span>
          <span style={{ color: "#4CAF7D" }}>Strong</span>
          <span style={{ color: "var(--green)" }}>Robust</span>
        </div>
      </div>
    </div>
  );
}
