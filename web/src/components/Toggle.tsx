interface ToggleProps {
  id: string;
  checked: boolean;
  onChange: () => void;
  label: string;
}

/**
 * A switch built on a real checkbox input, so labels, keyboard focus and
 * screen readers keep working — only the visual is replaced.
 *
 * The on state is the runner's teal, not the brand blue. Two dozen blue
 * switches down the panel competed with the wordmark for the same hue;
 * the teal is the other half of the same mark, so the panel still reads
 * as one identity while "on" stops shouting.
 *
 * 16x28 with a 12 px knob. Travel is track minus knob minus both insets,
 * which is why the knob shifts by exactly 12 px.
 */
export default function Toggle({ id, checked, onChange, label }: ToggleProps) {
  return (
    <span className="relative inline-flex shrink-0">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        aria-label={label}
        className="peer h-4 w-7 shrink-0 cursor-pointer appearance-none rounded-full
                   bg-switch-off transition-colors duration-200
                   checked:bg-brand-accent focus-visible:outline-2
                   focus-visible:outline-offset-2 focus-visible:outline-brand"
      />
      {/* Knob. pointer-events-none so the input keeps the whole hit area. */}
      <span
        aria-hidden
        className="pointer-events-none absolute left-0.5 top-0.5 size-3 rounded-full
                   bg-white shadow-sm transition-transform duration-200
                   peer-checked:translate-x-3"
      />
    </span>
  );
}
