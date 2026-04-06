// TODO: Implement persona switcher that persists the selected persona in session
// and passes it to all rule query requests.

type Persona = "developer" | "product" | "legal";

interface PersonaSwitcherProps {
  current?: Persona;
  onChange?: (persona: Persona) => void;
}

const PERSONAS: { value: Persona; label: string }[] = [
  { value: "developer", label: "Developer" },
  { value: "product", label: "Product" },
  { value: "legal", label: "Legal" },
];

export function PersonaSwitcher({
  current = "developer",
  onChange,
}: PersonaSwitcherProps) {
  return (
    <div>
      {PERSONAS.map(({ value, label }) => (
        <button
          key={value}
          disabled={current === value}
          onClick={() => onChange?.(value)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
