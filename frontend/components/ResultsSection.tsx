import { motion } from "framer-motion";
import { ArgumentAnalysis } from "../lib/types";
import ArgumentGraph from "./ArgumentGraph";
import SteelManPanel from "./SteelManPanel";
import AttackPanel from "./AttackPanel";
import WeakestLinkPanel from "./WeakestLinkPanel";
import StrengthPanel from "./StrengthPanel";
import ResilienceMeter from "./ResilienceMeter";

interface ResultsSectionProps {
  result: ArgumentAnalysis;
}

export default function ResultsSection({ result }: ResultsSectionProps) {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, ease: "easeOut" },
    },
  };

  const shortId = result.job_id.substring(0, 4).toUpperCase();
  const truncatedClaim = result.structure.main_claim.length > 50 
    ? result.structure.main_claim.substring(0, 50) + "..." 
    : result.structure.main_claim;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col w-full max-w-4xl mx-auto mt-8 font-sans"
    >
      <motion.div variants={itemVariants}>
        <ArgumentGraph 
          structure={result.structure}
          defense={result.defense}
          attack={result.attack}
          vulnerability={result.verdict.critical_vulnerability}
        />
      </motion.div>

      <motion.div variants={itemVariants} className="mb-8">
        <ResilienceMeter 
          score={result.verdict.resilience_score} 
          label={result.verdict.verdict} 
        />
      </motion.div>

      <motion.div variants={itemVariants} className="w-full flex flex-col">
        {/* Styled Card instead of ASCII Box */}
        <div 
          className="bg-ink shadow-xl"
          style={{
            border: "1px solid var(--steel)",
            borderLeft: "3px solid var(--amber)",
            fontFamily: "JetBrains Mono, monospace"
          }}
        >
          {/* Header */}
          <div className="border-b border-steel p-6 flex flex-col gap-3">
            <div className="flex text-amber font-bold text-lg tracking-wider">
              CASE FILE #{shortId}
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-ghost uppercase tracking-widest">Claim</span>
              <span className="text-warm-white text-base leading-relaxed">"{result.structure.main_claim}"</span>
            </div>
          </div>

          {/* Content Rows */}
          <div className="flex flex-col font-sans">
            <SteelManPanel defense={result.defense} />
            <AttackPanel attack={result.attack} />
            <WeakestLinkPanel vulnerability={result.verdict.critical_vulnerability} />
            <StrengthPanel originalClaim={result.structure.main_claim} strengthenedClaim={result.verdict.stronger_version} />
          </div>
        </div>
        
        {/* Footer Actions & Timing */}
        <div className="flex justify-between items-center mt-6">
          <div className="text-xs text-ghost font-mono">
            Analysis completed in {(result.processing_time_ms / 1000).toFixed(1)} seconds
          </div>
          <button 
            onClick={() => window.print()}
            className="text-xs text-warm-white font-mono uppercase tracking-wider border border-steel hover:border-amber hover:text-amber px-4 py-2 rounded transition-colors"
          >
            Export PDF
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
