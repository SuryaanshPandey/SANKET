import React from "react";

interface IconProps {
  className?: string;
  size?: number;
}

// 1. Suspect / Accused / Arrestee (Crimson reticle with silhouette)
export const SuspectIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <circle cx="12" cy="12" r="9.5" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3 2" />
    <circle cx="12" cy="9" r="3" stroke="#ef4444" strokeWidth="1.5" fill="rgba(239, 68, 68, 0.2)" />
    <path
      d="M6.5 18c0-3 2.5-4.5 5.5-4.5s5.5 1.5 5.5 4.5"
      stroke="#ef4444"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    <path d="M12 2v2m0 16v2M2 12h2m16 0h2" stroke="#ef4444" strokeWidth="1.2" />
  </svg>
);

// 2. Investigating Officer / SHO (Police Shield with Star)
export const OfficerIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <path
      d="M12 2L4 5v6c0 5.5 3.5 10.5 8 11.5 4.5-1 8-6 8-11.5V5l-8-3z"
      stroke="#00f0ff"
      strokeWidth="1.5"
      fill="rgba(0, 240, 255, 0.12)"
    />
    <polygon
      points="12,7 13.5,10.5 17,11 14.5,13.5 15,17 12,15 9,17 9.5,13.5 7,11 10.5,10.5"
      fill="#eab308"
    />
  </svg>
);

// 3. Pancha Witness (Sec 100(4) CrPC Independent Eye & Seal)
export const PanchaWitnessIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <path
      d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7z"
      stroke="#10b981"
      strokeWidth="1.5"
      fill="rgba(16, 185, 129, 0.12)"
    />
    <circle cx="12" cy="12" r="3.5" stroke="#10b981" strokeWidth="1.5" />
    <circle cx="12" cy="12" r="1.5" fill="#10b981" />
  </svg>
);

// 4. Seized Property & Material Evidence (Parcel with Official Brass Seal)
export const SeizedEvidenceIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <path
      d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
      stroke="#f59e0b"
      strokeWidth="1.5"
      fill="rgba(245, 158, 11, 0.12)"
    />
    <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="#f59e0b" strokeWidth="1.2" />
    <line x1="12" y1="22.08" x2="12" y2="12" stroke="#f59e0b" strokeWidth="1.2" />
    <circle cx="12" cy="12" r="2.5" fill="#eab308" />
  </svg>
);

// 5. Recovery Location & Crime Scene (Tactical Radar Pin)
export const CrimeLocationIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <path
      d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7z"
      stroke="#8b5cf6"
      strokeWidth="1.5"
      fill="rgba(139, 92, 246, 0.15)"
    />
    <circle cx="12" cy="9" r="2.5" stroke="#00f0ff" strokeWidth="1.2" fill="#06080e" />
  </svg>
);

// 6. Medico-Legal / Injury Report (Clinical Cross with Cadence Shield)
export const MedicalLegalIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <rect
      x="3"
      y="3"
      width="18"
      height="18"
      rx="4"
      stroke="#ef4444"
      strokeWidth="1.5"
      fill="rgba(239, 68, 68, 0.12)"
    />
    <path d="M12 7v10M7 12h10" stroke="#f8fafc" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

// 7. FSL Cyber & Digital Evidence (Microchip with SHA Hash Key)
export const ForensicCyberIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <rect
      x="5"
      y="5"
      width="14"
      height="14"
      rx="2"
      stroke="#00f0ff"
      strokeWidth="1.5"
      fill="rgba(0, 240, 255, 0.12)"
    />
    <path
      d="M9 9h6v6H9zM9 1v4m6-4v4M9 19v4m6-4v4M1 9h4m-4 6h4M19 9h4m-4 6h4"
      stroke="#00f0ff"
      strokeWidth="1.2"
    />
    <circle cx="12" cy="12" r="1.5" fill="#10b981" />
  </svg>
);

// 8. Sovereign Court & Judicial Record
export const JudicialCourtIcon: React.FC<IconProps> = ({ className = "", size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <line x1="2" y1="20" x2="22" y2="20" stroke="#eab308" strokeWidth="2" />
    <path d="M12 2L3 7h18l-9-5z" stroke="#eab308" strokeWidth="1.5" fill="rgba(234, 179, 8, 0.15)" />
    <line x1="5" y1="7" x2="5" y2="20" stroke="#eab308" strokeWidth="1.5" />
    <line x1="10" y1="7" x2="10" y2="20" stroke="#eab308" strokeWidth="1.5" />
    <line x1="14" y1="7" x2="14" y2="20" stroke="#eab308" strokeWidth="1.5" />
    <line x1="19" y1="7" x2="19" y2="20" stroke="#eab308" strokeWidth="1.5" />
  </svg>
);
