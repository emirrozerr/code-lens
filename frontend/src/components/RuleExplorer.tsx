// TODO: Implement rule explorer component using React Flow for graph visualization
// and Mermaid.js for sequence/component diagrams.

interface Rule {
  id: string;
  statement: string;
  domain: string;
  sourceFile: string;
  sourceLine: number;
}

interface RuleExplorerProps {
  rules?: Rule[];
}

export function RuleExplorer({ rules = [] }: RuleExplorerProps) {
  return (
    <div>
      <h2>Rule Explorer</h2>
      {rules.length === 0 ? (
        <p>No rules found.</p>
      ) : (
        <ul>
          {rules.map((rule) => (
            <li key={rule.id}>{rule.statement}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
