/** The icon artwork: lucide SVGs, and the sprites lucide has no glyph for. */

import amphora from "lucide-static/icons/amphora.svg?raw";
import waypoints from "lucide-static/icons/waypoints.svg?raw";
import toyBrick from "lucide-static/icons/toy-brick.svg?raw";
import bookOpen from "lucide-static/icons/book-open.svg?raw";
import flaskConical from "lucide-static/icons/flask-conical.svg?raw";
import school from "lucide-static/icons/school.svg?raw";
import briefcase from "lucide-static/icons/briefcase.svg?raw";
import building2 from "lucide-static/icons/building-2.svg?raw";
import flame from "lucide-static/icons/flame.svg?raw";
import goal from "lucide-static/icons/goal.svg?raw";
import hospital from "lucide-static/icons/hospital.svg?raw";
import mail from "lucide-static/icons/mail.svg?raw";
import scale from "lucide-static/icons/scale.svg?raw";
import shield from "lucide-static/icons/shield.svg?raw";
import shoppingBag from "lucide-static/icons/shopping-bag.svg?raw";
import shoppingCart from "lucide-static/icons/shopping-cart.svg?raw";
import store from "lucide-static/icons/store.svg?raw";
import trophy from "lucide-static/icons/trophy.svg?raw";
import bike from "lucide-static/icons/bike.svg?raw";
import keyRound from "lucide-static/icons/key-round.svg?raw";
import arrowLeftRight from "lucide-static/icons/arrow-left-right.svg?raw";
import busFront from "lucide-static/icons/bus-front.svg?raw";
import carTaxiFront from "lucide-static/icons/car-taxi-front.svg?raw";
import castle from "lucide-static/icons/castle.svg?raw";
import church from "lucide-static/icons/church.svg?raw";
import circleParking from "lucide-static/icons/circle-parking.svg?raw";
import drama from "lucide-static/icons/drama.svg?raw";
import frame from "lucide-static/icons/frame.svg?raw";
import graduationCap from "lucide-static/icons/graduation-cap.svg?raw";
import info from "lucide-static/icons/info.svg?raw";
import landmark from "lucide-static/icons/landmark.svg?raw";
import library from "lucide-static/icons/library.svg?raw";
import ship from "lucide-static/icons/ship.svg?raw";
import squareParking from "lucide-static/icons/square-parking.svg?raw";
import target from "lucide-static/icons/target.svg?raw";
import wrench from "lucide-static/icons/wrench.svg?raw";

export const SVG: Record<string, string> = {
  amphora,
  waypoints,
  "toy-brick": toyBrick,
  "book-open": bookOpen,
  "flask-conical": flaskConical,
  school,
  briefcase,
  "building-2": building2,
  flame,
  goal,
  hospital,
  mail,
  scale,
  shield,
  "shopping-bag": shoppingBag,
  "shopping-cart": shoppingCart,
  store,
  trophy,
  "arrow-left-right": arrowLeftRight,
  bike,
  "bus-front": busFront,
  "car-taxi-front": carTaxiFront,
  castle,
  church,
  "circle-parking": circleParking,
  drama,
  frame,
  "graduation-cap": graduationCap,
  info,
  landmark,
  library,
  ship,
  "square-parking": squareParking,
  target,
  wrench,
};

/** The drawing instructions inside a lucide file, without its <svg>. */
const inner = (svg: string) =>
  svg.replace(/[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>[\s\S]*$/, "");

const wrap = (body: string) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">${body}</svg>`;

/** Sprites lucide has no glyph for. Undefined for anything it does. */
export const BUILT: Record<string, ((color: string) => string) | undefined> = {
  "bike-parking": (c) => `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="${c}" stroke-width="2.3" stroke-linecap="round"
         stroke-linejoin="round">
      <path d="M3 13V1.8h4.1a2.9 2.9 0 0 1 0 5.8H3"/>
      <g transform="translate(7.6 8.4) scale(0.7)">${inner(bike)}</g>
    </svg>`,

  "bike-rental": (c) => `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="${c}" stroke-width="2.3" stroke-linecap="round"
         stroke-linejoin="round">
      <g transform="translate(-1.6 -1.9) scale(0.68)">${inner(keyRound)}</g>
      <g transform="translate(7.6 8.4) scale(0.7)">${inner(bike)}</g>
    </svg>`,

  "stop-dot": (c) => wrap(`
    <circle cx="10" cy="10" r="4.5" fill="${c}" stroke="${c}" stroke-width="2"/>`),

  "stop-ring": (c) => wrap(`
    <circle cx="10" cy="10" r="5" fill="#ffffff" stroke="${c}" stroke-width="3"/>`),

  "stop-split": (c) => wrap(`
    <circle cx="10" cy="10" r="7" fill="#ffffff" stroke="${c}" stroke-width="3"/>
    <path d="M 10 3 A 7 7 0 0 0 10 17 Z" fill="${c}"/>
    <line x1="10" y1="3" x2="10" y2="17" stroke="${c}" stroke-width="1.2"/>`),

  "stop-bullseye": (c) => wrap(`
    <circle cx="10" cy="10" r="7" fill="#ffffff" stroke="${c}" stroke-width="2.2"/>
    <circle cx="10" cy="10" r="2.6" fill="${c}" stroke="#ffffff" stroke-width="0.8"/>`),

  "stop-minor": (c) => wrap(`
    <circle cx="10" cy="10" r="2.4" fill="${c}"/>`),

  "metro-m": (color) => `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
         fill="none" stroke="${color}" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="9.5" fill="#ffffff"/>
      <path d="M7.5 16.5V8l4.5 5.5L16.5 8v8.5"/>
    </svg>`,
};

/** The same sprites as inline SVG, for the legend. */
export const builtSvg = (name: string | null | undefined, color: string) =>
  (name && BUILT[name]?.(color)) || null;
