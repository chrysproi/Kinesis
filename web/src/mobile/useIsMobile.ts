import { useEffect, useState } from "react";

const QUERY = "(max-width: 767px)";

/** Whether to render the phone layout. */
export function useIsMobile() {
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== "undefined" && window.matchMedia(QUERY).matches,
  );

  useEffect(() => {
    const query = window.matchMedia(QUERY);
    const update = () => setIsMobile(query.matches);

    query.addEventListener("change", update);
    update();

    return () => query.removeEventListener("change", update);
  }, []);

  return isMobile;
}
