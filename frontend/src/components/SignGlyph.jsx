export default function SignGlyph({ id }) {
  const common = {
    fill: "none",
    stroke: "#1b2430",
    strokeWidth: 4,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };
  return (
    <svg className="hand-svg" viewBox="0 0 160 90" aria-hidden>
      <rect x="4" y="4" width="152" height="82" rx="12" fill="#f4efe4" />
      {id === "HELLO" && (
        <g transform="translate(40 18)" {...common}>
          <path d="M40 62c0-20-8-36-8-48" />
          <path d="M48 62c0-22 0-40 8-52" />
          <path d="M56 62c8-18 16-28 16-40" />
          <path d="M32 62c-6-16-16-22-22-28" />
          <path d="M20 20h28" />
        </g>
      )}
      {id === "STOP" && (
        <g transform="translate(48 16)" {...common}>
          <path d="M32 64V18" />
          <path d="M20 64V28" />
          <path d="M44 64V24" />
          <path d="M56 64V32" />
          <path d="M8 50h12" />
          <rect x="18" y="8" width="28" height="14" rx="4" />
        </g>
      )}
      {id === "YES" && (
        <g transform="translate(55 20)" {...common}>
          <circle cx="28" cy="38" r="18" />
          <path d="M28 8v12" />
        </g>
      )}
      {id === "NO" && (
        <g transform="translate(40 18)" {...common}>
          <path d="M40 70V22" />
          <path d="M18 48h20" />
          <path d="M28 22c18-10 36 0 44 12" />
        </g>
      )}
      {id === "THANK_YOU" && (
        <g transform="translate(36 14)" {...common}>
          <circle cx="44" cy="18" r="10" />
          <path d="M44 32c-16 8-24 28-8 42 22 6 40-10 36-28" />
        </g>
      )}
      {id === "PLEASE" && (
        <g transform="translate(40 16)" {...common}>
          <circle cx="40" cy="40" r="22" strokeDasharray="6 6" />
          <path d="M40 40l14-10" />
        </g>
      )}
      {id === "HELP" && (
        <g transform="translate(28 22)" {...common}>
          <rect x="8" y="28" width="44" height="22" rx="6" />
          <circle cx="72" cy="40" r="16" />
        </g>
      )}
      {id === "WATER" && (
        <g transform="translate(42 16)" {...common}>
          <path d="M16 70V22" />
          <path d="M36 70V16" />
          <path d="M56 70V22" />
        </g>
      )}
      {id === "NAME" && (
        <g transform="translate(48 16)" {...common}>
          <path d="M24 70V18" />
          <path d="M44 70V18" />
          <path d="M12 36h20" />
        </g>
      )}
      {id === "GOOD" && (
        <g transform="translate(55 14)" {...common}>
          <path d="M20 38h28v24H20z" />
          <path d="M28 38V16c0-8 16-8 16 4v18" />
        </g>
      )}
    </svg>
  );
}
