/* Line icons, 1.6 stroke, 24 grid. No mosque silhouettes — the subject is the learning journey. */
const P = { fill: "none", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, viewBox: "0 0 24 24" };

export const IconCompass = () => (<svg {...P}><circle cx="12" cy="12" r="9" /><path d="M15.5 8.5l-2 5-5 2 2-5z" /></svg>);
export const IconCircle = () => (<svg {...P}><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="2.5" /><path d="M12 3.5v3M12 17.5v3M3.5 12h3M17.5 12h3" /></svg>);
export const IconStudents = () => (<svg {...P}><circle cx="9" cy="8" r="3.2" /><path d="M3.5 19c.6-3.3 2.9-5 5.5-5s4.9 1.7 5.5 5" /><circle cx="17" cy="9" r="2.4" /><path d="M15.5 14.2c2.2.2 4 1.7 4.5 4.3" /></svg>);
export const IconTeacher = () => (<svg {...P}><path d="M4 5h16v10H4z" /><path d="M8 19h8M12 15v4" /><path d="M7.5 9h6M7.5 12h9" /></svg>);
export const IconModules = () => (<svg {...P}><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><path d="M17 14v6M14 17h6" /></svg>);
export const IconBook = () => (<svg {...P}><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z" /><path d="M4 18V5.5M8 7h8M8 10.5h8" /></svg>);
export const IconArrow = () => (<svg {...P}><path d="M5 12h14M13 6l6 6-6 6" /></svg>);
export const IconCheck = () => (<svg {...P}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>);
export const IconX = () => (<svg {...P}><path d="M6 6l12 12M18 6L6 18" /></svg>);
export const IconGlobe = () => (<svg {...P}><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" /></svg>);
export const IconLogout = () => (<svg {...P}><path d="M10 4H5v16h5M14 8l4 4-4 4M18 12H9" /></svg>);
