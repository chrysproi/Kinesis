interface ToggleProps {
  id: string;
  checked: boolean;
  onChange: () => void;
  label: string;
}

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
      <span
        aria-hidden
        className="pointer-events-none absolute left-0.5 top-0.5 size-3 rounded-full
                   bg-white shadow-sm transition-transform duration-200
                   peer-checked:translate-x-3"
      />
    </span>
  );
}
