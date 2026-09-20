import React from "react";

interface SanketEmblemProps {
  className?: string;
  size?: number;
}

export const SanketEmblem: React.FC<SanketEmblemProps> = ({ className = "", size = 38 }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer Hex Shield */}
      <polygon
        points="24,2 44,12 44,36 24,46 4,36 4,12"
        fill="#FFFFFF"
        stroke="#0F766E"
        strokeWidth="1.5"
        strokeDasharray="4 2"
        opacity="0.8"
      />

      {/* Sovereign Gold Inner Ring */}
      <circle
        cx="24"
        cy="24"
        r="14"
        fill="url(#sanket-gold-grad)"
        fillOpacity="0.15"
        stroke="#A66A00"
        strokeWidth="1.2"
      />

      {/* Central 8-Ray Evidentiary Chakra */}
      <g stroke="#0F766E" strokeWidth="1.2">
        <line x1="24" y1="13" x2="24" y2="35" />
        <line x1="13" y1="24" x2="35" y2="24" />
        <line x1="16.2" y1="16.2" x2="31.8" y2="31.8" />
        <line x1="16.2" y1="31.8" x2="31.8" y2="16.2" />
      </g>

      {/* Core Cryptographic Eye / Node */}
      <circle cx="24" cy="24" r="4.5" fill="#F4F6F8" stroke="#0F766E" strokeWidth="1.5" />
      <circle cx="24" cy="24" r="1.8" fill="#16805B" />

      {/* Cardinal Sovereign Nodes */}
      <circle cx="24" cy="10" r="1.5" fill="#A66A00" />
      <circle cx="24" cy="38" r="1.5" fill="#A66A00" />
      <circle cx="10" cy="24" r="1.5" fill="#A66A00" />
      <circle cx="38" cy="24" r="1.5" fill="#A66A00" />

      <defs>
        <radialGradient id="sanket-gold-grad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#A66A00" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
        </radialGradient>
      </defs>
    </svg>
  );
};
