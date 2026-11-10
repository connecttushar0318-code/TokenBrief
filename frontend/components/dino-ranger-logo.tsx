"use client";

import React from "react";

interface DinoRangerLogoProps {
  size?: number | string;
  className?: string;
  animated?: boolean;
}

export function DinoRangerLogo({
  size = 36,
  className = "",
  animated = true,
}: DinoRangerLogoProps) {
  const pixelSize = typeof size === "number" ? `${size}px` : size;

  return (
    <div
      style={{ width: pixelSize, height: pixelSize }}
      className={`relative inline-flex shrink-0 items-center justify-center ${
        animated ? "transition-all duration-300 hover:scale-110 hover:drop-shadow-[0_0_12px_rgba(245,158,11,0.65)]" : ""
      } ${className}`}
      title="TokenBrief — Dino Power Ranger Edition"
    >
      <svg
        viewBox="0 0 100 100"
        width="100%"
        height="100%"
        className="overflow-visible select-none"
      >
        <defs>
          {/* Background Badge Gradient */}
          <linearGradient id="shieldGradComp" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0f172a" />
            <stop offset="50%" stop-color="#1e1b4b" />
            <stop offset="100%" stop-color="#090d16" />
          </linearGradient>

          {/* Metallic Gold Power Crest */}
          <linearGradient id="goldGradComp" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fef08a" />
            <stop offset="35%" stop-color="#f59e0b" />
            <stop offset="70%" stop-color="#d97706" />
            <stop offset="100%" stop-color="#78350f" />
          </linearGradient>

          {/* Dino Red Armor Gradient */}
          <linearGradient id="dinoRedComp" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#ff2e63" />
            <stop offset="40%" stop-color="#dc2626" />
            <stop offset="85%" stop-color="#991b1b" />
            <stop offset="100%" stop-color="#450a0a" />
          </linearGradient>

          {/* Cyber Cyan Visor Glow */}
          <linearGradient id="visorCyanComp" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#22d3ee" />
            <stop offset="50%" stop-color="#38bdf8" />
            <stop offset="100%" stop-color="#0284c7" />
          </linearGradient>

          {/* Drop Shadow Filter */}
          <filter id="rangerGlowComp" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#f59e0b" flood-opacity="0.45" />
            <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#dc2626" flood-opacity="0.35" />
          </filter>
        </defs>

        {/* Outer Ranger Power Coin Octagon */}
        <polygon
          points="50,3 93,22 93,78 50,97 7,78 7,22"
          fill="url(#shieldGradComp)"
          stroke="url(#goldGradComp)"
          strokeWidth="3.2"
          strokeLinejoin="round"
          filter="url(#rangerGlowComp)"
        />

        {/* Inner Armor Border Facet */}
        <polygon
          points="50,8 88,25 88,75 50,92 12,75 12,25"
          fill="none"
          stroke="#f59e0b"
          strokeWidth="0.8"
          strokeOpacity="0.5"
          strokeDasharray="3 1.5"
        />

        {/* T-Rex Dino Ranger Brow & Horn Crest (Forms the Top Crown & "T" Crossbar) */}
        <path
          d="M 18,24 L 50,11 L 82,24 L 74,35 L 59,32 L 50,22 L 41,32 L 26,35 Z"
          fill="url(#goldGradComp)"
          stroke="#78350f"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Central Forehead Dino Power Gem (Diamond) */}
        <polygon points="50,14 55,22 50,29 45,22" fill="#22d3ee" stroke="#ffffff" strokeWidth="1" />

        {/* Dino Ranger Main Helmet Faceplate (Crimson Red Armor) */}
        {/* Left Side: Styled as Sharp "T" Stem and T-Rex Jaw */}
        <path
          d="M 27,37 L 46,34 L 46,65 L 36,65 L 36,52 L 25,52 L 21,43 Z"
          fill="url(#dinoRedComp)"
          stroke="url(#goldGradComp)"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Central "T" Stem Accent Plate */}
        <polygon
          points="44,34 50,26 56,34 54,65 46,65"
          fill="url(#goldGradComp)"
          stroke="#78350f"
          strokeWidth="0.8"
        />

        {/* Right Side: Styled as Sharp Dino Ranger "B" With Dual Mechanical Energy Loops */}
        <path
          d="M 54,34 L 75,34 C 83,34 83,48 76,49 C 84,50 84,65 74,65 L 54,65 Z"
          fill="url(#dinoRedComp)"
          stroke="url(#goldGradComp)"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* "B" Upper Cutout (Dino Eye Socket / Top Armor Loop) */}
        <polygon points="62,40 72,40 73,45 62,45" fill="#0f172a" stroke="url(#goldGradComp)" strokeWidth="0.8" />
        {/* "B" Lower Cutout (Dino Jaw Vent / Bottom Armor Loop) */}
        <polygon points="62,51 72,51 73,59 62,59" fill="#0f172a" stroke="url(#goldGradComp)" strokeWidth="0.8" />

        {/* Aggressive Dino Ranger Visor (Cyan Energy Slits Behind the Crest) */}
        <polygon points="26,42 42,40 42,46 29,48" fill="url(#visorCyanComp)" />
        <polygon points="58,40 74,42 71,48 58,46" fill="url(#visorCyanComp)" />

        {/* Dino T-Rex Mechanical Fangs / Serrated Battle Teeth (Interlocking Gold & White) */}
        <polygon points="34,67 38,75 42,67" fill="#ffffff" stroke="url(#goldGradComp)" strokeWidth="0.6" />
        <polygon points="43,67 47,77 50,67" fill="#ffffff" stroke="url(#goldGradComp)" strokeWidth="0.6" />
        <polygon points="50,67 53,77 57,67" fill="#ffffff" stroke="url(#goldGradComp)" strokeWidth="0.6" />
        <polygon points="58,67 62,75 66,67" fill="#ffffff" stroke="url(#goldGradComp)" strokeWidth="0.6" />

        {/* Lower Dino Chin Guard & Lightning Bolt Chevron (Power Ranger Apex) */}
        <polygon
          points="50,91 32,77 43,77 39,83 50,81 46,88"
          fill="url(#goldGradComp)"
          stroke="#78350f"
          strokeWidth="0.6"
        />
        <polygon
          points="50,91 68,77 57,77 61,83 50,81 54,88"
          fill="url(#goldGradComp)"
          stroke="#78350f"
          strokeWidth="0.6"
        />

        {/* Highlight Sparks for Power Ranger Energy */}
        <circle cx="50" cy="22" r="1.5" fill="#ffffff" />
        <circle cx="28" cy="44" r="1" fill="#ffffff" />
        <circle cx="72" cy="44" r="1" fill="#ffffff" />
      </svg>
    </div>
  );
}
