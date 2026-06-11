import { motion } from "framer-motion";
import { ArgumentStructure, DefenseOutput, AttackOutput } from "../lib/types";

interface ArgumentGraphProps {
  structure: ArgumentStructure;
  defense: DefenseOutput;
  attack: AttackOutput;
  vulnerability: string;
}

export default function ArgumentGraph({ structure, defense, attack, vulnerability }: ArgumentGraphProps) {
  // Loose mapping: pair defense points with attack points for visual structure
  const pairs = Math.max(defense.supporting_points.length, attack.counterpoints.length);
  
  // Find the attack point that best matches the critical vulnerability
  const getWordOverlap = (s1: string, s2: string) => {
    const words1 = new Set(s1.toLowerCase().split(/\W+/).filter(w => w.length > 3));
    const words2 = new Set(s2.toLowerCase().split(/\W+/).filter(w => w.length > 3));
    let overlap = 0;
    for (const w of Array.from(words1)) if (words2.has(w)) overlap++;
    return overlap;
  };

  let criticalIndex = 0;
  let maxOverlap = -1;
  attack.counterpoints.forEach((point, idx) => {
    const overlap = getWordOverlap(point, vulnerability);
    if (overlap > maxOverlap) {
      maxOverlap = overlap;
      criticalIndex = idx;
    }
  });
  
  return (
    <div className="w-full bg-slate border border-steel rounded p-8 overflow-hidden mb-8 relative">
      <div className="absolute top-4 left-4 text-[10px] font-mono text-ghost uppercase tracking-widest">
        ⬡ Argument Anatomy
      </div>
      
      <div className="flex flex-col items-center mt-6">
        {/* Main Claim Node */}
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="bg-ink border-2 border-amber text-warm-white p-4 rounded-md max-w-lg text-center shadow-[0_0_15px_rgba(232,168,56,0.15)] z-10"
        >
          <div className="text-[10px] font-mono text-amber mb-2 uppercase tracking-widest">Core Claim</div>
          <div className="text-sm">{structure.main_claim}</div>
        </motion.div>

        {/* Stem Line */}
        <div className="w-px h-8 bg-steel"></div>
        <div className="w-full max-w-3xl h-px bg-steel"></div>

        {/* Pillars */}
        <div className="flex w-full max-w-3xl justify-between mt-0">
          {Array.from({ length: pairs }).map((_, i) => {
            const defPoint = defense.supporting_points[i];
            const attPoint = attack.counterpoints[i];
            
            return (
              <div key={i} className="flex flex-col items-center w-1/3 px-2">
                <div className="w-px h-8 bg-steel"></div>
                
                {/* Defense Node */}
                {defPoint ? (
                  <motion.div 
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 + (i * 0.1) }}
                    className="w-full bg-ink border border-sage p-3 text-xs text-ghost rounded"
                  >
                    <div className="w-2 h-2 rounded-full bg-sage mr-2 inline-block"></div>
                    {defPoint}
                  </motion.div>
                ) : (
                  <div className="w-full h-12"></div> // spacer
                )}

                {/* Connection to Attack */}
                {attPoint && (
                  <>
                    <div className="w-px h-6 bg-ember/50 border-l border-dashed border-ember"></div>
                    {/* Attack Node */}
                    <motion.div 
                      initial={{ y: 20, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      transition={{ delay: 0.5 + (i * 0.1) }}
                      className={`w-full bg-ember/10 border ${i === criticalIndex ? 'border-amber shadow-[0_0_10px_rgba(232,168,56,0.15)]' : 'border-ember'} p-3 text-xs text-warm-white rounded relative`}
                    >
                      <div className={`w-2 h-2 rounded-full ${i === criticalIndex ? 'bg-amber' : 'bg-ember'} mr-2 inline-block`}></div>
                      {attPoint}
                      
                      {/* Highlight if this is considered the critical vulnerability */}
                      {i === criticalIndex && (
                        <div className="absolute -bottom-2 -right-2 bg-amber text-ink text-[9px] font-sans font-semibold px-1 py-0.5 rounded shadow-lg animate-pulse">
                          CRITICAL
                        </div>
                      )}
                    </motion.div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
