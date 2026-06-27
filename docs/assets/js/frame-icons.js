/** Airframe SVG icons and frame-name → category mapping for SITL model picker. */
(function (global) {
  const SVG = {
    quad_plus: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="40" cy="40" r="5" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="35" x2="40" y2="14"/><line x1="40" y1="45" x2="40" y2="66"/>
      <line x1="35" y1="40" x2="14" y2="40"/><line x1="45" y1="40" x2="66" y2="40"/>
      <circle cx="40" cy="14" r="6"/><circle cx="40" cy="66" r="6"/>
      <circle cx="14" cy="40" r="6"/><circle cx="66" cy="40" r="6"/>
    </svg>`,
    quad_x: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="40" cy="40" r="5" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="40" x2="18" y2="18"/><line x1="40" y1="40" x2="62" y2="18"/>
      <line x1="40" y1="40" x2="18" y2="62"/><line x1="40" y1="40" x2="62" y2="62"/>
      <circle cx="18" cy="18" r="6"/><circle cx="62" cy="18" r="6"/>
      <circle cx="18" cy="62" r="6"/><circle cx="62" cy="62" r="6"/>
    </svg>`,
    hexa: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="40" cy="40" r="5" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="40" x2="40" y2="12"/><line x1="40" y1="40" x2="17" y2="26"/>
      <line x1="40" y1="40" x2="17" y2="54"/><line x1="40" y1="40" x2="40" y2="68"/>
      <line x1="40" y1="40" x2="63" y2="54"/><line x1="40" y1="40" x2="63" y2="26"/>
      <circle cx="40" cy="12" r="5"/><circle cx="17" cy="26" r="5"/><circle cx="17" cy="54" r="5"/>
      <circle cx="40" cy="68" r="5"/><circle cx="63" cy="54" r="5"/><circle cx="63" cy="26" r="5"/>
    </svg>`,
    octa: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="40" cy="40" r="5" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="40" x2="40" y2="10"/><line x1="40" y1="40" x2="18" y2="18"/>
      <line x1="40" y1="40" x2="10" y2="40"/><line x1="40" y1="40" x2="18" y2="62"/>
      <line x1="40" y1="40" x2="40" y2="70"/><line x1="40" y1="40" x2="62" y2="62"/>
      <line x1="40" y1="40" x2="70" y2="40"/><line x1="40" y1="40" x2="62" y2="18"/>
      <circle cx="40" cy="10" r="4.5"/><circle cx="18" cy="18" r="4.5"/><circle cx="10" cy="40" r="4.5"/>
      <circle cx="18" cy="62" r="4.5"/><circle cx="40" cy="70" r="4.5"/><circle cx="62" cy="62" r="4.5"/>
      <circle cx="70" cy="40" r="4.5"/><circle cx="62" cy="18" r="4.5"/>
    </svg>`,
    octa_quad: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <rect x="22" y="22" width="36" height="36" rx="4" opacity=".25"/>
      <circle cx="40" cy="40" r="4" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="40" x2="28" y2="28"/><line x1="40" y1="40" x2="52" y2="28"/>
      <line x1="40" y1="40" x2="28" y2="52"/><line x1="40" y1="40" x2="52" y2="52"/>
      <circle cx="28" cy="28" r="5"/><circle cx="52" cy="28" r="5"/>
      <circle cx="28" cy="52" r="5"/><circle cx="52" cy="52" r="5"/>
      <circle cx="22" cy="40" r="4"/><circle cx="58" cy="40" r="4"/>
      <circle cx="40" cy="22" r="4"/><circle cx="40" cy="58" r="4"/>
    </svg>`,
    tri: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="40" cy="44" r="5" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="44" x2="16" y2="58"/><line x1="40" y1="44" x2="64" y2="58"/>
      <line x1="40" y1="44" x2="40" y2="14"/>
      <circle cx="16" cy="58" r="6"/><circle cx="64" cy="58" r="6"/><circle cx="40" cy="14" r="6"/>
      <line x1="40" y1="58" x2="40" y2="68" stroke-dasharray="3 3"/>
    </svg>`,
    y6: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="40" cy="40" r="5" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="40" x2="22" y2="22"/><line x1="40" y1="40" x2="58" y2="22"/>
      <line x1="40" y1="40" x2="22" y2="58"/><line x1="40" y1="40" x2="58" y2="58"/>
      <circle cx="22" cy="22" r="5"/><circle cx="58" cy="22" r="5"/>
      <circle cx="22" cy="58" r="5"/><circle cx="58" cy="58" r="5"/>
      <circle cx="22" cy="32" r="4"/><circle cx="58" cy="32" r="4"/>
    </svg>`,
    coax: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="40" cy="40" r="8" fill="currentColor" opacity=".2"/>
      <circle cx="40" cy="40" r="5" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="40" x2="40" y2="12"/><line x1="40" y1="40" x2="40" y2="68"/>
      <circle cx="40" cy="12" r="7"/><circle cx="40" cy="68" r="7"/>
      <circle cx="40" cy="12" r="3" opacity=".5"/><circle cx="40" cy="68" r="3" opacity=".5"/>
    </svg>`,
    heli: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <ellipse cx="40" cy="42" rx="14" ry="10"/>
      <line x1="12" y1="32" x2="68" y2="32"/><line x1="40" y1="32" x2="40" y2="18"/>
      <circle cx="40" cy="18" r="3"/>
      <line x1="40" y1="52" x2="52" y2="62" stroke-width="1.5"/>
      <line x1="40" y1="52" x2="28" y2="58" stroke-width="1.5"/>
    </svg>`,
    plane: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round">
      <path d="M40 10 L12 38 L40 32 L68 38 Z"/>
      <line x1="40" y1="32" x2="40" y2="68"/>
      <line x1="28" y1="48" x2="52" y2="48"/>
      <path d="M34 68 L40 58 L46 68" opacity=".6"/>
    </svg>`,
    glider: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round">
      <path d="M40 14 L10 36 L40 30 L70 36 Z"/>
      <line x1="40" y1="30" x2="40" y2="66"/>
      <path d="M36 66 L40 58 L44 66"/>
    </svg>`,
    quadplane: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <path d="M40 18 L16 34 L40 30 L64 34 Z" opacity=".7"/>
      <circle cx="40" cy="46" r="4" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="42" x2="40" y2="28"/><line x1="40" y1="50" x2="40" y2="64"/>
      <line x1="36" y1="46" x2="20" y2="46"/><line x1="44" y1="46" x2="60" y2="46"/>
      <circle cx="40" cy="28" r="4"/><circle cx="40" cy="64" r="4"/>
      <circle cx="20" cy="46" r="4"/><circle cx="60" cy="46" r="4"/>
    </svg>`,
    tailsitter: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="34" y="16" width="12" height="48" rx="3"/>
      <path d="M22 64 L40 52 L58 64"/>
      <circle cx="40" cy="24" r="4" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="28" x2="40" y2="8"/><circle cx="40" cy="8" r="5"/>
    </svg>`,
    rover: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <rect x="14" y="32" width="52" height="22" rx="5"/>
      <circle cx="24" cy="58" r="8"/><circle cx="56" cy="58" r="8"/>
      <line x1="30" y1="32" x2="36" y2="22"/><line x1="50" y1="32" x2="44" y2="22"/>
    </svg>`,
    boat: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round">
      <path d="M14 48 Q40 62 66 48 L58 38 L22 38 Z"/>
      <line x1="40" y1="38" x2="40" y2="18"/>
      <path d="M32 18 L40 10 L48 18"/>
    </svg>`,
    balancebot: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="30" y="24" width="20" height="28" rx="4"/>
      <circle cx="40" cy="58" r="10"/>
      <line x1="40" y1="58" x2="40" y2="68"/>
    </svg>`,
    blimp: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2">
      <ellipse cx="40" cy="36" rx="26" ry="14"/>
      <rect x="34" y="48" width="12" height="10" rx="2"/>
      <line x1="40" y1="58" x2="40" y2="66"/>
    </svg>`,
    sub: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2">
      <ellipse cx="40" cy="40" rx="28" ry="12"/>
      <circle cx="54" cy="40" r="3" fill="currentColor"/>
      <rect x="36" y="28" width="8" height="6" rx="1"/>
      <path d="M12 40 Q8 34 12 28" opacity=".5"/>
    </svg>`,
    tracker: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M40 58 L40 28"/><circle cx="40" cy="24" r="6"/>
      <path d="M24 58 L56 58"/><rect x="20" y="58" width="40" height="8" rx="2"/>
      <path d="M40 28 L52 18" opacity=".6"/>
    </svg>`,
    single: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="40" cy="40" r="6" fill="currentColor" opacity=".4"/>
      <line x1="40" y1="34" x2="40" y2="12"/><circle cx="40" cy="12" r="8"/>
      <line x1="34" y1="46" x2="20" y2="58"/><line x1="46" y1="46" x2="60" y2="58"/>
    </svg>`,
    default: `<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="40" cy="40" r="20" opacity=".2"/>
      <path d="M40 26 v14 l8 6"/><circle cx="40" cy="40" r="3" fill="currentColor"/>
    </svg>`,
  };

  const LABELS = {
    quad_plus: "Quadcopter (+)",
    quad_x: "Quadcopter (X)",
    hexa: "Hexacopter",
    octa: "Octocopter",
    octa_quad: "Octo-Quad",
    tri: "Tricopter",
    y6: "Y6 Copter",
    coax: "Coaxial",
    heli: "Helicopter",
    plane: "Fixed Wing",
    glider: "Glider",
    quadplane: "QuadPlane / VTOL",
    tailsitter: "Tailsitter",
    rover: "Ground Rover",
    boat: "Boat",
    balancebot: "Balance Bot",
    blimp: "Airship / Blimp",
    sub: "Submarine",
    tracker: "Antenna Tracker",
    single: "Single Rotor",
    default: "Generic Airframe",
  };

  function category(frame, vehicle) {
    const f = (frame || "").toLowerCase();
    const v = vehicle || "";

    if (v === "PX4") {
      if (f.includes("vtol")) return "quadplane";
      if (f.includes("rover")) return "rover";
      if (f.includes("hexa")) return "hexa";
      if (f.includes("quad")) return "quad_x";
      return "default";
    }
    if (v === "AntennaTracker" || f === "tracker") return "tracker";
    if (v === "Blimp" || f.startsWith("blimp")) return "blimp";
    if (v === "ArduSub" || f.includes("sub") || f.includes("bluerov") || f.includes("6dof")) return "sub";
    if (v === "Rover") {
      if (f.includes("boat") || f.includes("sail")) return "boat";
      if (f.includes("balance")) return "balancebot";
      return "rover";
    }
    if (f.includes("quadplane") || f.startsWith("tilt") || f === "cl84") return "quadplane";
    if (f.includes("tailsitter")) return "tailsitter";
    if (f.includes("glider")) return "glider";
    if (v === "ArduPlane" || f.startsWith("plane") || f === "firefly" || f.includes("zephyr") || f.includes("jsbsim")) return "plane";
    if (f.startsWith("heli") || v === "Helicopter") return "heli";
    if (f.includes("coax")) return "coax";
    if (f.includes("octa-quad") || f.includes("octaquad")) return "octa_quad";
    if (f.startsWith("octa") || f.includes("dodeca") || f.includes("dotriaconta") || f.includes("hexadeca")) return "octa";
    if (f.startsWith("hexa") || f === "hexax") return "hexa";
    if (f === "y6" || f.startsWith("y6")) return "y6";
    if (f === "tri" || f.endsWith("-tri")) return "tri";
    if (f === "singlecopter" || f === "copter-single" || f.includes("single")) return "single";
    if (f === "+" || f === "quad" || f.includes("bfx") || f === "cwx") return "quad_plus";
    if (f === "x" || f.endsWith("-x") || f.includes("djix")) return "quad_x";
    if (v === "ArduCopter") return f.includes("x") ? "quad_x" : "quad_plus";
    return "default";
  }

  function getFrameMeta(frame, vehicle) {
    const cat = category(frame, vehicle);
    return {
      category: cat,
      label: LABELS[cat] || LABELS.default,
      description: frame,
      svg: SVG[cat] || SVG.default,
    };
  }

  global.FrameIcons = { getFrameMeta, category, SVG, LABELS };
})(window);
