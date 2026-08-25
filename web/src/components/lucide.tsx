import {
  Amphora,
  ArrowLeftRight,
  Bike,
  BookOpen,
  Briefcase,
  Building2,
  BusFront,
  CarTaxiFront,
  Castle,
  Church,
  CircleParking,
  Drama,
  Flame,
  FlaskConical,
  Frame,
  Goal,
  GraduationCap,
  Hospital,
  Info,
  Landmark,
  Library,
  Mail,
  Scale,
  School,
  Shield,
  Ship,
  ShoppingBag,
  ShoppingCart,
  SquareParking,
  Store,
  Target,
  ToyBrick,
  Trophy,
  Waypoints,
  Wrench,
  type LucideIcon,
} from "lucide-react";

/**
 * The same lucide set the map draws, as React components.
 *
 * lucide-react belongs in the DOM while the map uses lucide-static
 * rasters. Sharing the icon set is what lets the sidebar and legend act
 * as a key: a row shows exactly the mark it switches on.
 *
 * Keyed by the lucide name Python emits, so a sprite added in palette.py
 * needs one line here and nowhere else. A missing entry renders nothing
 * rather than throwing — which is why `lucideFor` is the only way in.
 */
const ICONS: Record<string, LucideIcon> = {
  amphora: Amphora,
  "arrow-left-right": ArrowLeftRight,
  bike: Bike,
  "book-open": BookOpen,
  briefcase: Briefcase,
  "building-2": Building2,
  "bus-front": BusFront,
  "car-taxi-front": CarTaxiFront,
  castle: Castle,
  church: Church,
  "circle-parking": CircleParking,
  drama: Drama,
  flame: Flame,
  "flask-conical": FlaskConical,
  frame: Frame,
  goal: Goal,
  "graduation-cap": GraduationCap,
  hospital: Hospital,
  info: Info,
  landmark: Landmark,
  library: Library,
  mail: Mail,
  scale: Scale,
  school: School,
  shield: Shield,
  ship: Ship,
  "shopping-bag": ShoppingBag,
  "shopping-cart": ShoppingCart,
  "square-parking": SquareParking,
  store: Store,
  target: Target,
  "toy-brick": ToyBrick,
  trophy: Trophy,
  waypoints: Waypoints,
  wrench: Wrench,
};

export const lucideFor = (name: string | null | undefined) =>
  (name && ICONS[name]) || null;
